export type ManifestToolRef = {
  name?: string | null;
  capability_id?: string | null;
  capability_version?: string | null;
};

export type ManifestRef = {
  manifest_id?: string | null;
  manifest_version?: string | null;
  tools?: ManifestToolRef[] | null;
};

export type CapabilityRef = {
  id?: string | null;
  version?: string | null;
  description?: string | null;
};

export type RouteRef = {
  route_id?: string | null;
  route_version?: string | null;
  tool_manifest?: string | null;
  tool_manifest_version?: string | null;
};

export type CapabilityUse = {
  manifest_id: string;
  manifest_version: string | null;
  tool_name: string | null;
  capability_version: string | null;
  route_id: string | null;
  route_version: string | null;
};

export type CapabilityUsageRow = {
  capability_id: string;
  version: string | null;
  description: string | null;
  uses: CapabilityUse[];
};

export function capabilityUsage(
  manifests: ManifestRef[] | null | undefined,
  capabilities: CapabilityRef[] | null | undefined = [],
  routes: RouteRef[] | null | undefined = [],
): CapabilityUsageRow[] {
  const rows = new Map<string, CapabilityUsageRow>();
  for (const capability of capabilities ?? []) {
    const id = capability.id?.trim();
    if (!id) continue;
    rows.set(id, {
      capability_id: id,
      version: capability.version ?? null,
      description: capability.description ?? null,
      uses: [],
    });
  }
  for (const manifest of manifests ?? []) {
    const manifestId = manifest.manifest_id?.trim();
    if (!manifestId) continue;
    for (const tool of manifest.tools ?? []) {
      const capabilityId = tool.capability_id?.trim();
      if (!capabilityId) continue;
      let row = rows.get(capabilityId);
      if (!row) {
        row = {
          capability_id: capabilityId,
          version: null,
          description: null,
          uses: [],
        };
        rows.set(capabilityId, row);
      }
      const use = {
        manifest_id: manifestId,
        manifest_version: manifest.manifest_version ?? null,
        tool_name: tool.name ?? null,
        capability_version: tool.capability_version ?? null,
      };
      const matching = matchingRoutes(use, routes ?? []);
      if (matching.length === 0) {
        row.uses.push({ ...use, route_id: null, route_version: null });
        continue;
      }
      for (const route of matching) {
        row.uses.push({
          ...use,
          route_id: route.route_id?.trim() || null,
          route_version: route.route_version ?? null,
        });
      }
    }
  }
  return [...rows.values()].sort((a, b) => a.capability_id.localeCompare(b.capability_id));
}

function matchingRoutes(use: Omit<CapabilityUse, "route_id" | "route_version">, routes: RouteRef[]) {
  return routes.filter((route) => {
    const manifestId = route.tool_manifest?.trim();
    if (!manifestId || manifestId !== use.manifest_id) return false;
    if (use.manifest_version && route.tool_manifest_version) {
      return route.tool_manifest_version === use.manifest_version;
    }
    return true;
  });
}
