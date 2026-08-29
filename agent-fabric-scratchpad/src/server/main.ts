import { createUiServer, listenPort } from "./ui-server.js";

const server = createUiServer();
const port = listenPort();
server.listen(port, "0.0.0.0", () => {
  console.log(
    JSON.stringify({
      service: "agent-fabric-scratchpad",
      chat: `http://0.0.0.0:${port}/chat`,
      jobs: `http://0.0.0.0:${port}/jobs`,
    }),
  );
});
