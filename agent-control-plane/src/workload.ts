export const WORKLOAD_ID = "acp" as const;
export const INTERNAL_BEARER = "Bearer fabric-internal";

export function workloadHeaders(): Record<string, string> {
  return {
    Authorization: INTERNAL_BEARER,
    "X-Workload": WORKLOAD_ID,
  };
}
