"""Contract intake agent for testing file guardrails.

Reviews an uploaded contract with the review_contract tool and returns a
summary. No guardrails configured — add them using the uipath-agents skill.
"""

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.constants import END, START
from langgraph.graph import StateGraph
from pydantic import BaseModel
from uipath.platform import UiPath
from uipath.platform.attachments import Attachment

from uipath_langchain.chat import UiPathChat
from uipath_langchain.guardrails import render_attachments_block


class Input(BaseModel):
    """Input schema for the contract intake agent."""

    contract: Attachment
    notes: str = ""


class Output(BaseModel):
    """Output schema for the contract intake agent."""

    summary: str


@tool
async def review_contract(contract: Attachment) -> str:
    """Read the uploaded contract and return its text for review.

    Args:
        contract: The uploaded contract file.

    Returns:
        The text of the contract.
    """
    async with UiPath().attachments.open_async(attachment=contract) as (_att, response):
        data = b"".join([chunk async for chunk in response.aiter_raw()])
    return data.decode("utf-8", errors="replace")


SYSTEM_PROMPT = """You are a contract intake assistant.
Always call review_contract on the uploaded contract before you answer, and never
judge a contract by its file name. Return a short plain-language summary."""


def create_llm():
    """Create the LLM instance."""
    return UiPathChat(model="gpt-4o-2024-08-06", temperature=0.0)


llm = create_llm()


def create_intake_agent():
    """Create the contract intake agent."""
    return create_agent(
        model=llm,
        tools=[review_contract],
        system_prompt=SYSTEM_PROMPT,
    )


agent = create_intake_agent()


async def intake_node(state: Input) -> Output:
    """Show the uploaded contract to the agent and return its summary."""
    attachment = state.contract.model_dump(mode="json", exclude_none=True)
    prompt = (
        f"Summarise the attached contract.\n{render_attachments_block([attachment])}\n"
        f"Notes: {state.notes}"
    )
    result = await agent.ainvoke({"messages": [HumanMessage(content=prompt)]})
    return Output(summary=result["messages"][-1].content)


builder = StateGraph(Input, input_schema=Input, output_schema=Output)
builder.add_node("intake", intake_node)
builder.add_edge(START, "intake")
builder.add_edge("intake", END)

graph = builder.compile()
