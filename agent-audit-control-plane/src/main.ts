import { auditDataPlaneUrl, boot } from "./boot.js";
import { AuditDataPlaneClient } from "./audit-client.js";
import { createUiServer, listenPort } from "./ui-server.js";

boot();
const client = new AuditDataPlaneClient(auditDataPlaneUrl());
const server = createUiServer(client);
const port = listenPort();
server.listen(port, "0.0.0.0", () => {
  console.log(
    JSON.stringify({ service: "agent-audit-control-plane", ui: `http://0.0.0.0:${port}` }),
  );
});
