from enum import Enum

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel
from uipath_langchain.chat import UiPathAzureChatOpenAI


class GraphInput(BaseModel):
    sentence: str


class GraphOutput(BaseModel):
    approver_count: int


class ReviewDecision(str, Enum):
    approved = "approved"
    requested_changes = "requested_changes"
    recused = "recused"


class Reviewer(BaseModel):
    name: str
    decision: ReviewDecision


class ReviewOutcome(BaseModel):
    reviewers: list[Reviewer]


class GraphState(BaseModel):
    sentence: str
    approver_count: int | None = None


SYSTEM_PROMPT = """You analyze a single sentence describing the outcome of a proposal \
review round. Identify every person mentioned by name and, for each one, decide whether \
they approved the proposal, requested changes to it, or recused themselves from the \
review. Classify every mentioned person into exactly one of these three categories \
based only on what the sentence states."""


async def count_approvers(state: GraphState) -> GraphOutput:
    llm = UiPathAzureChatOpenAI(model="gpt-4.1-mini-2025-04-14")
    structured_llm = llm.with_structured_output(ReviewOutcome)

    raw = await structured_llm.ainvoke(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": state.sentence},
        ]
    )
    outcome = ReviewOutcome.model_validate(raw)

    approver_count = sum(
        1 for reviewer in outcome.reviewers if reviewer.decision == ReviewDecision.approved
    )
    return GraphOutput(approver_count=approver_count)


builder = StateGraph(GraphState, input_schema=GraphInput, output_schema=GraphOutput)
builder.add_node("count_approvers", count_approvers)
builder.add_edge(START, "count_approvers")
builder.add_edge("count_approvers", END)

graph = builder.compile()
