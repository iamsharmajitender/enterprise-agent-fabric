import { catalogKey, claimsFor, claimsHeader, expandToken, groupByLabel } from "../shared/catalog.js";
import { FrontDoorClient, resultMessages, } from "./front-door.js";
import { addMessage, clearThread, showTyping, hideTyping } from "./thread.js";
/** Runtime Ollama client timeout is 300s; keep poll window above that plus stage overhead. */
const POLL_INTERVAL_MS = 500;
const POLL_MAX_WAIT_MS = 330_000;
const POLL_MAX_ATTEMPTS = Math.ceil(POLL_MAX_WAIT_MS / POLL_INTERVAL_MS);
export async function mountChat(root) {
    const client = new FrontDoorClient(claimsHeader(claimsFor(["accounts:read", "support:case"])));
    let sessionId = null;
    let chats = [];
    let selected = null;
    let busy = false;
    const setBusy = (next) => {
        busy = next;
        root.send.disabled = next;
        root.composer.disabled = next;
    };
    const resizeComposer = () => {
        root.composer.style.height = "auto";
        root.composer.style.height = `${Math.min(root.composer.scrollHeight, 128)}px`;
    };
    const applyChat = (chat) => {
        selected = chat;
        sessionId = null;
        client.setClaims(claimsHeader(claimsFor(chat.claims ?? [])));
        clearThread(root);
        root.composer.value = expandToken(chat.message ?? "");
        resizeComposer();
        const claims = (chat.claims ?? []).join(", ") || "none";
        const parts = [chat.label || "Chat", `claims ${claims}`];
        if (chat.hint_contains)
            parts.push("uses hint chip");
        root.meta.textContent = parts.join(" · ");
    };
    const resolveHintId = async () => {
        if (!selected)
            return null;
        const hints = await client.fetchJson("/v1/assistant/hints");
        sessionId = hints.session_id ?? sessionId;
        const list = hints.hints ?? [];
        if (selected.hint_contains) {
            const hit = list.find((h) => String(h.label ?? "").toLowerCase().includes(selected.hint_contains.toLowerCase()));
            if (!hit)
                throw new Error(`no hint matching ${selected.hint_contains}`);
            return hit.hint_id;
        }
        // Demo catalog rows pin a route via claims; when only one chip is eligible, bind layer ①.
        if (selected.route_id && list.length === 1) {
            return list[0].hint_id;
        }
        return null;
    };
    const poll = async (id) => {
        const seen = new Set();
        const flush = (ev) => {
            for (const msg of resultMessages(ev)) {
                if (seen.has(msg))
                    continue;
                seen.add(msg);
                addMessage(root, "assistant", msg);
            }
        };
        showTyping(root.thread, root.empty);
        for (let i = 0; i < POLL_MAX_ATTEMPTS; i += 1) {
            const ev = await client.fetchJson(`/v1/assistant/sessions/${encodeURIComponent(id)}/events`);
            flush(ev);
            const terminal = ev.status === "completed" || ev.status === "waiting" || ev.status === "failed";
            if (terminal) {
                hideTyping(root.thread);
                if (ev.status === "failed" && seen.size === 0) {
                    addMessage(root, "error", JSON.stringify(ev));
                }
                return;
            }
            await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS));
        }
        hideTyping(root.thread);
        addMessage(root, "error", "Timed out waiting for a reply.");
    };
    const sendTurn = async (message, optionId = null) => {
        const text = message.trim();
        if (!text || busy)
            return;
        addMessage(root, "user", text);
        root.composer.value = "";
        root.composer.style.height = "auto";
        setBusy(true);
        const isFirstTurn = !sessionId;
        try {
            const hintId = isFirstTurn && !optionId ? await resolveHintId() : null;
            const turn = await client.fetchJson("/v1/assistant/turns", {
                method: "POST",
                body: JSON.stringify({
                    session_id: sessionId,
                    message: text,
                    hint_id: hintId,
                    option_id: optionId,
                }),
            });
            sessionId = turn.session_id ?? sessionId;
            if (turn.status === "accepted") {
                await poll(sessionId);
            }
            else if (turn.status === "clarify") {
                addMessage(root, "assistant", turn.prompt ?? "Which did you mean?", turn.options, (opt) => {
                    void sendTurn(opt.label ?? opt.id ?? "Yes", opt.id);
                });
            }
            else if (turn.status === "abstain") {
                addMessage(root, "system", turn.prompt ?? "No matching route for that message.");
            }
            else {
                addMessage(root, "system", JSON.stringify(turn));
            }
        }
        catch (err) {
            addMessage(root, "error", err instanceof Error ? err.message : String(err));
        }
        finally {
            setBusy(false);
            root.composer.focus();
        }
    };
    const loadChats = async () => {
        const res = await fetch("/chats.json");
        if (!res.ok)
            throw new Error(`${res.status} loading /chats.json`);
        const body = (await res.json());
        chats = body.chats ?? [];
        if (!chats.length)
            throw new Error("chats.json has no chats");
        root.typeSelect.replaceChildren();
        for (const [label, rows] of groupByLabel(chats)) {
            const group = document.createElement("optgroup");
            group.label = label;
            for (const chat of rows) {
                const opt = document.createElement("option");
                opt.value = catalogKey(chat);
                opt.textContent = catalogKey(chat);
                group.append(opt);
            }
            root.typeSelect.append(group);
        }
        const preferred = chats.find((c) => catalogKey(c) === "shopassist_case_ask") ?? chats[0];
        root.typeSelect.value = catalogKey(preferred);
        applyChat(preferred);
    };
    root.typeSelect.addEventListener("change", () => {
        const chat = chats.find((c) => catalogKey(c) === root.typeSelect.value);
        if (chat)
            applyChat(chat);
    });
    root.newChat.addEventListener("click", () => {
        if (selected)
            applyChat(selected);
        root.composer.focus();
    });
    root.composer.addEventListener("input", () => {
        resizeComposer();
    });
    root.composer.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            root.form.requestSubmit();
        }
    });
    root.form.addEventListener("submit", (event) => {
        event.preventDefault();
        void sendTurn(root.composer.value);
    });
    try {
        await loadChats();
    }
    catch (err) {
        root.typeSelect.replaceChildren();
        const opt = document.createElement("option");
        opt.value = "";
        opt.textContent = "Catalog unavailable";
        root.typeSelect.append(opt);
        root.meta.textContent = "";
        addMessage(root, "error", `Chat types unavailable (${err instanceof Error ? err.message : err})`);
    }
}
export function chatElements() {
    return {
        thread: document.getElementById("thread"),
        empty: document.getElementById("empty"),
        typeSelect: document.getElementById("chat-type"),
        newChat: document.getElementById("new-chat"),
        composer: document.getElementById("m"),
        send: document.getElementById("send"),
        meta: document.getElementById("meta"),
        form: document.getElementById("f"),
    };
}
