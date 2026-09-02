import { claimsFor, claimsHeader } from "../shared/catalog.js";
import { FrontDoorClient, type JobStatus, resultMessages } from "./front-door.js";
import {
  addJobEvent,
  hideTyping,
  showTyping,
  type ThreadElements,
} from "./thread.js";

type HumanCatalog = {
  claims?: string[];
  default_packet?: Record<string, unknown>;
};

type HumanElements = ThreadElements & {
  correlationInput: HTMLInputElement;
  packetInput: HTMLTextAreaElement;
  resume: HTMLButtonElement;
  meta: HTMLElement;
  form: HTMLFormElement;
};

export async function mountHuman(root: HumanElements): Promise<void> {
  let busy = false;
  let claims = ["kyc:operate", "support:case", "accounts:read"];
  const client = new FrontDoorClient(claimsHeader(claimsFor(claims)));

  const setBusy = (next: boolean) => {
    busy = next;
    root.resume.disabled = next;
    root.correlationInput.disabled = next;
    root.packetInput.disabled = next;
  };

  const loadCatalog = async () => {
    const res = await fetch("/human.json");
    if (!res.ok) throw new Error(`${res.status} loading /human.json`);
    const body = (await res.json()) as HumanCatalog;
    if (body.claims?.length) {
      claims = body.claims;
      client.setClaims(claimsHeader(claimsFor(claims)));
    }
    root.packetInput.value = JSON.stringify(body.default_packet ?? {}, null, 2);
    root.meta.textContent = `Claims: ${claims.join(", ")}`;
  };

  const pollStatus = async (id: string) => {
    const seen = new Set<string>();
    showTyping(root.thread, root.empty);
    for (let i = 0; i < 120; i += 1) {
      const ev = await client.fetchJson<JobStatus>(`/v1/jobs/${encodeURIComponent(id)}`);
      for (const msg of resultMessages(ev)) {
        if (seen.has(msg)) continue;
        seen.add(msg);
        addJobEvent(root, "info", "Update", msg);
      }
      if (ev.status === "completed" || ev.status === "failed") {
        hideTyping(root.thread);
        addJobEvent(
          root,
          ev.status === "completed" ? "success" : "error",
          ev.status === "completed" ? "Result" : "Failed",
          seen.size ? "" : JSON.stringify(ev),
        );
        return;
      }
      await new Promise((resolve) => setTimeout(resolve, 500));
    }
    hideTyping(root.thread);
    addJobEvent(root, "error", "Timeout", "Timed out polling job status.");
  };

  const submitResume = async () => {
    if (busy) return;
    const correlationId = root.correlationInput.value.trim();
    if (!correlationId) {
      addJobEvent(root, "error", "Error", "Correlation id is required.");
      return;
    }
    let packet: Record<string, unknown>;
    const raw = root.packetInput.value.trim();
    if (!raw) {
      addJobEvent(root, "error", "Error", "Gate packet JSON is required.");
      return;
    }
    try {
      packet = JSON.parse(raw) as Record<string, unknown>;
    } catch {
      addJobEvent(root, "error", "Error", "Gate packet is not valid JSON.");
      return;
    }

    root.empty.hidden = true;
    addJobEvent(root, "info", "Resume", correlationId);
    setBusy(true);
    try {
      const body = await client.fetchJson<JobStatus>(
        `/v1/jobs/${encodeURIComponent(correlationId)}/turns`,
        { method: "POST", body: JSON.stringify(packet) },
      );
      addJobEvent(root, "success", "Accepted", JSON.stringify(body));
      if (body.status !== "completed" && body.status !== "failed") {
        await pollStatus(correlationId);
      }
    } catch (err) {
      addJobEvent(root, "error", "Error", err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
      root.correlationInput.focus();
    }
  };

  root.form.addEventListener("submit", (event) => {
    event.preventDefault();
    void submitResume();
  });

  try {
    await loadCatalog();
  } catch (err) {
    addJobEvent(
      root,
      "error",
      "Error",
      `Catalog unavailable (${err instanceof Error ? err.message : err})`,
    );
  }
}

export function humanElements(): HumanElements {
  return {
    thread: document.getElementById("thread") as HTMLElement,
    empty: document.getElementById("empty") as HTMLElement,
    correlationInput: document.getElementById("correlation-id") as HTMLInputElement,
    packetInput: document.getElementById("packet") as HTMLTextAreaElement,
    resume: document.getElementById("resume") as HTMLButtonElement,
    meta: document.getElementById("meta") as HTMLElement,
    form: document.getElementById("f") as HTMLFormElement,
  };
}
