export class FrontDoorClient {
  constructor(private claimsJson: string) {}

  setClaims(claimsJson: string): void {
    this.claimsJson = claimsJson;
  }

  private headers(): HeadersInit {
    return {
      Authorization: "Bearer stub",
      "Content-Type": "application/json",
      "X-Stub-Claims": this.claimsJson,
    };
  }

  async fetchJson<T>(path: string, init: RequestInit = {}): Promise<T> {
    const res = await fetch(path, { headers: this.headers(), ...init });
    const text = await res.text();
    let body: T;
    try {
      body = JSON.parse(text) as T;
    } catch {
      body = { raw: text } as T;
    }
    if (!res.ok) {
      throw new Error(`${res.status} ${text}`);
    }
    return body;
  }
}

export type TurnResponse = {
  session_id?: string;
  status?: string;
  prompt?: string;
  options?: { id: string; label?: string }[];
  message?: string;
  result?: { message?: string };
};

export type EventsResponse = {
  status?: string;
  message?: string;
  result?: { message?: string };
};

export type HintsResponse = {
  session_id?: string;
  hints?: { hint_id: string; label?: string }[];
};

export type JobAccepted = {
  correlation_id?: string;
};

export type JobStatus = {
  status?: string;
  message?: string;
  result?: { message?: string };
};
