from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel

class GraphInput(BaseModel):
    value: int

class GraphOutput(BaseModel):
    size: str

class GraphState(TypedDict):
    value: int
    size: str

async def classify(state: GraphState):
    size = "small" if state["value"] < 50 else "large"
    return {"size": size}

builder = StateGraph(GraphState, input_schema=GraphInput, output_schema=GraphOutput)
builder.add_node("classify", classify)
builder.add_edge(START, "classify")
builder.add_edge("classify", END)
graph = builder.compile()
