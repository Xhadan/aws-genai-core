import boto3
import json
import random
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


class LoadBalancedBedrockClient:
    """
    Distribute load across multiple regions and models.
    """

    def __init__(self, model_id: str, regions: List[str] = None):
        self.model_id = model_id
        self.regions = regions or ['us-east-1', 'us-west-2', 'eu-west-1']

        # Create clients for each region
        self.clients = {
            region: boto3.client('bedrock-runtime', region_name=region)
            for region in self.regions
        }

        # Track region health
        self.region_health = {region: True for region in self.regions}
        self.region_latencies = {region: [] for region in self.regions}

        # Thread-safe region selection
        self._lock = threading.Lock()
        self._current_region_index = 0

    def invoke_with_load_balancing(
        self,
        body: Dict[str, Any],
        strategy: str = 'round_robin'
    ) -> Dict[str, Any]:
        """
        Invoke model with load balancing across regions.

        Strategies:
        - 'round_robin': Rotate through regions
        - 'random': Random region selection
        - 'latency': Prefer lowest latency region
        - 'failover': Try primary, fallback on failure
        """
        if strategy = 'round_robin':
            return self._round_robin_invoke(body)
        elif strategy = 'random':
            return self._random_invoke(body)
        elif strategy = 'latency':
            return self._latency_based_invoke(body)
        elif strategy = 'failover':
            return self._failover_invoke(body)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    def _round_robin_invoke(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Round-robin load balancing.
        """
        with self._lock:
            healthy_regions = [r for r, h in self.region_health.items() if h]
            if not healthy_regions:
                healthy_regions = self.regions  # Reset if all unhealthy

            region = healthy_regions[
                self._current_region_index % len(healthy_regions)
            ]
            self._current_region_index += 1

        return self._invoke_region(region, body)

    def _random_invoke(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Random region selection.
        """
        healthy_regions = [r for r, h in self.region_health.items() if h]
        if not healthy_regions:
            healthy_regions = self.regions

        region = random.choice(healthy_regions)
        return self._invoke_region(region, body)

    def _latency_based_invoke(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Select region with lowest average latency.
        """
        # Calculate average latencies
        avg_latencies = {}
        for region, latencies in self.region_latencies.items():
            if latencies and self.region_health[region]:
                avg_latencies[region] = sum(latencies[-10:]) / len(latencies[-10:])

        if not avg_latencies:
            # No latency data yet, use random
            return self._random_invoke(body)

        # Select lowest latency region
        region = min(avg_latencies, key=avg_latencies.get)
        return self._invoke_region(region, body)

    def _failover_invoke(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Try regions in order until one succeeds.
        """
        last_error = None

        for region in self.regions:
            try:
                return self._invoke_region(region, body)
            except Exception as e:
                last_error = e
                self.region_health[region] = False
                continue

        raise last_error

    def _invoke_region(
        self,
        region: str,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Invoke model in specific region with latency tracking.
        """
        import time
        start = time.time()

        try:
            response = self.clients[region].invoke_model(
                modelId=self.model_id,
                body=json.dumps(body)
            )

            latency = time.time() - start
            self.region_latencies[region].append(latency)

            # Keep only last 100 latencies
            if len(self.region_latencies[region]) > 100:
                self.region_latencies[region] = self.region_latencies[region][-100:]

            self.region_health[region] = True

            result = json.loads(response['body'].read())
            result['_region'] = region
            result['_latency'] = latency

            return result

        except Exception as e:
            self.region_health[region] = False
            raise


class ProvisionedThroughputManager:
    """
    Manage provisioned throughput for consistent performance.
    """

    def __init__(self):
        self.bedrock = boto3.client('bedrock')

    def create_provisioned_throughput(
        self,
        model_id: str,
        model_units: int,
        commitment_duration: str = 'ONE_MONTH',
        throughput_name: str = None
    ) -> Dict[str, Any]:
        """
        Create provisioned throughput for a model.

        commitment_duration: 'ONE_MONTH' or 'SIX_MONTHS' for discount
        """
        throughput_name = throughput_name or f"pt-{model_id.split('.')[-1]}"

        response = self.bedrock.create_provisioned_model_throughput(
            modelUnits=model_units,
            provisionedModelName=throughput_name,
            modelId=model_id,
            commitmentDuration=commitment_duration
        )

        return {
            'provisioned_model_arn': response['provisionedModelArn'],
            'throughput_name': throughput_name,
            'model_units': model_units,
            'status': 'Creating'
        }

    def get_throughput_status(
        self,
        provisioned_model_id: str
    ) -> Dict[str, Any]:
        """
        Get status of provisioned throughput.
        """
        response = self.bedrock.get_provisioned_model_throughput(
            provisionedModelId=provisioned_model_id
        )

        return {
            'name': response['provisionedModelName'],
            'status': response['status'],
            'model_units': response['modelUnits'],
            'model_arn': response['modelArn'],
            'created_at': response.get('creationTime'),
            'commitment_expiration': response.get('commitmentExpirationTime')
        }

    def list_provisioned_throughputs(self) -> List[Dict[str, Any]]:
        """
        List all provisioned throughputs.
        """
        throughputs = []
        paginator = self.bedrock.get_paginator(
            'list_provisioned_model_throughputs'
        )

        for page in paginator.paginate():
            for pt in page['provisionedModelSummaries']:
                throughputs.append({
                    'name': pt['provisionedModelName'],
                    'arn': pt['provisionedModelArn'],
                    'status': pt['status'],
                    'model_arn': pt['modelArn']
                })

        return throughputs

    def calculate_required_units(
        self,
        expected_tpm: int,
        model_id: str
    ) -> int:
        """
        Calculate model units needed for expected TPM.
        Note: Actual capacity per unit varies by model.
        """
        # Example capacity estimates (varies by model)
        capacity_per_unit = {
            'anthropic.claude-3-5-sonnet': 50000,  # TPM per unit
            'anthropic.claude-3-haiku': 100000,
            'amazon.titan-text-express': 80000
        }

        model_family = model_id.split('-v')[0]
        unit_capacity = capacity_per_unit.get(model_family, 50000)

        # Calculate units needed with 20% buffer
        required_units = int((expected_tpm / unit_capacity) * 1.2) + 1

        return max(1, required_units)


class RequestThrottler:
    """
    Client-side request throttling to prevent hitting limits.
    """

    def __init__(self, requests_per_second: float = 10.0):
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0.0
        self._lock = threading.Lock()

    def wait(self) -> None:
        """
        Wait if necessary to maintain rate limit.
        """
        with self._lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time

            if time_since_last < self.min_interval:
                sleep_time = self.min_interval - time_since_last
                time.sleep(sleep_time)

            self.last_request_time = time.time()

    def throttled_invoke(
        self,
        client: boto3.client,
        model_id: str,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Invoke with client-side rate limiting.
        """
        self.wait()

        response = client.invoke_model(
            modelId=model_id,
            body=json.dumps(body)
        )

        return json.loads(response['body'].read())