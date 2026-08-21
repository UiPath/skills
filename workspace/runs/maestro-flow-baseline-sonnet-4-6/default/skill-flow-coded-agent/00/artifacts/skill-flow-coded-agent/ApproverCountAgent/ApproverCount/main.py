from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import START, StateGraph, END
from pydantic import BaseModel, Field


class GraphInput(BaseModel):
    sentence: str = Field(description="Sentence describing the outcome of a proposal review round")


class GraphOutput(BaseModel):
    approver_count: int = Field(description="Number of people who approved")


async def count_approvers(state: GraphInput) -> GraphOutput:
    from uipath_langchain.chat.models import UiPathAzureChatOpenAI

    llm = UiPathAzureChatOpenAI(model="gpt-4o-mini-2024-07-18")
    structured_llm = llm.with_structured_output(GraphOutput)

    system_prompt = (
        "You are a reviewer analyst. Given a sentence describing the outcome of a proposal review round, "
        "identify each person mentioned and determine their action: approved, requested changes, or recused. "
        "Return the exact count of people who approved (not requested changes, not recused)."
    )

    result = await structured_llm.ainvoke(
        [SystemMessage(system_prompt), HumanMessage(state.sentence)]
    )
    return GraphOutput.model_validate(result)


builder = StateGraph(GraphInput, output=GraphOutput)
builder.add_node("count_approvers", count_approvers)
builder.add_edge(START, "count_approvers")
builder.add_edge("count_approvers", END)

graph = builder.compile()
