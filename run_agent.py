"""
Agent script to test the Gateway
Run this after setup: python run_agent.py
"""

from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamablehttp_client
from bedrock_agentcore_starter_toolkit.operations.gateway.client import GatewayClient
import json
import sys

def create_streamable_http_transport(mcp_url: str, access_token: str):
    return streamablehttp_client(mcp_url, headers={"Authorization": f"Bearer {access_token}"})

def get_full_tools_list(client):
    """Get all tools with pagination support"""
    more_tools = True
    tools = []
    pagination_token = None
    while more_tools:
        tmp_tools = client.list_tools_sync(pagination_token=pagination_token)
        tools.extend(tmp_tools)
        if tmp_tools.pagination_token is None:
            more_tools = False
        else:
            more_tools = True
            pagination_token = tmp_tools.pagination_token
    return tools

def run_agent():
    # Load configuration
    try:
        with open("gateway_config.json", "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        print("❌ Error: gateway_config.json not found!")
        print("Please run 'python setup_gateway.py' first to create the Gateway.")
        sys.exit(1)

    gateway_url = config["gateway_url"]
    client_info = config["client_info"]

    # Get access token for the agent
    print("Getting access token...")
    client = GatewayClient(region_name=config["region"])
    access_token = client.get_access_token_for_cognito(client_info)
    print("✓ Access token obtained\n")

    # Model configuration - change if needed
    model_id = "anthropic.claude-3-7-sonnet-20250219-v1:0"

    print("🤖 Starting AgentCore Gateway Test Agent")
    print(f"Gateway URL: {gateway_url}")
    print(f"Model: {model_id}")
    print("-" * 60)

    # Setup Bedrock model
    bedrockmodel = BedrockModel(
        inference_profile_id=model_id,
        streaming=True,
    )

    # Setup MCP client
    mcp_client = MCPClient(lambda: create_streamable_http_transport(gateway_url, access_token))

    with mcp_client:
        # List available tools
        tools = get_full_tools_list(mcp_client)
        print(f"\n📋 Available tools: {[tool.tool_name for tool in tools]}")
        print("-" * 60)

        # Create agent
        agent = Agent(model=bedrockmodel, tools=tools)

        # Interactive loop
        print("\n💬 Interactive Agent Ready!")
        print("Try asking: 'What's the weather in Seattle?'")
        print("Type 'exit', 'quit', or 'bye' to end.\n")

        while True:
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("👋 Goodbye!")
                break

            print("\n🤔 Thinking...\n")
            response = agent(user_input)
            print(f"\nAgent: {response.message.get('content', response)}\n")

if __name__ == "__main__":
    run_agent()
