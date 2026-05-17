import logging

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.shared.config.settings import settings

_logger = logging.getLogger("otel")
_is_initialized = False


def _resolve_traces_endpoint() -> str:
    if settings.OTEL_EXPORTER_OTLP_TRACES_ENDPOINT:
        return settings.OTEL_EXPORTER_OTLP_TRACES_ENDPOINT
    base = settings.OTEL_EXPORTER_OTLP_ENDPOINT.rstrip("/")
    return f"{base}/v1/traces"


def _resolve_metrics_endpoint() -> str:
    if settings.OTEL_EXPORTER_OTLP_METRICS_ENDPOINT:
        return settings.OTEL_EXPORTER_OTLP_METRICS_ENDPOINT
    base = settings.OTEL_EXPORTER_OTLP_ENDPOINT.rstrip("/")
    return f"{base}/v1/metrics"


def _parse_headers(raw_headers: str | None) -> dict[str, str] | None:
    if not raw_headers:
        return None
    pairs = [part.strip() for part in raw_headers.split(",") if part.strip()]
    parsed: dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            continue
        key, value = pair.split("=", 1)
        parsed[key.strip()] = value.strip()
    return parsed or None


def init_otel() -> None:
    global _is_initialized
    if not settings.OTEL_ENABLED or _is_initialized:
        return

    resource = Resource.create({SERVICE_NAME: settings.OTEL_SERVICE_NAME})
    tracer_provider = TracerProvider(resource=resource)
    span_exporter = OTLPSpanExporter(
        endpoint=_resolve_traces_endpoint(),
        headers=_parse_headers(settings.OTEL_EXPORTER_OTLP_HEADERS),
    )
    tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
    trace.set_tracer_provider(tracer_provider)

    metric_exporter = OTLPMetricExporter(
        endpoint=_resolve_metrics_endpoint(),
        headers=_parse_headers(settings.OTEL_EXPORTER_OTLP_HEADERS),
    )
    metric_reader = PeriodicExportingMetricReader(metric_exporter)
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])

    LoggingInstrumentor().instrument(set_logging_format=False)
    # Set global meter provider only after all components are ready.
    from opentelemetry import metrics

    metrics.set_meter_provider(meter_provider)

    _is_initialized = True
    _logger.info(
        "OpenTelemetry initialized",
        extra={
            "otel_enabled": settings.OTEL_ENABLED,
            "otel_service_name": settings.OTEL_SERVICE_NAME,
            "otel_traces_endpoint": _resolve_traces_endpoint(),
            "otel_metrics_endpoint": _resolve_metrics_endpoint(),
        },
    )


def instrument_fastapi(app: FastAPI) -> None:
    if not settings.OTEL_ENABLED:
        return
    FastAPIInstrumentor.instrument_app(app)
