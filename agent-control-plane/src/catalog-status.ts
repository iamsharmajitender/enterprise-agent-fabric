export type CatalogStatus = "draft" | "published" | "active" | "retired";

export type CatalogStatusInput = {
  status?: string | null;
  active?: boolean | null;
  live?: boolean | null;
};

export const CATALOG_STATUSES: CatalogStatus[] = ["draft", "published", "active", "retired"];

export const LIST_TAB_STATUSES: CatalogStatus[] = ["active", "published", "draft", "retired"];

export function parseListTabStatus(raw: string | null | undefined): CatalogStatus {
  const value = (raw ?? "").trim().toLowerCase();
  return (LIST_TAB_STATUSES as string[]).includes(value) ? (value as CatalogStatus) : "active";
}

const LABELS: Record<CatalogStatus, string> = {
  draft: "Draft",
  published: "Published",
  active: "Active",
  retired: "Retired",
};

export function catalogStatus(input: CatalogStatusInput = {}): CatalogStatus {
  const raw = (input.status ?? "").trim().toLowerCase();
  if (raw === "draft") return "draft";
  if (raw === "deprecated" || raw === "retired") return "retired";
  if (raw === "active") return "active";
  if (input.active === true) return "active";
  if (input.live === true) return "active";
  if (input.active === false) return "published";
  if (input.live === false) return "published";
  if (raw === "published" || raw === "") return "active";
  return "published";
}

export function catalogStatusLabel(status: CatalogStatus): string {
  return LABELS[status];
}

export function catalogStatusClass(status: CatalogStatus): string {
  if (status === "active") return "ok";
  if (status === "retired") return "warn";
  if (status === "published") return "info";
  return "";
}

export function compareCatalogVersion(left: string, right: string): number {
  const a = versionParts(left);
  const b = versionParts(right);
  const n = Math.max(a.length, b.length);
  for (let i = 0; i < n; i += 1) {
    const compared = (a[i] ?? 0) - (b[i] ?? 0);
    if (compared !== 0) return compared;
  }
  return 0;
}

export function livePublishedInputs(
  rows: Array<{ id: string; version: string; status?: string | null }>,
): CatalogStatusInput[] {
  const latest = new Map<string, string>();
  for (const row of rows) {
    const raw = (row.status ?? "published").trim().toLowerCase();
    if (raw !== "published" && raw !== "") continue;
    const current = latest.get(row.id);
    if (!current || compareCatalogVersion(row.version, current) > 0) {
      latest.set(row.id, row.version);
    }
  }
  return rows.map((row) => {
    const raw = (row.status ?? "published").trim().toLowerCase();
    const live = (raw === "published" || raw === "") && latest.get(row.id) === row.version;
    return { status: row.status, live };
  });
}

export type CatalogStatusCounts = Record<CatalogStatus, number> & { total: number };

export function countCatalogStatuses(inputs: CatalogStatusInput[]): CatalogStatusCounts {
  const counts: CatalogStatusCounts = {
    draft: 0,
    published: 0,
    active: 0,
    retired: 0,
    total: inputs.length,
  };
  for (const input of inputs) {
    counts[catalogStatus(input)] += 1;
  }
  return counts;
}

function versionParts(version: string): number[] {
  if (!version) return [];
  return version.split(".").map((part) => {
    const parsed = Number.parseInt(part, 10);
    return Number.isFinite(parsed) ? parsed : 0;
  });
}
