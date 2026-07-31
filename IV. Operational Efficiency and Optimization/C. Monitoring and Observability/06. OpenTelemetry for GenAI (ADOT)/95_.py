from opentelemetry import trace, metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

def configure_metrics(service_name: str):
    """Configure OpenTelemetry metrics alongside traces"""
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint='http://otel-collector:4317', insecure=True),
        export_interval_millis=60000
    )

    meter_provider = MeterProvider(metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    return metrics.get_meter(service_name)


class MetricsInstrumentedClient:
    """Client with both tracing and metrics instrumentation"""

    def __init__(self, tracer: trace.Tracer, meter: metrics.Meter):
        self.bedrock = boto3.client('bedrock-runtime')
        self.tracer = tracer
        self.meter = meter

        # Create metrics instruments
        self.invocation_counter = meter.create_counter(
            name='genai.invocations',
            description='Number of model invocations',
            unit='1'
        )

        self.token_counter = meter.create_counter(
            name='genai.tokens',
            description='Token usage',
            unit='tokens'
        )

        self.latency_histogram = meter.create_histogram(
            name='genai.latency',
            description='Model invocation latency',
            unit='ms'
        )

    def invoke(self, model_id: str, prompt: str) -> dict:
        """Invoke with both traces and metrics"""
        import time
        start_time = time.time()

        attributes = {
            'model_id': model_id,
            'service': 'chatbot'
        }

        with self.tracer.start_as_current_span('gen_ai.invoke') as span:
            span.set_attribute(GenAIAttributes.REQUEST_MODEL, model_id)

            try:
                body = json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1000,
                    "messages": [{"role": "user", "content": prompt}]
                })

                response = self.bedrock.invoke_model(modelId=model_id, body=body)
                response_body = json.loads(response['body'].read())
                usage = response_body['usage']

                # Record metrics
                self.invocation_counter.add(1, attributes)
                self.token_counter.add(
                    usage['input_tokens'],
                    {**attributes, 'token_type': 'input'}
                )
                self.token_counter.add(
                    usage['output_tokens'],
                    {**attributes, 'token_type': 'output'}
                )

                latency_ms = (time.time() - start_time) * 1000
                self.latency_histogram.record(latency_ms, attributes)

                return {
                    'text': response_body['content'][0]['text'],
                    'usage': usage
                }

            except Exception as e:
                self.invocation_counter.add(
                    1,
                    {**attributes, 'error': 'true'}
                )
                raise