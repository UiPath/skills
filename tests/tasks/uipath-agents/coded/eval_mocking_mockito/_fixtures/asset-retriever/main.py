import requests
from langgraph.graph import START, StateGraph, END
from pydantic import BaseModel
from uipath.platform import UiPath


class GraphInput(BaseModel):
    asset_name: str


class GraphState(BaseModel):
    asset_name: str
    secret_value: str = ""


class GraphOutput(BaseModel):
    masked_key: str
    label: str


def fetch_label(key_id: str) -> str:
    """Fetch human-readable label from remote registry."""
    url = f"https://registry.example.com/labels/{key_id}"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json().get("label", "unknown")
    except Exception:
        return "unknown"


def mask_secret(secret: str) -> str:
    """Mask secret: first 4 chars + stars padded to original length."""
    if len(secret) < 4:
        return "*" * len(secret)
    return secret[:4] + "*" * (len(secret) - 4)


async def retrieve_asset(state: GraphState) -> dict:
    sdk = UiPath()
    asset = sdk.assets.retrieve(state.asset_name, folder_name="Shared")
    return {"secret_value": asset.value}


async def build_summary(state: GraphState) -> GraphOutput:
    return GraphOutput(
        masked_key=mask_secret(state.secret_value),
        label=fetch_label(state.asset_name),
    )


builder = StateGraph(GraphState, input=GraphInput, output=GraphOutput)

builder.add_node("retrieve_asset", retrieve_asset)
builder.add_node("build_summary", build_summary)

builder.add_edge(START, "retrieve_asset")
builder.add_edge("retrieve_asset", "build_summary")
builder.add_edge("build_summary", END)

graph = builder.compile()
