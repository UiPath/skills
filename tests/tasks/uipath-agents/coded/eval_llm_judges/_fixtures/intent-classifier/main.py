from typing import Annotated, Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from uipath_langchain.chat import UiPathAzureChatOpenAI
from pydantic import BaseModel, Field


class GraphInput(BaseModel):
    text: str = Field(description="Free-text user request to classify")


class GraphOutput(BaseModel):
    category: Literal["weather", "news", "joke"] = Field(
        description="Classified category: weather, news, or joke"
    )
    text: str = Field(description="The original input text")


class GraphState(BaseModel):
    text: str = Field(description="Free-text user request to classify")
    messages: Annotated[list, add_messages] = Field(default_factory=list)
    category: str = Field(default="", description="Classified category")


@tool
def submit_category(category: Literal["weather", "news", "joke"]) -> str:
    """Record the final intent category for the user's request."""
    return f"recorded:{category}"


SYSTEM_PROMPT = (
    "You are an intent classifier. Classify the user's request into exactly one "
    "of these three categories: weather, news, joke.\n\n"
    "- weather: weather, temperature, forecast, climate conditions\n"
    "- news: current events, headlines, news stories, recent happenings\n"
    "- joke: jokes, humor, funny content, making the user laugh\n\n"
    "You MUST call the `submit_category` tool exactly once with your chosen label. "
    "Do not answer in plain text."
)


async def model_node(state: GraphState) -> dict:
    llm = UiPathAzureChatOpenAI(
        model="gpt-4.1-mini-2025-04-14",
        temperature=0,
    ).bind_tools([submit_category])
    msgs = state.messages or [SystemMessage(SYSTEM_PROMPT), HumanMessage(state.text)]
    response = await llm.ainvoke(msgs)
    return {"messages": [response]}


def extract_node(state: GraphState) -> GraphOutput:
    category = ""
    for message in state.messages:
        for call in getattr(message, "tool_calls", None) or []:
            if call.get("name") == "submit_category":
                category = call.get("args", {}).get("category", "")
    if category not in ("weather", "news", "joke"):
        category = "joke"
    return GraphOutput(category=category, text=state.text)


def route(state: GraphState) -> str:
    last = state.messages[-1]
    if getattr(last, "tool_calls", None):
        return "tools"
    return "extract"


builder = StateGraph(GraphState, input=GraphInput, output=GraphOutput)
builder.add_node("model", model_node)
builder.add_node("tools", ToolNode([submit_category]))
builder.add_node("extract", extract_node)

builder.add_edge(START, "model")
builder.add_conditional_edges("model", route, {"tools": "tools", "extract": "extract"})
builder.add_edge("tools", "model")
builder.add_edge("extract", END)

graph = builder.compile()
