from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import START, StateGraph, END
from pydantic import BaseModel, Field


class GraphInput(BaseModel):
    sentence: str = Field(description="A sentence describing the outcome of a proposal review round")


class GraphOutput(BaseModel):
    approver_count: int = Field(description="The number of people who approved the proposal")


class GraphState(BaseModel):
    sentence: str
    approver_count: int = 0


class ApprovalAnalysis(BaseModel):
    approver_count: int = Field(
        description="The total number of distinct people who explicitly approved the proposal"
    )


async def analyze_approvals(state: GraphState) -> GraphOutput:
    from uipath_langchain.chat.models import UiPathAzureChatOpenAI

    llm = UiPathAzureChatOpenAI(model="gpt-4o-mini-2024-07-18")
    structured_llm = llm.with_structured_output(ApprovalAnalysis)

    system_prompt = (
        "You are an analyst that reads a sentence describing the outcome of a proposal review round. "
        "Identify every person mentioned and determine their action:\n"
        "  - 'approved' / 'approves' / 'approved it' → approved\n"
        "  - 'requested changes' / 'asked for changes' / 'wants changes' → requested changes\n"
        "  - 'recused' / 'recused themselves' / 'abstained' → recused\n"
        "Count only the people who approved. Return that count as an integer."
    )

    result = await structured_llm.ainvoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=state.sentence)]
    )

    analysis = ApprovalAnalysis.model_validate(result)
    return GraphOutput(approver_count=analysis.approver_count)


builder = StateGraph(GraphState, input=GraphInput, output=GraphOutput)

builder.add_node("analyze_approvals", analyze_approvals)

builder.add_edge(START, "analyze_approvals")
builder.add_edge("analyze_approvals", END)

graph = builder.compile()
