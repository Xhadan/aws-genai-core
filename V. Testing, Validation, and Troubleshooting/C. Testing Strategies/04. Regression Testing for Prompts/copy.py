import boto3
import json
import sys
from datetime import datetime

class CIRegressionRunner:
    """Run regression tests in CI/CD pipeline."""

    def __init__(self, config_path: str, baseline_bucket: str):
        self.s3 = boto3.client('s3')
        self.baseline_bucket = baseline_bucket

        with open(config_path, 'r') as f:
            self.config = json.load(f)

    def run_ci_tests(self, baseline_name: str) -> bool:
        """Run regression tests and return pass/fail."""

        print(f"Loading baseline: {baseline_name}")

        # Load baseline
        baseline = self._load_baseline(baseline_name)

        # Load test queries from baseline
        test_queries = [
            {'id': qid, 'text': r['query']}
            for qid, r in baseline['results'].items()
        ]

        print(f"Running {len(test_queries)} regression tests...")

        # Run tests
        from regression_tester import GenAIRegressionTester
        tester = GenAIRegressionTester(baseline, tolerance=0.05)
        report = tester.run_regression_test(self.config, test_queries)

        # Output results
        self._print_report(report)

        # Store results for history
        self._store_results(report, baseline_name)

        # Return pass/fail for CI
        return report['passed']

    def _load_baseline(self, name: str) -> Dict:
        response = self.s3.get_object(
            Bucket=self.baseline_bucket,
            Key=f'baselines/{name}.json'
        )
        return json.loads(response['Body'].read())

    def _print_report(self, report: Dict):
        """Print regression test report."""
        print("\n" + "=" * 50)
        print("REGRESSION TEST REPORT")
        print("=" * 50)
        print(f"Status: {'PASSED' if report['passed'] else 'FAILED'}")
        print(f"Total Tests: {report['total_tests']}")
        print(f"Regressions: {report['regressions']}")
        print(f"Improvements: {report['improvements']}")
        print(f"Baseline Mean: {report['baseline_mean']:.3f}")
        print(f"New Mean: {report['new_mean']:.3f}")
        print(f"Delta: {report['mean_delta']:+.3f}")

        if report['regressed_queries']:
            print("\nRegressed Queries:")
            for rq in report['regressed_queries'][:5]:
                print(f"  - {rq['query'][:50]}... (delta: {rq['delta']:+.3f})")

        print("=" * 50)

    def _store_results(self, report: Dict, baseline_name: str):
        """Store test results for historical tracking."""
        timestamp = datetime.utcnow().strftime('%Y%m%d-%H%M%S')
        key = f'regression-results/{baseline_name}/{timestamp}.json'

        self.s3.put_object(
            Bucket=self.baseline_bucket,
            Key=key,
            Body=json.dumps(report, indent=2),
            ContentType='application/json'
        )

# CI/CD entry point
if __name__ = '__main__':
    runner = CIRegressionRunner(
        config_path='config/current.json',
        baseline_bucket='my-genai-baselines'
    )

    passed = runner.run_ci_tests(baseline_name='production-v1.2')

    # Exit with appropriate code for CI
    sys.exit(0 if passed else 1)