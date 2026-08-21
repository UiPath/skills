from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import START, StateGraph, END
from pydantic import BaseModel, Field


class GraphInput(BaseModel):
    sentence: str = Field(description="A sentence describing the outcome of a proposal review round")


class GraphOutput(BaseModel):
    approver_count: int = Field(description="The number of people who approved the proposal")


class GraphState(BaseModel):
    sentence: str = Field(description="A sentence describing the outcome of a proposal review round")
    approver_count: int = Field(default=0, description="The number of people who approved the proposal")


async def count_approvers(state: GraphState) -> GraphOutput:
    from uipath_langchain.chat.models import UiPathAzureChatOpenAI

    llm = UiPathAzureChatOpenAI(
        model="gpt-4o-mini-2024-07-18",
        temperature=0,
        max_tokens=512,
        timeout=30,
        max_retries=2,
    )

    structured_llm = llm.with_structured_output(GraphOutput)

    system_prompt = (
        "You analyze sentences that describe the outcome of a proposal review round. "
        "For each person mentioned, determine their action: approved, requested changes, or recused. "
        "Count and return only the number of people who approved. "
        "Return the count as the integer field 'approver_count'."
    )

    user_prompt = (
        f"Analyze the following sentence and count how many people approved:\n\n{state.sentence}"
    )

    raw_result: dict = await structured_llm.ainvoke(
        [SystemMessage(system_prompt), HumanMessage(user_prompt)]
    )
    result = GraphOutput.model_validate(raw_result)
    return result


builder = StateGraph(GraphState, input=GraphInput, output=GraphOutput)

builder.add_node("count_approvers", count_approvers)

builder.add_edge(START, "count_approvers")
builder.add_edge("count_approvers", END)

graph = builder.compile()
