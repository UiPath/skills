from typing import Optional
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import START, StateGraph, END
from uipath_langchain.chat import UiPathAzureChatOpenAI
from pydantic import BaseModel, Field


# ── Input / Output schemas ──────────────────────────────────────────────────

class GraphInput(BaseModel):
    sentence: str = Field(description="A sentence describing the outcome of a proposal review round.")


class GraphOutput(BaseModel):
    approver_count: int = Field(description="The number of people who approved the proposal.")


# ── State ───────────────────────────────────────────────────────────────────

class GraphState(BaseModel):
    sentence: str
    approver_count: Optional[int] = None


# ── Structured extraction schema ────────────────────────────────────────────

class ReviewerDecision(BaseModel):
    name: str = Field(description="The name of the person.")
    decision: str = Field(
        description="One of: 'approved', 'requested_changes', or 'recused'."
    )


class ReviewResult(BaseModel):
    reviewers: list[ReviewerDecision] = Field(
        description="Every person mentioned and their decision."
    )


# ── Graph node ───────────────────────────────────────────────────────────────

async def count_approvers(state: GraphState) -> GraphOutput:
    """Identify each reviewer's decision and count approvals."""
    llm = UiPathAzureChatOpenAI(model="gpt-4o-mini-2024-07-18")
    structured_llm = llm.with_structured_output(ReviewResult)

    system_prompt = (
        "You are an expert at reading proposal review summaries. "
        "Given a sentence about a review round, identify every person mentioned "
        "and classify each person's decision as exactly one of:\n"
        "  - 'approved'           (they approved the proposal)\n"
        "  - 'requested_changes'  (they asked for changes, rejected, or voted against)\n"
        "  - 'recused'            (they abstained, recused, or stepped aside)\n"
        "Return every person in the 'reviewers' list."
    )

    result = await structured_llm.ainvoke(
        [SystemMessage(system_prompt), HumanMessage(state.sentence)]
    )

    # result is a dict when with_structured_output returns raw; cast via model_validate
    if isinstance(result, dict):
        review = ReviewResult.model_validate(result)
    else:
        review = result  # already a ReviewResult

    count = sum(1 for r in review.reviewers if r.decision == "approved")
    return GraphOutput(approver_count=count)


# ── Graph definition ─────────────────────────────────────────────────────────

builder = StateGraph(GraphState, input=GraphInput, output=GraphOutput)
builder.add_node("count_approvers", count_approvers)
builder.add_edge(START, "count_approvers")
builder.add_edge("count_approvers", END)

graph = builder.compile()
