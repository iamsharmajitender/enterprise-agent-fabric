import { workloadHeaders } from "./workload.js";

export class RegistryClient {
  constructor(
    private readonly baseUrl: string,
    private readonly fetchImpl: typeof fetch = fetch,
  ) {}

  listCapabilities(q?: string, include?: string): Promise<Response> {
    const url = new URL("/v1/capabilities", this.ensureTrailingSlash(this.baseUrl));
    if (q) {
      url.searchParams.set("q", q);
    }
    if (include) url.searchParams.set("include", include);
    return this.fetchImpl(url, { headers: workloadHeaders() });
  }

  getCapability(id: string, version?: string): Promise<Response> {
    const path = version
      ? `/v1/capabilities/${encodeURIComponent(id)}/versions/${encodeURIComponent(version)}`
      : `/v1/capabilities/${encodeURIComponent(id)}`;
    const url = new URL(path, this.ensureTrailingSlash(this.baseUrl));
    return this.fetchImpl(url, { headers: workloadHeaders() });
  }

  listCapabilityVersions(id: string): Promise<Response> {
    const url = new URL(
      `/v1/capabilities/${encodeURIComponent(id)}/versions`,
      this.ensureTrailingSlash(this.baseUrl),
    );
    return this.fetchImpl(url, { headers: workloadHeaders() });
  }

  private ensureTrailingSlash(baseUrl: string): string {
    return baseUrl.endsWith("/") ? baseUrl : `${baseUrl}/`;
  }
}
