import { catalogKey, claimsFor, claimsHeader, expandPayload, groupByLabel, } from "../shared/catalog.js";
import { FrontDoorClient } from "./front-door.js";
import { addJobEvent, clearThread, hideTyping, showTyping, } from "./thread.js";
export async function mountJobs(root) {
    const client = new FrontDoorClient(claimsHeader(claimsFor(["accounts:read", "claims:read"])));
    let jobs = [];
    let selected = null;
    let busy = false;
    const setBusy = (next) => {
        busy = next;
        root.start.disabled = next;
        root.payloadInput.disabled = next;
        root.typeSelect.disabled = next;
    };
    const resizeComposer = () => {
        root.payloadInput.style.height = "auto";
        root.payloadInput.style.height = `${Math.min(root.payloadInput.scrollHeight, 128)}px`;
    };
    const applyJob = (job) => {
        selected = job;
        client.setClaims(claimsHeader(claimsFor(job.claims ?? [])));
        clearThread(root);
        root.payloadInput.value = JSON.stringify(expandPayload(job.payload ?? {}), null, 0);
        resizeComposer();
        const claims = (job.claims ?? []).join(", ") || "none";
        root.meta.textContent = `${job.label || "Job"} · claims ${claims}`;
    };
    const poll = async (id) => {
        showTyping(root.thread, root.empty);
        for (let i = 0; i < 40; i += 1) {
            const ev = await client.fetchJson(`/v1/jobs/${encodeURIComponent(id)}`);
            const msg = ev.message ?? ev.result?.message;
            if (ev.status === "completed" || msg) {
                hideTyping(root.thread);
                addJobEvent(root, "success", "Result", msg ?? JSON.stringify(ev));
                return;
            }
            if (ev.status === "failed") {
                hideTyping(root.thread);
                addJobEvent(root, "error", "Failed", msg ?? JSON.stringify(ev));
                return;
            }
            await new Promise((resolve) => setTimeout(resolve, 250));
        }
        hideTyping(root.thread);
        addJobEvent(root, "error", "Timeout", "Timed out waiting for job completion.");
    };
    const startJob = async () => {
        const routeId = selected?.route_id?.trim();
        if (!routeId || busy)
            return;
        let payload = {};
        const raw = root.payloadInput.value.trim();
        if (raw) {
            try {
                payload = JSON.parse(raw);
            }
            catch {
                addJobEvent(root, "error", "Error", "Payload is not valid JSON.");
                return;
            }
        }
        const idempotencyKey = `job-${routeId}:${crypto.randomUUID()}`;
        addJobEvent(root, "info", "Start", `${routeId} · key=${idempotencyKey}`);
        setBusy(true);
        try {
            const accepted = await client.fetchJson("/v1/jobs", {
                method: "POST",
                body: JSON.stringify({ route_id: routeId, idempotency_key: idempotencyKey, payload }),
            });
            const id = accepted.correlation_id;
            if (!id) {
                addJobEvent(root, "error", "Error", "Front Door did not return a correlation_id.");
                return;
            }
            addJobEvent(root, "success", "Accepted", id);
            await poll(id);
        }
        catch (err) {
            addJobEvent(root, "error", "Error", err instanceof Error ? err.message : String(err));
        }
        finally {
            setBusy(false);
            root.payloadInput.focus();
        }
    };
    const loadJobs = async () => {
        const res = await fetch("/jobs.json");
        if (!res.ok)
            throw new Error(`${res.status} loading /jobs.json`);
        const body = (await res.json());
        jobs = body.jobs ?? [];
        if (!jobs.length)
            throw new Error("jobs.json has no jobs");
        root.typeSelect.replaceChildren();
        for (const [label, rows] of groupByLabel(jobs)) {
            const group = document.createElement("optgroup");
            group.label = label;
            for (const job of rows) {
                const opt = document.createElement("option");
                opt.value = catalogKey(job);
                opt.textContent = catalogKey(job);
                group.append(opt);
            }
            root.typeSelect.append(group);
        }
        const preferred = jobs.find((j) => j.route_id === "shopassist_case") ?? jobs[0];
        root.typeSelect.value = catalogKey(preferred);
        applyJob(preferred);
    };
    root.typeSelect.addEventListener("change", () => {
        const job = jobs.find((j) => catalogKey(j) === root.typeSelect.value);
        if (job)
            applyJob(job);
    });
    root.newJob.addEventListener("click", () => {
        if (selected)
            applyJob(selected);
        root.payloadInput.focus();
    });
    root.payloadInput.addEventListener("input", () => {
        resizeComposer();
    });
    root.payloadInput.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            root.form.requestSubmit();
        }
    });
    root.form.addEventListener("submit", (event) => {
        event.preventDefault();
        void startJob();
    });
    try {
        await loadJobs();
    }
    catch (err) {
        root.typeSelect.replaceChildren();
        const opt = document.createElement("option");
        opt.value = "";
        opt.textContent = "Catalog unavailable";
        root.typeSelect.append(opt);
        root.meta.textContent = "";
        addJobEvent(root, "error", "Error", `Job types unavailable (${err instanceof Error ? err.message : err})`);
    }
}
export function jobElements() {
    return {
        thread: document.getElementById("thread"),
        empty: document.getElementById("empty"),
        typeSelect: document.getElementById("job-type"),
        newJob: document.getElementById("new-job"),
        payloadInput: document.getElementById("payload"),
        start: document.getElementById("start"),
        meta: document.getElementById("meta"),
        form: document.getElementById("f"),
    };
}
