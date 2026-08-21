from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import START, StateGraph, END
from uipath_langchain.chat import UiPathAzureChatOpenAI
from pydantic import BaseModel


class GraphState(BaseModel):
    sentence: str


class GraphOutput(BaseModel):
    approverCount: int


class Decision(BaseModel):
    name: str
    outcome: Literal["approved", "requested_changes", "recused"]


class ReviewAnalysis(BaseModel):
    decisions: list[Decision]


SYSTEM_PROMPT = (
    "You analyze a sentence describing the outcome of a proposal review round. "
    "Identify every distinct person mentioned in the sentence and classify what each "
    "person did: 'approved' (they approved the proposal), 'requested_changes' "
    "(they asked for changes / did not approve as-is), or 'recused' (they recused "
    "themselves / abstained / did not participate in the decision). "
    "List every person exactly once. Base your answer only on the sentence provided."
)


async def analyze_review(state: GraphState) -> GraphOutput:
    llm = UiPathAzureChatOpenAI(model="gpt-5.4")
    structured_llm = llm.with_structured_output(ReviewAnalysis)

    raw = await structured_llm.ainvoke(
        [SystemMessage(SYSTEM_PROMPT), HumanMessage(state.sentence)]
    )
    analysis = ReviewAnalysis.model_validate(raw)

    approver_count = sum(
        1 for decision in analysis.decisions if decision.outcome == "approved"
    )
    return GraphOutput(approverCount=approver_count)


builder = StateGraph(GraphState, output=GraphOutput)

builder.add_node("analyze_review", analyze_review)

builder.add_edge(START, "analyze_review")
builder.add_edge("analyze_review", END)

graph = builder.compile()
