import { boot } from "./boot.js";
import { acrBaseUrl, adpBaseUrl } from "./boot.js";
import { DataPlaneClient } from "./data-plane-client.js";
import { RegistryClient } from "./registry-client.js";
import { startTelemetry, tracedFetch } from "./telemetry.js";
import { createUiServer, listenPort } from "./ui-server.js";

startTelemetry();
boot();

const fetchImpl = tracedFetch(fetch);
const client = new DataPlaneClient(adpBaseUrl(), fetchImpl);
const registry = new RegistryClient(acrBaseUrl(), fetchImpl);
const server = createUiServer(client, registry);
const port = listenPort();
server.listen(port, "0.0.0.0", () => {
  console.log(JSON.stringify({ service: "agent-control-plane", ui: `http://0.0.0.0:${port}` }));
});

const jane = JSON.stringify({ sub: "jane", emts: { "accounts:read": true } });

async function proveClient(): Promise<void> {
  let lastError: unknown;
  for (let attempt = 0; attempt < 20; attempt += 1) {
    try {
      const eligible = await client.getEligible("web", jane);
      const catalogue = await client.getCatalogueRoute("fee_explain", "2026.08.1");
      console.log(
        JSON.stringify({
          eligible_status: eligible.status,
          fee_explain_status: catalogue.status,
          fee_explain: await catalogue.json().catch(() => null),
        }),
      );
      return;
    } catch (err) {
      lastError = err;
      await new Promise((resolve) => setTimeout(resolve, 1000));
    }
  }
  console.error(lastError);
}

void proveClient();
