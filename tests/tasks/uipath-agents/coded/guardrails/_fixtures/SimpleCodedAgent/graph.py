"""Simple customer support agent for testing guardrail addition.

Answers questions about customer accounts using a tool to look up account info.
No guardrails configured — add them using the uipath-agents skill.
"""

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.constants import END, START
from langgraph.graph import StateGraph
from pydantic import BaseModel

from uipath_langchain.chat import UiPathChat


class Input(BaseModel):
    """Input schema for the support agent."""

    question: str


class Output(BaseModel):
    """Output schema for the support agent."""

    answer: str


@tool
def lookup_account_info(customer_id: str) -> str:
    """Look up account information for a customer.

    Args:
        customer_id: The unique identifier of the customer account.

    Returns:
        A string with the account details including name, status, and plan.
    """
    return f"Account {customer_id}: Active, Pro plan, member since 2022."


SYSTEM_PROMPT = """You are a helpful customer support agent.
Use the lookup_account_info tool to retrieve customer account details
when the user provides their customer ID. Always be polite and concise."""


def create_llm():
    """Create the LLM instance."""
    return UiPathChat(model="gpt-4o-2024-08-06", temperature=0.0)


llm = create_llm()


def create_support_agent():
    """Create the support agent."""
    return create_agent(
        model=llm,
        tools=[lookup_account_info],
        system_prompt=SYSTEM_PROMPT,
    )


agent = create_support_agent()


async def support_node(state: Input) -> Output:
    """Convert question to messages, call agent, and extract answer."""
    messages = [HumanMessage(content=state.question)]
    result = await agent.ainvoke({"messages": messages})
    answer = result["messages"][-1].content
    return Output(answer=answer)


builder = StateGraph(Input, input_schema=Input, output_schema=Output)
builder.add_node("support", support_node)
builder.add_edge(START, "support")
builder.add_edge("support", END)

graph = builder.compile()
