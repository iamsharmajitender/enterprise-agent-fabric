const form = document.getElementById("lookup");
const out = document.getElementById("out");

function fillFromQuery() {
  const params = new URLSearchParams(window.location.search);
  const corr = params.get("correlation_id");
  const sess = params.get("session_id");
  if (corr && form?.correlation_id) form.correlation_id.value = corr;
  if (sess && form?.session_id) form.session_id.value = sess;
  return Boolean(corr || sess);
}

async function loadChain() {
  const data = new FormData(form);
  const correlationId = String(data.get("correlation_id") || "").trim();
  const sessionId = String(data.get("session_id") || "").trim();
  out.textContent = "Loading…";
  try {
    let url;
    if (correlationId) {
      url = `/api/chains?correlation_id=${encodeURIComponent(correlationId)}`;
    } else if (sessionId) {
      url = `/api/sessions?session_id=${encodeURIComponent(sessionId)}`;
    } else {
      out.textContent = "Enter correlation_id or session_id.";
      return;
    }
    const res = await fetch(url);
    const body = await res.json();
    const events = Array.isArray(body.events) ? body.events : [];
    if (!events.length) {
      const detail = body.error ? ` — ${body.error}` : "";
      out.textContent = `No events (HTTP ${res.status}, upstream ${body.upstream ?? "n/a"})${detail}.`;
      return;
    }
    out.textContent = events
      .map((e) => {
        const stage = e.payload?.stage_id ? ` stage=${e.payload.stage_id}` : "";
        return `${e.occurred_at}  ${e.event_type}  [${e.producer}]${stage}\n${JSON.stringify(e.payload, null, 2)}`;
      })
      .join("\n\n—\n\n");
  } catch (err) {
    out.textContent = String(err);
  }
}

form?.addEventListener("submit", async (event) => {
  event.preventDefault();
  await loadChain();
});

if (fillFromQuery()) {
  loadChain();
}
