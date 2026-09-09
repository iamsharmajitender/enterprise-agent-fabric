---
title: Running locally
sidebar_label: Start the fabric
---

# Running locally

From the repository root:

```bash
./agent-fabric-scripts/stack/start-app.sh
```

That builds and starts Compose in the background. Chat demos: [stack/README.md](https://github.com/iamsharmajitender/enterprise-agent-fabric/blob/main/agent-fabric-scripts/stack/README.md).

| Port | Process |
| --- | --- |
| 3005 | Agent Front Door (chat + jobs) |
| 3006 | Control Plane UI |
| 3007 | Agent Data Plane |
| 3008 | Agent Runtime |
| 3009 | Agent Capability Registry |

Compose, health checks, seed reload, and Grafana: root [README.md](https://github.com/iamsharmajitender/enterprise-agent-fabric/blob/main/README.md). This page does not repeat that runbook.

What the binary does after start: [request lifecycle](/concepts/executing-a-request/request-lifecycle). Catalogue routes: [catalogue](/catalogue/).
