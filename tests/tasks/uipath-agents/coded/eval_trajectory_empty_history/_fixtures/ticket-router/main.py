from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel

class GraphInput(BaseModel):
    text: str

class GraphOutput(BaseModel):
    category: str

class GraphState(TypedDict):
    text: str
    category: str

async def route(state: GraphState):
    lower = state["text"].lower()
    if any(w in lower for w in ("invoice", "charge", "bill", "refund")):
        return {"category": "billing"}
    return {"category": "technical"}

builder = StateGraph(GraphState, input_schema=GraphInput, output_schema=GraphOutput)
builder.add_node("route", route)
builder.add_edge(START, "route")
builder.add_edge("route", END)
graph = builder.compile()
