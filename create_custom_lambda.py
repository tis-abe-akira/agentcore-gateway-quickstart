"""Create a custom Lambda function and add it as a Gateway target"""

import boto3
import json
import io
import zipfile
import time
from bedrock_agentcore_starter_toolkit.operations.gateway.client import GatewayClient

def create_custom_lambda(region, gateway_role_arn):
    lambda_client = boto3.client('lambda', region_name=region)
    iam = boto3.client('iam')

    # Lambda code
    lambda_code = '''
import json

def lambda_handler(event, context):
    tool_name = context.client_context.custom.get('bedrockAgentCoreToolName', 'unknown')

    if 'calculate_sum' in tool_name:
        a = event.get('a', 0)
        b = event.get('b', 0)
        return {
            'statusCode': 200,
            'body': json.dumps({'result': a + b})
        }
    elif 'multiply' in tool_name:
        x = event.get('x', 0)
        y = event.get('y', 0)
        return {
            'statusCode': 200,
            'body': json.dumps({'result': x * y})
        }

    return {'statusCode': 200, 'body': json.dumps({'error': 'Unknown tool'})}
'''

    # Create zip
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr('lambda_function.py', lambda_code)
    zip_buffer.seek(0)

    # Create execution role
    role_name = 'CustomCalculatorLambdaRole'
    try:
        role = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps({
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": {"Service": "lambda.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }]
            })
        )
        iam.attach_role_policy(
            RoleName=role_name,
            PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
        )
        role_arn = role['Role']['Arn']
        print(f"Created Lambda execution role: {role_arn}")
        time.sleep(10)
    except iam.exceptions.EntityAlreadyExistsException:
        role = iam.get_role(RoleName=role_name)
        role_arn = role['Role']['Arn']

    # Create Lambda
    function_name = 'CustomCalculatorFunction'
    try:
        response = lambda_client.create_function(
            FunctionName=function_name,
            Runtime='python3.9',
            Role=role_arn,
            Handler='lambda_function.lambda_handler',
            Code={'ZipFile': zip_buffer.read()},
            Description='Custom calculator for AgentCore Gateway'
        )
        lambda_arn = response['FunctionArn']
        print(f"Created Lambda: {lambda_arn}")

        lambda_client.add_permission(
            FunctionName=function_name,
            StatementId='AllowAgentCoreInvoke',
            Action='lambda:InvokeFunction',
            Principal=gateway_role_arn
        )
    except lambda_client.exceptions.ResourceConflictException:
        response = lambda_client.get_function(FunctionName=function_name)
        lambda_arn = response['Configuration']['FunctionArn']
        print(f"Lambda already exists: {lambda_arn}")

    return lambda_arn

# Main execution
with open("gateway_config.json", "r") as f:
    config = json.load(f)

client = GatewayClient(region_name=config["region"])
gateway = client.client.get_gateway(gatewayIdentifier=config["gateway_id"])

print("Creating custom Lambda function...")
lambda_arn = create_custom_lambda(config["region"], gateway["roleArn"])

# Add as target
target_payload = {
    "lambdaArn": lambda_arn,
    "toolSchema": {
        "inlinePayload": [
            {
                "name": "calculate_sum",
                "description": "Add two numbers",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "number", "description": "First number"},
                        "b": {"type": "number", "description": "Second number"}
                    },
                    "required": ["a", "b"]
                }
            },
            {
                "name": "multiply",
                "description": "Multiply two numbers",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "x": {"type": "number", "description": "First number"},
                        "y": {"type": "number", "description": "Second number"}
                    },
                    "required": ["x", "y"]
                }
            }
        ]
    }
}

target = client.create_mcp_gateway_target(
    gateway=gateway,
    name="CustomCalculator",
    target_type="lambda",
    target_payload=target_payload
)

print(f"✓ Custom Lambda target added: {target['targetId']}")
print("\nRun 'python run_agent.py' and try: 'Calculate the sum of 42 and 58'")
