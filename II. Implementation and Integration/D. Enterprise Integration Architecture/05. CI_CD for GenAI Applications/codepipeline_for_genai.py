# CloudFormation template for GenAI CI/CD Pipeline
CODEPIPELINE_TEMPLATE = """
AWSTemplateFormatVersion: '2010-09-09'
Description: CI/CD Pipeline for GenAI Application

Resources:
  GenAIPipeline:
    Type: AWS::CodePipeline::Pipeline
    Properties:
      Name: genai-deployment-pipeline
      RoleArn: !GetAtt PipelineRole.Arn
      Stages:
        # Source Stage
        - Name: Source
          Actions:
            - Name: SourceAction
              ActionTypeId:
                Category: Source
                Owner: AWS
                Provider: CodeCommit
                Version: '1'
              Configuration:
                RepositoryName: genai-app
                BranchName: main
              OutputArtifacts:
                - Name: SourceOutput

        # Build and Validate Stage
        - Name: Build
          Actions:
            - Name: BuildAndValidate
              ActionTypeId:
                Category: Build
                Owner: AWS
                Provider: CodeBuild
                Version: '1'
              Configuration:
                ProjectName: !Ref BuildProject
              InputArtifacts:
                - Name: SourceOutput
              OutputArtifacts:
                - Name: BuildOutput

        # Prompt Evaluation Stage
        - Name: Evaluation
          Actions:
            - Name: RunEvaluation
              ActionTypeId:
                Category: Build
                Owner: AWS
                Provider: CodeBuild
                Version: '1'
              Configuration:
                ProjectName: !Ref EvaluationProject
              InputArtifacts:
                - Name: BuildOutput
              OutputArtifacts:
                - Name: EvalOutput

        # Deploy to Staging
        - Name: DeployStaging
          Actions:
            - Name: DeployToStaging
              ActionTypeId:
                Category: Deploy
                Owner: AWS
                Provider: CloudFormation
                Version: '1'
              Configuration:
                ActionMode: CREATE_UPDATE
                StackName: genai-app-staging
                TemplatePath: BuildOutput::template.yaml
                ParameterOverrides: '{"Environment": "staging"}'

        # Manual Approval
        - Name: Approval
          Actions:
            - Name: ManualApproval
              ActionTypeId:
                Category: Approval
                Owner: AWS
                Provider: Manual
                Version: '1'
              Configuration:
                NotificationArn: !Ref ApprovalTopic
                CustomData: "Review evaluation results and approve production deployment"

        # Deploy to Production
        - Name: DeployProduction
          Actions:
            - Name: DeployToProduction
              ActionTypeId:
                Category: Deploy
                Owner: AWS
                Provider: CloudFormation
                Version: '1'
              Configuration:
                ActionMode: CREATE_UPDATE
                StackName: genai-app-production
                TemplatePath: BuildOutput::template.yaml
                ParameterOverrides: '{"Environment": "production"}'

  EvaluationProject:
    Type: AWS::CodeBuild::Project
    Properties:
      Name: genai-evaluation
      ServiceRole: !GetAtt CodeBuildRole.Arn
      Environment:
        Type: LINUX_CONTAINER
        ComputeType: BUILD_GENERAL1_MEDIUM
        Image: aws/codebuild/amazonlinux2-x86_64-standard:4.0
        EnvironmentVariables:
          - Name: EVAL_THRESHOLD
            Value: '0.75'
      Source:
        Type: CODEPIPELINE
        BuildSpec: |
          version: 0.2
          phases:
            install:
              commands:
                - pip install boto3 pytest
            build:
              commands:
                - python scripts/run_evaluation.py --threshold $EVAL_THRESHOLD
            post_build:
              commands:
                - python scripts/generate_eval_report.py
          artifacts:
            files:
              - evaluation_report.json
              - '**/*'
          reports:
            evaluation-reports:
              files:
                - evaluation_report.json
"""

# CodeBuild evaluation script
EVALUATION_SCRIPT = """
#!/usr/bin/env python3
import sys
import json
import argparse
from evaluator import GenAIEvaluator, load_test_cases, load_prompts

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--threshold', type=float, default=0.75)
    args = parser.parse_args()

    # Load configurations
    test_cases = load_test_cases('tests/eval_cases.yaml')
    prompts = load_prompts('prompts/')

    evaluator = GenAIEvaluator()
    all_results = []
    failed = False

    for prompt_config in prompts:
        results = evaluator.evaluate(
            test_cases=test_cases,
            prompt_template=prompt_config['template'],
            prompt_version=prompt_config['version'],
            threshold=args.threshold
        )

        all_results.extend(results)

        # Check for failures
        failures = [r for r in results if not r.passed]
        if failures:
            failed = True
            print(f"FAILED: {prompt_config['prompt_id']} - {len(failures)} test cases failed")
            for f in failures:
                print(f"  - {f.test_case_id}: {f.metrics}")

    # Write results
    with open('evaluation_report.json', 'w') as f:
        json.dump({
            'total_tests': len(all_results),
            'passed': len([r for r in all_results if r.passed]),
            'failed': len([r for r in all_results if not r.passed]),
            'threshold': args.threshold,
            'results': [vars(r) for r in all_results]
        }, f, indent=2)

    if failed:
        print("\\nEvaluation FAILED - some tests did not meet threshold")
        sys.exit(1)

    print("\\nEvaluation PASSED - all tests met threshold")

if __name__ = '__main__':
    main()
"""