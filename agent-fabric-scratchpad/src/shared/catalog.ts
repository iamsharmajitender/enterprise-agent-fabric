import type { Claims } from "./types.js";

export function catalogKey(row: { id?: string; route_id: string }): string {
  return row.id ?? row.route_id;
}

export function mintToken(): string {
  return crypto.randomUUID().replace(/-/g, "").slice(0, 12);
}

export function expandToken(text: string, token = mintToken()): string {
  return String(text ?? "").replaceAll("{id}", token);
}

export function expandPayload(
  payload: Record<string, unknown>,
  token = mintToken(),
): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(payload)) {
    if (typeof value === "string") {
      out[key] = value.replaceAll("{id}", token);
    } else {
      out[key] = value;
    }
  }
  return out;
}

export function claimsFor(claimIds: string[]): Claims {
  const emts: Record<string, boolean> = {};
  for (const claim of claimIds) {
    emts[claim] = true;
  }
  return { sub: "jane", emts };
}

export function claimsHeader(claims: Claims): string {
  return JSON.stringify(claims);
}

export function groupByLabel<T extends { label: string }>(rows: T[]): Map<string, T[]> {
  const groups = new Map<string, T[]>();
  for (const row of rows) {
    const label = row.label || "Other";
    const bucket = groups.get(label);
    if (bucket) {
      bucket.push(row);
    } else {
      groups.set(label, [row]);
    }
  }
  return groups;
}
