from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import START, StateGraph, END
from uipath_langchain.chat import UiPathAzureChatOpenAI
from pydantic import BaseModel, Field
from typing import List


class GraphInput(BaseModel):
    sentence: str = Field(description="A sentence describing the outcome of a proposal review round")


class ReviewerDecision(BaseModel):
    name: str = Field(description="The name of the reviewer")
    decision: str = Field(description="One of: approved, requested_changes, recused")


class ReviewAnalysis(BaseModel):
    reviewers: List[ReviewerDecision] = Field(description="List of all reviewers and their decisions")


class GraphOutput(BaseModel):
    approver_count: int = Field(description="The number of people who approved the proposal")


class GraphState(BaseModel):
    sentence: str = ""
    approver_count: int = 0


async def analyze_review(state: GraphState) -> GraphOutput:
    llm = UiPathAzureChatOpenAI(model="gpt-4o-mini-2024-07-18")
    structured_llm = llm.with_structured_output(ReviewAnalysis)

    system_prompt = (
        "You are a review outcome parser. "
        "Given a sentence describing the outcome of a proposal review round, "
        "identify every person mentioned and determine their decision. "
        "Classify each decision as exactly one of: "
        "'approved' (they approved the proposal), "
        "'requested_changes' (they asked for changes, rejected, or did not approve), "
        "'recused' (they abstained or recused themselves). "
        "Return the complete list of reviewers and their decisions."
    )

    raw = await structured_llm.ainvoke(
        [SystemMessage(system_prompt), HumanMessage(state.sentence)]
    )
    analysis = ReviewAnalysis.model_validate(raw)

    count = sum(1 for r in analysis.reviewers if r.decision == "approved")
    return GraphOutput(approver_count=count)


builder = StateGraph(GraphState, input=GraphInput, output=GraphOutput)
builder.add_node("analyze_review", analyze_review)
builder.add_edge(START, "analyze_review")
builder.add_edge("analyze_review", END)

graph = builder.compile()
