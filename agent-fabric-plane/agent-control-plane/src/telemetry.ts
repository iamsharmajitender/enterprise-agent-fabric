import { context, propagation, SpanStatusCode, trace } from "@opentelemetry/api";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
import { Resource } from "@opentelemetry/resources";
import { BatchSpanProcessor } from "@opentelemetry/sdk-trace-base";
import { NodeTracerProvider } from "@opentelemetry/sdk-trace-node";

let started = false;

export function startTelemetry(): void {
  if (started) return;
  started = true;
  const endpoint = (process.env.OTEL_EXPORTER_OTLP_ENDPOINT ?? "http://localhost:4318").replace(
    /\/$/,
    "",
  );
  const serviceName = process.env.OTEL_SERVICE_NAME ?? "agent-control-plane";
  const provider = new NodeTracerProvider({
    resource: new Resource({
      "service.name": serviceName,
      "service.namespace": "agent-fabric",
      "deployment.environment": "local",
    }),
  });
  provider.addSpanProcessor(
    new BatchSpanProcessor(new OTLPTraceExporter({ url: `${endpoint}/v1/traces` })),
  );
  provider.register();
}

export function tracedFetch(fetchImpl: typeof fetch = fetch): typeof fetch {
  const tracer = trace.getTracer("agent-control-plane");
  return async (input, init = {}) => {
    const url =
      typeof input === "string"
        ? input
        : input instanceof URL
          ? input.toString()
          : input.url;
    return tracer.startActiveSpan(`HTTP ${init.method ?? "GET"}`, async (span) => {
      span.setAttribute("http.url", url.split("?")[0] ?? url);
      span.setAttribute("http.method", init.method ?? "GET");
      const headers = new Headers(init.headers);
      propagation.inject(context.active(), headers, {
        set: (h, k, v) => h.set(k, v),
      });
      try {
        const response = await fetchImpl(input, { ...init, headers });
        span.setAttribute("http.status_code", response.status);
        if (response.status >= 500) {
          span.setStatus({ code: SpanStatusCode.ERROR });
        }
        return response;
      } catch (err) {
        span.setStatus({
          code: SpanStatusCode.ERROR,
          message: err instanceof Error ? err.message : "fetch failed",
        });
        throw err;
      } finally {
        span.end();
      }
    });
  };
}
