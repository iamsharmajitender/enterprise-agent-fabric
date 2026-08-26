from typing import Any
from uuid import uuid4

from app import telemetry
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
from app.core.memory import memory_profile, notes_from_working, persist_stage, save_loop, save_working, slots_from_working, working_payload
from app.core.state import RunPin, RunStore
from app.graph.human_gate import parse_gate_packet
from app.graph.llm import LlmPort
from app.graph.workflow import build_agent_loop, build_tool_graph
from app.tools.invoker import ToolInvoker


class RunService:
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
    ) -> None:
        """Hold store, catalogue, registry, and optional graph/tool/LLM ports."""
        self._store = store
        self._catalogue = catalogue
        self._registry = registry
        self._graph = graph
        self._invoker = invoker
        self._llm = llm
        self._prefetch = prefetch
        self._jobs = jobs

    def _graph_for(
        self,
        tools: list[dict[str, Any]],
        *,
        correlation_id: str,
        profile: dict[str, Any],
        row: dict[str, Any] | None = None,
        start_index: int = 0,
    ) -> GraphPort:
        """Use an injected graph, or build a Pattern 1 loop / linear graph."""
        if self._graph is not None:
            return self._graph
        if self._invoker is None:
            raise RuntimeError("tool invoker required when no graph is injected")

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

        row = row or {}
        mode = int(row.get("autonomy_mode") or 0)
        retrieval = row.get("retrieval") if isinstance(row.get("retrieval"), dict) else None
        sliced = tools[start_index:] if start_index else tools
        if mode == 1:
            if self._llm is None:
                raise RuntimeError("llm required for autonomy_mode 1")
            extra = ""
            prompt_id = str(row.get("prompt_id") or "")
            if prompt_id:
                extra = str(self._catalogue.get_prompt(prompt_id).get("host") or "")
            return build_agent_loop(
                sliced,
                self._invoker,
                self._llm,
                max_steps=int(row.get("max_loop_steps") or 8),
                on_stage=on_stage,
                system=extra,
                retrieval=retrieval,
                prefetch=self._prefetch,
                catalogue=self._catalogue,
                jobs=self._jobs,
            )
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

    def _route_row(self, route_id: str, route_version: str) -> dict[str, Any]:
        """Load the pinned catalogue row for hydrate and memory flags."""
        if not route_id or not route_version:
            return {}
        return self._catalogue.get_route(route_id, route_version)

    def start(self, body: dict[str, Any]) -> str:
        """Hydrate, pin, and execute a new run. Same idempotency key returns the original id."""
        if body.get("mode") != "new":
            raise ValueError("mode must be new")
        key = str(body.get("idempotency_key") or "").strip()
        session_id = str(body.get("session_id") or "").strip()
        if not key or not session_id:
            raise ValueError("idempotency_key and session_id are required")
        existing = self._store.find_by_idempotency(key)
        if existing is not None:
            telemetry.attach(
                session_id=session_id,
                correlation_id=existing.correlation_id,
                route_id=existing.route_id,
                route_version=existing.route_version,
            )
            return existing.correlation_id
        route_id = str(body.get("route_id") or "")
        route_version = str(body.get("route_version") or "")
        telemetry.attach(session_id=session_id, route_id=route_id, route_version=route_version)
        journey_id = f"chat.{route_id}" if route_id else "chat.turn"
        if session_id.startswith("job:"):
            journey_id = f"job.{route_id}" if route_id else "job.turn"
        profile: dict[str, Any] = {}
        try:
            with telemetry.tracer().start_as_current_span("hydrate") as span:
                span.set_attribute("route_id", route_id)
                span.set_attribute("route_version", route_version)
                span.set_attribute("session_id", session_id)
                if telemetry.current_request_id():
                    span.set_attribute("request_id", telemetry.current_request_id())
                try:
                    row = self._route_row(route_id, route_version)
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
        pin = RunPin(
            correlation_id=_mint_correlation_id(),
            idempotency_key=key,
            session_id=session_id,
            route_id=route_id,
            route_version=route_version,
            activation_target=str(body.get("activation_target") or "") or None,
            agent_client_id=str(body.get("agent_client_id") or "") or None,
            hydrated_tools=tools,
            status="running",
        )
        saved = self._store.insert(pin)
        if saved.correlation_id != pin.correlation_id:
            telemetry.attach(correlation_id=saved.correlation_id)
            return saved.correlation_id
        telemetry.attach(correlation_id=saved.correlation_id)
        telemetry.emit(
            "run.started",
            journey_id=journey_id,
            correlation_id=saved.correlation_id,
            session_id=session_id,
            route_id=route_id,
            route_version=route_version,
            outcome="started",
        )
        run_loop(
            self._graph_for(
                saved.hydrated_tools,
                correlation_id=saved.correlation_id,
                profile=profile,
                row=row,
            ),
            self._store,
            saved,
            goal=body.get("goal") if isinstance(body.get("goal"), dict) else {},
            profile=profile,
        )
        return saved.correlation_id

    def resume(self, correlation_id: str, body: dict[str, Any]) -> dict[str, Any] | None:
        """Re-invoke the graph for an existing pin and return its slim status."""
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
        prior_notes = notes_from_working(pin.working) if save_working(profile) else []
        prior_slots = slots_from_working(pin.working) if save_working(profile) else {}

        if pin.status == "waiting":
            checkpoint = pin.checkpoint if isinstance(pin.checkpoint, dict) else {}
            packet = parse_gate_packet(body if isinstance(body, dict) else {})
            if packet is None:
                raise ValueError("human_gate resume packet required")
            stage_id = str(checkpoint.get("stage_id") or "")
            if not stage_id:
                raise ValueError("human_gate checkpoint missing stage_id")
            decision = str(packet.get("decision") or "").strip().lower()
            if decision == "reject":
                failed = self._store.fail(
                    correlation_id,
                    {"message": str(packet.get("comment") or "human_gate rejected")},
                )
                return failed.slim_status()
            resume_index = int(checkpoint.get("resume_index") or checkpoint.get("step", -1) + 1)
            goal = checkpoint.get("goal") if isinstance(checkpoint.get("goal"), dict) else {}
            merged_slots = dict(prior_slots)
            merged_slots[stage_id] = packet
            if save_working(profile):
                self._store.save_progress(
                    correlation_id,
                    working=working_payload(prior_notes, merged_slots),
                )
            pin = self._store.mark_running(correlation_id)
            run_loop(
                self._graph_for(
                    pin.hydrated_tools,
                    correlation_id=pin.correlation_id,
                    profile=profile,
                    row=row,
                    start_index=resume_index,
                ),
                self._store,
                pin,
                goal=goal,
                notes=prior_notes,
                slots=merged_slots,
                profile=profile,
            )
            return self.status(correlation_id)

        if pin.status == "failed":
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
            run_loop(
                self._graph_for(
                    pin.hydrated_tools,
                    correlation_id=pin.correlation_id,
                    profile=profile,
                    row=row,
                    start_index=resume_index,
                ),
                self._store,
                pin,
                goal=goal,
                notes=prior_notes,
                slots=prior_slots,
                profile=profile,
                resume_loop_step=resume_loop,
            )
            return self.status(correlation_id)

        run_loop(
            self._graph_for(
                pin.hydrated_tools,
                correlation_id=pin.correlation_id,
                profile=profile,
                row=row,
            ),
            self._store,
            pin,
            goal=body if isinstance(body, dict) else {},
            notes=prior_notes,
            slots=prior_slots,
            profile=profile,
        )
        return self.status(correlation_id)

    def status(self, correlation_id: str) -> dict[str, Any] | None:
        """Return slim status for a correlation id, or None if unknown."""
        telemetry.attach(correlation_id=correlation_id)
        pin = self._store.get(correlation_id)
        if pin is not None:
            telemetry.attach(session_id=pin.session_id, route_id=pin.route_id)
        return None if pin is None else pin.slim_status()

    def open_run(self, session_id: str) -> dict[str, Any]:
        """Return the latest run for a session, or `{runs: []}` if none."""
        telemetry.attach(session_id=session_id)
        pin = self._store.find_by_session(session_id)
        if pin is None:
            return {"runs": []}
        telemetry.attach(correlation_id=pin.correlation_id, route_id=pin.route_id)
        return pin.open_run()


def _hydrate_reason(exc: HydrateError) -> str:
    """Map a hydrate failure to a coarse reason_class for telemetry."""
    text = str(exc).lower()
    if "404" in text or "miss" in text:
        return "not_found"
    if "required" in text or "missing" in text:
        return "missing_pin"
    return "upstream"


def _mint_correlation_id() -> str:
    """Mint a new corr-… id for a run pin."""
    return "corr-" + uuid4().hex[:12]
