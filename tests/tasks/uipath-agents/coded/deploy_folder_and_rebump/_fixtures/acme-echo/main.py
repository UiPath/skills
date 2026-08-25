from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import START, StateGraph, END
from uipath_langchain.chat import UiPathChatAnthropicBedrock
from pydantic import BaseModel, Field


class GraphInput(BaseModel):
    message: str = Field(description="The message to echo back")


class GraphOutput(BaseModel):
    echoed_message: str = Field(description="The message echoed back by the LLM")


async def echo(state: GraphInput) -> GraphOutput:
    llm = UiPathChatAnthropicBedrock(
        model="anthropic.claude-haiku-4-5-20251001-v1:0",
        temperature=0,
    )
    system_prompt = (
        "You are an echo agent. Repeat the user's message back verbatim, "
        "with no additions, commentary, or formatting changes."
    )
    output = await llm.ainvoke(
        [SystemMessage(system_prompt), HumanMessage(state.message)]
    )
    return GraphOutput(echoed_message=output.content)


builder = StateGraph(GraphInput, output=GraphOutput)

builder.add_node("echo", echo)

builder.add_edge(START, "echo")
builder.add_edge("echo", END)

graph = builder.compile()
