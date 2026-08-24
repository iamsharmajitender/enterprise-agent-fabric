import { capabilityUsage } from "./capability-usage.js";
import {
  LIST_TAB_STATUSES,
  catalogStatus,
  catalogStatusClass,
  catalogStatusLabel,
  countCatalogStatuses,
  livePublishedInputs,
  parseListTabStatus,
} from "./catalog-status.js";

const pageEl = document.querySelector("#page");
const metaEl = document.querySelector("#table-meta");
const statusEl = document.querySelector("#status");

const SECTIONS = [
  {
    title: "Identity",
    fields: [
      ["route_id", "Route"],
      ["intent_label", "Intent"],
      ["autonomy_mode", "Autonomy"],
      ["route_version", "Route version"],
    ],
  },
  {
    title: "Activation",
    fields: [
      ["activation_target", "Activation target"],
      ["agent_client_id", "Agent client"],
    ],
  },
  {
    title: "Policy and model",
    fields: [
      ["policy_profile", "Policy"],
      ["model_profile", "Model"],
      ["fallback", "Fallback"],
      ["max_loop_steps", "Max loop steps"],
    ],
  },
  {
    title: "Tools and retrieval",
    stacked: true,
    fields: [
      ["manifest", "Manifest"],
      ["retrieval", "Retrieval"],
    ],
  },
  {
    title: "Memory",
    fields: [["memory_profile", "Memory profile"]],
  },
  {
    title: "Artifacts",
    fields: [
      ["workflow_id", "Workflow"],
      ["prompt_id", "Prompt"],
      ["output_schema_id", "Output schema"],
      ["eval_suite_id", "Eval suite"],
    ],
  },
  {
    title: "Access",
    fields: [
      ["required_claims", "Required claims"],
      ["channels", "Channels"],
      ["chat_visible", "Chat visible"],
    ],
  },
];

const CAPABILITY_SECTIONS = [
  {
    title: "Identity",
    fields: [
      ["id", "Capability"],
      ["version", "Version"],
      ["kind", "Kind"],
      ["owner", "Owner"],
      ["status", "Status"],
    ],
  },
  {
    title: "Description",
    fields: [["description", "Description"]],
  },
  {
    title: "Schemas",
    fields: [
      ["input_schema", "Input schema"],
      ["output_schema", "Output schema"],
    ],
  },
  {
    title: "Invoke",
    fields: [["invoke", "Invoke"]],
  },
  {
    title: "Docs",
    fields: [["snippet", "Snippet"]],
  },
];

const PROMPT_SECTIONS = [
  {
    title: "Identity",
    fields: [
      ["prompt_id", "Prompt"],
      ["prompt_version", "Version"],
      ["owner", "Owner"],
      ["status", "Status"],
    ],
  },
  {
    title: "Host",
    fields: [["host", "Host"]],
  },
  {
    title: "Roles",
    fields: [["by_llm_role", "Roles"]],
  },
];

const WORKFLOW_SECTIONS = [
  {
    title: "Identity",
    fields: [
      ["workflow_id", "Workflow"],
      ["workflow_version", "Version"],
      ["status", "Status"],
    ],
  },
];

const POLICY_LABEL = {
  high_risk_step_up: "High risk",
  read_only_standard: "Read only",
  low_risk_chat: "Low risk",
};

const KIND_LABEL = {
  domain: "Domain",
  agent: "Agent",
  agent_start: "Agent",
};

const KIND_CLASS = {
  domain: "kind-domain",
  agent: "kind-agent",
  agent_start: "kind-agent",
};

const CATALOG_PATH = {
  prompt_id: "prompts",
  workflow_id: "workflows",
  capability_id: "capabilities",
  manifest_id: "manifests",
  tool_manifest: "manifests",
};

const AUTONOMY_MODE_LABEL = {
  0: "Single inference",
  1: "Autonomous",
  2: "Deterministic",
  3: "Guided",
};

const AUTONOMY_MODE_CLASS = {
  0: "autonomy-single",
  1: "autonomy-autonomous",
  2: "autonomy-deterministic",
  3: "autonomy-guided",
};

const FIELD_LABEL = {
  pdp_action: "Action",
  ttl_hours: "TTL",
  by_llm_role: "By role",
  chat_visible: "Visible in chat",
  tool_manifest: "Manifest",
  properties: "Fields",
  retrieve_only: "Retrieve only",
  deterministic_prefetch: "Prefetch",
  autonomy_mode: "Autonomy",
};

function fieldLabel(key) {
  return String(key)
    .split(".")
    .filter(Boolean)
    .map((segment) => {
      if (Object.hasOwn(FIELD_LABEL, segment)) return FIELD_LABEL[segment];
      return segment
        .split("_")
        .filter(Boolean)
        .map((part) => {
          if (part === "id") return "ID";
          if (part === "url") return "URL";
          if (part === "ttl") return "TTL";
          return part.charAt(0).toUpperCase() + part.slice(1);
        })
        .join(" ");
    })
    .join(" · ");
}

const historyState = {
  routeId: null,
  selected: [],
  compare: false,
};

function resetHistory(routeId) {
  if (historyState.routeId !== routeId) {
    historyState.routeId = routeId;
    historyState.selected = [];
    historyState.compare = false;
  }
}

const capabilityHistoryState = {
  capabilityId: null,
  selected: [],
  compare: false,
};

function resetCapabilityHistory(capabilityId) {
  if (capabilityHistoryState.capabilityId !== capabilityId) {
    capabilityHistoryState.capabilityId = capabilityId;
    capabilityHistoryState.selected = [];
    capabilityHistoryState.compare = false;
  }
}

const promptHistoryState = { promptId: null, selected: [], compare: false };
const workflowHistoryState = { workflowId: null, selected: [], compare: false };
const manifestHistoryState = { manifestId: null, selected: [], compare: false };

function resetPromptHistory(promptId) {
  if (promptHistoryState.promptId !== promptId) {
    promptHistoryState.promptId = promptId;
    promptHistoryState.selected = [];
    promptHistoryState.compare = false;
  }
}

function resetWorkflowHistory(workflowId) {
  if (workflowHistoryState.workflowId !== workflowId) {
    workflowHistoryState.workflowId = workflowId;
    workflowHistoryState.selected = [];
    workflowHistoryState.compare = false;
  }
}

function resetManifestHistory(manifestId) {
  if (manifestHistoryState.manifestId !== manifestId) {
    manifestHistoryState.manifestId = manifestId;
    manifestHistoryState.selected = [];
    manifestHistoryState.compare = false;
  }
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text != null) node.textContent = text;
  return node;
}

function pill(text, extra) {
  return el("span", extra ? `chip ${extra}` : "chip", text);
}

function idLink(href, text, extra) {
  if (!href || isEmpty(text) || text === "none") return el("span", "empty", "—");
  const a = el("a", extra ? `id-link ${extra}` : "id-link", String(text));
  a.href = href;
  a.title = `Open ${text}`;
  a.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    go(href);
  });
  return a;
}

function catalogHref(key, id) {
  const collection = CATALOG_PATH[key];
  if (!collection || isEmpty(id) || id === "none") return "";
  return `/${collection}/${encodeURIComponent(String(id))}`;
}

function linkCell(href, text, extra) {
  const td = document.createElement("td");
  td.append(idLink(href, text, extra));
  return td;
}

const COUNT_ICON_SVG =
  'viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"';
const API_COUNT_ICON = `<svg ${COUNT_ICON_SVG}><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>`;
const AGENT_COUNT_ICON = `<svg ${COUNT_ICON_SVG}><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/></svg>`;

function isAgentKind(kind) {
  return kind === "agent" || kind === "agent_start";
}

function manifestKindCounts(tools, kinds) {
  let api = 0;
  let agent = 0;
  for (const tool of tools ?? []) {
    const id = String(tool?.capability_id ?? "").trim();
    const kind = id ? kinds.get(id) : undefined;
    if (isAgentKind(kind)) agent += 1;
    else api += 1;
  }
  return { api, agent };
}

async function loadCapabilityKinds() {
  const kinds = new Map();
  try {
    const res = await fetch("/api/capabilities?include=all");
    if (!res.ok) return kinds;
    const payload = await res.json();
    for (const cap of payload.capabilities ?? []) {
      const id = String(cap.id ?? "").trim();
      if (id) kinds.set(id, cap.kind);
    }
  } catch {
    /* Routes still render; unknown tools count as API. */
  }
  return kinds;
}

/** Small count badge (icon + number), same visual weight as History's revision pill. */
function countIcon(count, { label, svg, extraClass = "" }) {
  const node = el("span", extraClass ? `count-icon ${extraClass}` : "count-icon");
  node.title = label;
  node.setAttribute("aria-label", label);
  const glyph = el("span", "count-icon__glyph");
  glyph.setAttribute("aria-hidden", "true");
  glyph.innerHTML = svg;
  node.append(glyph, el("span", "count-icon__value", String(count)));
  return node;
}

function manifestCell(item, kinds = new Map()) {
  const td = document.createElement("td");
  const wrap = el("span", "cell-with-count");
  wrap.append(idLink(catalogHref("tool_manifest", item.tool_manifest), item.tool_manifest, "mono"));
  const tools = item.manifest?.tools;
  if (
    Array.isArray(tools) &&
    !isEmpty(item.tool_manifest) &&
    item.tool_manifest !== "none"
  ) {
    const { api, agent } = manifestKindCounts(tools, kinds);
    if (api > 0) {
      wrap.append(
        countIcon(api, {
          label: api === 1 ? "1 API" : `${api} APIs`,
          svg: API_COUNT_ICON,
          extraClass: "count-icon--api",
        }),
      );
    }
    if (agent > 0) {
      wrap.append(
        countIcon(agent, {
          label: agent === 1 ? "1 agent" : `${agent} agents`,
          svg: AGENT_COUNT_ICON,
          extraClass: "count-icon--agent",
        }),
      );
    }
  }
  td.append(wrap);
  return td;
}

function showError(message) {
  statusEl.hidden = false;
  statusEl.textContent = message;
}

function clearError() {
  statusEl.hidden = true;
  statusEl.textContent = "";
}

function policyClass(profile) {
  return profile === "high_risk_step_up" ? "risk" : "";
}

function retrievalMode(retrieval) {
  if (retrieval == null || typeof retrieval !== "object" || Array.isArray(retrieval)) {
    return null;
  }
  const mode = String(retrieval.mode ?? "").trim().toLowerCase();
  if (!mode || mode === "none" || mode === "omit") return null;
  return mode;
}

function hasRetrieval(retrieval) {
  return retrievalMode(retrieval) != null;
}

function retrievalChip(retrieval) {
  const mode = retrievalMode(retrieval);
  if (mode === "deterministic_prefetch") return "Retrieval · prefetch";
  if (mode === "tool") return "Retrieval · tool";
  if (mode) return `Retrieval · ${mode}`;
  return "";
}

function retrievalListLabel(retrieval) {
  const mode = retrievalMode(retrieval);
  if (mode === "deterministic_prefetch") return "Prefetch";
  if (mode === "tool") return "Tool";
  if (mode) return mode;
  return null;
}

function retrievalScope(retrieval) {
  if (!Array.isArray(retrieval?.scope)) return [];
  return retrieval.scope.filter((id) => id != null && String(id).trim() !== "");
}

function autonomyModeListLabel(code) {
  if (code == null || code === "") return null;
  return AUTONOMY_MODE_LABEL[code] ?? String(code);
}

function autonomyModeClass(code) {
  return AUTONOMY_MODE_CLASS[code] ?? "";
}

function autonomyPill(code) {
  const label = autonomyModeListLabel(code);
  if (isEmpty(label)) return el("span", "empty", "—");
  return pill(label, autonomyModeClass(code));
}

function autonomyCell(code) {
  const td = document.createElement("td");
  td.append(autonomyPill(code));
  return td;
}

const listSortState = Object.create(null);

function compareSortValues(left, right) {
  const emptyLeft = left == null || left === "" || Number.isNaN(left);
  const emptyRight = right == null || right === "" || Number.isNaN(right);
  if (emptyLeft && emptyRight) return 0;
  if (emptyLeft) return 1;
  if (emptyRight) return -1;
  if (typeof left === "number" && typeof right === "number") return left - right;
  return String(left).localeCompare(String(right), undefined, {
    numeric: true,
    sensitivity: "base",
  });
}

function sortMark(dir) {
  const mark = el("span", "sort-btn__mark", dir === "desc" ? "↓" : dir === "asc" ? "↑" : "↕");
  mark.setAttribute("aria-hidden", "true");
  return mark;
}

function policyLabel(profile) {
  return POLICY_LABEL[profile] ?? profile ?? "Policy";
}

function isEmpty(value) {
  return value == null || value === "" || (Array.isArray(value) && value.length === 0);
}

function isManifest(value) {
  return (
    value != null &&
    typeof value === "object" &&
    !Array.isArray(value) &&
    Object.hasOwn(value, "manifest_id") &&
    Object.hasOwn(value, "tools")
  );
}

function isObjectSchema(value) {
  return (
    value != null &&
    typeof value === "object" &&
    !Array.isArray(value) &&
    value.properties != null &&
    typeof value.properties === "object" &&
    !Array.isArray(value.properties)
  );
}

function schemaTypeLabel(schema) {
  if (schema == null || typeof schema !== "object") return "—";
  const type = schema.type;
  if (type === "array") {
    const itemType = schema.items?.type;
    return itemType ? `${itemType}[]` : "array";
  }
  if (Array.isArray(type)) return type.filter(Boolean).join(" | ");
  if (typeof type === "string" && type) return type;
  if (schema.properties) return "object";
  return "—";
}

function renderJsonSchema(schema) {
  const properties = schema.properties ?? {};
  const names = Object.keys(properties);
  if (names.length === 0) return el("span", "empty", "No fields");
  const required = new Set(Array.isArray(schema.required) ? schema.required : []);
  const root = el("div", "table-root table-root--primary");
  const scroll = el("div", "table__scroll-container");
  const table = document.createElement("table");
  table.className = "table__content table__content--compact";
  table.append(el("caption", "sr-only", "Schema fields"));
  const thead = document.createElement("thead");
  thead.className = "table__header";
  const headRow = el("tr", "table__row");
  for (const label of ["Field", "Type", "Required"]) {
    const th = el("th", "table__column", label);
    th.scope = "col";
    headRow.append(th);
  }
  thead.append(headRow);
  table.append(thead);
  const tbody = document.createElement("tbody");
  tbody.className = "table__body";
  for (const name of names) {
    const tr = el("tr", "table__row");
    tr.append(
      tableCell(el("span", "mono", name)),
      tableCell(el("span", "mono", schemaTypeLabel(properties[name]))),
      tableCell(
        required.has(name) ? pill("Required", "ok") : el("span", "empty", "Optional"),
      ),
    );
    tbody.append(tr);
  }
  table.append(tbody);
  scroll.append(table);
  root.append(scroll);
  return root;
}

function tableCell(child) {
  const td = el("td", "table__cell");
  td.append(child);
  return td;
}

function riskChip(tier) {
  if (isEmpty(tier)) return el("span", "empty", "—");
  const tone = tier === "high" ? "risk" : tier === "medium" ? "warn" : "ok";
  return pill(String(tier), tone);
}

function renderToolsTable(tools) {
  tools = Array.isArray(tools) ? tools : [];
  const root = el("div", "table-root table-root--primary");
  const scroll = el("div", "table__scroll-container");
  const table = document.createElement("table");
  table.className = "table__content";
  table.append(el("caption", "sr-only", "tools"));
  const thead = document.createElement("thead");
  thead.className = "table__header";
  const headRow = el("tr", "table__row");
  for (const label of ["Name", "Capability", "Version", "Action", "Risk"]) {
    const th = el("th", "table__column", label);
    th.scope = "col";
    headRow.append(th);
  }
  thead.append(headRow);
  table.append(thead);
  const tbody = document.createElement("tbody");
  tbody.className = "table__body";
  if (tools.length === 0) {
    const empty = el("td", "table__cell table__empty", "No tools");
    empty.colSpan = 5;
    const tr = el("tr", "table__row");
    tr.append(empty);
    tbody.append(tr);
  } else {
    for (const tool of tools) {
      const name = tool?.name ?? tool?.capability_id;
      const nameNode = tool?.capability_id
        ? idLink(catalogHref("capability_id", tool.capability_id), name, "mono")
        : isEmpty(name)
          ? el("span", "empty", "—")
          : el("span", "mono", name);
      const version = isEmpty(tool?.capability_version)
        ? el("span", "empty", "—")
        : el("span", "mono", tool.capability_version);
      const action = isEmpty(tool?.pdp_action)
        ? el("span", "empty", "—")
        : el("span", "mono", tool.pdp_action);
      const tr = el("tr", "table__row");
      tr.append(
        tableCell(nameNode),
        tableCell(idLink(catalogHref("capability_id", tool.capability_id), tool.capability_id, "mono")),
        tableCell(version),
        tableCell(action),
        tableCell(riskChip(tool?.risk_tier)),
      );
      tbody.append(tr);
    }
  }
  table.append(tbody);
  scroll.append(table);
  root.append(scroll);
  return root;
}

function renderWorkflowTable(workflow) {
  const card = el("article", "card card--default");
  card.setAttribute("aria-label", "Workflow stages");
  const stages = Array.isArray(workflow?.stages) ? workflow.stages : [];
  const header = el("div", "card__section-head");
  header.append(el("h3", "card__title", "Stages"), pill(String(stages.length)));
  const content = el("div", "card__content");
  content.append(renderStagesTable(stages));
  card.append(header, content);
  return card;
}

function stageBranch(branch) {
  if (branch == null || typeof branch !== "object" || Array.isArray(branch)) return null;
  const entries = Object.entries(branch);
  if (entries.length === 0) return null;
  const wrap = el("span", "chips");
  for (const [from, to] of entries) {
    wrap.append(pill(`${from} → ${to}`, "mono"));
  }
  return wrap;
}

function renderStagesTable(stages) {
  const root = el("div", "table-root table-root--primary");
  const scroll = el("div", "table__scroll-container");
  const table = document.createElement("table");
  table.className = "table__content";
  table.append(el("caption", "sr-only", "stages"));
  const thead = document.createElement("thead");
  thead.className = "table__header";
  const headRow = el("tr", "table__row");
  for (const label of ["Stage", "Tool", "Type", "LLM role", "Corpus", "Branch", "Gates"]) {
    const th = el("th", "table__column", label);
    th.scope = "col";
    headRow.append(th);
  }
  thead.append(headRow);
  table.append(thead);
  const tbody = document.createElement("tbody");
  tbody.className = "table__body";
  if (stages.length === 0) {
    const empty = el("td", "table__cell table__empty", "No stages");
    empty.colSpan = 7;
    const tr = el("tr", "table__row");
    tr.append(empty);
    tbody.append(tr);
  } else {
    for (const stage of stages) {
      const gates = el("span", "chips");
      if (stage?.side_effect) gates.append(pill("Side effect", "warn"));
      if (stage?.requires_approval) gates.append(pill("Approval", "risk"));
      const tr = el("tr", "table__row");
      tr.append(
        tableCell(
          isEmpty(stage?.id) ? el("span", "empty", "—") : el("span", "mono", stage.id),
        ),
        tableCell(
          isEmpty(stage?.tool)
            ? el("span", "empty", "—")
            : idLink(catalogHref("capability_id", stage.tool), stage.tool, "mono"),
        ),
        tableCell(
          isEmpty(stage?.type) ? el("span", "empty", "—") : el("span", "", fieldLabel(stage.type)),
        ),
        tableCell(
          isEmpty(stage?.llm_role) || stage.llm_role === "none"
            ? el("span", "empty", "—")
            : el("span", "", fieldLabel(stage.llm_role)),
        ),
        tableCell(
          isEmpty(stage?.corpus) ? el("span", "empty", "—") : el("span", "mono", stage.corpus),
        ),
        tableCell(stageBranch(stage?.branch) ?? el("span", "empty", "—")),
        tableCell(gates.childNodes.length === 0 ? el("span", "empty", "—") : gates),
      );
      tbody.append(tr);
    }
  }
  table.append(tbody);
  scroll.append(table);
  root.append(scroll);
  return root;
}

function renderManifestTable(manifest, heading = "h3") {
  const card = el("article", "card card--default");
  card.setAttribute("aria-label", "Manifest");
  const header = el("header", "card__header");
  header.append(el(heading, "card__title", "Manifest"));
  const dl = document.createElement("dl");
  const idValue = el("dd");
  idValue.append(idLink(catalogHref("manifest_id", manifest.manifest_id), manifest.manifest_id, "mono"));
  const versionValue = el("dd");
  versionValue.append(
    isEmpty(manifest.manifest_version)
      ? el("span", "empty", "—")
      : el("span", "mono", manifest.manifest_version),
  );
  const descriptionValue = el("dd");
  descriptionValue.append(
    isEmpty(manifest.description)
      ? el("span", "empty", "—")
      : document.createTextNode(manifest.description),
  );
  dl.append(
    el("dt", "", "Manifest ID"),
    idValue,
    el("dt", "", "Version"),
    versionValue,
    el("dt", "", "Description"),
    descriptionValue,
  );
  const tools = Array.isArray(manifest.tools) ? manifest.tools : [];
  const toolsHead = el("div", "card__section-head");
  const toolsHeading = heading === "h3" ? "h4" : "h5";
  toolsHead.append(el(toolsHeading, "card__title", "Tools"), pill(String(tools.length)));
  const content = el("div", "card__content");
  content.append(dl, el("hr", "separator"), toolsHead, renderToolsTable(tools));
  card.append(header, content);
  return card;
}

function renderValue(value, key, extra = {}) {
  if (key === "status") {
    return statusPill({ status: value, live: extra.live, active: extra.active });
  }
  if (key === "kind") {
    return kindPill(value);
  }
  if (key === "autonomy_mode") {
    return autonomyPill(value);
  }
  if (key && Object.hasOwn(CATALOG_PATH, key)) {
    return idLink(catalogHref(key, value), value, "mono");
  }
  if (isEmpty(value)) return el("span", "empty", "—");
  if (typeof value === "boolean") return document.createTextNode(value ? "Yes" : "No");
  if (isManifest(value)) return renderManifestTable(value);
  if (isObjectSchema(value)) return renderJsonSchema(value);
  if (Array.isArray(value)) {
    const scalars = value.every((item) => item == null || typeof item !== "object");
    if (scalars) {
      const wrap = el("span", "chips");
      for (const item of value) {
        if (item == null) continue;
        wrap.append(pill(String(item), "mono"));
      }
      return wrap;
    }
    const list = el("div", "nested-list");
    for (const item of value) list.append(renderValue(item));
    return list;
  }
  if (typeof value === "object") {
    const nested = el("div", "nested");
    for (const [nestedKey, nestedValue] of Object.entries(value)) {
      const row = el("div", "nested-row");
      row.append(el("span", "", fieldLabel(nestedKey)));
      const cell = el("span");
      cell.append(renderValue(nestedValue, nestedKey));
      row.append(cell);
      nested.append(row);
    }
    return nested;
  }
  return document.createTextNode(String(value));
}

function isPlainRecord(value) {
  return value != null && typeof value === "object" && !Array.isArray(value);
}

function isRoleSpec(value) {
  return isPlainRecord(value) && (Object.hasOwn(value, "text") || Object.hasOwn(value, "task_type"));
}

function renderExpandedValue(key, value, extra) {
  if (key === "kind") {
    return kindPill(value);
  }
  if (key === "ttl_hours" && value != null && value !== "") {
    return document.createTextNode(`${value} hours`);
  }
  if (key === "eval_suite_id" && isEmpty(value)) {
    const dash = el("span", "empty", "—");
    dash.title =
      "No per-route quality suite. Empty is correct for free-form chat. Routing labels are the Data Plane golden set, not this field.";
    return dash;
  }
  if (key && Object.hasOwn(CATALOG_PATH, key)) {
    if (isEmpty(value)) return el("span", "empty", "—");
    return idLink(catalogHref(key, value), fieldLabel(String(value)));
  }
  if (typeof value === "string" && /^[a-z][a-z0-9_]*$/.test(value)) {
    return document.createTextNode(fieldLabel(value));
  }
  return renderValue(value, key, extra);
}

function appendDlField(dl, label, value, key, extra, wide = false) {
  const dt = el("dt", wide ? "field-wide" : "", label);
  const dd = el("dd", wide ? "field-wide" : "");
  dd.append(renderExpandedValue(key, value, extra));
  dl.append(dt, dd);
}

function appendExpandedFields(dl, value, extra) {
  for (const [key, nested] of Object.entries(value)) {
    if (isRoleSpec(nested)) {
      const dt = el("dt", "", fieldLabel(key));
      const dd = el("dd", "role-value");
      if (nested.task_type) dd.append(pill(fieldLabel(String(nested.task_type))));
      if (!isEmpty(nested.text)) dd.append(el("p", "role-text", String(nested.text)));
      for (const [nestedKey, nestedValue] of Object.entries(nested)) {
        if (nestedKey === "task_type" || nestedKey === "text") continue;
        const extraRow = el("div", "role-extra");
        extraRow.append(el("span", "", fieldLabel(nestedKey)));
        extraRow.append(renderExpandedValue(nestedKey, nestedValue, extra));
        dd.append(extraRow);
      }
      dl.append(dt, dd);
      continue;
    }
    appendDlField(dl, fieldLabel(key), nested, key, extra);
  }
}

function renderEmptyCard(title, value, key, extra) {
  const card = el("article", "card card--default");
  card.setAttribute("aria-label", title);
  const header = el("header", "card__header");
  header.append(el("h4", "card__title", title));
  const content = el("div", "card__content");
  if (isEmpty(value)) content.append(el("span", "empty", "—"));
  else content.append(renderValue(value, key, extra));
  card.append(header, content);
  return card;
}

function renderRetrievalCard(value) {
  const card = el("article", "card card--default");
  card.setAttribute("aria-label", "Retrieval");
  const header = el("header", "card__header");
  const head = el("div", "card__section-head");
  head.append(el("h4", "card__title", "Retrieval"));
  if (hasRetrieval(value)) {
    head.append(pill(retrievalListLabel(value), "info"));
  }
  header.append(head);
  const content = el("div", "card__content");
  if (!hasRetrieval(value)) {
    content.append(el("span", "empty", "—"));
  } else {
    const dl = document.createElement("dl");
    const scope = retrievalScope(value);
    appendDlField(dl, "Scope", scope.length === 0 ? null : scope, "scope");
    content.append(dl);
  }
  card.append(header, content);
  return card;
}

function renderStackedField(key, label, value, extra) {
  if (key === "manifest") {
    return isManifest(value)
      ? renderManifestTable(value, "h4")
      : renderEmptyCard("Manifest", value, key, extra);
  }
  if (key === "retrieval") return renderRetrievalCard(value);
  return renderEmptyCard(label, value, key, extra);
}

function buildSection(section, row, extra = {}) {
  const block = el("section", "section");
  block.append(el("h3", "", section.title));
  if (section.stacked) {
    const stack = el("div", "section-stack");
    for (const [key, label] of section.fields) {
      stack.append(renderStackedField(key, label, row[key], extra));
    }
    block.append(stack);
    return block;
  }
  const dl = document.createElement("dl");
  appendSectionFields(dl, section.fields, row, extra);
  block.append(dl);
  return block;
}

function appendSectionField(dl, key, label, value, extra) {
  if (isManifest(value) || isObjectSchema(value)) {
    appendDlField(dl, label, value, key, extra, true);
    return;
  }
  if (isPlainRecord(value)) {
    if (Object.keys(value).length === 0) {
      appendDlField(dl, label, null, key, extra);
      return;
    }
    appendExpandedFields(dl, value, extra);
    return;
  }
  appendDlField(dl, label, value, key, extra);
}

function appendSectionFields(dl, fields, row, extra = {}) {
  for (const [key, label] of fields) {
    appendSectionField(dl, key, label, row[key], extra);
  }
}

const CATALOG_ICON_SVG =
  'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"';
const CATALOG_ICONS = {
  routes: `<svg ${CATALOG_ICON_SVG}><circle cx="6" cy="6" r="2.5"/><circle cx="18" cy="6" r="2.5"/><circle cx="12" cy="18" r="2.5"/><path d="M18 8.5v1.2c0 .7-.6 1.3-1.3 1.3H7.3C6.6 11 6 10.4 6 9.7V8.5"/><path d="M12 12.5v3"/></svg>`,
  capabilities: `<svg ${CATALOG_ICON_SVG}><path d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09A1.65 1.65 0 0 0 15 4.6a1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>`,
  prompts: `<svg ${CATALOG_ICON_SVG}><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"/><path d="M8 12h10a2 2 0 0 1 2 2v6l-3-2h-7a2 2 0 0 1-2-2v-4a2 2 0 0 1 2-2z"/></svg>`,
  workflows: `<svg ${CATALOG_ICON_SVG}><rect x="9" y="2" width="6" height="5" rx="1"/><rect x="2" y="17" width="6" height="5" rx="1"/><rect x="16" y="17" width="6" height="5" rx="1"/><path d="M12 7v4M5 17v-2.5A1.5 1.5 0 0 1 6.5 13h11a1.5 1.5 0 0 1 1.5 1.5V17"/></svg>`,
  manifests: `<svg ${CATALOG_ICON_SVG}><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h6M9 9h2"/></svg>`,
};

function catalogIcon(kind) {
  const node = el("span", "catalog-row__icon");
  node.setAttribute("aria-hidden", "true");
  const svg = CATALOG_ICONS[kind];
  if (svg) node.innerHTML = svg;
  return node;
}

function skeletonCards() {
  const catalog = el("div", "catalog");
  catalog.setAttribute("aria-busy", "true");
  catalog.setAttribute("aria-label", "Loading catalogue counts");
  for (let i = 0; i < 5; i += 1) {
    const row = el("section", "catalog-row");
    row.append(el("div", "skel catalog-row__skel"));
    const tiles = el("div", "catalog-row__tiles");
    for (let j = 0; j < 4; j += 1) {
      const tile = el("div", "tile tile--default");
      tile.append(el("div", "skel skel-title"), el("div", "skel skel-value"));
      tiles.append(tile);
    }
    row.append(tiles);
    catalog.append(row);
  }
  pageEl.replaceChildren(catalog);
}

function skeletonTable() {
  const wrap = el("div", "skeleton");
  wrap.setAttribute("aria-hidden", "true");
  wrap.setAttribute("aria-label", "Loading routes");
  for (let i = 0; i < 6; i += 1) wrap.append(el("div", "skel"));
  pageEl.replaceChildren(wrap);
}

function buildStatusTile({ status, count, href }) {
  const tone = catalogStatusClass(status) || "default";
  const tile = el("a", `tile tile--${tone}`);
  tile.href = href;
  tile.setAttribute(
    "aria-label",
    `${catalogStatusLabel(status)}, ${count}`,
  );
  tile.addEventListener("click", (event) => {
    event.preventDefault();
    go(href);
  });
  tile.append(
    el("p", "tile__label", catalogStatusLabel(status)),
    el("p", "tile__value", String(count)),
  );
  return tile;
}

function buildCatalogRow({ title, href, icon, counts }) {
  const section = el("section", "catalog-row");
  const headingId = `catalog-${title.toLowerCase()}-title`;
  const heading = el("h2", "catalog-row__title");
  heading.id = headingId;
  const link = el("a", "catalog-row__link");
  link.href = href;
  link.append(catalogIcon(icon), el("span", "catalog-row__name", title));
  link.addEventListener("click", (event) => {
    event.preventDefault();
    go(href);
  });
  heading.append(link);
  const tiles = el("div", "catalog-row__tiles");
  for (const status of LIST_TAB_STATUSES) {
    tiles.append(
      buildStatusTile({
        status,
        count: counts[status] ?? 0,
        href: listTabHref(href, status),
      }),
    );
  }
  section.setAttribute("aria-labelledby", headingId);
  section.append(heading, tiles);
  return section;
}

function migrateLegacyHash() {
  const raw = location.hash.replace(/^#\/?/, "");
  if (!raw) return;
  const parts = raw.split("/").filter(Boolean).map((part) => decodeURIComponent(part));
  if (!parts[0] || parts[0] === "routes") return;
  const next =
    parts[1] === "history"
      ? `/routes/${encodeURIComponent(parts[0])}/history`
      : parts[1]
        ? `/routes/${encodeURIComponent(parts[0])}/${encodeURIComponent(parts[1])}`
        : `/routes/${encodeURIComponent(parts[0])}`;
  history.replaceState({}, "", next);
}

function parsePath() {
  const path = location.pathname.replace(/\/+$/, "") || "/";
  if (path === "/") return { page: "home" };
  if (path === "/routes") return { page: "routes" };
  if (path === "/capabilities") return { page: "capabilities" };
  if (path === "/prompts") return { page: "prompts" };
  if (path === "/workflows") return { page: "workflows" };
  if (path === "/manifests") return { page: "manifests" };
  if (path === "/capability/usage") return { page: "usage" };
  const promptMatch = path.match(/^\/prompts\/([^/]+)(?:\/([^/]+))?$/);
  if (promptMatch) {
    const promptId = decodeURIComponent(promptMatch[1] ?? "");
    const rest = promptMatch[2] ? decodeURIComponent(promptMatch[2]) : "";
    if (rest === "history") return { page: "prompt-history", promptId };
    if (rest) return { page: "prompt", promptId, version: rest };
    return { page: "prompt", promptId };
  }
  const workflowMatch = path.match(/^\/workflows\/([^/]+)(?:\/([^/]+))?$/);
  if (workflowMatch) {
    const workflowId = decodeURIComponent(workflowMatch[1] ?? "");
    const rest = workflowMatch[2] ? decodeURIComponent(workflowMatch[2]) : "";
    if (rest === "history") return { page: "workflow-history", workflowId };
    if (rest) return { page: "workflow", workflowId, version: rest };
    return { page: "workflow", workflowId };
  }
  const manifestMatch = path.match(/^\/manifests\/([^/]+)(?:\/([^/]+))?$/);
  if (manifestMatch) {
    const manifestId = decodeURIComponent(manifestMatch[1] ?? "");
    const rest = manifestMatch[2] ? decodeURIComponent(manifestMatch[2]) : "";
    if (rest === "history") return { page: "manifest-history", manifestId };
    if (rest) return { page: "manifest", manifestId, version: rest };
    return { page: "manifest", manifestId };
  }
  const capMatch = path.match(/^\/capabilities\/([^/]+)(?:\/([^/]+))?$/);
  if (capMatch) {
    const capabilityId = decodeURIComponent(capMatch[1] ?? "");
    const rest = capMatch[2] ? decodeURIComponent(capMatch[2]) : "";
    if (rest === "history") return { page: "capability-history", capabilityId };
    if (rest) return { page: "capability", capabilityId, version: rest };
    return { page: "capability", capabilityId };
  }
  const match = path.match(/^\/routes\/([^/]+)(?:\/([^/]+))?$/);
  if (!match) return { page: "home" };
  const routeId = decodeURIComponent(match[1] ?? "");
  const rest = match[2] ? decodeURIComponent(match[2]) : "";
  if (rest === "history") return { page: "history", routeId };
  if (rest) return { page: "route", routeId, routeVersion: rest };
  return { page: "route", routeId };
}

function go(path, state) {
  history.pushState(state ?? {}, "", path);
  void renderFromPath();
}

async function renderFromPath() {
  const parsed = parsePath();
  if (parsed.page === "prompt-history") return showPromptHistory(parsed.promptId);
  if (parsed.page === "prompt") return showPrompt(parsed.promptId, parsed.version);
  if (parsed.page === "prompts") return showPrompts();
  if (parsed.page === "workflow-history") return showWorkflowHistory(parsed.workflowId);
  if (parsed.page === "workflow") return showWorkflow(parsed.workflowId, parsed.version);
  if (parsed.page === "workflows") return showWorkflows();
  if (parsed.page === "manifest-history") return showManifestHistory(parsed.manifestId);
  if (parsed.page === "manifest") return showManifest(parsed.manifestId, parsed.version);
  if (parsed.page === "manifests") return showManifests();
  if (parsed.page === "usage") return showUsage();
  if (parsed.page === "capability-history") return showCapabilityHistory(parsed.capabilityId);
  if (parsed.page === "capability") return showCapability(parsed.capabilityId, parsed.version);
  if (parsed.page === "capabilities") return showCapabilities();
  if (parsed.page === "history") return showHistory(parsed.routeId);
  if (parsed.page === "route") return showRoute(parsed.routeId, parsed.routeVersion);
  if (parsed.page === "routes") return showRoutes();
  return showLanding();
}

function clearMeta() {
  metaEl.replaceChildren();
}

async function refreshMeta() {
  clearMeta();
}

function goRoutes() {
  historyState.routeId = null;
  historyState.selected = [];
  historyState.compare = false;
  go("/routes");
}

function goCapabilities() {
  capabilityHistoryState.capabilityId = null;
  capabilityHistoryState.selected = [];
  capabilityHistoryState.compare = false;
  go("/capabilities");
}

function kindLabel(kind) {
  return KIND_LABEL[kind] ?? kind ?? "Kind";
}

function kindClass(kind) {
  return KIND_CLASS[kind] ?? "";
}

function kindPill(kind) {
  return pill(kindLabel(kind), kindClass(kind));
}

function kindCell(kind) {
  const td = document.createElement("td");
  td.append(kindPill(kind));
  return td;
}

function listTabStatus() {
  return parseListTabStatus(new URL(location.href).searchParams.get("status"));
}

function listTabHref(basePath, status) {
  return status === "active" ? basePath : `${basePath}?status=${encodeURIComponent(status)}`;
}

function livePublishedStatuses(items, idKey, versionKey) {
  return livePublishedInputs(
    items.map((item) => ({
      id: item[idKey],
      version: item[versionKey],
      status: item.status,
    })),
  ).map((input) => catalogStatus(input));
}

function countResolvedStatuses(statuses) {
  const counts = { draft: 0, published: 0, active: 0, retired: 0, total: statuses.length };
  for (const status of statuses) counts[status] += 1;
  return counts;
}

function buildStatusTabs({ basePath, counts, selected }) {
  const tablist = el("div", "status-tabs");
  tablist.setAttribute("role", "tablist");
  tablist.setAttribute("aria-label", "Filter by status");
  for (const status of LIST_TAB_STATUSES) {
    const selectedNow = status === selected;
    const tone = catalogStatusClass(status);
    const tab = el(
      "button",
      ["status-tabs__tab", "chip", tone, selectedNow && "is-selected"]
        .filter(Boolean)
        .join(" "),
    );
    tab.dataset.status = status;
    tab.type = "button";
    tab.id = `status-tab-${status}`;
    tab.setAttribute("role", "tab");
    tab.setAttribute("aria-selected", String(selectedNow));
    tab.setAttribute("aria-controls", "status-tab-panel");
    tab.tabIndex = selectedNow ? 0 : -1;
    tab.append(document.createTextNode(catalogStatusLabel(status)));
    tab.append(el("span", "status-tabs__count", String(counts[status] ?? 0)));
    tab.addEventListener("click", () => go(listTabHref(basePath, status), { fromTab: true }));
    tablist.append(tab);
  }
  tablist.addEventListener("keydown", (event) => {
    const index = LIST_TAB_STATUSES.indexOf(selected);
    let next = -1;
    if (event.key === "ArrowRight" || event.key === "ArrowDown") {
      next = (index + 1) % LIST_TAB_STATUSES.length;
    } else if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
      next = (index - 1 + LIST_TAB_STATUSES.length) % LIST_TAB_STATUSES.length;
    } else if (event.key === "Home") {
      next = 0;
    } else if (event.key === "End") {
      next = LIST_TAB_STATUSES.length - 1;
    }
    if (next < 0) return;
    event.preventDefault();
    go(listTabHref(basePath, LIST_TAB_STATUSES[next]), { fromTab: true });
  });
  return tablist;
}

function statusPill(input) {
  const status = catalogStatus(input);
  return pill(catalogStatusLabel(status), catalogStatusClass(status));
}

function statusCell(input) {
  const td = document.createElement("td");
  td.append(statusPill(input));
  return td;
}

async function showLanding() {
  clearError();
  document.body.classList.remove(
    "showing-detail",
    "showing-history",
    "showing-routes",
    "showing-capabilities",
    "showing-prompts",
    "showing-workflows",
    "showing-manifests",
    "showing-usage",
  );
  document.body.classList.add("showing-home");
  document.title = "Enterprise Agent Fabric";
  clearMeta();
  skeletonCards();
  const [res, capsRes, promptsRes, workflowsRes, manifestsRes] = await Promise.all([
    fetch("/api/routes?include=all"),
    fetch("/api/capabilities?include=all"),
    fetch("/api/prompts?include=all"),
    fetch("/api/workflows?include=all"),
    fetch("/api/manifests?include=all"),
  ]);
  if (!res.ok) {
    pageEl.replaceChildren();
    showError(`Catalogue read failed (${res.status}).`);
    return;
  }
  const table = await res.json();
  const routes = Array.isArray(table.routes) ? table.routes : [];
  let capabilities = [];
  if (capsRes.ok) {
    const payload = await capsRes.json();
    capabilities = Array.isArray(payload.capabilities) ? payload.capabilities : [];
  }
  let prompts = [];
  if (promptsRes.ok) {
    const payload = await promptsRes.json();
    prompts = Array.isArray(payload.prompts) ? payload.prompts : [];
  }
  let workflows = [];
  if (workflowsRes.ok) {
    const payload = await workflowsRes.json();
    workflows = Array.isArray(payload.workflows) ? payload.workflows : [];
  }
  let manifests = [];
  if (manifestsRes.ok) {
    const payload = await manifestsRes.json();
    manifests = Array.isArray(payload.manifests) ? payload.manifests : [];
  }
  const routeCounts = countCatalogStatuses(
    routes.map((route) => ({ status: route.status, active: route.active })),
  );
  const capabilityCounts = countCatalogStatuses(
    livePublishedInputs(
      capabilities.map((item) => ({ id: item.id, version: item.version, status: item.status })),
    ),
  );
  const promptCounts = countCatalogStatuses(
    livePublishedInputs(
      prompts.map((item) => ({
        id: item.prompt_id,
        version: item.prompt_version,
        status: item.status,
      })),
    ),
  );
  const workflowCounts = countCatalogStatuses(
    livePublishedInputs(
      workflows.map((item) => ({
        id: item.workflow_id,
        version: item.workflow_version,
        status: item.status ?? "published",
      })),
    ),
  );
  const manifestCounts = countCatalogStatuses(
    livePublishedInputs(
      manifests.map((item) => ({
        id: item.manifest_id,
        version: item.manifest_version,
        status: item.status ?? "published",
      })),
    ),
  );
  const catalog = el("div", "catalog");
  catalog.append(
    buildCatalogRow({ title: "Routes", href: "/routes", icon: "routes", counts: routeCounts }),
    buildCatalogRow({ title: "Capabilities", href: "/capabilities", icon: "capabilities", counts: capabilityCounts }),
    buildCatalogRow({ title: "Prompts", href: "/prompts", icon: "prompts", counts: promptCounts }),
    buildCatalogRow({ title: "Workflows", href: "/workflows", icon: "workflows", counts: workflowCounts }),
    buildCatalogRow({ title: "Manifests", href: "/manifests", icon: "manifests", counts: manifestCounts }),
  );
  pageEl.replaceChildren(catalog);
  pageEl.focus();
  if (!capsRes.ok) showError(`Capability registry read failed (${capsRes.status}).`);
}

async function showRoutes() {
  let kinds = new Map();
  return showResourceList({
    bodyClass: "showing-routes",
    title: "Routes",
    api: "/api/routes?include=all",
    itemsKey: "routes",
    basePath: "/routes",
    noun: "routes",
    columns: ["Route", "Intent", "Autonomy", "Description", "Model", "Policy", "Manifest", "Prompt", "Retrieval", "Chat"],
    error: "Catalogue read failed ({status}).",
    caption: "Routes in the selected status. Activate a row to open route detail.",
    ready: loadCapabilityKinds().then((map) => {
      kinds = map;
    }),
    statusesOf: (items) =>
      items.map((item) => catalogStatus({ status: item.status, active: item.active })),
    hrefOf: (item) =>
      item.active
        ? `/routes/${encodeURIComponent(item.route_id)}`
        : `/routes/${encodeURIComponent(item.route_id)}/${encodeURIComponent(item.route_version)}`,
    cellsOf: (item) => [
      idHeadCell(item.route_id),
      cell(item.intent_label),
      autonomyCell(item.autonomy_mode),
      cell(item.description, "clip"),
      cell(item.model_profile, "mono"),
      cell(item.policy_profile ? policyLabel(item.policy_profile) : null),
      manifestCell(item, kinds),
      linkCell(catalogHref("prompt_id", item.prompt_id), item.prompt_id, "mono"),
      cell(retrievalListLabel(item.retrieval)),
      cell(item.chat_visible == null ? null : item.chat_visible ? "Yes" : "No"),
    ],
    sortKeys: {
      Autonomy: (item) => {
        const code = Number(item.autonomy_mode);
        return Number.isFinite(code) ? code : autonomyModeListLabel(item.autonomy_mode);
      },
      Description: (item) => item.description ?? "",
    },
  });
}

async function showCapabilities() {
  return showResourceList({
    bodyClass: "showing-capabilities",
    title: "Capabilities",
    api: "/api/capabilities?include=all",
    itemsKey: "capabilities",
    basePath: "/capabilities",
    noun: "capabilities",
    columns: ["Capability", "Kind", "Description", "Owner", "Version"],
    error: "Capability registry read failed ({status}).",
    caption: "Capabilities in the selected status. Activate a row to open detail.",
    statusesOf: (items) => livePublishedStatuses(items, "id", "version"),
    hrefOf: (item, status) =>
      status === "active"
        ? `/capabilities/${encodeURIComponent(item.id)}`
        : `/capabilities/${encodeURIComponent(item.id)}/${encodeURIComponent(item.version)}`,
    cellsOf: (item) => [
      idHeadCell(item.id),
      kindCell(item.kind),
      cell(item.description, "clip"),
      cell(item.owner, "mono"),
      cell(item.version, "mono"),
    ],
  });
}

async function showCapability(capabilityId, version) {
  clearError();
  resetCapabilityHistory(capabilityId);
  document.body.classList.remove("showing-history", "showing-routes", "showing-capabilities");
  document.body.classList.add("showing-detail");
  document.title = `${capabilityId} · Control Plane`;
  void refreshMeta();
  const path = `/api/capabilities/${encodeURIComponent(capabilityId)}`;
  const rowUrl = version ? `${path}?version=${encodeURIComponent(version)}` : path;
  const [res, versionsRes, manifestsRes, routesRes] = await Promise.all([
    fetch(rowUrl),
    fetch(`${path}/versions`),
    fetch("/api/manifests"),
    fetch("/api/routes"),
  ]);
  if (!res.ok) {
    showError(`Capability ${capabilityId} was not found.`);
    return;
  }
  const row = await res.json();
  const versionsPayload = versionsRes.ok ? await versionsRes.json() : { versions: [] };
  const revisionCount = Array.isArray(versionsPayload.versions)
    ? versionsPayload.versions.length
    : 0;

  const back = el("button", "back page-back", "← Capabilities");
  back.type = "button";
  back.addEventListener("click", () => goCapabilities());

  const kicker = el("p", "detail-kicker");
  kicker.append(kindPill(row.kind));
  const head = el("div", "detail-head");
  head.append(
    back,
    kicker,
    el("h2", "", row.id),
    el("p", "lead", row.description ?? ""),
  );
  const chips = el("div", "chip-row");
  chips.append(pill(row.version ?? "unversioned", "mono"));
  chips.append(
    statusPill({
      status: row.status,
      live: !version && (row.status === "published" || !row.status),
    }),
  );
  if (row.owner) chips.append(pill(row.owner, "mono"));

  const historyBtn = el("button", "ghost-btn");
  historyBtn.type = "button";
  historyBtn.append("History");
  historyBtn.append(pill(String(revisionCount), "mono"));
  historyBtn.setAttribute(
    "aria-label",
    revisionCount === 1 ? "History, 1 revision" : `History, ${revisionCount} revisions`,
  );
  historyBtn.addEventListener("click", () => {
    go(`/capabilities/${encodeURIComponent(capabilityId)}/history`, {
      capabilityId,
      page: "capability-history",
    });
  });

  const jsonBtn = el("button", "ghost-btn", "JSON");
  jsonBtn.type = "button";
  jsonBtn.setAttribute("aria-expanded", "false");
  jsonBtn.setAttribute("aria-controls", "capability-json");

  const actions = el("div", "chip-actions");
  actions.append(historyBtn, jsonBtn);
  const bar = el("div", "chip-bar");
  bar.append(chips, actions);
  head.append(bar);

  const sections = [];
  for (const section of CAPABILITY_SECTIONS) {
    sections.push(
      buildSection(section, row, {
        live: !version && (row.status === "published" || !row.status),
      }),
    );
  }

  let usedBy = [];
  if (manifestsRes.ok) {
    const payload = await manifestsRes.json();
    const routesPayload = routesRes.ok ? await routesRes.json() : { routes: [] };
    const rowUsage = capabilityUsage(
      payload.manifests ?? [],
      [row],
      routesPayload.routes ?? [],
    ).find((item) => item.capability_id === capabilityId);
    usedBy = rowUsage?.uses ?? [];
  }
  sections.push(buildUsedBySection(usedBy));

  const jsonPanel = buildJsonPanel(row, "Capability JSON", "capability-json");
  jsonPanel.hidden = true;
  jsonBtn.addEventListener("click", () => {
    const open = jsonPanel.hidden;
    jsonPanel.hidden = !open;
    jsonBtn.setAttribute("aria-expanded", String(open));
    jsonBtn.setAttribute("aria-pressed", String(open));
    for (const block of sections) block.hidden = open;
    if (open) jsonPanel.querySelector("summary")?.focus();
  });

  pageEl.replaceChildren(head, jsonPanel, ...sections);
  pageEl.focus();
}

async function showCapabilityHistory(capabilityId) {
  clearError();
  resetCapabilityHistory(capabilityId);
  document.body.classList.remove("showing-detail", "showing-routes", "showing-capabilities");
  document.body.classList.add("showing-history");
  document.title = `${capabilityId} history · Control Plane`;
  void refreshMeta();
  const res = await fetch(`/api/capabilities/${encodeURIComponent(capabilityId)}/versions`);
  if (!res.ok) {
    showError(`History for ${capabilityId} was not found.`);
    return;
  }
  const payload = await res.json();
  const versions = payload.versions ?? [];
  const latestVersion = versions[0]?.version;

  const back = el("button", "back page-back", "← Capability");
  back.type = "button";
  back.addEventListener("click", () => {
    go(`/capabilities/${encodeURIComponent(capabilityId)}`, { capabilityId });
  });

  const head = el("div", "detail-head");
  head.append(
    back,
    el("p", "detail-kicker", "Version history"),
    el("h2", "", capabilityId),
    el("p", "lead", `${versions.length} versions · newest first`),
  );

  const nodes = [head];
  if (versions.length >= 2) {
    const toolbar = el("div", "history-toolbar");
    toolbar.append(el("p", "history-lead", "Select two versions, then compare."));
    const compareBtn = el("button", "ghost-btn", "Compare");
    compareBtn.type = "button";
    compareBtn.disabled = capabilityHistoryState.selected.length !== 2;
    compareBtn.addEventListener("click", () => {
      if (capabilityHistoryState.selected.length !== 2) return;
      capabilityHistoryState.compare = true;
      void showCapabilityHistory(capabilityId);
    });
    toolbar.append(compareBtn);
    nodes.push(toolbar);
  }

  const table = document.createElement("table");
  table.className = "version-table";
  const caption = document.createElement("caption");
  caption.className = "sr-only";
  caption.textContent = "Versioned capabilities, newest first";
  table.append(caption);

  const thead = document.createElement("thead");
  const headRow = document.createElement("tr");
  const selectHead = el("th");
  selectHead.append(el("span", "sr-only", "Select"));
  headRow.append(selectHead);
  for (const label of ["Version", "Kind", "Owner", "Status", "Description"]) {
    headRow.append(el("th", "", label));
  }
  thead.append(headRow);
  table.append(thead);

  const tbody = document.createElement("tbody");
  if (versions.length === 0) {
    const emptyRow = document.createElement("tr");
    const emptyCell = document.createElement("td");
    emptyCell.colSpan = 6;
    emptyCell.append(el("p", "empty", "No versioned rows for this capability."));
    emptyRow.append(emptyCell);
    tbody.append(emptyRow);
  }
  for (const item of versions) {
    const tr = document.createElement("tr");
    const selectCell = document.createElement("td");
    const check = document.createElement("input");
    check.type = "checkbox";
    check.name = "capability-version";
    check.value = item.version;
    check.checked = capabilityHistoryState.selected.includes(item.version);
    check.setAttribute("aria-label", `Select ${item.version}`);
    check.addEventListener("change", () => {
      toggleCapabilityHistorySelect(item.version, check.checked);
      void showCapabilityHistory(capabilityId);
    });
    selectCell.append(check);

    const versionCell = document.createElement("td");
    const openBtn = el("button", "version-open", item.version);
    openBtn.type = "button";
    openBtn.append(
      statusPill({
        status: item.status,
        live: item.status === "published" && item.version === latestVersion,
      }),
    );
    openBtn.addEventListener("click", () => {
      const path =
        item.version === latestVersion
          ? `/capabilities/${encodeURIComponent(capabilityId)}`
          : `/capabilities/${encodeURIComponent(capabilityId)}/${encodeURIComponent(item.version)}`;
      go(path, { capabilityId, version: item.version });
    });
    versionCell.append(openBtn);

    tr.append(
      selectCell,
      versionCell,
      kindCell(item.kind),
      cell(item.owner, "mono"),
      statusCell({
        status: item.status,
        live: item.status === "published" && item.version === latestVersion,
      }),
      cell(item.description, "clip"),
    );
    tbody.append(tr);
  }
  table.append(tbody);
  const wrap = el("div", "version-table-wrap");
  wrap.append(table);
  nodes.push(wrap);

  if (capabilityHistoryState.compare && capabilityHistoryState.selected.length === 2) {
    const [newer, older] = [...capabilityHistoryState.selected].sort((a, b) =>
      a === b ? 0 : a > b ? -1 : 1,
    );
    const left = versions.find((item) => item.version === newer);
    const right = versions.find((item) => item.version === older);
    if (left && right) {
      const compare = buildCompare(left, right, () => {
        capabilityHistoryState.compare = false;
        void showCapabilityHistory(capabilityId);
      });
      compare.querySelector(".history-lead").textContent = `${left.version} (newer) vs ${right.version}`;
      const headingRow = compare.querySelector("thead tr");
      if (headingRow) {
        headingRow.replaceChildren(el("th", "", "Field"), el("th", "", left.version), el("th", "", right.version));
      }
      nodes.push(compare);
    }
  }
  pageEl.replaceChildren(...nodes);
  pageEl.focus();
}

function toggleCapabilityHistorySelect(version, checked) {
  if (checked) {
    if (!capabilityHistoryState.selected.includes(version)) {
      capabilityHistoryState.selected.push(version);
    }
    if (capabilityHistoryState.selected.length > 2) capabilityHistoryState.selected.shift();
  } else {
    capabilityHistoryState.selected = capabilityHistoryState.selected.filter((item) => item !== version);
    capabilityHistoryState.compare = false;
  }
}

async function showRoute(routeId, routeVersion) {
  clearError();
  resetHistory(routeId);
  document.body.classList.remove("showing-history", "showing-routes", "showing-capabilities");
  document.body.classList.add("showing-detail");
  document.title = `${routeId} · Control Plane`;
  void refreshMeta();
  const path = `/api/routes/${encodeURIComponent(routeId)}`;
  const rowUrl = routeVersion
    ? `${path}?route_version=${encodeURIComponent(routeVersion)}`
    : path;
  const [res, versionsRes] = await Promise.all([
    fetch(rowUrl),
    fetch(`${path}/versions`),
  ]);
  if (!res.ok) {
    showError(`Route ${routeId} was not found.`);
    return;
  }
  const row = await res.json();
  const versionsPayload = versionsRes.ok ? await versionsRes.json() : { versions: [] };
  const revisionCount = Array.isArray(versionsPayload.versions)
    ? versionsPayload.versions.length
    : 0;

  const back = el("button", "back page-back", "← Routes");
  back.type = "button";
  back.addEventListener("click", () => goRoutes());

  const head = el("div", "detail-head");
  head.append(
    back,
    el("p", "detail-kicker", row.intent_label ?? "Route"),
    el("h2", "", row.route_id),
    el("p", "lead", row.description ?? ""),
  );
  const chips = el("div", "chip-row");
  chips.append(pill(row.route_version ?? "unversioned", "mono"));
  chips.append(statusPill({ status: row.status, active: row.active }));
  const autonomyLabel = autonomyModeListLabel(row.autonomy_mode);
  if (autonomyLabel) chips.append(pill(autonomyLabel, autonomyModeClass(row.autonomy_mode)));
  if (row.policy_profile) {
    chips.append(pill(policyLabel(row.policy_profile), policyClass(row.policy_profile)));
  }
  if (row.model_profile) chips.append(pill(row.model_profile, "mono"));
  if (row.fallback) chips.append(pill(`Fallback ${row.fallback}`));
  if (hasRetrieval(row.retrieval)) chips.append(pill(retrievalChip(row.retrieval), "info"));
  if (row.chat_visible) chips.append(pill("Chat visible", "ok"));

  const historyBtn = el("button", "ghost-btn");
  historyBtn.type = "button";
  historyBtn.append("History");
  historyBtn.append(pill(String(revisionCount), "mono"));
  historyBtn.setAttribute(
    "aria-label",
    revisionCount === 1 ? "History, 1 revision" : `History, ${revisionCount} revisions`,
  );
  historyBtn.addEventListener("click", () => {
    go(`/routes/${encodeURIComponent(routeId)}/history`, { routeId, page: "history" });
  });

  const jsonBtn = el("button", "ghost-btn", "JSON");
  jsonBtn.type = "button";
  jsonBtn.setAttribute("aria-expanded", "false");
  jsonBtn.setAttribute("aria-controls", "route-json");

  const actions = el("div", "chip-actions");
  actions.append(historyBtn, jsonBtn);
  const bar = el("div", "chip-bar");
  bar.append(chips, actions);
  head.append(bar);

  const sections = [];
  for (const section of SECTIONS) {
    sections.push(buildSection(section, row));
  }

  const jsonPanel = buildJsonPanel(row);
  jsonPanel.hidden = true;
  jsonBtn.addEventListener("click", () => {
    const open = jsonPanel.hidden;
    jsonPanel.hidden = !open;
    jsonBtn.setAttribute("aria-expanded", String(open));
    jsonBtn.setAttribute("aria-pressed", String(open));
    for (const block of sections) block.hidden = open;
    if (open) jsonPanel.querySelector("summary")?.focus();
  });

  pageEl.replaceChildren(head, jsonPanel, ...sections);
  pageEl.focus();
}

async function showHistory(routeId) {
  clearError();
  resetHistory(routeId);
  document.body.classList.remove("showing-detail", "showing-routes", "showing-capabilities");
  document.body.classList.add("showing-history");
  document.title = `${routeId} history · Control Plane`;
  void refreshMeta();
  const res = await fetch(`/api/routes/${encodeURIComponent(routeId)}/versions`);
  if (!res.ok) {
    showError(`History for ${routeId} was not found.`);
    return;
  }
  const payload = await res.json();
  const versions = payload.versions ?? [];

  const back = el("button", "back page-back", "← Route");
  back.type = "button";
  back.addEventListener("click", () => {
    go(`/routes/${encodeURIComponent(routeId)}`, { routeId });
  });

  const head = el("div", "detail-head");
  head.append(
    back,
    el("p", "detail-kicker", "Version history"),
    el("h2", "", routeId),
    el("p", "lead", `${versions.length} versions · newest first`),
  );

  const nodes = [head];
  if (versions.length >= 2) {
    const toolbar = el("div", "history-toolbar");
    toolbar.append(el("p", "history-lead", "Select two versions, then compare."));
    const compareBtn = el("button", "ghost-btn", "Compare");
    compareBtn.type = "button";
    compareBtn.disabled = historyState.selected.length !== 2;
    compareBtn.addEventListener("click", () => {
      if (historyState.selected.length !== 2) return;
      historyState.compare = true;
      void showHistory(routeId);
    });
    toolbar.append(compareBtn);
    nodes.push(toolbar);
  }

  const table = document.createElement("table");
  table.className = "version-table";
  const caption = document.createElement("caption");
  caption.className = "sr-only";
  caption.textContent = "Versioned rows, newest first";
  table.append(caption);

  const thead = document.createElement("thead");
  const headRow = document.createElement("tr");
  const selectHead = el("th");
  selectHead.append(el("span", "sr-only", "Select"));
  headRow.append(selectHead);
  for (const label of ["Version", "Description", "Model", "Prompt", "Loop", "Policy"]) {
    headRow.append(el("th", "", label));
  }
  thead.append(headRow);
  table.append(thead);

  const tbody = document.createElement("tbody");
  if (versions.length === 0) {
    const emptyRow = document.createElement("tr");
    const emptyCell = document.createElement("td");
    emptyCell.colSpan = 7;
    emptyCell.append(el("p", "empty", "No versioned rows for this route."));
    emptyRow.append(emptyCell);
    tbody.append(emptyRow);
  }
  for (const version of versions) {
    const tr = document.createElement("tr");
    const selectCell = document.createElement("td");
    const check = document.createElement("input");
    check.type = "checkbox";
    check.name = "route-version";
    check.value = version.route_version;
    check.checked = historyState.selected.includes(version.route_version);
    check.setAttribute("aria-label", `Select ${version.route_version}`);
    check.addEventListener("change", () => {
      toggleHistorySelect(version.route_version, check.checked);
      void showHistory(routeId);
    });
    selectCell.append(check);

    const versionCell = document.createElement("td");
    const openBtn = el("button", "version-open", version.route_version);
    openBtn.type = "button";
    if (version.active) {
      openBtn.append(statusPill({ status: version.status, active: version.active }));
    } else {
      openBtn.append(statusPill({ status: version.status, active: false }));
    }
    openBtn.addEventListener("click", () => {
      const path = version.active
        ? `/routes/${encodeURIComponent(routeId)}`
        : `/routes/${encodeURIComponent(routeId)}/${encodeURIComponent(version.route_version)}`;
      go(path, { routeId, routeVersion: version.route_version });
    });
    versionCell.append(openBtn);

    tr.append(
      selectCell,
      versionCell,
      cell(version.description),
      cell(version.model_profile, "mono"),
      linkCell(catalogHref("prompt_id", version.prompt_id), version.prompt_id, "mono"),
      cell(version.max_loop_steps == null ? null : String(version.max_loop_steps)),
      cell(version.policy_profile ? policyLabel(version.policy_profile) : null),
    );
    tbody.append(tr);
  }
  table.append(tbody);
  const wrap = el("div", "version-table-wrap");
  wrap.append(table);
  nodes.push(wrap);

  if (historyState.compare && historyState.selected.length === 2) {
    const [newer, older] = [...historyState.selected].sort().reverse();
    const left = versions.find((item) => item.route_version === newer);
    const right = versions.find((item) => item.route_version === older);
    if (left && right) nodes.push(buildCompare(left, right));
  }
  pageEl.replaceChildren(...nodes);
  pageEl.focus();
}

function goPrompts() {
  promptHistoryState.promptId = null;
  promptHistoryState.selected = [];
  promptHistoryState.compare = false;
  go("/prompts");
}

function goWorkflows() {
  workflowHistoryState.workflowId = null;
  workflowHistoryState.selected = [];
  workflowHistoryState.compare = false;
  go("/workflows");
}

function goManifests() {
  manifestHistoryState.manifestId = null;
  manifestHistoryState.selected = [];
  manifestHistoryState.compare = false;
  go("/manifests");
}

async function showResourceList({
  bodyClass,
  title,
  api,
  itemsKey,
  columns,
  empty,
  error,
  hrefOf,
  cellsOf,
  caption,
  itemsOf,
  basePath,
  noun,
  statusesOf,
  sortKeys,
  ready,
}) {
  clearError();
  document.body.classList.remove(
    "showing-detail",
    "showing-history",
    "showing-routes",
    "showing-capabilities",
    "showing-prompts",
    "showing-workflows",
    "showing-manifests",
    "showing-usage",
  );
  document.body.classList.add(bodyClass);
  document.title = `${title} · Control Plane`;
  skeletonTable();
  void refreshMeta();
  const [res] = await Promise.all([fetch(api), ready]);
  if (!res.ok) {
    pageEl.replaceChildren();
    showError(error.replace("{status}", String(res.status)));
    return;
  }
  const payload = await res.json();
  const items = itemsOf ? itemsOf(payload) : payload[itemsKey] ?? [];
  const selected = listTabStatus();
  const statuses = statusesOf ? statusesOf(items) : items.map(() => "active");
  const counts = countResolvedStatuses(statuses);
  const tabs = buildStatusTabs({ basePath, counts, selected });
  const sortId = basePath ?? title;
  if (!listSortState[sortId]) listSortState[sortId] = { key: null, dir: "asc" };
  const list = document.createElement("table");
  list.className = "routes-table";
  list.append(el("caption", "sr-only", caption));
  const thead = document.createElement("thead");
  const tbody = document.createElement("tbody");

  function visibleRows() {
    const rows = [];
    for (let index = 0; index < items.length; index += 1) {
      if (statuses[index] !== selected) continue;
      rows.push({ item: items[index], status: statuses[index] });
    }
    const state = listSortState[sortId];
    const sortOf = sortKeys?.[state.key];
    if (!sortOf) return rows;
    const dir = state.dir === "desc" ? -1 : 1;
    return [...rows].sort(
      (left, right) => dir * compareSortValues(sortOf(left.item), sortOf(right.item)),
    );
  }

  function headerRow() {
    const row = document.createElement("tr");
    const state = listSortState[sortId];
    for (const label of columns) {
      const th = document.createElement("th");
      const sortable = Boolean(sortKeys?.[label]);
      if (!sortable) {
        th.textContent = label;
        row.append(th);
        continue;
      }
      const active = state.key === label;
      th.setAttribute("aria-sort", active ? (state.dir === "desc" ? "descending" : "ascending") : "none");
      const button = document.createElement("button");
      button.type = "button";
      button.className = "sort-btn";
      button.dataset.sort = label;
      button.append(document.createTextNode(label), sortMark(active ? state.dir : null));
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        if (state.key === label) {
          state.dir = state.dir === "asc" ? "desc" : "asc";
        } else {
          state.key = label;
          state.dir = "asc";
        }
        paint();
        thead.querySelector(`[data-sort="${CSS.escape(label)}"]`)?.focus();
      });
      th.append(button);
      row.append(th);
    }
    return row;
  }

  function bodyRows() {
    const nodes = [];
    const rows = visibleRows();
    for (const { item, status } of rows) {
      const tr = document.createElement("tr");
      const href = hrefOf(item, status);
      tr.tabIndex = 0;
      tr.setAttribute("role", "link");
      tr.setAttribute("aria-label", `Open ${href}`);
      const open = () => go(href);
      tr.addEventListener("click", open);
      tr.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          open();
        }
      });
      for (const node of cellsOf(item, status)) tr.append(node);
      nodes.push(tr);
    }
    if (nodes.length === 0) {
      const emptyRow = document.createElement("tr");
      const emptyCell = document.createElement("td");
      emptyCell.colSpan = columns.length;
      const label = catalogStatusLabel(selected).toLowerCase();
      emptyCell.append(el("p", "empty", empty ?? `No ${label} ${noun}.`));
      emptyRow.append(emptyCell);
      nodes.push(emptyRow);
    }
    return nodes;
  }

  function paint() {
    thead.replaceChildren(headerRow());
    tbody.replaceChildren(...bodyRows());
  }

  paint();
  list.append(thead, tbody);
  const wrap = el("div", "version-table-wrap");
  wrap.append(list);
  const panel = el("div", "status-tabs__panel");
  panel.id = "status-tab-panel";
  panel.setAttribute("role", "tabpanel");
  panel.setAttribute("aria-labelledby", `status-tab-${selected}`);
  panel.append(wrap);
  const heading = el("h2", "page-title", title);
  heading.id = "page-title";
  pageEl.replaceChildren(heading, tabs, panel);
  if (history.state?.fromTab) {
    tabs.querySelector(".is-selected")?.focus();
  } else {
    pageEl.focus();
  }
}

function idHeadCell(text) {
  const idCell = document.createElement("th");
  idCell.scope = "row";
  idCell.append(el("span", "rid", text));
  return idCell;
}

async function showPrompts() {
  return showResourceList({
    bodyClass: "showing-prompts",
    title: "Prompts",
    api: "/api/prompts?include=all",
    itemsKey: "prompts",
    basePath: "/prompts",
    noun: "prompts",
    columns: ["Prompt", "Version", "Owner", "Host"],
    error: "Prompt catalogue read failed ({status}).",
    caption: "Prompts in the selected status. Activate a row to open detail.",
    statusesOf: (items) => livePublishedStatuses(items, "prompt_id", "prompt_version"),
    hrefOf: (item, status) =>
      status === "active"
        ? `/prompts/${encodeURIComponent(item.prompt_id)}`
        : `/prompts/${encodeURIComponent(item.prompt_id)}/${encodeURIComponent(item.prompt_version)}`,
    cellsOf: (item) => [
      idHeadCell(item.prompt_id),
      cell(item.prompt_version, "mono"),
      cell(item.owner, "mono"),
      cell(item.host, "clip"),
    ],
  });
}

async function showWorkflows() {
  return showResourceList({
    bodyClass: "showing-workflows",
    title: "Workflows",
    api: "/api/workflows?include=all",
    itemsKey: "workflows",
    basePath: "/workflows",
    noun: "workflows",
    columns: ["Workflow", "Version", "Description", "Stages"],
    error: "Workflow catalogue read failed ({status}).",
    caption: "Workflows in the selected status. Activate a row to open detail.",
    statusesOf: (items) => livePublishedStatuses(items, "workflow_id", "workflow_version"),
    hrefOf: (item, status) =>
      status === "active"
        ? `/workflows/${encodeURIComponent(item.workflow_id)}`
        : `/workflows/${encodeURIComponent(item.workflow_id)}/${encodeURIComponent(item.workflow_version)}`,
    cellsOf: (item) => [
      idHeadCell(item.workflow_id),
      cell(item.workflow_version, "mono"),
      cell(item.description, "clip"),
      cell(Array.isArray(item.stages) ? String(item.stages.length) : "0"),
    ],
  });
}

async function showManifests() {
  return showResourceList({
    bodyClass: "showing-manifests",
    title: "Manifests",
    api: "/api/manifests?include=all",
    itemsKey: "manifests",
    basePath: "/manifests",
    noun: "manifests",
    columns: ["Manifest", "Version", "Description", "Tools"],
    error: "Manifest catalogue read failed ({status}).",
    caption: "Manifests in the selected status. Activate a row to open detail.",
    statusesOf: (items) => livePublishedStatuses(items, "manifest_id", "manifest_version"),
    hrefOf: (item, status) =>
      status === "active"
        ? `/manifests/${encodeURIComponent(item.manifest_id)}`
        : `/manifests/${encodeURIComponent(item.manifest_id)}/${encodeURIComponent(item.manifest_version)}`,
    cellsOf: (item) => [
      idHeadCell(item.manifest_id),
      cell(item.manifest_version, "mono"),
      cell(item.description, "clip"),
      cell(Array.isArray(item.tools) ? String(item.tools.length) : "0"),
    ],
  });
}

function usageList(uses, empty = "Unused in latest manifests.") {
  if (!uses.length) return el("p", "empty", empty);
  const list = document.createElement("ul");
  list.className = "usage-list";
  for (const use of uses) {
    const item = document.createElement("li");
    if (use.route_id) {
      const routeHref = `/routes/${encodeURIComponent(use.route_id)}`;
      const routeLabel = use.route_version
        ? `${use.route_id}@${use.route_version}`
        : use.route_id;
      item.append(idLink(routeHref, routeLabel, "mono"));
    }
    if (use.manifest_id) {
      if (use.route_id) item.append(document.createTextNode(" · "));
      const href = `/manifests/${encodeURIComponent(use.manifest_id)}`;
      const label = use.manifest_version
        ? `${use.manifest_id}@${use.manifest_version}`
        : use.manifest_id;
      item.append(idLink(href, label, "mono"));
    }
    if (use.tool_name) {
      item.append(document.createTextNode(` · ${use.tool_name}`));
    }
    if (use.capability_version) {
      item.append(document.createTextNode(` @ ${use.capability_version}`));
    }
    list.append(item);
  }
  return list;
}

function buildUsedBySection(uses, empty) {
  const block = el("section", "section");
  block.append(el("h3", "", "Used by"));
  block.append(usageList(uses, empty));
  return block;
}

function promptUses(routes, promptId) {
  return (routes ?? [])
    .filter((route) => route.prompt_id === promptId)
    .map((route) => ({
      route_id: route.route_id ?? null,
      route_version: route.route_version ?? null,
    }));
}

async function showUsage() {
  clearError();
  document.body.classList.remove(
    "showing-detail",
    "showing-history",
    "showing-routes",
    "showing-capabilities",
    "showing-prompts",
    "showing-workflows",
    "showing-manifests",
    "showing-home",
  );
  document.body.classList.add("showing-usage");
  document.title = "Capability usage · Control Plane";
  skeletonTable();
  void refreshMeta();
  const [capsRes, manifestsRes, routesRes] = await Promise.all([
    fetch("/api/capabilities"),
    fetch("/api/manifests"),
    fetch("/api/routes"),
  ]);
  if (!capsRes.ok || !manifestsRes.ok) {
    pageEl.replaceChildren();
    const status = !capsRes.ok ? capsRes.status : manifestsRes.status;
    showError(`Usage read failed (${status}).`);
    return;
  }
  const capsPayload = await capsRes.json();
  const manifestsPayload = await manifestsRes.json();
  const routesPayload = routesRes.ok ? await routesRes.json() : { routes: [] };
  const rows = capabilityUsage(
    manifestsPayload.manifests ?? [],
    capsPayload.capabilities ?? [],
    routesPayload.routes ?? [],
  );

  const head = el("div", "detail-head");
  const back = el("button", "back page-back", "← Home");
  back.type = "button";
  back.addEventListener("click", () => go("/"));
  head.append(
    back,
    el("p", "detail-kicker", "Catalogue"),
    el("h2", "", "Capability usage"),
    el(
      "p",
      "lead",
      "Which latest routes and manifests reference each capability. One capability can appear on many routes.",
    ),
  );

  const list = document.createElement("table");
  list.className = "routes-table";
  list.append(
    el("caption", "sr-only", "Capabilities and the latest manifests that reference them."),
  );
  const thead = document.createElement("thead");
  const headRow = document.createElement("tr");
  for (const label of ["Capability", "Version", "Used by"]) {
    headRow.append(el("th", "", label));
  }
  thead.append(headRow);
  list.append(thead);
  const tbody = document.createElement("tbody");
  if (rows.length === 0) {
    const emptyRow = document.createElement("tr");
    const emptyCell = document.createElement("td");
    emptyCell.colSpan = 3;
    emptyCell.append(el("p", "empty", "No capabilities or manifests."));
    emptyRow.append(emptyCell);
    tbody.append(emptyRow);
  }
  for (const row of rows) {
    const tr = document.createElement("tr");
    const capHref = `/capabilities/${encodeURIComponent(row.capability_id)}`;
    const idCell = document.createElement("th");
    idCell.scope = "row";
    idCell.append(idLink(capHref, row.capability_id, "rid"));
    const used = document.createElement("td");
    used.append(usageList(row.uses));
    tr.append(idCell, cell(row.version, "mono"), used);
    tbody.append(tr);
  }
  list.append(tbody);
  const wrap = el("div", "version-table-wrap");
  wrap.append(list);
  pageEl.replaceChildren(head, wrap);
  pageEl.focus();
}

async function showCatalogDetail({
  id,
  version,
  apiBase,
  versionsPath,
  notFound,
  backLabel,
  onBack,
  kicker,
  titleOf,
  leadOf,
  chipsOf,
  historyHref,
  jsonTitle,
  jsonId,
  sectionsOf,
  extraNodes,
  afterNodes,
}) {
  clearError();
  document.body.classList.remove(
    "showing-history",
    "showing-routes",
    "showing-capabilities",
    "showing-prompts",
    "showing-workflows",
    "showing-manifests",
    "showing-usage",
  );
  document.body.classList.add("showing-detail");
  document.title = `${id} · Control Plane`;
  void refreshMeta();
  const rowUrl = version ? `${apiBase}?version=${encodeURIComponent(version)}` : apiBase;
  const [res, versionsRes] = await Promise.all([fetch(rowUrl), fetch(versionsPath)]);
  if (!res.ok) {
    showError(notFound);
    return;
  }
  const row = await res.json();
  const versionsPayload = versionsRes.ok ? await versionsRes.json() : { versions: [] };
  const revisionCount = Array.isArray(versionsPayload.versions)
    ? versionsPayload.versions.length
    : 0;
  const back = el("button", "back page-back", backLabel);
  back.type = "button";
  back.addEventListener("click", onBack);
  const head = el("div", "detail-head");
  head.append(back, el("p", "detail-kicker", kicker(row)), el("h2", "", titleOf(row)), el("p", "lead", leadOf(row)));
  const chips = el("div", "chip-row");
  for (const chip of chipsOf(row, version)) chips.append(chip);
  const historyBtn = el("button", "ghost-btn");
  historyBtn.type = "button";
  historyBtn.append("History");
  historyBtn.append(pill(String(revisionCount), "mono"));
  historyBtn.setAttribute(
    "aria-label",
    revisionCount === 1 ? "History, 1 revision" : `History, ${revisionCount} revisions`,
  );
  historyBtn.addEventListener("click", () => go(historyHref));
  const jsonBtn = el("button", "ghost-btn", "JSON");
  jsonBtn.type = "button";
  jsonBtn.setAttribute("aria-expanded", "false");
  jsonBtn.setAttribute("aria-controls", jsonId);
  const actions = el("div", "chip-actions");
  actions.append(historyBtn, jsonBtn);
  const bar = el("div", "chip-bar");
  bar.append(chips, actions);
  head.append(bar);
  const sections = extraNodes ? extraNodes(row) : [];
  if (sectionsOf) {
    for (const section of sectionsOf) {
      sections.push(
        buildSection(section, row, {
          live: !version && (row.status === "published" || !row.status),
        }),
      );
    }
  }
  if (afterNodes) sections.push(...afterNodes(row));
  const jsonPanel = buildJsonPanel(row, jsonTitle, jsonId);
  jsonPanel.hidden = true;
  jsonBtn.addEventListener("click", () => {
    const open = jsonPanel.hidden;
    jsonPanel.hidden = !open;
    jsonBtn.setAttribute("aria-expanded", String(open));
    jsonBtn.setAttribute("aria-pressed", String(open));
    for (const block of sections) block.hidden = open;
    if (open) jsonPanel.querySelector("summary")?.focus();
  });
  pageEl.replaceChildren(head, jsonPanel, ...sections);
  pageEl.focus();
}

async function showPrompt(promptId, version) {
  resetPromptHistory(promptId);
  const routesRes = await fetch("/api/routes");
  const routesPayload = routesRes.ok ? await routesRes.json() : { routes: [] };
  const uses = promptUses(routesPayload.routes ?? [], promptId);
  return showCatalogDetail({
    id: promptId,
    version,
    apiBase: `/api/prompts/${encodeURIComponent(promptId)}`,
    versionsPath: `/api/prompts/${encodeURIComponent(promptId)}/versions`,
    notFound: `Prompt ${promptId} was not found.`,
    backLabel: "← Prompts",
    onBack: () => goPrompts(),
    kicker: () => "Prompt",
    titleOf: (row) => row.prompt_id,
    leadOf: (row) => row.host ?? "",
    chipsOf: (row, pinned) => [
      pill(row.prompt_version ?? "unversioned", "mono"),
      statusPill({ status: row.status, live: !pinned && row.status === "published" }),
      row.owner ? pill(row.owner, "mono") : pill("—"),
    ],
    historyHref: `/prompts/${encodeURIComponent(promptId)}/history`,
    jsonTitle: "Prompt JSON",
    jsonId: "prompt-json",
    sectionsOf: PROMPT_SECTIONS,
    afterNodes: () => [buildUsedBySection(uses, "Unused by any route.")],
  });
}

async function showWorkflow(workflowId, version) {
  resetWorkflowHistory(workflowId);
  return showCatalogDetail({
    id: workflowId,
    version,
    apiBase: `/api/workflows/${encodeURIComponent(workflowId)}`,
    versionsPath: `/api/workflows/${encodeURIComponent(workflowId)}/versions`,
    notFound: `Workflow ${workflowId} was not found.`,
    backLabel: "← Workflows",
    onBack: () => goWorkflows(),
    kicker: () => "Workflow",
    titleOf: (row) => row.workflow_id,
    leadOf: (row) => row.description ?? "",
    chipsOf: (row, pinned) => [
      pill(row.workflow_version ?? "unversioned", "mono"),
      statusPill({
        status: row.status ?? "published",
        live: !pinned && (!row.status || row.status === "published"),
      }),
      pill(`${Array.isArray(row.stages) ? row.stages.length : 0} stages`, "mono"),
    ],
    historyHref: `/workflows/${encodeURIComponent(workflowId)}/history`,
    jsonTitle: "Workflow JSON",
    jsonId: "workflow-json",
    sectionsOf: WORKFLOW_SECTIONS,
    extraNodes: (row) => [renderWorkflowTable(row)],
  });
}

async function showManifest(manifestId, version) {
  resetManifestHistory(manifestId);
  return showCatalogDetail({
    id: manifestId,
    version,
    apiBase: `/api/manifests/${encodeURIComponent(manifestId)}`,
    versionsPath: `/api/manifests/${encodeURIComponent(manifestId)}/versions`,
    notFound: `Manifest ${manifestId} was not found.`,
    backLabel: "← Manifests",
    onBack: () => goManifests(),
    kicker: () => "Manifest",
    titleOf: (row) => row.manifest_id,
    leadOf: (row) => row.description ?? "",
    chipsOf: (row, pinned) => [
      pill(row.manifest_version ?? "unversioned", "mono"),
      statusPill({
        status: row.status ?? "published",
        live: !pinned && (!row.status || row.status === "published"),
      }),
      pill(`${Array.isArray(row.tools) ? row.tools.length : 0} tools`, "mono"),
    ],
    historyHref: `/manifests/${encodeURIComponent(manifestId)}/history`,
    jsonTitle: "Manifest JSON",
    jsonId: "manifest-json",
    extraNodes: (row) => [renderManifestTable(row)],
  });
}

async function showVersionHistory({
  id,
  api,
  backHref,
  backLabel,
  versionKey,
  columns,
  cellsOf,
  state,
  reset,
  rerender,
  latestPath,
  versionPath,
}) {
  clearError();
  reset(id);
  document.body.classList.remove(
    "showing-detail",
    "showing-routes",
    "showing-capabilities",
    "showing-prompts",
    "showing-workflows",
    "showing-manifests",
    "showing-usage",
  );
  document.body.classList.add("showing-history");
  document.title = `${id} history · Control Plane`;
  void refreshMeta();
  const res = await fetch(api);
  if (!res.ok) {
    showError(`History for ${id} was not found.`);
    return;
  }
  const payload = await res.json();
  const versions = payload.versions ?? [];
  const latestVersion = versions[0]?.[versionKey];
  const back = el("button", "back page-back", backLabel);
  back.type = "button";
  back.addEventListener("click", () => go(backHref));
  const head = el("div", "detail-head");
  head.append(
    back,
    el("p", "detail-kicker", "Version history"),
    el("h2", "", id),
    el("p", "lead", `${versions.length} versions · newest first`),
  );
  const nodes = [head];
  if (versions.length >= 2) {
    const toolbar = el("div", "history-toolbar");
    toolbar.append(el("p", "history-lead", "Select two versions, then compare."));
    const compareBtn = el("button", "ghost-btn", "Compare");
    compareBtn.type = "button";
    compareBtn.disabled = state.selected.length !== 2;
    compareBtn.addEventListener("click", () => {
      if (state.selected.length !== 2) return;
      state.compare = true;
      void rerender(id);
    });
    toolbar.append(compareBtn);
    nodes.push(toolbar);
  }
  const table = document.createElement("table");
  table.className = "version-table";
  table.append(el("caption", "sr-only", "Versioned rows, newest first"));
  const thead = document.createElement("thead");
  const headRow = document.createElement("tr");
  const selectHead = el("th");
  selectHead.append(el("span", "sr-only", "Select"));
  headRow.append(selectHead);
  for (const label of columns) headRow.append(el("th", "", label));
  thead.append(headRow);
  table.append(thead);
  const tbody = document.createElement("tbody");
  if (versions.length === 0) {
    const emptyRow = document.createElement("tr");
    const emptyCell = document.createElement("td");
    emptyCell.colSpan = columns.length + 1;
    emptyCell.append(el("p", "empty", "No versioned rows."));
    emptyRow.append(emptyCell);
    tbody.append(emptyRow);
  }
  for (const item of versions) {
    const tr = document.createElement("tr");
    const selectCell = document.createElement("td");
    const check = document.createElement("input");
    check.type = "checkbox";
    check.value = item[versionKey];
    check.checked = state.selected.includes(item[versionKey]);
    check.setAttribute("aria-label", `Select ${item[versionKey]}`);
    check.addEventListener("change", () => {
      if (check.checked) {
        if (!state.selected.includes(item[versionKey])) state.selected.push(item[versionKey]);
        if (state.selected.length > 2) state.selected.shift();
      } else {
        state.selected = state.selected.filter((value) => value !== item[versionKey]);
        state.compare = false;
      }
      void rerender(id);
    });
    selectCell.append(check);
    const versionCell = document.createElement("td");
    const openBtn = el("button", "version-open", item[versionKey]);
    openBtn.type = "button";
    openBtn.append(
      statusPill({
        status: item.status,
        live: (item.status === "published" || !item.status) && item[versionKey] === latestVersion,
      }),
    );
    openBtn.addEventListener("click", () => {
      go(item[versionKey] === latestVersion ? latestPath : versionPath(item[versionKey]));
    });
    versionCell.append(openBtn);
    tr.append(selectCell, versionCell, ...cellsOf(item, latestVersion));
    tbody.append(tr);
  }
  table.append(tbody);
  const wrap = el("div", "version-table-wrap");
  wrap.append(table);
  nodes.push(wrap);
  if (state.compare && state.selected.length === 2) {
    const [newer, older] = [...state.selected].sort().reverse();
    const left = versions.find((item) => item[versionKey] === newer);
    const right = versions.find((item) => item[versionKey] === older);
    if (left && right) {
      const compare = buildCompare(left, right, () => {
        state.compare = false;
        void rerender(id);
      });
      const lead = compare.querySelector(".history-lead");
      if (lead) lead.textContent = `${left[versionKey]} (newer) vs ${right[versionKey]}`;
      const headingRow = compare.querySelector("thead tr");
      if (headingRow) {
        headingRow.replaceChildren(
          el("th", "", "Field"),
          el("th", "", left[versionKey]),
          el("th", "", right[versionKey]),
        );
      }
      nodes.push(compare);
    }
  }
  pageEl.replaceChildren(...nodes);
  pageEl.focus();
}

async function showPromptHistory(promptId) {
  return showVersionHistory({
    id: promptId,
    api: `/api/prompts/${encodeURIComponent(promptId)}/versions`,
    backHref: `/prompts/${encodeURIComponent(promptId)}`,
    backLabel: "← Prompt",
    versionKey: "prompt_version",
    columns: ["Version", "Status", "Owner", "Host"],
    cellsOf: (item, latestVersion) => [
      statusCell({
        status: item.status,
        live: item.status === "published" && item.prompt_version === latestVersion,
      }),
      cell(item.owner, "mono"),
      cell(item.host, "clip"),
    ],
    state: promptHistoryState,
    reset: resetPromptHistory,
    rerender: showPromptHistory,
    latestPath: `/prompts/${encodeURIComponent(promptId)}`,
    versionPath: (version) => `/prompts/${encodeURIComponent(promptId)}/${encodeURIComponent(version)}`,
  });
}

async function showWorkflowHistory(workflowId) {
  return showVersionHistory({
    id: workflowId,
    api: `/api/workflows/${encodeURIComponent(workflowId)}/versions`,
    backHref: `/workflows/${encodeURIComponent(workflowId)}`,
    backLabel: "← Workflow",
    versionKey: "workflow_version",
    columns: ["Version", "Description", "Stages"],
    cellsOf: (item) => [
      cell(item.description, "clip"),
      cell(Array.isArray(item.stages) ? String(item.stages.length) : "0"),
    ],
    state: workflowHistoryState,
    reset: resetWorkflowHistory,
    rerender: showWorkflowHistory,
    latestPath: `/workflows/${encodeURIComponent(workflowId)}`,
    versionPath: (version) =>
      `/workflows/${encodeURIComponent(workflowId)}/${encodeURIComponent(version)}`,
  });
}

async function showManifestHistory(manifestId) {
  return showVersionHistory({
    id: manifestId,
    api: `/api/manifests/${encodeURIComponent(manifestId)}/versions`,
    backHref: `/manifests/${encodeURIComponent(manifestId)}`,
    backLabel: "← Manifest",
    versionKey: "manifest_version",
    columns: ["Version", "Description", "Tools"],
    cellsOf: (item) => [
      cell(item.description, "clip"),
      cell(Array.isArray(item.tools) ? String(item.tools.length) : "0"),
    ],
    state: manifestHistoryState,
    reset: resetManifestHistory,
    rerender: showManifestHistory,
    latestPath: `/manifests/${encodeURIComponent(manifestId)}`,
    versionPath: (version) =>
      `/manifests/${encodeURIComponent(manifestId)}/${encodeURIComponent(version)}`,
  });
}

function cell(text, extra) {
  const td = document.createElement("td");
  if (isEmpty(text)) td.append(el("span", "empty", "—"));
  else td.append(el("span", extra ?? "", String(text)));
  return td;
}

function toggleHistorySelect(version, checked) {
  if (checked) {
    if (!historyState.selected.includes(version)) historyState.selected.push(version);
    if (historyState.selected.length > 2) historyState.selected.shift();
  } else {
    historyState.selected = historyState.selected.filter((item) => item !== version);
    historyState.compare = false;
  }
}

function flatten(value, prefix = "", out = {}) {
  if (value == null || typeof value !== "object" || Array.isArray(value)) {
    if (prefix) out[prefix] = value;
    return out;
  }
  for (const [key, nested] of Object.entries(value)) {
    const path = prefix ? `${prefix}.${key}` : key;
    if (nested && typeof nested === "object" && !Array.isArray(nested)) {
      flatten(nested, path, out);
    } else {
      out[path] = nested;
    }
  }
  return out;
}

function display(value) {
  if (value == null || value === "") return "—";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (Array.isArray(value)) return value.join(", ");
  return String(value);
}

function buildCompare(left, right, onClose) {
  const section = el("section", "section compare");
  section.setAttribute("aria-labelledby", "compare-heading");
  const heading = el("h3", "", "Compare");
  heading.id = "compare-heading";
  const close = el("button", "ghost-btn", "Close");
  close.type = "button";
  close.addEventListener("click", () => {
    if (onClose) {
      onClose();
      return;
    }
    historyState.compare = false;
    void showHistory(left.route_id);
  });
  const bar = el("div", "json-toolbar");
  bar.append(heading, close);
  section.append(bar);
  section.append(
    el(
      "p",
      "history-lead",
      `${left.route_version} (newer) vs ${right.route_version}`,
    ),
  );

  const leftFlat = flatten(left);
  const rightFlat = flatten(right);
  const keys = [...new Set([...Object.keys(leftFlat), ...Object.keys(rightFlat)])].sort();
  const table = document.createElement("table");
  table.className = "compare-table";
  const thead = document.createElement("thead");
  const headRow = document.createElement("tr");
  for (const label of ["Field", left.route_version, right.route_version]) {
    headRow.append(el("th", "", label));
  }
  thead.append(headRow);
  const tbody = document.createElement("tbody");
  for (const key of keys) {
    const a = display(leftFlat[key]);
    const b = display(rightFlat[key]);
    const changed = a !== b;
    const tr = document.createElement("tr");
    if (changed) tr.className = "changed";
    tr.append(el("th", "", fieldLabel(key)));
    const leftCell = el("td", "", a);
    const rightCell = el("td", "", b);
    tr.append(leftCell, rightCell);
    tbody.append(tr);
  }
  table.append(thead, tbody);
  section.append(table);
  return section;
}

function jsonToken(kind, text) {
  return el("span", `json-${kind}`, text);
}

function collectionSize(value) {
  return Array.isArray(value) ? value.length : Object.keys(value).length;
}

function renderJsonScalar(value) {
  if (value === null) return jsonToken("null", "null");
  if (typeof value === "boolean") return jsonToken("bool", String(value));
  if (typeof value === "number") return jsonToken("number", String(value));
  return jsonToken("string", JSON.stringify(value));
}

function renderJsonNode(value, key, trailingComma) {
  const isCollection = value !== null && typeof value === "object";
  if (!isCollection || collectionSize(value) === 0) {
    const line = el("div", "json-line");
    if (key !== undefined) {
      line.append(jsonToken("key", JSON.stringify(key)), jsonToken("punct", ": "));
    }
    if (isCollection) {
      line.append(jsonToken("punct", Array.isArray(value) ? "[]" : "{}"));
    } else {
      line.append(renderJsonScalar(value));
    }
    if (trailingComma) line.append(jsonToken("punct", ","));
    return line;
  }

  const isArray = Array.isArray(value);
  const open = isArray ? "[" : "{";
  const close = isArray ? "]" : "}";
  const size = collectionSize(value);
  const unit = isArray ? (size === 1 ? "item" : "items") : size === 1 ? "key" : "keys";
  const name = key !== undefined ? String(key) : isArray ? "array" : "object";

  const details = el("details", "json-node");
  details.open = true;
  const summary = document.createElement("summary");
  summary.setAttribute("aria-label", `${name}, ${isArray ? "array" : "object"} with ${size} ${unit}`);
  if (key !== undefined) {
    summary.append(jsonToken("key", JSON.stringify(key)), jsonToken("punct", `: ${open}`));
  } else {
    summary.append(jsonToken("punct", open));
  }
  const preview = jsonToken("preview", ` … ${close}`);
  preview.setAttribute("aria-hidden", "true");
  summary.append(preview);
  if (trailingComma) {
    const collapsedComma = jsonToken("collapsed-comma", ",");
    collapsedComma.setAttribute("aria-hidden", "true");
    summary.append(collapsedComma);
  }
  details.append(summary);

  const children = el("div", "json-children");
  if (isArray) {
    value.forEach((item, index) => {
      children.append(renderJsonNode(item, undefined, index < value.length - 1));
    });
  } else {
    const keys = Object.keys(value);
    keys.forEach((childKey, index) => {
      children.append(renderJsonNode(value[childKey], childKey, index < keys.length - 1));
    });
  }
  details.append(children);

  const closer = el("div", "json-close");
  closer.append(jsonToken("punct", close));
  if (trailingComma) closer.append(jsonToken("punct", ","));
  details.append(closer);
  return details;
}

function buildJsonPanel(data, title = "Route JSON", panelId = "route-json") {
  const json = JSON.stringify(data, null, 2);
  const panel = el("section", "json-panel");
  panel.id = panelId;
  const toolbar = el("div", "json-toolbar");
  toolbar.append(el("h3", "", title));
  const copyBtn = el("button", "ghost-btn", "Copy");
  copyBtn.type = "button";
  copyBtn.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(json);
      copyBtn.textContent = "Copied";
      window.setTimeout(() => {
        copyBtn.textContent = "Copy";
      }, 1600);
    } catch {
      copyBtn.textContent = "Copy failed";
    }
  });
  toolbar.append(copyBtn);
  const tree = el("div", "json-tree");
  tree.append(renderJsonNode(JSON.parse(json)));
  panel.append(toolbar, tree);
  return panel;
}

window.addEventListener("popstate", () => {
  void renderFromPath();
});

document.querySelector(".brand-home")?.addEventListener("click", (event) => {
  event.preventDefault();
  go("/");
});

const glossaryEl = document.querySelector("#glossary");
const glossaryOpen = document.querySelector("#glossary-open");
const glossaryClose = document.querySelector("#glossary-close");

function glossarySections() {
  return glossaryEl?.querySelectorAll("details.glossary__section") ?? [];
}

function closeOtherGlossarySections(except) {
  for (const section of glossarySections()) {
    if (section !== except) section.open = false;
  }
}

function setGlossaryOpen(open) {
  if (!glossaryEl) return;
  glossaryEl.hidden = !open;
  glossaryOpen?.setAttribute("aria-expanded", String(open));
  if (open) glossaryClose?.focus();
  else {
    closeOtherGlossarySections();
    glossaryOpen?.focus();
  }
}

for (const section of glossarySections()) {
  section.addEventListener("toggle", () => {
    if (section.open) closeOtherGlossarySections(section);
  });
}

glossaryOpen?.addEventListener("click", () => setGlossaryOpen(true));
glossaryClose?.addEventListener("click", () => setGlossaryOpen(false));
glossaryEl?.addEventListener("click", (event) => {
  if (event.target === glossaryEl) setGlossaryOpen(false);
});
document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape" || !glossaryEl || glossaryEl.hidden) return;
  event.preventDefault();
  setGlossaryOpen(false);
});

migrateLegacyHash();
renderFromPath().catch((err) => {
  pageEl.replaceChildren();
  showError(err instanceof Error ? err.message : "Failed to load routes.");
});
