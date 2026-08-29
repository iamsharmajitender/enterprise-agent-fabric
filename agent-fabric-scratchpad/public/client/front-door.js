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
