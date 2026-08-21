from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import START, StateGraph, END
from pydantic import BaseModel, Field


class GraphInput(BaseModel):
    sentence: str = Field(description="A sentence describing the outcome of a proposal review round")


class GraphOutput(BaseModel):
    approver_count: int = Field(description="The number of people who approved the proposal")


class GraphState(GraphInput):
    approver_count: int = 0


async def count_approvers(state: GraphState) -> GraphOutput:
    from uipath_langchain.chat.models import UiPathAzureChatOpenAI

    llm = UiPathAzureChatOpenAI(model="gpt-4o-mini-2024-07-18")

    system_prompt = (
        "You are an expert at analyzing proposal review outcomes. "
        "Given a sentence describing a proposal review round, identify every person mentioned "
        "and determine their stance: approved, requested changes, or recused themselves. "
        "Return ONLY a JSON object with a single integer field 'approver_count' equal to the number "
        "of people who explicitly approved. Do not include people who requested changes or recused themselves. "
        'Example output: {"approver_count": 2}'
    )

    user_message = (
        f"Analyze this review outcome sentence and count the approvers:\n\n{state.sentence}"
    )

    class ApproverResult(BaseModel):
        approver_count: int

    structured_llm = llm.with_structured_output(ApproverResult)
    result = await structured_llm.ainvoke(
        [SystemMessage(system_prompt), HumanMessage(user_message)]
    )

    if isinstance(result, dict):
        approver_count = result["approver_count"]
    else:
        approver_count = result.approver_count

    return GraphOutput(approver_count=approver_count)


builder = StateGraph(GraphState, input=GraphInput, output=GraphOutput)
builder.add_node("count_approvers", count_approvers)
builder.add_edge(START, "count_approvers")
builder.add_edge("count_approvers", END)

graph = builder.compile()
