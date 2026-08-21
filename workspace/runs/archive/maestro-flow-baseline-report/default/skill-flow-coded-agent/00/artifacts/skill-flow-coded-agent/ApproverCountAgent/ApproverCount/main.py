from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import START, StateGraph, END
from uipath_langchain.chat.models import UiPathAzureChatOpenAI
from pydantic import BaseModel, Field


class GraphInput(BaseModel):
    sentence: str = Field(description="A sentence describing the outcome of a proposal review round")


class GraphOutput(BaseModel):
    approver_count: int = Field(description="The number of people who approved the proposal")


class GraphState(GraphInput):
    approver_count: int = Field(default=0, description="The number of people who approved the proposal")


async def count_approvers(state: GraphState) -> GraphOutput:
    llm = UiPathAzureChatOpenAI(model="gpt-4o-mini-2024-07-18")

    class ReviewResult(BaseModel):
        approver_count: int = Field(
            description="The number of distinct people who approved the proposal"
        )

    structured_llm = llm.with_structured_output(ReviewResult)

    system_prompt = (
        "You are an expert at analyzing proposal review outcomes. "
        "Given a sentence describing what happened in a proposal review round, "
        "identify every person mentioned and determine their stance: "
        "approved, requested changes, or recused themselves. "
        "Count only the people who explicitly approved (gave approval / voted yes / approved). "
        "People who requested changes or recused themselves do NOT count as approvers. "
        "Return the exact integer count of approvers."
    )

    raw = await structured_llm.ainvoke(
        [SystemMessage(system_prompt), HumanMessage(state.sentence)]
    )
    result = ReviewResult.model_validate(raw)
    return GraphOutput(approver_count=result.approver_count)


builder = StateGraph(GraphState, input_schema=GraphInput, output_schema=GraphOutput)
builder.add_node("count_approvers", count_approvers)
builder.add_edge(START, "count_approvers")
builder.add_edge("count_approvers", END)

graph = builder.compile()
