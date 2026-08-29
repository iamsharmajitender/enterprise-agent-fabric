export function scrollThread(thread) {
    requestAnimationFrame(() => {
        thread.scrollTo({ top: thread.scrollHeight, behavior: "smooth" });
    });
}
export function clearThread({ thread, empty }) {
    thread.querySelectorAll(".msg, .typing, .options-wrap, .log-line, .job-event").forEach((node) => node.remove());
    empty.hidden = false;
}
export function addJobEvent({ thread, empty }, kind, label, text) {
    empty.hidden = true;
    hideTyping(thread);
    const wrap = document.createElement("div");
    wrap.className = `job-event job-event--${kind}`;
    const tag = document.createElement("div");
    tag.className = "job-event__label";
    tag.textContent = label;
    const bubble = document.createElement("div");
    bubble.className = "job-event__bubble";
    bubble.textContent = text;
    wrap.append(tag, bubble);
    thread.append(wrap);
    scrollThread(thread);
}
export function appendLogLine(thread, empty, text) {
    const kind = text.startsWith("error:")
        ? "error"
        : text.startsWith("result:")
            ? "success"
            : text.startsWith("accepted:")
                ? "success"
                : "info";
    const label = kind === "error" ? "Error" : kind === "success" ? "Success" : "Job";
    addJobEvent({ thread, empty }, kind, label, text);
}
let typingEl = null;
export function hideTyping(thread) {
    typingEl?.remove();
    typingEl = null;
}
export function showTyping(thread, empty) {
    hideTyping(thread);
    empty.hidden = true;
    typingEl = document.createElement("div");
    typingEl.className = "typing";
    typingEl.setAttribute("aria-label", "Assistant is typing");
    typingEl.innerHTML = "<span></span><span></span><span></span>";
    thread.append(typingEl);
    scrollThread(thread);
}
export function addMessage({ thread, empty }, role, text, options, onOption) {
    empty.hidden = true;
    hideTyping(thread);
    const wrap = document.createElement("div");
    wrap.className = `msg msg--${role}`;
    const label = document.createElement("div");
    label.className = "msg__label";
    label.textContent =
        role === "user" ? "You" : role === "assistant" ? "Assistant" : role === "error" ? "Error" : "System";
    const bubble = document.createElement("div");
    bubble.className = "msg__bubble";
    bubble.textContent = text;
    wrap.append(label, bubble);
    thread.append(wrap);
    if (options?.length && onOption) {
        const opts = document.createElement("div");
        opts.className = "options-wrap";
        const row = document.createElement("div");
        row.className = "options";
        for (const opt of options) {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = "option";
            btn.textContent = opt.label || opt.id;
            btn.addEventListener("click", () => onOption(opt));
            row.append(btn);
        }
        opts.append(row);
        thread.append(opts);
    }
    scrollThread(thread);
}
