from langgraph.graph import START, StateGraph, END
from pydantic import BaseModel, Field


class GraphInput(BaseModel):
    sentence: str = Field(description="A sentence describing the outcome of a proposal review round")


class GraphOutput(BaseModel):
    approver_count: int = Field(description="The number of people who approved the proposal")


class GraphState(BaseModel):
    sentence: str = Field(description="A sentence describing the outcome of a proposal review round")
    approver_count: int = Field(default=0, description="The number of people who approved the proposal")


async def analyze_review(state: GraphState) -> GraphState:
    from uipath_langchain.chat.models import UiPathAzureChatOpenAI
    from pydantic import BaseModel as PydanticBaseModel, Field as PydanticField

    class ReviewAnalysis(PydanticBaseModel):
        approver_count: int = PydanticField(
            description="The number of distinct people who explicitly approved the proposal"
        )

    llm = UiPathAzureChatOpenAI(
        model="gpt-4o-mini-2024-07-18",
        temperature=0,
        max_tokens=512,
        timeout=30,
        max_retries=2,
    )
    structured_llm = llm.with_structured_output(ReviewAnalysis)

    prompt = (
        "You are analyzing the outcome of a proposal review. "
        "Read the following sentence and identify every person mentioned. "
        "For each person, determine their action: approved, requested changes, or recused. "
        "Count only those who APPROVED. "
        "Return ONLY the integer count of approvers.\n\n"
        f"Review sentence: {state.sentence}"
    )

    raw = await structured_llm.ainvoke(prompt)
    result = ReviewAnalysis.model_validate(raw)
    return GraphState(sentence=state.sentence, approver_count=result.approver_count)


builder = StateGraph(GraphState, input=GraphInput, output=GraphOutput)
builder.add_node("analyze_review", analyze_review)
builder.add_edge(START, "analyze_review")
builder.add_edge("analyze_review", END)

graph = builder.compile()
