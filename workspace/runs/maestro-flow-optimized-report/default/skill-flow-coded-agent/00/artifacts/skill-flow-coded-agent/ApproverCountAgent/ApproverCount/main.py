from langgraph.graph import START, StateGraph, END
from pydantic import BaseModel, Field
from uipath_langchain.chat import UiPathAzureChatOpenAI


class GraphInput(BaseModel):
    sentence: str = Field(description="A sentence describing the outcome of a proposal review round.")


class GraphOutput(BaseModel):
    approver_count: int = Field(description="The number of people who approved the proposal.")


class GraphState(BaseModel):
    sentence: str
    approver_count: int = 0


class ReviewAnalysis(BaseModel):
    approver_count: int = Field(
        description="The number of distinct people who approved the proposal."
    )


async def analyze_review(state: GraphState) -> GraphOutput:
    llm = UiPathAzureChatOpenAI(model="gpt-4o-mini-2024-07-18")
    structured_llm = llm.with_structured_output(ReviewAnalysis)

    system_prompt = (
        "You are an expert at analyzing proposal review sentences. "
        "Read the sentence carefully and identify every person mentioned. "
        "For each person, determine their action: approved, requested changes, or recused. "
        "Count only the people who explicitly approved. "
        "Return the exact integer count of approvers."
    )

    prompt = (
        f"Analyze the following review outcome sentence and count how many people approved:\n\n"
        f'"{state.sentence}"\n\n'
        "Return the number of people who approved as approver_count."
    )

    from langchain_core.messages import HumanMessage, SystemMessage

    raw = await structured_llm.ainvoke(
        [SystemMessage(system_prompt), HumanMessage(prompt)]
    )
    result = ReviewAnalysis.model_validate(raw)
    return GraphOutput(approver_count=result.approver_count)


builder = StateGraph(GraphState, input=GraphInput, output=GraphOutput)
builder.add_node("analyze_review", analyze_review)
builder.add_edge(START, "analyze_review")
builder.add_edge("analyze_review", END)

graph = builder.compile()
