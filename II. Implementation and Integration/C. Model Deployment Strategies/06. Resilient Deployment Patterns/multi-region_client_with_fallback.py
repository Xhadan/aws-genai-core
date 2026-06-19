import boto3
import json
import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List
from threading import Lock

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery

@dataclass
class CircuitBreaker:
    """Circuit breaker for resilient service calls."""
    failure_threshold: int = 5
    recovery_timeout: int = 30
    half_open_max_calls: int = 3

    _failures: int = field(default=0, initlse)
    _state: CircuitState = field(default=CircuitState.CLOSED, initlse)
    _last_failure_time: float = field(default=0, initlse)
    _half_open_calls: int = field(default=0, initlse)
    _lock: Lock = field(default_factory=Lock, initlse)

    def can_execute(self) -> bool:
        with self._lock:
            if self._state = CircuitState.CLOSED:
                return True
            elif self._state = CircuitState.OPEN:
                if time.time() - self._last_failure_time > self.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                    return True
                return False
            else:  # HALF_OPEN
                return self._half_open_calls < self.half_open_max_calls

    def record_success(self):
        with self._lock:
            if self._state = CircuitState.HALF_OPEN:
                self._half_open_calls += 1
                if self._half_open_calls >= self.half_open_max_calls:
                    self._state = CircuitState.CLOSED
                    self._failures = 0
            else:
                self._failures = 0

    def record_failure(self):
        with self._lock:
            self._failures += 1
            self._last_failure_time = time.time()
            if self._state = CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
            elif self._failures >= self.failure_threshold:
                self._state = CircuitState.OPEN

class ResilientBedrockClient:
    """Multi-region Bedrock client with fallback and circuit breaker."""

    def __init__(
        self,
        primary_region: str = "us-east-1",
        fallback_regions: List[str] = None,
        primary_model: str = "anthropic.claude-3-sonnet-20240229-v1:0",
        fallback_model: str = "anthropic.claude-3-haiku-20240307-v1:0"
    ):
        self.regions = [primary_region] + (fallback_regions or ["us-west-2"])
        self.primary_model = primary_model
        self.fallback_model = fallback_model

        # Create clients for each region
        self.clients = {
            region: boto3.client('bedrock-runtime', region_name=region)
            for region in self.regions
        }

        # Circuit breaker per region
        self.circuit_breakers = {
            region: CircuitBreaker() for region in self.regions
        }

    def invoke_model(
        self,
        prompt: str,
        max_tokens: int = 1024,
        use_fallback_model: bool = False
    ) -> dict:
        """
        Invoke model with automatic failover across regions.
        """
        model_id = self.fallback_model if use_fallback_model else self.primary_model
        last_error = None

        for region in self.regions:
            circuit = self.circuit_breakers[region]

            if not circuit.can_execute():
                print(f"Circuit open for {region}, skipping")
                continue

            try:
                response = self._invoke_single_region(
                    region=region,
                    model_id=model_id,
                    prompt=prompt,
                    max_tokens=max_tokens
                )
                circuit.record_success()
                return {
                    'response': response,
                    'region': region,
                    'model': model_id,
                    'fallback_used': use_fallback_model
                }

            except self.clients[region].exceptions.ThrottlingException as e:
                print(f"Throttled in {region}: {e}")
                circuit.record_failure()
                last_error = e

            except Exception as e:
                print(f"Error in {region}: {e}")
                circuit.record_failure()
                last_error = e

        # All regions failed with primary model, try fallback
        if not use_fallback_model:
            print("All regions failed, trying fallback model")
            return self.invoke_model(
                prompt=prompt,
                max_tokens=max_tokens,
                use_fallback_model=True
            )

        raise Exception(f"All regions and fallback failed: {last_error}")

    def _invoke_single_region(
        self,
        region: str,
        model_id: str,
        prompt: str,
        max_tokens: int
    ) -> str:
        client = self.clients[region]

        response = client.invoke_model(
            modelId=model_id,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}]
            })
        )

        result = json.loads(response['body'].read())
        return result['content'][0]['text']

# Usage
client = ResilientBedrockClient(
    primary_region="us-east-1",
    fallback_regions=["us-west-2", "eu-west-1"]
)

result = client.invoke_model("Explain cloud computing")
print(f"Response from {result['region']} using {result['model']}")
print(f"Fallback used: {result['fallback_used']}")