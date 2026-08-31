# Chat / Jobs scratchpad

TypeScript UI for local Front Door demos. Serves chat and jobs scratchpads on **3014**, proxies `/v1/*` to Agent Front Door (`AFD_URL`, default `http://localhost:3005`).

## Run locally

```bash
cd agent-fabric-scratchpad
npm ci
npm run build
npm start
```

Open [http://localhost:3014/chat](http://localhost:3014/chat) and [http://localhost:3014/jobs](http://localhost:3014/jobs).

With Compose up, Front Door is proxied automatically inside the container. From the host, run with `AFD_URL=http://localhost:3005 npm start`.

## Layout

| Path | Role |
| --- | --- |
| `src/client/` | Browser TypeScript (compiled to `public/client/` and `public/shared/`) |
| `src/server/` | Static file server + AFD proxy |
| `src/shared/` | Catalog helpers shared by client and tests |
| `catalog/` | Chat and job demo definitions (`chats.json`, `jobs.json`) |
| `public/` | HTML shells, CSS, compiled client JS |

## Tests

```bash
npm test
```

Keeps bundled catalogs present and checks the HTML shells.

## Non-goals

- Not a product UI; stub auth only (`Bearer stub` + `X-Stub-Claims`)
- Does not call Control Plane or Runtime directly — only Front Door
