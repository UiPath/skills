from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import START, StateGraph, END
from pydantic import BaseModel, Field
from uipath_langchain.chat import UiPathAzureChatOpenAI


class GraphInput(BaseModel):
    sentence: str = Field(description="A sentence describing the outcome of a proposal review round.")


class GraphOutput(BaseModel):
    approver_count: int = Field(description="The number of people who approved the proposal.")


class AnalysisResult(BaseModel):
    approver_count: int = Field(description="The number of people who approved the proposal.")


async def count_approvers(state: GraphInput) -> GraphOutput:
    llm = UiPathAzureChatOpenAI(model="gpt-4o-mini-2024-07-18")
    structured_llm = llm.with_structured_output(AnalysisResult)

    system_prompt = (
        "You are an expert at analysing proposal review outcomes. "
        "Given a sentence that describes what each reviewer did, "
        "identify every person mentioned and classify their action as one of: "
        "APPROVED, REQUESTED_CHANGES, or RECUSED. "
        "Then count only the people whose action is APPROVED and return that integer count. "
        "Do not count people who abstained, recused themselves, requested changes, or had any other outcome."
    )

    result_dict = await structured_llm.ainvoke(
        [SystemMessage(system_prompt), HumanMessage(state.sentence)]
    )
    result = AnalysisResult.model_validate(result_dict)
    return GraphOutput(approver_count=result.approver_count)


builder = StateGraph(GraphInput, output=GraphOutput)
builder.add_node("count_approvers", count_approvers)
builder.add_edge(START, "count_approvers")
builder.add_edge("count_approvers", END)

graph = builder.compile()
