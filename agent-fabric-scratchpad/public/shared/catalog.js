export function catalogKey(row) {
    return row.id ?? row.route_id;
}
/**
 * Demo chat catalog pins layer ① via opaque hint chips (FR-5: no route_id on the wire).
 * Prefer `hint_contains` against chip labels; if only one chip is eligible, use it.
 */
export function pickDemoHintId(hints, selected) {
    if (!selected)
        return null;
    const list = hints ?? [];
    if (selected.hint_contains) {
        const needle = selected.hint_contains.toLowerCase();
        const hit = list.find((h) => String(h.label ?? "").toLowerCase().includes(needle));
        if (!hit) {
            throw new Error(`no hint matching ${selected.hint_contains}`);
        }
        return hit.hint_id;
    }
    if (selected.route_id) {
        if (list.length === 1)
            return list[0].hint_id;
        if (!list.length) {
            throw new Error(`no eligible hints for ${selected.route_id}`);
        }
        throw new Error(`ambiguous hints for ${selected.route_id}; set hint_contains on the catalog row`);
    }
    return null;
}
export function mintToken() {
    return crypto.randomUUID().replace(/-/g, "").slice(0, 12);
}
export function expandToken(text, token = mintToken()) {
    return String(text ?? "").replaceAll("{id}", token);
}
export function expandPayload(payload, token = mintToken()) {
    const out = {};
    for (const [key, value] of Object.entries(payload)) {
        if (typeof value === "string") {
            out[key] = value.replaceAll("{id}", token);
        }
        else {
            out[key] = value;
        }
    }
    return out;
}
export function claimsFor(claimIds) {
    const emts = {};
    for (const claim of claimIds) {
        emts[claim] = true;
    }
    return { sub: "jane", emts };
}
export function claimsHeader(claims) {
    return JSON.stringify(claims);
}
export function groupByLabel(rows) {
    const groups = new Map();
    for (const row of rows) {
        const label = row.label || "Other";
        const bucket = groups.get(label);
        if (bucket) {
            bucket.push(row);
        }
        else {
            groups.set(label, [row]);
        }
    }
    return groups;
}
