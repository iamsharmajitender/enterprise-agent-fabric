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

| Port | Component | Job |
| --- | --- | --- |
| 3005 | [Agent Front Door](/architecture/service-packs/agent-front-door) | Only public ingress. Chat and jobs. |
| 3006 | Control Plane UI | Catalogue browser. |
| 3007 | [Agent Data Plane](/architecture/service-packs/agent-plane) | Catalogue and classify. |
| 3008 | [Agent Runtime](/architecture/service-packs/agent-runtime) | Pin, hydrate, run. |
| 3009 | [Agent Capability Plane](/architecture/service-packs/agent-capability-registry) | Published capabilities. |
| 3014 | Chat scratchpad | Seeded demo UI. |

Open [http://localhost:3014/chat](http://localhost:3014/chat) when you want a browser, or stay on the next page and use `curl`.

Health check the door:

```bash
curl -sf http://localhost:3005/health
```

A healthy Front Door is enough to continue.

## Next

Send [your first request](/guides/first-request). Compose, Grafana, and seed reload details stay in the root [README](https://github.com/iamsharmajitender/enterprise-agent-fabric/blob/main/README.md).
