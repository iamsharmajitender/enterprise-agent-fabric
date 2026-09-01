"""Run lifecycle orchestration for Agent Runtime.

Owns the durable run identity (RunPin) and the high-level start/resume API.
Does NOT own LangGraph stage logic — that lives under app.graph.

Lifecycle for a new run:
  validate → idempotency → hydrate → persist → snapshot → schedule → execute

schedule_run is injectable:
  - production: run_in_background (daemon thread, 202 returns before graph finishes)
  - tests:     run_inline (same thread, deterministic)
"""

import contextvars
import logging
import os
import threading
from collections.abc import Callable
from typing import Any
from uuid import uuid4

from app import telemetry
from app.agents.audit_client import emit_async, hydrate_snapshot, run_terminal, stage_completed
from app.agents.hydrate import CataloguePort, HydrateError, RegistryPort, hydrate
from app.agents.jobs_client import JobsPort
from app.agents.prefetch import PrefetchPort
from app.core.checkpoint import (
    checkpoint_goal,
    checkpoint_resume_index,
    loop_resume_step,
    parse_checkpoint_resume,
)
from app.core.execution import GraphPort, run_loop
from app.core.memory import (
    memory_profile,
    notes_from_working,
    persist_stage,
    save_loop,
    save_working,
    slots_from_working,
    working_payload,
)
from app.core.session_ids import is_jobs_session
from app.core.state import RunPin, RunStore
from app.graph.human_gate import parse_gate_packet
from app.graph.llm import LlmPort
from app.graph.state import append_customer_reply
from app.graph.subagent_gate import merge_subagent_packet, parse_subagent_packet, poll_subagents
from app.graph.workflow import build_agent_loop, build_tool_graph
from app.tools.invoker import ToolInvoker

log = logging.getLogger(__name__)

# How graph work is kicked off after the pin is durable.
ScheduleRun = Callable[[Callable[[], None]], None]


def run_inline(fn: Callable[[], None]) -> None:
    """Run on the calling thread (tests / TestClient — completion before 202 returns)."""
    fn()


def run_in_background(fn: Callable[[], None]) -> None:
    """Fire-and-forget daemon thread; copy contextvars so request_id/telemetry survive."""
    ctx = contextvars.copy_context()

    def _safe() -> None:
        try:
            ctx.run(fn)
        except Exception:
            # Never let an uncaught graph error kill the worker thread silently.
            log.exception("background run failed")

    threading.Thread(target=_safe, name="ar-run-execute", daemon=True).start()


class RunService:
    """Application service behind POST /v1/runs and resume/status.

    Dependencies are ports so tests can inject fakes; production wires HTTP clients
    in app.api.app.build_app().
    """

    def __init__(
        self,
        store: RunStore,
        catalogue: CataloguePort,
        registry: RegistryPort,
        graph: GraphPort | None = None,
        invoker: ToolInvoker | None = None,
        llm: LlmPort | None = None,
        prefetch: PrefetchPort | None = None,
        jobs: JobsPort | None = None,
        schedule_run: ScheduleRun | None = None,
    ) -> None:
        self._store = store
        self._catalogue = catalogue
        self._registry = registry
        # Optional injected compiled graph (tests). If set, skips build_agent_loop / build_tool_graph.
        self._graph = graph
        self._invoker = invoker
        self._llm = llm
        self._prefetch = prefetch
        self._jobs = jobs
        # Default production: background. create_app() overrides to run_inline for tests.
        self._schedule_run = schedule_run or run_in_background

    # --- start ---------------------------------------------------------------

    def start(self, body: dict[str, Any]) -> str:
        """Start a new agent run.

        Returns correlation_id after the pin is durable (status ``running``).
        Graph work is scheduled separately so the HTTP handler can 202 quickly.

        Idempotent: the same idempotency_key always resolves to the same
        correlation_id and must not start a second graph execution.
        """
        # 1. Contract check before any catalogue / DB work.
        self._validate_start_request(body)

        # 2. Fast path: key already used → return the original run identity.
        if existing := self._find_existing(body):
            return self._return_existing(existing, body)

        # 3. Resolve route → tools / memory profile (may call ADP + ACR).
        context = self._hydrate(body)

        # 4. Durable pin. created=False means another writer won the insert race.
        run, created = self._persist_run(body, context)
        if not created:
            # Do not snapshot or schedule again — that would double-execute.
            return run.correlation_id

        # 5. Audit what was hydrated at start time (governance / replay).
        self._snapshot(run, context)
        # 6. Hand off to the agent execution loop (async in production).
        self._schedule(run, body, context)

        return run.correlation_id

    def _validate_start_request(self, body: dict[str, Any]) -> None:
        """Reject malformed start bodies before hydrate or insert."""
        if body.get("mode") != "new":
            raise ValueError("mode must be new")
        if not str(body.get("idempotency_key") or "").strip():
            raise ValueError("idempotency_key is required")
        if not str(body.get("session_id") or "").strip():
            raise ValueError("session_id is required")

    def _find_existing(self, body: dict[str, Any]) -> RunPin | None:
        """Lookup by idempotency key (non-atomic; insert still handles races)."""
        key = str(body["idempotency_key"]).strip()
        return self._store.find_by_idempotency(key)

    def _return_existing(self, run: RunPin, body: dict[str, Any]) -> str:
        """Duplicate start: attach telemetry to the original pin and return its id."""
        telemetry.attach(
            session_id=str(body["session_id"]).strip(),
            correlation_id=run.correlation_id,
            route_id=run.route_id,
            route_version=run.route_version,
        )
        return run.correlation_id

    def _hydrate(self, body: dict[str, Any]) -> dict[str, Any]:
        """Build the runtime context for this start: catalogue row, tools, memory profile.

        Returns a single context dict so later steps (persist / snapshot / schedule)
        do not thread many loose variables.
        """
        route_id = str(body.get("route_id") or "")
        route_version = str(body.get("route_version") or "")
        session_id = str(body["session_id"]).strip()
        journey_id = self._journey_id(session_id, route_id)
        telemetry.attach(session_id=session_id, route_id=route_id, route_version=route_version)

        try:
            with telemetry.tracer().start_as_current_span("hydrate") as span:
                span.set_attribute("route_id", route_id)
                span.set_attribute("route_version", route_version)
                span.set_attribute("session_id", session_id)
                if telemetry.current_request_id():
                    span.set_attribute("request_id", telemetry.current_request_id())
                try:
                    row = self._route_row(route_id, route_version)
                    # Pattern-specific node list (prefetch, manifest tools, synthesis, …).
                    tools = hydrate(body, self._catalogue, self._registry, row=row or None)
                    profile = memory_profile(row)
                except HydrateError as exc:
                    telemetry.record_error(span, exc)
                    raise
            telemetry.emit(
                "run.hydrate.succeeded",
                journey_id=journey_id,
                route_id=route_id,
                route_version=route_version,
                session_id=session_id,
                outcome="hydrate_ok",
            )
            return {
                "row": row,
                "tools": tools,
                "profile": profile,
                "route_id": route_id,
                "route_version": route_version,
                "session_id": session_id,
                "journey_id": journey_id,
            }
        except HydrateError as exc:
            telemetry.emit(
                "run.hydrate.failed",
                journey_id=journey_id,
                route_id=route_id,
                route_version=route_version,
                session_id=session_id,
                outcome="hydrate_failed",
                reason_class=_hydrate_reason(exc),
            )
            raise

    def _create_run(self, body: dict[str, Any], context: dict[str, Any]) -> RunPin:
        """Mint an in-memory RunPin; not durable until _persist_run inserts it."""
        return RunPin(
            correlation_id=_mint_correlation_id(),
            idempotency_key=str(body["idempotency_key"]).strip(),
            session_id=str(body["session_id"]).strip(),
            route_id=context["route_id"],
            route_version=context["route_version"],
            activation_target=str(body.get("activation_target") or "") or None,
            agent_client_id=str(body.get("agent_client_id") or "") or None,
            hydrated_tools=context["tools"],  # frozen capability list for this run
            status="running",
        )

    def _persist_run(
        self, body: dict[str, Any], context: dict[str, Any]
    ) -> tuple[RunPin, bool]:
        """Insert the pin. Unique idempotency_key is the race backstop.

        Returns (saved_pin, created). created=False when another concurrent start
        with the same key already inserted — callers must not schedule twice.
        """
        pin = self._create_run(body, context)
        saved = self._store.insert(pin)
        if saved.correlation_id != pin.correlation_id:
            self._attach_existing(saved, str(body["session_id"]).strip())
            return saved, False
        self._attach_run(saved)
        return saved, True

    def _attach_existing(self, run: RunPin, session_id: str) -> None:
        """Bind span/log fields for a run we did not create (idempotent / race loser)."""
        telemetry.attach(
            session_id=session_id,
            correlation_id=run.correlation_id,
            route_id=run.route_id,
            route_version=run.route_version,
        )

    def _attach_run(self, run: RunPin) -> None:
        """Bind span/log fields for a newly inserted pin."""
        telemetry.attach(
            correlation_id=run.correlation_id,
            session_id=run.session_id,
            route_id=run.route_id,
            route_version=run.route_version,
        )

    def _snapshot(self, run: RunPin, context: dict[str, Any]) -> None:
        """Record hydrated config for audit, then emit run.graph.started.

        Snapshot captures route/tools/prompt/retrieval at start time so later
        catalogue edits do not rewrite history for this correlation_id.
        """
        row = context.get("row") or {}
        retrieval = row.get("retrieval") if isinstance(row.get("retrieval"), dict) else None
        emit_async(
            hydrate_snapshot(
                run.correlation_id,
                run.session_id,
                run.route_id,
                run.route_version,
                context["tools"],
                manifest_id=str(row.get("tool_manifest") or ""),
                manifest_version=str(row.get("tool_manifest_version") or ""),
                prompt_id=str(row.get("prompt_id") or ""),
                retrieval=retrieval,
            )
        )
        telemetry.emit(
            "run.graph.started",
            journey_id=context["journey_id"],
            correlation_id=run.correlation_id,
            session_id=run.session_id,
            route_id=run.route_id,
            route_version=run.route_version,
            outcome="started",
        )

    def _schedule(
        self, run: RunPin, body: dict[str, Any], context: dict[str, Any]
    ) -> None:
        """Hand the durable run to the execution engine without blocking start().

        Why this exists separately from _execute_new_run:
        - HTTP start must return 202 as soon as the pin is durable.
        - Production uses a background thread; tests use run_inline.
        - The lambda closes over run + context so the worker has everything it needs.

        goal is the customer utterance / job payload the graph reads as state["goal"].
        """
        goal = body.get("goal")
        if not isinstance(goal, dict):
            goal = {}
        # _schedule_run is either run_in_background or run_inline (injected).
        self._schedule_run(
            lambda: self._execute_new_run(
                run,
                row=context["row"],
                profile=context["profile"],
                goal=goal,
                session_id=run.session_id,
            )
        )

    def _execute_new_run(
        self,
        pin: RunPin,
        *,
        row: dict[str, Any],
        profile: dict[str, Any],
        goal: dict[str, Any],
        session_id: str,
    ) -> None:
        """Build the pattern graph, invoke it, then emit terminal audit.

        Called from the scheduled worker (or inline in tests), not from the
        request thread in production.
        """
        finished = run_loop(
            self._graph_for(
                pin.hydrated_tools,
                correlation_id=pin.correlation_id,
                profile=profile,
                row=row,
                session_id=session_id,
            ),
            self._store,
            pin,
            goal=goal,
            profile=profile,
        )
        # If the graph paused waiting on a child agent, poll jobs and resume later.
        self._maybe_schedule_subagent_join(finished)
        self._emit_run_terminal(finished)

    def _journey_id(self, session_id: str, route_id: str) -> str:
        """Stable telemetry journey key: chat.<route> or job.<route>."""
        prefix = "job" if is_jobs_session(session_id) else "chat"
        suffix = route_id or "turn"
        return f"{prefix}.{suffix}"

    # --- resume --------------------------------------------------------------

    def resume(self, correlation_id: str, body: dict[str, Any]) -> dict[str, Any] | None:
        """Continue an existing pin after a wait, failure, or follow-up turn.

        Branches on pin.status:
        - waiting → apply gate / customer_ask / subagent packet, then continue
        - failed  → checkpoint resume when memory.loop is enabled
        - else    → re-run with the request body as the new goal
        """
        pin = self._store.get(correlation_id)
        if pin is None:
            return None
        telemetry.attach(
            correlation_id=correlation_id,
            session_id=pin.session_id,
            route_id=pin.route_id,
            route_version=pin.route_version,
        )
        row = self._route_row(pin.route_id, pin.route_version)
        profile = memory_profile(row)
        prior_notes, prior_slots = self._prior_working(pin, profile)

        if pin.status == "waiting":
            return self._resume_waiting(correlation_id, pin, body, row, profile, prior_notes, prior_slots)
        if pin.status == "failed":
            return self._resume_failed(correlation_id, pin, body, row, profile, prior_notes, prior_slots)
        return self._resume_rerun(correlation_id, pin, body, row, profile, prior_notes, prior_slots)

    def _prior_working(
        self, pin: RunPin, profile: dict[str, Any]
    ) -> tuple[list[str], dict[str, Any]]:
        """Restore notes/slots from working memory when the route profile allows it."""
        if not save_working(profile):
            return [], {}
        return notes_from_working(pin.working), slots_from_working(pin.working)

    def _resume_waiting(
        self,
        correlation_id: str,
        pin: RunPin,
        body: dict[str, Any],
        row: dict[str, Any],
        profile: dict[str, Any],
        prior_notes: list[str],
        prior_slots: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Apply the wait packet, mark running, and continue the graph mid-pipeline."""
        checkpoint = pin.checkpoint if isinstance(pin.checkpoint, dict) else {}
        waiting_for = str(checkpoint.get("waiting_for") or "human_gate")
        stage_id = str(checkpoint.get("stage_id") or "")
        if not stage_id:
            raise ValueError(f"{waiting_for} checkpoint missing stage_id")

        goal = checkpoint.get("goal") if isinstance(checkpoint.get("goal"), dict) else {}
        merged_slots = dict(prior_slots)
        resume_index = int(checkpoint.get("resume_index") or checkpoint.get("step", -1) + 1)
        resume_loop: int | None = None

        if waiting_for == "subagent":
            prior_notes, merged_slots, resume_loop = self._apply_subagent_resume(
                body, checkpoint, stage_id, prior_notes, merged_slots
            )
        elif waiting_for == "customer_ask":
            prior_notes, resume_loop = self._apply_customer_ask_resume(
                body, checkpoint, prior_notes
            )
        else:
            # human_gate: approve continues; reject fails the run immediately.
            rejected = self._apply_human_gate_resume(
                correlation_id, body, stage_id, merged_slots
            )
            if rejected is not None:
                return rejected

        if save_working(profile):
            self._store.save_progress(
                correlation_id,
                working=working_payload(prior_notes, merged_slots),
            )

        pin = self._store.mark_running(correlation_id)
        # Pattern 1 keeps the full tool list (LLM chooses next CALL).
        # Linear graphs (0/2/3) resume at resume_index to skip finished stages.
        row_mode = int(row.get("autonomy_mode") or 0)
        keep_tools = row_mode == 1 and waiting_for in {"subagent", "customer_ask"}
        start_index = 0 if keep_tools else resume_index
        run_loop(
            self._graph_for(
                pin.hydrated_tools,
                correlation_id=pin.correlation_id,
                profile=profile,
                row=row,
                start_index=start_index,
                session_id=pin.session_id,
            ),
            self._store,
            pin,
            goal=goal,
            notes=prior_notes,
            slots=merged_slots,
            profile=profile,
            resume_loop_step=resume_loop,
        )
        finished = self._store.get(correlation_id)
        if finished is not None:
            self._maybe_schedule_subagent_join(finished)
            self._emit_run_terminal(finished)
        return self.status(correlation_id)

    def _apply_subagent_resume(
        self,
        body: dict[str, Any],
        checkpoint: dict[str, Any],
        stage_id: str,
        prior_notes: list[str],
        merged_slots: dict[str, Any],
    ) -> tuple[list[str], dict[str, Any], int | None]:
        """Merge child job results into the parent slot map."""
        packet = parse_subagent_packet(body if isinstance(body, dict) else {})
        if packet is None:
            raise ValueError("subagent resume packet required")
        expected = {
            str(item) for item in (checkpoint.get("subagent_ids") or []) if item
        }
        got = {item["correlation_id"] for item in packet}
        if expected and got != expected:
            raise ValueError("subagent resume packet missing expected correlation ids")
        merged_slots = merge_subagent_packet(merged_slots, stage_id, packet)
        note = f"Joined subagent {stage_id}: {[p['status'] for p in packet]}"
        notes = list(prior_notes) + [note]
        resume_loop = (
            int(checkpoint["resume_loop_step"])
            if checkpoint.get("resume_loop_step") is not None
            else None
        )
        return notes, merged_slots, resume_loop

    def _apply_customer_ask_resume(
        self,
        body: dict[str, Any],
        checkpoint: dict[str, Any],
        prior_notes: list[str],
    ) -> tuple[list[str], int | None]:
        """Append the customer's reply into notes (Pattern 1 ASK → locator)."""
        reply = str((body or {}).get("message") or "").strip()
        if not reply:
            raise ValueError("customer_ask resume requires message")
        notes = append_customer_reply(prior_notes, reply)
        resume_loop = (
            int(checkpoint["resume_loop_step"])
            if checkpoint.get("resume_loop_step") is not None
            else None
        )
        return notes, resume_loop

    def _apply_human_gate_resume(
        self,
        correlation_id: str,
        body: dict[str, Any],
        stage_id: str,
        merged_slots: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Apply human_gate decision. Returns slim status on reject; else mutates slots."""
        gate_packet = parse_gate_packet(body if isinstance(body, dict) else {})
        if gate_packet is None:
            raise ValueError("human_gate resume packet required")
        decision = str(gate_packet.get("decision") or "").strip().lower()
        if decision == "reject":
            failed = self._store.fail(
                correlation_id,
                {"message": str(gate_packet.get("comment") or "human_gate rejected")},
            )
            self._emit_run_terminal(failed)
            return failed.slim_status()
        merged_slots[stage_id] = gate_packet
        return None

    def _resume_failed(
        self,
        correlation_id: str,
        pin: RunPin,
        body: dict[str, Any],
        row: dict[str, Any],
        profile: dict[str, Any],
        prior_notes: list[str],
        prior_slots: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Recoverable failure resume: restart from the checkpointed stage index."""
        if not save_loop(profile):
            raise ValueError("checkpoint resume not enabled for this route")
        checkpoint = pin.checkpoint if isinstance(pin.checkpoint, dict) else {}
        if not parse_checkpoint_resume(body if isinstance(body, dict) else {}):
            raise ValueError("checkpoint resume requires {} or resume=true")
        resume_index = checkpoint_resume_index(
            checkpoint,
            pin.hydrated_tools,
            prior_slots,
        )
        if resume_index is None:
            raise ValueError("checkpoint resume not available")
        goal = checkpoint_goal(checkpoint)
        row_mode = int(row.get("autonomy_mode") or 0)
        resume_loop = loop_resume_step(checkpoint) if row_mode == 1 else None
        pin = self._store.mark_running(correlation_id)
        finished = run_loop(
            self._graph_for(
                pin.hydrated_tools,
                correlation_id=pin.correlation_id,
                profile=profile,
                row=row,
                start_index=resume_index,
                session_id=pin.session_id,
            ),
            self._store,
            pin,
            goal=goal,
            notes=prior_notes,
            slots=prior_slots,
            profile=profile,
            resume_loop_step=resume_loop,
        )
        self._emit_run_terminal(finished)
        return self.status(correlation_id)

    def _resume_rerun(
        self,
        correlation_id: str,
        pin: RunPin,
        body: dict[str, Any],
        row: dict[str, Any],
        profile: dict[str, Any],
        prior_notes: list[str],
        prior_slots: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Follow-up turn on a non-waiting pin: re-invoke with body as goal."""
        finished = run_loop(
            self._graph_for(
                pin.hydrated_tools,
                correlation_id=pin.correlation_id,
                profile=profile,
                row=row,
                session_id=pin.session_id,
            ),
            self._store,
            pin,
            goal=body if isinstance(body, dict) else {},
            notes=prior_notes,
            slots=prior_slots,
            profile=profile,
        )
        self._emit_run_terminal(finished)
        return self.status(correlation_id)

    # --- status / open -------------------------------------------------------

    def status(self, correlation_id: str) -> dict[str, Any] | None:
        """Slim channel-facing status for polling clients."""
        telemetry.attach(correlation_id=correlation_id)
        pin = self._store.get(correlation_id)
        if pin is not None:
            telemetry.attach(session_id=pin.session_id, route_id=pin.route_id)
        return None if pin is None else pin.slim_status()

    def open_run(self, session_id: str) -> dict[str, Any]:
        """Latest run for a session, or empty list when none exists."""
        telemetry.attach(session_id=session_id)
        pin = self._store.find_by_session(session_id)
        if pin is None:
            return {"runs": []}
        telemetry.attach(correlation_id=pin.correlation_id, route_id=pin.route_id)
        return pin.open_run()

    # --- graph build ---------------------------------------------------------

    def _graph_for(
        self,
        tools: list[dict[str, Any]],
        *,
        correlation_id: str,
        profile: dict[str, Any],
        row: dict[str, Any] | None = None,
        start_index: int = 0,
        session_id: str | None = None,
    ) -> GraphPort:
        """Select Pattern 1 agent loop vs linear/branch tool graph from autonomy_mode."""
        if self._graph is not None:
            return self._graph
        if self._invoker is None:
            raise RuntimeError("tool invoker required when no graph is injected")

        on_stage = self._make_on_stage(tools, correlation_id, profile, session_id)
        on_progress = self._make_on_progress(correlation_id)
        row = row or {}
        mode = int(row.get("autonomy_mode") or 0)
        retrieval = row.get("retrieval") if isinstance(row.get("retrieval"), dict) else None

        # Mode 1: LLM chooses CALL/ASK/DONE. Modes 0/2/3: fixed stage order (or branch).
        if mode == 1:
            return self._build_pattern1_loop(tools, row, on_stage, on_progress, retrieval, start_index)
        return build_tool_graph(
            tools,
            self._invoker,
            llm=self._llm,
            on_stage=on_stage,
            retrieval=retrieval,
            prefetch=self._prefetch,
            catalogue=self._catalogue,
            start_index=start_index,
            jobs=self._jobs,
        )

    def _make_on_stage(
        self,
        tools: list[dict[str, Any]],
        correlation_id: str,
        profile: dict[str, Any],
        session_id: str | None,
    ) -> Callable[[int, str, dict[str, Any]], None]:
        """Per-stage callback: persist working memory + emit stage.completed audit."""

        def on_stage(step: int, stage_id: str, state: dict[str, Any]) -> None:
            persist_stage(
                self._store,
                correlation_id,
                profile,
                step,
                stage_id,
                state,
                tools=tools,
            )
            tool = tools[step] if 0 <= step < len(tools) else {}
            slots = state.get("slots") if isinstance(state.get("slots"), dict) else {}
            slot = slots.get(stage_id) if isinstance(slots, dict) else None
            # Prefer structured slot body; fall back to notes for LLM-only stages.
            response_body = slot if slot is not None else state.get("notes") or []
            if stage_id == "customer_ask":
                response_body = {"message": str(state.get("result") or "")}
            llm_role = str(tool.get("llm_role") or "none")
            request_body = state.get("_audit_request")
            if request_body is None:
                request_body = state.get("goal") or {}
            latency_ms = telemetry.emit_stage_completed(
                stage_id,
                response_body,
                outcome="completed",
                llm_role=llm_role,
            )
            emit_async(
                stage_completed(
                    correlation_id,
                    session_id,
                    stage_id,
                    llm_role,
                    "completed",
                    latency_ms,
                    request_body,
                    response_body,
                )
            )

        return on_stage

    def _make_on_progress(self, correlation_id: str) -> Callable[[str], None]:
        """Persist interim assistant text on the pin while status is still running."""

        def on_progress(message: str) -> None:
            text = message.strip()
            if not text:
                return
            pin = self._store.get(correlation_id)
            if pin is None or pin.status != "running":
                return
            prior = pin.result if isinstance(pin.result, dict) else {}
            messages = [str(item) for item in (prior.get("messages") or [])]
            if text not in messages:
                messages.append(text)
            self._store.save_progress(
                correlation_id,
                result={"message": text, "messages": messages},
            )

        return on_progress

    def _build_pattern1_loop(
        self,
        tools: list[dict[str, Any]],
        row: dict[str, Any],
        on_stage: Callable[[int, str, dict[str, Any]], None],
        on_progress: Callable[[str], None],
        retrieval: dict[str, Any] | None,
        start_index: int,
    ) -> GraphPort:
        """Compile the autonomous agent loop (manifest tools + host prompt)."""
        if self._llm is None:
            raise RuntimeError("llm required for autonomy_mode 1")
        if self._invoker is None:
            raise RuntimeError("tool invoker required when no graph is injected")
        prompt_id = str(row.get("prompt_id") or "")
        host = ""
        if prompt_id:
            host = str(self._catalogue.get_prompt(prompt_id).get("host") or "")
        # start_index slices tools on linear resume; Pattern 1 normally uses 0.
        sliced = tools[start_index:] if start_index else tools
        return build_agent_loop(
            sliced,
            self._invoker,
            self._llm,
            max_steps=int(row.get("max_loop_steps") or 8),
            on_stage=on_stage,
            on_progress=on_progress,
            system=host,
            retrieval=retrieval,
            prefetch=self._prefetch,
            catalogue=self._catalogue,
            jobs=self._jobs,
        )

    def _route_row(self, route_id: str, route_version: str) -> dict[str, Any]:
        """Pinned catalogue route row (empty if ids missing — hydrate will fail closed)."""
        if not route_id or not route_version:
            return {}
        return self._catalogue.get_route(route_id, route_version)

    # --- audit / subagent join -----------------------------------------------

    def _emit_run_terminal(self, pin: RunPin | None) -> None:
        """Tell audit the run left in_progress (completed / waiting / failed)."""
        if pin is None:
            return
        emit_async(
            run_terminal(
                pin.correlation_id,
                pin.session_id,
                pin.status,
                pin.route_id,
                pin.route_version,
            )
        )

    def _maybe_schedule_subagent_join(self, pin: RunPin) -> None:
        """If parent paused for subagent join, poll jobs in the background and resume."""
        if pin.status != "waiting":
            return
        checkpoint = pin.checkpoint if isinstance(pin.checkpoint, dict) else {}
        if checkpoint.get("waiting_for") != "subagent":
            return
        if self._jobs is None:
            log.warning(
                "subagent join skipped: jobs client not configured (%s)",
                pin.correlation_id,
            )
            return
        parent_id = pin.correlation_id
        self._schedule_run(lambda: self._join_subagents(parent_id))

    def _join_subagents(self, parent_correlation_id: str) -> None:
        """Poll child job statuses until terminal, then resume the parent with results."""
        pin = self._store.get(parent_correlation_id)
        if pin is None or pin.status != "waiting":
            return
        checkpoint = pin.checkpoint if isinstance(pin.checkpoint, dict) else {}
        if checkpoint.get("waiting_for") != "subagent":
            return
        ids = [str(item) for item in (checkpoint.get("subagent_ids") or []) if item]
        if not ids or self._jobs is None:
            return
        try:
            interval = float(os.environ.get("SUBAGENT_JOIN_POLL_S", "0.5"))
            timeout = float(os.environ.get("SUBAGENT_JOIN_TIMEOUT_S", "120"))
            packet = poll_subagents(
                self._jobs,
                ids,
                interval_s=interval,
                timeout_s=timeout,
            )
            self.resume(parent_correlation_id, {"subagents": packet})
        except Exception:
            log.exception("subagent join failed for %s", parent_correlation_id)
            failed = self._store.fail(
                parent_correlation_id,
                {"message": "subagent join failed", "recoverable": True},
            )
            self._emit_run_terminal(failed)


def _hydrate_reason(exc: HydrateError) -> str:
    """Map hydrate failures to coarse reason_class labels for telemetry."""
    text = str(exc).lower()
    if "404" in text or "miss" in text:
        return "not_found"
    if "required" in text or "missing" in text:
        return "missing_pin"
    return "upstream"


def _mint_correlation_id() -> str:
    """New corr-… id (full UUID; same shape family as chat- session ids)."""
    return "corr-" + str(uuid4())
