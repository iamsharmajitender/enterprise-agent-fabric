export type CatalogueRoute = {
  prompt_id?: string | null;
  workflow_id?: string | null;
  tool_manifest?: string | null;
  manifest?: { manifest_id?: string | null } | null;
};

export type CatalogueTable = {
  routes?: CatalogueRoute[];
};

export type FabricPrompt = {
  prompt_id?: string | null;
};

export type FabricWorkflow = {
  workflow_id?: string | null;
};

export type FabricManifest = {
  manifest_id?: string | null;
  tools?: Array<{ capability_id?: string | null }> | null;
};

export type FabricCapability = {
  id?: string | null;
};

export type FabricCatalogues = {
  routes?: CatalogueRoute[] | null;
  prompts?: FabricPrompt[] | null;
  workflows?: FabricWorkflow[] | null;
  manifests?: FabricManifest[] | null;
  capabilities?: FabricCapability[] | null;
};

export type FabricRelation = {
  used: number;
  total: number;
  unused: number;
  unboundRoutes: number;
};

export type FabricWiring = {
  prompts: FabricRelation;
  manifests: FabricRelation;
  workflows: FabricRelation;
  capabilities: FabricRelation;
};

export function catalogueStats(table: CatalogueTable | null | undefined) {
  const routes = Array.isArray(table?.routes) ? table.routes : [];
  const prompts = new Set<string>();
  const manifests = new Set<string>();
  for (const route of routes) {
    if (route.prompt_id) prompts.add(route.prompt_id);
    const manifestId = route.tool_manifest ?? route.manifest?.manifest_id;
    if (manifestId && manifestId !== "none") manifests.add(manifestId);
  }
  return {
    routes: routes.length,
    prompts: prompts.size,
    manifests: manifests.size,
  };
}

export function fabricWiring(catalogues: FabricCatalogues | null | undefined): FabricWiring {
  const routes = Array.isArray(catalogues?.routes) ? catalogues.routes : [];
  const promptIds = uniqueIds((catalogues?.prompts ?? []).map((item) => item.prompt_id));
  const workflowIds = uniqueIds((catalogues?.workflows ?? []).map((item) => item.workflow_id));
  const manifestIds = uniqueIds((catalogues?.manifests ?? []).map((item) => item.manifest_id));
  const capabilityIds = uniqueIds((catalogues?.capabilities ?? []).map((item) => item.id));
  const usedPrompts = uniqueIds(routes.map((route) => route.prompt_id));
  const usedWorkflows = uniqueIds(routes.map((route) => route.workflow_id));
  const usedManifests = uniqueIds(routes.map(routeManifestId));
  const usedCapabilities = uniqueIds(
    (catalogues?.manifests ?? []).flatMap((manifest) =>
      (manifest.tools ?? []).map((tool) => tool.capability_id),
    ),
  );
  return {
    prompts: relation(promptIds, usedPrompts, routes.filter((route) => !trimId(route.prompt_id)).length),
    manifests: relation(
      manifestIds,
      usedManifests,
      routes.filter((route) => routeManifestId(route) == null).length,
    ),
    workflows: relation(
      workflowIds,
      usedWorkflows,
      routes.filter((route) => !trimId(route.workflow_id)).length,
    ),
    capabilities: relation(capabilityIds, usedCapabilities, 0),
  };
}

function relation(catalog: Set<string>, referenced: Set<string>, unboundRoutes: number): FabricRelation {
  let used = 0;
  for (const id of catalog) {
    if (referenced.has(id)) used += 1;
  }
  return {
    used,
    total: catalog.size,
    unused: catalog.size - used,
    unboundRoutes,
  };
}

function routeManifestId(route: CatalogueRoute): string | null {
  return trimId(route.tool_manifest ?? route.manifest?.manifest_id);
}

function uniqueIds(values: Array<string | null | undefined>): Set<string> {
  const ids = new Set<string>();
  for (const value of values) {
    const id = trimId(value);
    if (id) ids.add(id);
  }
  return ids;
}

function trimId(value: string | null | undefined): string | null {
  const id = value?.trim();
  if (!id || id === "none") return null;
  return id;
}
