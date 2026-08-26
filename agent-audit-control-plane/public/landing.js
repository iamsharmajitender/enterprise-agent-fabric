const PAGE_SIZE = 50;
const tbody = document.querySelector("#workflows tbody");
const statusEl = document.getElementById("status");
const pageLabel = document.getElementById("page-label");
const prevBtn = document.getElementById("prev");
const nextBtn = document.getElementById("next");
const colWhen = document.getElementById("col-when");
const panel = document.getElementById("panel-workflows");
const tabs = [...document.querySelectorAll(".tab[data-status]")];
const viewBtns = [...document.querySelectorAll(".view-btn[data-view]")];

let offset = 0;
let total = 0;
let statusFilter = "completed";
/** @type {"nested" | "flat"} */
let listView = "nested";
/** Parents the user has expanded (nested view starts collapsed). */
const expanded = new Set();

function formatWhen(iso) {
  if (!iso) return "—";
  return String(iso).replace(/\.\d+Z$/, "Z");
}

/** Control Plane catalogue UI (local demo). */
const CONTROL_PLANE_ORIGIN = "http://localhost:3006";

function searchHref(row) {
  const params = new URLSearchParams();
  if (row.correlation_id) params.set("correlation_id", row.correlation_id);
  if (row.session_id) params.set("session_id", row.session_id);
  return `/search?${params.toString()}`;
}

function routeHref(row) {
  if (!row?.route_id) return null;
  const base = `${CONTROL_PLANE_ORIGIN}/routes/${encodeURIComponent(row.route_id)}`;
  if (row.route_version) return `${base}/${encodeURIComponent(row.route_version)}`;
  return base;
}

function routeLabel(row) {
  if (row.route_id && row.route_version) return `${row.route_id}@${row.route_version}`;
  return row.route_id || "—";
}

/** Route title: link to Control Plane route detail when route_id is known. */
function renderRouteTitle(row, { synthetic = false } = {}) {
  const title = document.createElement(synthetic || !row?.route_id ? "span" : "a");
  title.className = "route-title";
  if (synthetic) {
    title.textContent = "Parent run";
    return title;
  }
  title.textContent = routeLabel(row);
  const href = routeHref(row);
  if (href && title instanceof HTMLAnchorElement) {
    title.href = href;
    title.target = "_blank";
    title.rel = "noopener noreferrer";
    title.title = "Open route in Control Plane";
    title.addEventListener("click", (event) => event.stopPropagation());
  }
  return title;
}

function statusLabel(status) {
  const s = String(status || "").toLowerCase();
  if (s === "completed") return "success";
  return status || "—";
}

function statusClass(status) {
  const s = String(status || "").toLowerCase();
  if (s === "failed") return "status-pill status-pill--failed";
  if (s === "completed" || s === "success") return "status-pill status-pill--ok";
  if (s === "waiting") return "status-pill status-pill--wait";
  if (s === "running") return "status-pill status-pill--run";
  return "status-pill";
}

function sortByTimeDesc(a, b) {
  const at = String(a.completed_at || a.started_at || "");
  const bt = String(b.completed_at || b.started_at || "");
  return bt.localeCompare(at);
}

function sortChildrenAsc(a, b) {
  const at = String(a.started_at || a.completed_at || "");
  const bt = String(b.started_at || b.completed_at || "");
  return at.localeCompare(bt);
}

/** Nest every child under its parent_correlation_id (stub parent if missing from page). */
function groupFamilies(items) {
  const childrenByParent = new Map();
  const childIds = new Set();

  for (const row of items) {
    const parentId = row.parent_correlation_id;
    if (!parentId || parentId === row.correlation_id) continue;
    if (!childrenByParent.has(parentId)) childrenByParent.set(parentId, []);
    childrenByParent.get(parentId).push(row);
    childIds.add(row.correlation_id);
  }

  for (const kids of childrenByParent.values()) {
    kids.sort(sortChildrenAsc);
  }

  const families = [];
  const seenParents = new Set();
  const pageRoots = items
    .filter((row) => !childIds.has(row.correlation_id))
    .slice()
    .sort(sortByTimeDesc);

  for (const root of pageRoots) {
    families.push({
      parent: root,
      children: childrenByParent.get(root.correlation_id) || [],
      synthetic: false,
    });
    seenParents.add(root.correlation_id);
  }

  for (const [parentId, kids] of childrenByParent) {
    if (seenParents.has(parentId)) continue;
    families.push({
      parent: {
        correlation_id: parentId,
        session_id: null,
        route_id: null,
        route_version: null,
        status: null,
        started_at: kids[0]?.started_at || null,
        completed_at: kids[kids.length - 1]?.completed_at || null,
        parent_correlation_id: null,
        _synthetic: true,
      },
      children: kids,
      synthetic: true,
    });
  }

  return families;
}

function appendTextCell(tr, text) {
  const td = document.createElement("td");
  td.textContent = text;
  tr.appendChild(td);
  return td;
}

function toggleFamily(parentId) {
  if (!parentId) return;
  if (expanded.has(parentId)) expanded.delete(parentId);
  else expanded.add(parentId);
  const last = tbody._lastItems;
  if (Array.isArray(last)) renderRows(last);
}

function resetExpanded() {
  expanded.clear();
}

function bindFlatRowNav(tr, row) {
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
}

function renderStatusCell(tr, status) {
  const td = document.createElement("td");
  if (!status) {
    td.textContent = "—";
    tr.appendChild(td);
    return;
  }
  const pill = document.createElement("span");
  pill.className = statusClass(status);
  pill.textContent = statusLabel(status);
  td.appendChild(pill);
  tr.appendChild(td);
}

function renderCorrCell(tr, row) {
  const td = document.createElement("td");
  if (row?.correlation_id) {
    const a = document.createElement("a");
    a.href = row._synthetic
      ? `/search?correlation_id=${encodeURIComponent(row.correlation_id)}`
      : searchHref(row);
    a.textContent = row.correlation_id;
    a.title = "Open evidence chain";
    td.appendChild(a);
  } else {
    td.textContent = "—";
  }
  tr.appendChild(td);
}

function renderFlatRow(row) {
  const tr = document.createElement("tr");
  appendTextCell(tr, formatWhen(row.completed_at));
  appendTextCell(tr, formatWhen(row.started_at));

  const routeTd = document.createElement("td");
  const wrap = document.createElement("div");
  wrap.className = "route-cell route-cell--flat";
  const main = document.createElement("div");
  main.className = "route-main";
  main.appendChild(renderRouteTitle(row));
  if (row.parent_correlation_id) {
    const meta = document.createElement("span");
    meta.className = "route-meta";
    meta.textContent = `child of ${row.parent_correlation_id}`;
    main.appendChild(meta);
  }
  wrap.appendChild(main);
  routeTd.appendChild(wrap);
  tr.appendChild(routeTd);

  renderStatusCell(tr, row.status);
  renderCorrCell(tr, row);
  appendTextCell(tr, row.session_id || "—");
  bindFlatRowNav(tr, row);
  tbody.appendChild(tr);
}

function renderParentRow(family) {
  const { parent, children, synthetic } = family;
  const tr = document.createElement("tr");
  tr.classList.add("family-parent");
  if (synthetic) tr.classList.add("is-synthetic");
  if (children.length) tr.classList.add("has-children");
  tr.dataset.familyId = parent.correlation_id || "";

  const isOpen = children.length > 0 && expanded.has(parent.correlation_id);
  if (isOpen) tr.classList.add("is-expanded");
  else if (children.length) tr.classList.add("is-collapsed");

  appendTextCell(tr, formatWhen(parent.completed_at));
  appendTextCell(tr, formatWhen(parent.started_at));

  const routeTd = document.createElement("td");
  const wrap = document.createElement("div");
  wrap.className = "route-cell";

  if (children.length) {
    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "family-toggle";
    toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
    toggle.setAttribute(
      "aria-label",
      `${isOpen ? "Collapse" : "Expand"} ${children.length} agent child routes`,
    );
    toggle.textContent = isOpen ? "▾" : "▸";
    toggle.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      toggleFamily(parent.correlation_id);
    });
    wrap.appendChild(toggle);
  } else {
    const spacer = document.createElement("span");
    spacer.className = "family-toggle-spacer";
    spacer.setAttribute("aria-hidden", "true");
    wrap.appendChild(spacer);
  }

  const main = document.createElement("div");
  main.className = "route-main";
  main.appendChild(renderRouteTitle(parent, { synthetic }));

  if (children.length) {
    const badge = document.createElement("span");
    badge.className = "child-badge";
    badge.textContent = `${children.length} child${children.length === 1 ? "" : "ren"}`;
    main.appendChild(badge);

    const meta = document.createElement("span");
    meta.className = "route-meta";
    meta.textContent = isOpen ? "expanded — click row to close" : "click row to expand";
    main.appendChild(meta);
  } else if (synthetic) {
    const meta = document.createElement("span");
    meta.className = "route-meta";
    meta.textContent = "parent not on this page";
    main.appendChild(meta);
  }

  wrap.appendChild(main);
  routeTd.appendChild(wrap);
  tr.appendChild(routeTd);

  renderStatusCell(tr, parent.status);
  renderCorrCell(tr, parent);
  appendTextCell(tr, parent.session_id || "—");

  if (children.length) {
    tr.addEventListener("click", (event) => {
      if (event.target instanceof HTMLAnchorElement) return;
      if (event.target.closest("button")) return;
      toggleFamily(parent.correlation_id);
    });
    tr.tabIndex = 0;
    tr.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        toggleFamily(parent.correlation_id);
      }
    });
  } else if (!synthetic && parent.correlation_id) {
    bindFlatRowNav(tr, parent);
  } else {
    tr.classList.add("is-static");
  }

  tbody.appendChild(tr);
}

function renderChildRow(child, { isLast }) {
  const tr = document.createElement("tr");
  tr.classList.add("family-child");
  if (isLast) tr.classList.add("is-last-child");

  appendTextCell(tr, formatWhen(child.completed_at));
  appendTextCell(tr, formatWhen(child.started_at));

  const routeTd = document.createElement("td");
  const wrap = document.createElement("div");
  wrap.className = "route-cell route-cell--child";

  const tree = document.createElement("span");
  tree.className = "tree-branch";
  tree.setAttribute("aria-hidden", "true");
  tree.textContent = isLast ? "└" : "├";
  wrap.appendChild(tree);

  const main = document.createElement("div");
  main.className = "route-main";
  main.appendChild(renderRouteTitle(child));
  const role = document.createElement("span");
  role.className = "route-meta";
  role.textContent = "agent child";
  main.appendChild(role);
  wrap.appendChild(main);

  routeTd.appendChild(wrap);
  tr.appendChild(routeTd);

  renderStatusCell(tr, child.status);
  renderCorrCell(tr, child);
  appendTextCell(tr, child.session_id || "—");
  bindFlatRowNav(tr, child);
  tbody.appendChild(tr);
}

function renderRows(items) {
  tbody._lastItems = items;
  tbody.replaceChildren();

  if (listView === "flat") {
    panel?.classList.remove("is-nested");
    panel?.classList.add("is-flat");
    for (const row of items.slice().sort(sortByTimeDesc)) {
      renderFlatRow(row);
    }
    return;
  }

  panel?.classList.add("is-nested");
  panel?.classList.remove("is-flat");
  const families = groupFamilies(items);

  // Drop stale expand keys that are not on this page.
  const onPage = new Set(
    families.filter((f) => f.children.length).map((f) => f.parent.correlation_id),
  );
  for (const id of [...expanded]) {
    if (!onPage.has(id)) expanded.delete(id);
  }

  for (const family of families) {
    const groupStart = tbody.children.length;
    const open = family.children.length > 0 && expanded.has(family.parent.correlation_id);
    renderParentRow(family);
    if (open) {
      family.children.forEach((child, i) => {
        renderChildRow(child, { isLast: i === family.children.length - 1 });
      });
    }
    const rows = [...tbody.children].slice(groupStart);
    rows.forEach((row, i) => {
      row.classList.add("in-family");
      if (i === 0) row.classList.add("family-first");
      if (i === rows.length - 1) row.classList.add("family-last");
      if (family.children.length) row.dataset.family = family.parent.correlation_id;
    });
  }
}

function setListView(next, { persist = true } = {}) {
  const prev = listView;
  listView = next === "flat" ? "flat" : "nested";
  // Entering nested always starts fully collapsed.
  if (listView === "nested" && prev !== "nested") resetExpanded();
  for (const btn of viewBtns) {
    const active = btn.dataset.view === listView;
    btn.classList.toggle("is-active", active);
    btn.setAttribute("aria-pressed", active ? "true" : "false");
  }
  if (persist) {
    const url = new URL(window.location.href);
    if (listView === "flat") url.searchParams.set("view", "flat");
    else url.searchParams.delete("view");
    window.history.replaceState({}, "", url);
  }
  const last = tbody._lastItems;
  if (Array.isArray(last)) renderRows(last);
  updateStatusCopy(Array.isArray(last) ? last.length : 0);
}

function updateStatusCopy(itemCount) {
  if (!itemCount) {
    statusEl.textContent =
      statusFilter === "in_progress" ? "No in-progress workflows." : "No finished workflows yet.";
    return;
  }
  if (listView === "flat") {
    statusEl.textContent =
      "Flat list — every run on its own row. Click Route for Control Plane; correlation_id for the evidence chain.";
  } else {
    statusEl.textContent =
      "Nested — agent children group under the parent (closed). Click Route for Control Plane; expand parents for children; correlation_id for the chain.";
  }
}

function updatePager() {
  const from = total === 0 ? 0 : offset + 1;
  const to = Math.min(offset + PAGE_SIZE, total);
  pageLabel.textContent = total ? `${from}–${to} of ${total}` : "0 of 0";
  prevBtn.disabled = offset <= 0;
  nextBtn.disabled = offset + PAGE_SIZE >= total;
}

function setActiveTab(nextStatus) {
  statusFilter = nextStatus === "in_progress" ? "in_progress" : "completed";
  for (const tab of tabs) {
    const active = tab.dataset.status === statusFilter;
    tab.classList.toggle("is-active", active);
    tab.setAttribute("aria-selected", active ? "true" : "false");
    if (active && panel) {
      panel.setAttribute("aria-labelledby", tab.id);
    }
  }
  if (colWhen) {
    colWhen.textContent = statusFilter === "in_progress" ? "Updated" : "Finished";
  }
}

async function loadPage() {
  statusEl.textContent = "Loading…";
  // Fresh page data → every family closed again.
  if (listView === "nested") resetExpanded();
  try {
    const res = await fetch(
      `/api/workflows?status=${encodeURIComponent(statusFilter)}&limit=${PAGE_SIZE}&offset=${offset}`,
    );
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
    updateStatusCopy(items.length);
    updatePager();
  } catch (err) {
    statusEl.textContent = String(err);
    renderRows([]);
    total = 0;
    updatePager();
  }
}

function selectTab(nextStatus) {
  if (nextStatus === statusFilter) return;
  setActiveTab(nextStatus);
  offset = 0;
  resetExpanded();
  loadPage();
}

for (const tab of tabs) {
  tab.addEventListener("click", () => selectTab(tab.dataset.status));
  tab.addEventListener("keydown", (event) => {
    if (event.key !== "ArrowRight" && event.key !== "ArrowLeft") return;
    event.preventDefault();
    const idx = tabs.indexOf(tab);
    const next =
      event.key === "ArrowRight"
        ? tabs[(idx + 1) % tabs.length]
        : tabs[(idx - 1 + tabs.length) % tabs.length];
    next.focus();
    selectTab(next.dataset.status);
  });
}

for (const btn of viewBtns) {
  btn.addEventListener("click", () => setListView(btn.dataset.view));
}

prevBtn?.addEventListener("click", () => {
  offset = Math.max(0, offset - PAGE_SIZE);
  loadPage();
});

nextBtn?.addEventListener("click", () => {
  offset = offset + PAGE_SIZE;
  loadPage();
});

const params = new URLSearchParams(window.location.search);
const initial = params.get("status") === "in_progress" ? "in_progress" : "completed";
const initialView = params.get("view") === "flat" ? "flat" : "nested";
setActiveTab(initial);
setListView(initialView, { persist: false });
loadPage();
