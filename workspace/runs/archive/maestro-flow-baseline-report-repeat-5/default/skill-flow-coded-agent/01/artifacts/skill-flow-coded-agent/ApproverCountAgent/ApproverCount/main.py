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


class ReviewAnalysis(BaseModel):
    approver_count: int = Field(description="Number of people who approved the proposal")


async def count_approvers(state: GraphState) -> GraphState:
    from uipath_langchain.chat import UiPathAzureChatOpenAI

    llm = UiPathAzureChatOpenAI(model="gpt-4o-mini-2024-07-18")
    structured_llm = llm.with_structured_output(ReviewAnalysis)

    system_prompt = (
        "You are a proposal review analyzer. "
        "Given a sentence describing the outcome of a proposal review round, "
        "identify each person mentioned and determine their decision: "
        "approved, requested changes, or recused themselves. "
        "Count ONLY the people who explicitly approved (voted in favor). "
        "People who requested changes or recused themselves do NOT count as approvers. "
        "Return only the integer count of approvers."
    )

    result = await structured_llm.ainvoke(
        [SystemMessage(system_prompt), HumanMessage(state.sentence)]
    )
    review: ReviewAnalysis = ReviewAnalysis.model_validate(result)
    return GraphState(sentence=state.sentence, approver_count=review.approver_count)


builder = StateGraph(GraphState, input=GraphInput, output=GraphOutput)

builder.add_node("count_approvers", count_approvers)

builder.add_edge(START, "count_approvers")
builder.add_edge("count_approvers", END)

graph = builder.compile()
