const PAGE_SIZE = 50;
const tbody = document.querySelector("#workflows tbody");
const statusEl = document.getElementById("status");
const pageLabel = document.getElementById("page-label");
const prevBtn = document.getElementById("prev");
const nextBtn = document.getElementById("next");

let offset = 0;
let total = 0;

function formatWhen(iso) {
  if (!iso) return "—";
  return String(iso).replace(/\.\d+Z$/, "Z");
}

function searchHref(row) {
  const params = new URLSearchParams();
  if (row.correlation_id) params.set("correlation_id", row.correlation_id);
  if (row.session_id) params.set("session_id", row.session_id);
  return `/search?${params.toString()}`;
}

function renderRows(items) {
  tbody.replaceChildren();
  for (const row of items) {
    const tr = document.createElement("tr");
    const route =
      row.route_id && row.route_version
        ? `${row.route_id}@${row.route_version}`
        : row.route_id || "—";
    const cells = [
      formatWhen(row.completed_at),
      formatWhen(row.started_at),
      route,
      row.status || "—",
      row.correlation_id || "—",
      row.session_id || "—",
    ];
    cells.forEach((text, i) => {
      const td = document.createElement("td");
      if (i === 4 && row.correlation_id) {
        const a = document.createElement("a");
        a.href = searchHref(row);
        a.textContent = text;
        td.appendChild(a);
      } else {
        td.textContent = text;
      }
      tr.appendChild(td);
    });
    tr.addEventListener("click", (event) => {
      if (event.target instanceof HTMLAnchorElement) return;
      if (row.correlation_id) window.location.href = searchHref(row);
    });
    tr.tabIndex = 0;
    tr.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && row.correlation_id) {
        window.location.href = searchHref(row);
      }
    });
    tbody.appendChild(tr);
  }
}

function updatePager() {
  const from = total === 0 ? 0 : offset + 1;
  const to = Math.min(offset + PAGE_SIZE, total);
  pageLabel.textContent = total ? `${from}–${to} of ${total}` : "0 of 0";
  prevBtn.disabled = offset <= 0;
  nextBtn.disabled = offset + PAGE_SIZE >= total;
}

async function loadPage() {
  statusEl.textContent = "Loading…";
  try {
    const res = await fetch(`/api/workflows?limit=${PAGE_SIZE}&offset=${offset}`);
    const body = await res.json();
    if (!res.ok) {
      statusEl.textContent = body.error || `Failed (HTTP ${res.status})`;
      renderRows([]);
      total = 0;
      updatePager();
      return;
    }
    const items = Array.isArray(body.items) ? body.items : [];
    total = Number(body.total) || 0;
    offset = Number(body.offset) || offset;
    renderRows(items);
    statusEl.textContent = items.length
      ? "Click a row to open the evidence chain."
      : "No completed workflows yet.";
    updatePager();
  } catch (err) {
    statusEl.textContent = String(err);
    renderRows([]);
    total = 0;
    updatePager();
  }
}

prevBtn?.addEventListener("click", () => {
  offset = Math.max(0, offset - PAGE_SIZE);
  loadPage();
});

nextBtn?.addEventListener("click", () => {
  offset = offset + PAGE_SIZE;
  loadPage();
});

loadPage();
