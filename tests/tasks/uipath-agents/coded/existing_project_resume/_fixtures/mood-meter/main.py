from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel

class GraphInput(BaseModel):
    text: str

class GraphOutput(BaseModel):
    mood: str

class GraphState(TypedDict):
    text: str
    mood: str

async def classify_mood(state: GraphState):
    lower = state["text"].lower()
    if "great" in lower or "love" in lower:
        mood = "happy"
    elif "bad" in lower or "hate" in lower:
        mood = "sad"
    else:
        mood = "neutral"
    return {"mood": mood}

builder = StateGraph(GraphState, input_schema=GraphInput, output_schema=GraphOutput)
builder.add_node("classify_mood", classify_mood)
builder.add_edge(START, "classify_mood")
builder.add_edge("classify_mood", END)
graph = builder.compile()
