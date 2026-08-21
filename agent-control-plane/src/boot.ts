import { WORKLOAD_ID } from "./workload.js";
import { listenPort } from "./ui-server.js";

export function adpBaseUrl(): string {
  return process.env.ADP_BASE_URL ?? "http://localhost:3007";
}

export function acrBaseUrl(): string {
  return process.env.ACR_BASE_URL ?? "http://localhost:3009";
}

export function boot(log: (line: string) => void = console.log): void {
  log(
    JSON.stringify({
      service: "agent-control-plane",
      role: "client",
      listen: listenPort() > 0,
      port: listenPort(),
      adp: adpBaseUrl(),
      acr: acrBaseUrl(),
      workload: WORKLOAD_ID,
    }),
  );
}
