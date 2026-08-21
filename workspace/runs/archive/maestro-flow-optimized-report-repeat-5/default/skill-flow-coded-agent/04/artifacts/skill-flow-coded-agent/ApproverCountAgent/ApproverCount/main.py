from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import START, StateGraph, END
from uipath_langchain.chat import UiPathAzureChatOpenAI
from pydantic import BaseModel, Field


class GraphInput(BaseModel):
    sentence: str = Field(description="A sentence describing the outcome of a proposal review round")


class GraphOutput(BaseModel):
    approver_count: int = Field(description="The number of people who approved the proposal")


class GraphState(BaseModel):
    sentence: str = Field(description="A sentence describing the outcome of a proposal review round")
    approver_count: int = Field(default=0, description="The number of people who approved the proposal")


async def analyze_approvals(state: GraphState) -> GraphState:
    llm = UiPathAzureChatOpenAI(model="gpt-4o-mini-2024-07-18")

    system_prompt = (
        "You analyze proposal review sentences. "
        "Identify every person mentioned and determine their action: "
        "approved, requested changes, or recused themselves. "
        "Count only the people who explicitly approved. "
        "Respond with ONLY a single integer representing the number of approvals. "
        "No explanation, no punctuation — just the integer."
    )

    output = await llm.ainvoke(
        [SystemMessage(system_prompt), HumanMessage(state.sentence)]
    )

    count_str = output.content.strip()
    try:
        approver_count = int(count_str)
    except ValueError:
        # Fallback: extract the first integer found in the response
        import re
        numbers = re.findall(r"\d+", count_str)
        approver_count = int(numbers[0]) if numbers else 0

    return GraphState(sentence=state.sentence, approver_count=approver_count)


builder = StateGraph(GraphState, input=GraphInput, output=GraphOutput)

builder.add_node("analyze_approvals", analyze_approvals)

builder.add_edge(START, "analyze_approvals")
builder.add_edge("analyze_approvals", END)

graph = builder.compile()
