export function auditDataPlaneUrl(): string {
  return process.env.AUDIT_DATA_PLANE_URL ?? "http://localhost:3012";
}

export function boot(): void {
  console.log(
    JSON.stringify({
      service: "agent-audit-control-plane",
      audit_data_plane: auditDataPlaneUrl(),
    }),
  );
}
