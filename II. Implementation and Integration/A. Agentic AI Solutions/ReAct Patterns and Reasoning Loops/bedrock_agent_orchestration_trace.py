import boto3

bedrock_runtime = boto3.client('bedrock-agent-runtime')

def invoke_with_trace(agent_id: str, alias_id: str, session_id: str, query: str):
    """Invoke agent and analyze orchestration trace."""

    response = bedrock_runtime.invoke_agent(
        agentId=agent_id,
        agentAliasId=alias_id,
        sessionId=session_id,
        inputText=query,
        enableTrace=True
    )

    traces = []
    completion = ""

    for event in response['completion']:
        if 'chunk' in event:
            completion += event['chunk']['bytes'].decode('utf-8')

        if 'trace' in event:
            trace_data = event['trace'].get('trace', {})

            # Pre-processing trace
            if 'preProcessingTrace' in trace_data:
                pre = trace_data['preProcessingTrace']
                traces.append({
                    'phase': 'pre-processing',
                    'input': pre.get('modelInvocationInput', {}).get('text'),
                    'output': pre.get('modelInvocationOutput', {})
                })

            # Orchestration trace (ReAct loop)
            if 'orchestrationTrace' in trace_data:
                orch = trace_data['orchestrationTrace']

                # Rationale (Thought phase)
                if 'rationale' in orch:
                    traces.append({
                        'phase': 'thought',
                        'reasoning': orch['rationale'].get('text')
                    })

                # Invocation input (Action phase)
                if 'invocationInput' in orch:
                    inv = orch['invocationInput']
                    action_info = {}
                    if 'actionGroupInvocationInput' in inv:
                        ag = inv['actionGroupInvocationInput']
                        action_info = {
                            'action_group': ag.get('actionGroupName'),
                            'api_path': ag.get('apiPath'),
                            'parameters': ag.get('parameters')
                        }
                    traces.append({
                        'phase': 'action',
                        'action': action_info
                    })

                # Observation
                if 'observation' in orch:
                    obs = orch['observation']
                    traces.append({
                        'phase': 'observation',
                        'result': obs.get('actionGroupInvocationOutput', {}).get('text')
                    })

            # Post-processing trace
            if 'postProcessingTrace' in trace_data:
                post = trace_data['postProcessingTrace']
                traces.append({
                    'phase': 'post-processing',
                    'output': post.get('modelInvocationOutput', {})
                })

    return {
        'completion': completion,
        'traces': traces
    }


# Analyze agent behavior
result = invoke_with_trace(
    agent_id='AGENT123',
    alias_id='ALIAS123',
    session_id='session-001',
    query="What's the status of my order ORD-12345?"
)

print("== Agent Response ==")
print(result['completion'])
print("\n== ReAct Trace ==")
for trace in result['traces']:
    print(f"\n[{trace['phase'].upper()}]")
    for key, value in trace.items():
        if key != 'phase':
            print(f"  {key}: {value}")