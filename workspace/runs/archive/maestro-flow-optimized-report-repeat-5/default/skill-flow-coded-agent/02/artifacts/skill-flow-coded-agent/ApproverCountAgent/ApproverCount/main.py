from langgraph.graph import START, StateGraph, END
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage
from uipath_langchain.chat.models import UiPathAzureChatOpenAI


class GraphInput(BaseModel):
    sentence: str = Field(description="A sentence describing the outcome of a proposal review round.")


class ReviewOutcome(BaseModel):
    approved_count: int = Field(description="Number of people who approved the proposal.")


class GraphState(BaseModel):
    sentence: str = Field(description="Input sentence to analyse.")
    approved_count: int = Field(default=0, description="Number of approvers identified.")


async def analyse_approvals(state: GraphState) -> GraphState:
    llm = UiPathAzureChatOpenAI(
        model="gpt-4o-mini-2024-07-18",
        temperature=0,
        max_tokens=256,
        timeout=30,
        max_retries=2,
    )
    structured_llm = llm.with_structured_output(ReviewOutcome)

    system_prompt = (
        "You are an expert at reading proposal review outcome sentences. "
        "Identify every person mentioned in the sentence. "
        "For each person determine one of three statuses:\n"
        "  - approved: the person explicitly approved or voted in favour.\n"
        "  - requested_changes: the person asked for changes, objected, or voted against.\n"
        "  - recused: the person recused themselves or abstained.\n"
        "Count only the people who approved and return that count as the integer field 'approved_count'."
    )

    result = await structured_llm.ainvoke(
        [SystemMessage(system_prompt), HumanMessage(state.sentence)]
    )

    # with_structured_output may return a dict or a Pydantic object
    if isinstance(result, dict):
        count = result.get("approved_count", 0)
    else:
        count = result.approved_count

    return GraphState(sentence=state.sentence, approved_count=count)


class GraphOutput(BaseModel):
    approved_count: int = Field(description="Number of people who approved the proposal.")


builder = StateGraph(GraphState, input=GraphInput, output=GraphOutput)
builder.add_node("analyse_approvals", analyse_approvals)
builder.add_edge(START, "analyse_approvals")
builder.add_edge("analyse_approvals", END)

graph = builder.compile()
