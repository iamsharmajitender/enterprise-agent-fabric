import type { ClarifyOption } from "../shared/types.js";

export type ThreadElements = {
  thread: HTMLElement;
  empty: HTMLElement;
};

export function scrollThread(thread: HTMLElement): void {
  requestAnimationFrame(() => {
    thread.scrollTo({ top: thread.scrollHeight, behavior: "smooth" });
  });
}

export function clearThread({ thread, empty }: ThreadElements): void {
  thread.querySelectorAll(".msg, .typing, .options-wrap, .log-line, .job-event").forEach((node) =>
    node.remove(),
  );
  empty.hidden = false;
}

export type JobEventKind = "info" | "success" | "error";

export function addJobEvent(
  { thread, empty }: ThreadElements,
  kind: JobEventKind,
  label: string,
  text: string,
): void {
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

export function appendLogLine(thread: HTMLElement, empty: HTMLElement, text: string): void {
  const kind: JobEventKind = text.startsWith("error:")
    ? "error"
    : text.startsWith("result:")
      ? "success"
      : text.startsWith("accepted:")
        ? "success"
        : "info";
  const label =
    kind === "error" ? "Error" : kind === "success" ? "Success" : "Job";
  addJobEvent({ thread, empty }, kind, label, text);
}

let typingEl: HTMLElement | null = null;

export function hideTyping(thread: HTMLElement): void {
  typingEl?.remove();
  typingEl = null;
}

export function showTyping(thread: HTMLElement, empty: HTMLElement): void {
  hideTyping(thread);
  empty.hidden = true;
  typingEl = document.createElement("div");
  typingEl.className = "typing";
  typingEl.setAttribute("aria-label", "Assistant is typing");
  typingEl.innerHTML = "<span></span><span></span><span></span>";
  thread.append(typingEl);
  scrollThread(thread);
}

export function addMessage(
  { thread, empty }: ThreadElements,
  role: "user" | "assistant" | "system" | "error",
  text: string,
  options?: ClarifyOption[],
  onOption?: (option: ClarifyOption) => void,
): void {
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
