---
title: Start the fabric
sidebar_label: Start the fabric
slug: /running-locally
description: "Build and start the local Enterprise Agent Fabric stack, then open the surfaces you will use."
---

# Start the fabric

This is the local platform: one Front Door, one Agent Plane, one Runtime, and the shared boxes they call. You will start it, confirm it is up, then send a request on the next page.

## Prerequisites

- Docker and Docker Compose
- The repository cloned locally

## Start

From the repository root:

```bash
./agent-fabric-scripts/stack/start-app.sh
```

That builds and starts Compose in the background. Load the seed catalogue if the script did not:

```bash
./agent-fabric-scripts/stack/add-seed-data.sh
```

Chat demos and extra flags: [stack/README.md](https://github.com/iamsharmajitender/enterprise-agent-fabric/blob/main/agent-fabric-scripts/stack/README.md).

## What should be listening

| Component | Job |
| --- | --- |
| [Agent Front Door](/architecture/service-packs/agent-front-door) | Only public ingress. Chat and jobs. |
| Control Plane UI | Catalogue browser. |
| [Agent Data Plane](/architecture/service-packs/agent-plane) | Catalogue and classify. |
| [Agent Runtime](/architecture/service-packs/agent-runtime) | Pin, hydrate, run. |
| [Agent Capability Plane](/architecture/service-packs/agent-capability-registry) | Published capabilities. |
| Chat scratchpad | Seeded demo UI. |

Local binds are in the [stack README](https://github.com/iamsharmajitender/enterprise-agent-fabric/blob/main/agent-fabric-scripts/stack/README.md). A healthy Front Door (`GET /health`) is enough to continue.

## Next

Send [your first request](/guides/first-request). Compose, Grafana, and seed reload details stay in the root [README](https://github.com/iamsharmajitender/enterprise-agent-fabric/blob/main/README.md).
