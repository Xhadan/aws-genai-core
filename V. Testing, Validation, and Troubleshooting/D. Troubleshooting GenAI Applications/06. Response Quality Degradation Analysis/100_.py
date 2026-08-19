import boto3
import json
from typing import Dict, Any, List
from collections import Counter
import numpy as np
from scipy import stats


class DriftDetector:
    """
    Detect various types of drift in GenAI systems.
    """

    def __init__(self):
        self.cloudwatch = boto3.client('cloudwatch')

    def detect_input_drift(
        self,
        baseline_inputs: List[str],
        current_inputs: List[str]
    ) -> Dict[str, Any]:
        """
        Detect drift in input patterns.
        """
        # Analyze input length distribution
        baseline_lengths = [len(i) for i in baseline_inputs]
        current_lengths = [len(i) for i in current_inputs]

        # Kolmogorov-Smirnov test for distribution change
        ks_statistic, p_value = stats.ks_2samp(baseline_lengths, current_lengths)

        # Analyze vocabulary shift
        baseline_words = self._extract_vocabulary(baseline_inputs)
        current_words = self._extract_vocabulary(current_inputs)

        new_words = current_words - baseline_words
        missing_words = baseline_words - current_words

        vocab_drift = len(new_words) / max(len(baseline_words), 1)

        return {
            'length_distribution_drift': {
                'ks_statistic': ks_statistic,
                'p_value': p_value,
                'significant': p_value < 0.05
            },
            'vocabulary_drift': {
                'new_term_ratio': vocab_drift,
                'new_terms_sample': list(new_words)[:20],
                'missing_terms_sample': list(missing_words)[:20]
            },
            'drift_detected': p_value < 0.05 or vocab_drift > 0.2
        }

    def _extract_vocabulary(self, texts: List[str]) -> set:
        """
        Extract vocabulary from texts.
        """
        words = set()
        for text in texts:
            words.update(text.lower().split())
        return words

    def detect_response_drift(
        self,
        baseline_responses: List[Dict],
        current_responses: List[Dict]
    ) -> Dict[str, Any]:
        """
        Detect drift in response patterns.
        """
        # Analyze response length
        baseline_lengths = [len(r.get('text', '')) for r in baseline_responses]
        current_lengths = [len(r.get('text', '')) for r in current_responses]

        length_change = (
            np.mean(current_lengths) - np.mean(baseline_lengths)
        ) / max(np.mean(baseline_lengths), 1)

        # Analyze response structure (if applicable)
        baseline_has_lists = sum(1 for r in baseline_responses if '- ' in r.get('text', ''))
        current_has_lists = sum(1 for r in current_responses if '- ' in r.get('text', ''))

        format_change = abs(
            baseline_has_lists / max(len(baseline_responses), 1) -
            current_has_lists / max(len(current_responses), 1)
        )

        return {
            'length_drift': {
                'baseline_mean': np.mean(baseline_lengths),
                'current_mean': np.mean(current_lengths),
                'change_percent': length_change * 100
            },
            'format_drift': {
                'baseline_list_ratio': baseline_has_lists / max(len(baseline_responses), 1),
                'current_list_ratio': current_has_lists / max(len(current_responses), 1),
                'change': format_change
            },
            'drift_detected': abs(length_change) > 0.25 or format_change > 0.2
        }


class QualityRemediator:
    """
    Remediate quality degradation issues.
    """

    def __init__(self, model_id: str):
        self.model_id = model_id
        self.bedrock_runtime = boto3.client('bedrock-runtime')

    def diagnose_root_cause(
        self,
        degradation_result: Dict[str, Any],
        sample_inputs: List[str],
        sample_outputs: List[str]
    ) -> Dict[str, Any]:
        """
        Diagnose root cause of quality degradation.
        """
        diagnosis = {
            'likely_causes': [],
            'recommended_actions': [],
            'priority': 'medium'
        }

        degradations = degradation_result.get('degradations', [])

        for d in degradations:
            metric = d['metric']

            if metric = 'faithfulness':
                diagnosis['likely_causes'].append('Knowledge base staleness or retrieval issues')
                diagnosis['recommended_actions'].extend([
                    'Refresh knowledge base with current information',
                    'Review and update retrieval parameters',
                    'Check for source document changes'
                ])

            elif metric = 'relevance':
                diagnosis['likely_causes'].append('Prompt template decay or input pattern shift')
                diagnosis['recommended_actions'].extend([
                    'Analyze recent input patterns for changes',
                    'Update prompt templates with new examples',
                    'Review and refine system instructions'
                ])

            elif metric = 'correctness':
                diagnosis['likely_causes'].append('Model knowledge gap or instruction ambiguity')
                diagnosis['recommended_actions'].extend([
                    'Add clarifying instructions to prompts',
                    'Consider fine-tuning for specific use cases',
                    'Implement additional guardrails'
                ])

            elif metric = 'latency_p95':
                diagnosis['likely_causes'].append('Increased prompt complexity or throttling')
                diagnosis['recommended_actions'].extend([
                    'Optimize prompt length and complexity',
                    'Check for throttling or quota issues',
                    'Consider provisioned throughput'
                ])

        # Set priority based on severity
        if any(d.get('decline_percent', 0) > 25 for d in degradations):
            diagnosis['priority'] = 'high'
        elif any(d.get('decline_percent', 0) > 15 for d in degradations):
            diagnosis['priority'] = 'medium'
        else:
            diagnosis['priority'] = 'low'

        return diagnosis

    def generate_prompt_update_suggestions(
        self,
        current_prompt: str,
        sample_failures: List[Dict]
    ) -> Dict[str, Any]:
        """
        Generate suggestions for prompt updates based on failures.
        """
        analysis_prompt = f"""Analyze the following prompt and sample failures to suggest improvements.

Current Prompt:
{current_prompt}

Sample Failures (input -> actual output -> expected behavior):
{json.dumps(sample_failures[:5], indent=2)}

Provide specific suggestions to improve the prompt to address these failures.
Focus on:
1. Clarity of instructions
2. Handling edge cases
3. Output format specifications
4. Examples that could help

Format your response as a JSON object with:
- issues: list of identified issues
- suggestions: list of specific improvements
- revised_prompt: improved version of the prompt"""

        body = {
            'anthropic_version': 'bedrock-2023-05-31',
            'max_tokens': 2000,
            'messages': [
                {'role': 'user', 'content': analysis_prompt}
            ]
        }

        response = self.bedrock_runtime.invoke_model(
            modelId=self.model_id,
            body=json.dumps(body)
        )

        result = json.loads(response['body'].read())

        try:
            suggestions = json.loads(result['content'][0]['text'])
        except json.JSONDecodeError:
            suggestions = {
                'raw_response': result['content'][0]['text'],
                'parse_error': True
            }

        return suggestions

    def create_remediation_plan(
        self,
        diagnosis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create actionable remediation plan.
        """
        plan = {
            'immediate_actions': [],
            'short_term_actions': [],
            'long_term_actions': [],
            'monitoring_changes': []
        }

        priority = diagnosis.get('priority', 'medium')
        actions = diagnosis.get('recommended_actions', [])

        if priority = 'high':
            plan['immediate_actions'] = actions[:2]
            plan['short_term_actions'] = actions[2:4]
            plan['long_term_actions'] = actions[4:]
            plan['monitoring_changes'] = [
                'Increase evaluation frequency to every hour',
                'Lower alert thresholds by 50%',
                'Enable detailed logging for all requests'
            ]

        elif priority = 'medium':
            plan['short_term_actions'] = actions[:3]
            plan['long_term_actions'] = actions[3:]
            plan['monitoring_changes'] = [
                'Increase evaluation frequency to every 4 hours',
                'Add specific metric tracking for affected areas'
            ]

        else:
            plan['long_term_actions'] = actions
            plan['monitoring_changes'] = [
                'Continue standard monitoring',
                'Schedule review in 1 week'
            ]

        return plan