"""
Setup script to create Gateway with Lambda target and save configuration
Run this first: python setup_gateway.py
"""

from bedrock_agentcore_starter_toolkit.operations.gateway.client import GatewayClient
import json
import logging
import time

def setup_gateway():
    # Configuration
    region = "us-west-2"  # Change to your preferred region

    print("🚀 Setting up AgentCore Gateway...")
    print(f"Region: {region}\n")

    # Initialize client
    client = GatewayClient(region_name=region)
    client.logger.setLevel(logging.INFO)

    # Step 2.1: Create OAuth authorizer
    print("Step 2.1: Creating OAuth authorization server...")
    cognito_response = client.create_oauth_authorizer_with_cognito("TestGateway")
    print("✓ Authorization server created\n")

    # Step 2.2: Create Gateway
    print("Step 2.2: Creating Gateway...")
    gateway = client.create_mcp_gateway(
        # the name of the Gateway - if you don't set one, one will be generated.
        name=None,
        # the role arn that the Gateway will use - if you don't set one, one will be created.
        # NOTE: if you are using your own role make sure it has a trust policy that trusts bedrock-agentcore.amazonaws.com
        role_arn=None,
        # the OAuth authorization server details. If you are providing your own authorization server,
        # then pass an input of the following form: {"customJWTAuthorizer": {"allowedClients": ["<INSERT CLIENT ID>"], "discoveryUrl": "<INSERT DISCOVERY URL">}}
        authorizer_config=cognito_response["authorizer_config"],
        # enable semantic search
        enable_semantic_search=True,
    )
    print(f"✓ Gateway created: {gateway['gatewayUrl']}\n")

    # If role_arn was not provided, fix IAM permissions
    # NOTE: This is handled internally by the toolkit when no role is provided
    client.fix_iam_permissions(gateway)
    print("⏳ Waiting 30s for IAM propagation...")
    time.sleep(30)
    print("✓ IAM permissions configured\n")

    # Step 2.3: Add Lambda target
    print("Step 2.3: Adding Lambda target...")
    lambda_target = client.create_mcp_gateway_target(
        # the gateway created in the previous step
        gateway=gateway,
        # the name of the Target - if you don't set one, one will be generated.
        name=None,
        # the type of the Target
        target_type="lambda",
        # the target details - set this to define your own lambda if you pre-created one.
        # Otherwise leave this None and one will be created for you.
        target_payload=None,
        # you will see later in the tutorial how to use this to connect to APIs using API keys and OAuth credentials.
        credentials=None,
    )
    print("✓ Lambda target added\n")

    # Step 2.4: Save configuration for agent
    config = {
        "gateway_url": gateway["gatewayUrl"],
        "gateway_id": gateway["gatewayId"],
        "region": region,
        "client_info": cognito_response["client_info"]
    }

    with open("gateway_config.json", "w") as f:
        json.dump(config, f, indent=2)

    print("=" * 60)
    print("✅ Gateway setup complete!")
    print(f"Gateway URL: {gateway['gatewayUrl']}")
    print(f"Gateway ID: {gateway['gatewayId']}")
    print("\nConfiguration saved to: gateway_config.json")
    print("\nNext step: Run 'python run_agent.py' to test your Gateway")
    print("=" * 60)

    return config

if __name__ == "__main__":
    setup_gateway()
