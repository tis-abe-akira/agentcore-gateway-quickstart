from bedrock_agentcore_starter_toolkit.operations.gateway.client import GatewayClient
import json
import os
from dotenv import load_dotenv

load_dotenv()

with open("gateway_config.json", "r") as f:
    config = json.load(f)

client = GatewayClient(region_name=config["region"])

nasa_spec = {
    "openapi": "3.0.0",
    "info": {"title": "NASA API", "version": "1.0.0"},
    "servers": [{"url": "https://api.nasa.gov"}],
    "paths": {
        "/planetary/apod": {
            "get": {
                "operationId": "getAstronomyPictureOfDay",
                "summary": "Get NASA's Astronomy Picture of the Day",
                "parameters": [
                    {
                        "name": "date",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "string"},
                        "description": "Date in YYYY-MM-DD format"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Success",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "title": {"type": "string"},
                                        "explanation": {"type": "string"},
                                        "url": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

gateway = client.client.get_gateway(gatewayIdentifier=config["gateway_id"])

nasa_target = client.create_mcp_gateway_target(
    gateway=gateway,
    name="NasaApi",
    target_type="openApiSchema",
    target_payload={"inlinePayload": json.dumps(nasa_spec)},
    credentials={
        "api_key": os.getenv("NASA_API_KEY"),
        "credential_location": "QUERY_PARAMETER",
        "credential_parameter_name": "api_key"
    }
)

print(f"✓ NASA API added! Try: 'Get NASA's astronomy picture for 2024-12-25'")
print("Run 'python run_agent.py' and try: 'Get NASA's astronomy picture for 2024-12-25'")
