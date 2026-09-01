export class FrontDoorClient {
    claimsJson;
    constructor(claimsJson) {
        this.claimsJson = claimsJson;
    }
    setClaims(claimsJson) {
        this.claimsJson = claimsJson;
    }
    headers() {
        return {
            Authorization: "Bearer stub",
            "Content-Type": "application/json",
            "X-Stub-Claims": this.claimsJson,
        };
    }
    async fetchJson(path, init = {}) {
        const res = await fetch(path, { headers: this.headers(), ...init });
        const text = await res.text();
        let body;
        try {
            body = JSON.parse(text);
        }
        catch {
            body = { raw: text };
        }
        if (!res.ok) {
            throw new Error(`${res.status} ${text}`);
        }
        return body;
    }
}
export function resultMessages(ev) {
    const out = [];
    const result = ev.result;
    if (result && Array.isArray(result.messages)) {
        for (const item of result.messages) {
            out.push(String(item));
        }
    }
    else if (result?.message) {
        out.push(String(result.message));
    }
    if (ev.message) {
        out.push(String(ev.message));
    }
    return out;
}
