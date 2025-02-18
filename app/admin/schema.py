import json
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import JSONResponse

# Create readonly router
schema_router_readonly = APIRouter()

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Path to agent schema
AGENT_SCHEMA_PATH = PROJECT_ROOT / "models" / "agent_schema.json"


@schema_router_readonly.get(
    "/schema/agent", tags=["Schema"], operation_id="get_agent_schema"
)
async def get_agent_schema() -> JSONResponse:
    """Get the JSON schema for Agent model.

    Returns:
        JSONResponse: The complete JSON schema for the Agent model with application/json content type
    """
    with open(AGENT_SCHEMA_PATH) as f:
        schema = json.load(f)
    return JSONResponse(content=schema, media_type="application/json")
