export function catalogKey(row) {
    return row.id ?? row.route_id;
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
