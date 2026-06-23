from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from uipath_langchain.chat.models import UiPathChat
from pydantic import BaseModel
from typing import TypedDict

llm = UiPathChat(model="gpt-4o-mini-2024-07-18", temperature=0)

class GraphInput(BaseModel):
    text: str

class GraphOutput(BaseModel):
    category: str
    text: str

class GraphState(TypedDict):
    text: str
    category: str | None

async def classify(state):
    result = await llm.ainvoke(f"Classify: {state['text']}")
    return Command(update={"category": str(result), "text": state["text"]})

builder = StateGraph(GraphState, input=GraphInput, output=GraphOutput)
builder.add_node("classify", classify)
builder.add_edge(START, "classify")
builder.add_edge("classify", END)
graph = builder.compile()
