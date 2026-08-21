from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import START, StateGraph, END
from uipath_langchain.chat import UiPathAzureChatOpenAI
from pydantic import BaseModel


class GraphState(BaseModel):
    sentence: str


class GraphOutput(BaseModel):
    approver_count: int


async def count_approvers(state: GraphState) -> GraphOutput:
    llm = UiPathAzureChatOpenAI(model="gpt-4.1-mini-2025-04-14")
    system_prompt = (
        "You are an approval-round analyst. "
        "Given a sentence describing the outcome of a proposal review round, "
        "identify each person mentioned and their decision: approved, requested changes, or recused. "
        "Return ONLY a single integer — the number of people who approved. "
        "No explanation, no text, just the integer."
    )
    output = await llm.ainvoke(
        [SystemMessage(system_prompt), HumanMessage(state.sentence)]
    )
    count = int(output.content.strip())
    return GraphOutput(approver_count=count)


builder = StateGraph(GraphState, output=GraphOutput)

builder.add_node("count_approvers", count_approvers)

builder.add_edge(START, "count_approvers")
builder.add_edge("count_approvers", END)

graph = builder.compile()
