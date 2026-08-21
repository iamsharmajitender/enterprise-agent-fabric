import { workloadHeaders } from "./workload.js";

export class DataPlaneClient {
  constructor(
    private readonly baseUrl: string,
    private readonly fetchImpl: typeof fetch = fetch,
  ) {}

  getEligible(channel = "web", claimsJson?: string): Promise<Response> {
    const url = new URL("/v1/intent/eligible", this.ensureTrailingSlash(this.baseUrl));
    url.searchParams.set("channel", channel);
    const headers = new Headers(workloadHeaders());
    if (claimsJson) {
      headers.set("X-Stub-Claims", claimsJson);
    }
    return this.fetchImpl(url, { headers });
  }

  listRoutes(include?: string): Promise<Response> {
    const url = new URL("/v1/catalog/routes", this.ensureTrailingSlash(this.baseUrl));
    if (include) url.searchParams.set("include", include);
    return this.fetchImpl(url, { headers: workloadHeaders() });
  }

  getCatalogueRoute(routeId: string, routeVersion?: string): Promise<Response> {
    const url = new URL(
      `/v1/catalog/routes/${encodeURIComponent(routeId)}`,
      this.ensureTrailingSlash(this.baseUrl),
    );
    if (routeVersion) {
      url.searchParams.set("route_version", routeVersion);
    }
    return this.fetchImpl(url, { headers: workloadHeaders() });
  }

  listRouteVersions(routeId: string): Promise<Response> {
    const url = new URL(
      `/v1/catalog/routes/${encodeURIComponent(routeId)}/versions`,
      this.ensureTrailingSlash(this.baseUrl),
    );
    return this.fetchImpl(url, { headers: workloadHeaders() });
  }

  listPrompts(include?: string): Promise<Response> {
    const url = new URL("/v1/catalog/prompts", this.ensureTrailingSlash(this.baseUrl));
    if (include) url.searchParams.set("include", include);
    return this.fetchImpl(url, { headers: workloadHeaders() });
  }

  getPrompt(promptId: string, promptVersion?: string): Promise<Response> {
    const path = promptVersion
      ? `/v1/catalog/prompts/${encodeURIComponent(promptId)}/versions/${encodeURIComponent(promptVersion)}`
      : `/v1/catalog/prompts/${encodeURIComponent(promptId)}`;
    const url = new URL(path, this.ensureTrailingSlash(this.baseUrl));
    return this.fetchImpl(url, { headers: workloadHeaders() });
  }

  listPromptVersions(promptId: string): Promise<Response> {
    const url = new URL(
      `/v1/catalog/prompts/${encodeURIComponent(promptId)}/versions`,
      this.ensureTrailingSlash(this.baseUrl),
    );
    return this.fetchImpl(url, { headers: workloadHeaders() });
  }

  listWorkflows(include?: string): Promise<Response> {
    const url = new URL("/v1/catalog/workflows", this.ensureTrailingSlash(this.baseUrl));
    if (include) url.searchParams.set("include", include);
    return this.fetchImpl(url, { headers: workloadHeaders() });
  }

  getWorkflow(workflowId: string, workflowVersion?: string): Promise<Response> {
    const path = workflowVersion
      ? `/v1/catalog/workflows/${encodeURIComponent(workflowId)}/versions/${encodeURIComponent(workflowVersion)}`
      : `/v1/catalog/workflows/${encodeURIComponent(workflowId)}`;
    const url = new URL(path, this.ensureTrailingSlash(this.baseUrl));
    return this.fetchImpl(url, { headers: workloadHeaders() });
  }

  listWorkflowVersions(workflowId: string): Promise<Response> {
    const url = new URL(
      `/v1/catalog/workflows/${encodeURIComponent(workflowId)}/versions`,
      this.ensureTrailingSlash(this.baseUrl),
    );
    return this.fetchImpl(url, { headers: workloadHeaders() });
  }

  listManifests(include?: string): Promise<Response> {
    const url = new URL("/v1/catalog/manifests", this.ensureTrailingSlash(this.baseUrl));
    if (include) url.searchParams.set("include", include);
    return this.fetchImpl(url, { headers: workloadHeaders() });
  }

  getManifest(manifestId: string, manifestVersion?: string): Promise<Response> {
    const path = manifestVersion
      ? `/v1/catalog/manifests/${encodeURIComponent(manifestId)}/versions/${encodeURIComponent(manifestVersion)}`
      : `/v1/catalog/manifests/${encodeURIComponent(manifestId)}`;
    const url = new URL(path, this.ensureTrailingSlash(this.baseUrl));
    return this.fetchImpl(url, { headers: workloadHeaders() });
  }

  listManifestVersions(manifestId: string): Promise<Response> {
    const url = new URL(
      `/v1/catalog/manifests/${encodeURIComponent(manifestId)}/versions`,
      this.ensureTrailingSlash(this.baseUrl),
    );
    return this.fetchImpl(url, { headers: workloadHeaders() });
  }

  private ensureTrailingSlash(baseUrl: string): string {
    return baseUrl.endsWith("/") ? baseUrl : `${baseUrl}/`;
  }
}
