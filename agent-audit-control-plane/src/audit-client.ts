import { workloadHeaders } from "./workload.js";

export type AuditEvent = {
  event_id: string;
  event_type: string;
  occurred_at: string;
  producer: string;
  correlation_id: string | null;
  session_id: string | null;
  decision_id: string | null;
  payload: Record<string, unknown>;
};

export type CompletedWorkflow = {
  correlation_id: string;
  session_id: string | null;
  decision_id: string | null;
  route_id: string | null;
  route_version: string | null;
  status: string;
  started_at: string;
  completed_at: string;
};

export type WorkflowPage = {
  status: number;
  items: CompletedWorkflow[];
  total: number;
  limit: number;
  offset: number;
};

export class AuditDataPlaneClient {
  constructor(
    private readonly baseUrl: string,
    private readonly fetchImpl: typeof fetch = fetch,
  ) {}

  async getChain(correlationId: string): Promise<{ status: number; events: AuditEvent[] }> {
    const url = new URL(`/v1/audit/chains/${encodeURIComponent(correlationId)}`, this.baseUrl);
    const res = await this.fetchImpl(url, { headers: workloadHeaders() });
    if (!res.ok) {
      return { status: res.status, events: [] };
    }
    const events = (await res.json()) as AuditEvent[];
    return { status: res.status, events: Array.isArray(events) ? events : [] };
  }

  async getSession(sessionId: string): Promise<{ status: number; events: AuditEvent[] }> {
    const url = new URL(`/v1/audit/sessions/${encodeURIComponent(sessionId)}`, this.baseUrl);
    const res = await this.fetchImpl(url, { headers: workloadHeaders() });
    if (!res.ok) {
      return { status: res.status, events: [] };
    }
    const events = (await res.json()) as AuditEvent[];
    return { status: res.status, events: Array.isArray(events) ? events : [] };
  }

  async listWorkflows(limit = 50, offset = 0): Promise<WorkflowPage> {
    const url = new URL("/v1/audit/workflows", this.baseUrl);
    url.searchParams.set("limit", String(limit));
    url.searchParams.set("offset", String(offset));
    const res = await this.fetchImpl(url, { headers: workloadHeaders() });
    if (!res.ok) {
      return { status: res.status, items: [], total: 0, limit, offset };
    }
    const body = (await res.json()) as {
      items?: CompletedWorkflow[];
      total?: number;
      limit?: number;
      offset?: number;
    };
    return {
      status: res.status,
      items: Array.isArray(body.items) ? body.items : [],
      total: Number(body.total) || 0,
      limit: Number(body.limit) || limit,
      offset: Number(body.offset) || offset,
    };
  }
}
