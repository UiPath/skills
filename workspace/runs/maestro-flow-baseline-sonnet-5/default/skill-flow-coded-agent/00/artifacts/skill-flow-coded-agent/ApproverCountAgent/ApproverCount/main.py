from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field


class GraphState(BaseModel):
    sentence: str = Field(
        description="A sentence describing the outcome of a proposal review round."
    )


class Person(BaseModel):
    name: str = Field(description="The person's name as mentioned in the sentence.")
    decision: Literal["approved", "requested_changes", "recused"] = Field(
        description="Whether the person approved, requested changes, or recused themselves."
    )


class PeopleDecisions(BaseModel):
    people: list[Person] = Field(
        description="Every person mentioned in the sentence, with their decision."
    )


class GraphOutput(BaseModel):
    approved_count: int = Field(description="The number of people who approved.")


SYSTEM_PROMPT = (
    "You analyze a sentence describing the outcome of a proposal review round. "
    "Identify every person mentioned by name, and classify each person's decision as exactly one of: "
    '"approved", "requested_changes", or "recused". '
    "A person who explicitly asked for revisions, changes, or edits made requested_changes. "
    "A person who stepped back, abstained, or recused themselves from the review is recused. "
    "Anyone else who signed off, agreed with, or approved the proposal is approved. "
    "List every person mentioned exactly once."
)


async def classify_people(state: GraphState) -> GraphOutput:
    from uipath_langchain.chat import UiPathAzureChatOpenAI

    llm = UiPathAzureChatOpenAI(model="gpt-4.1-mini-2025-04-14", temperature=0)
    structured_llm = llm.with_structured_output(PeopleDecisions)
    raw = await structured_llm.ainvoke(
        [SystemMessage(SYSTEM_PROMPT), HumanMessage(state.sentence)]
    )
    decisions = PeopleDecisions.model_validate(raw)
    approved_count = sum(1 for person in decisions.people if person.decision == "approved")
    return GraphOutput(approved_count=approved_count)


builder = StateGraph(GraphState, output=GraphOutput)

builder.add_node("classify_people", classify_people)

builder.add_edge(START, "classify_people")
builder.add_edge("classify_people", END)

graph = builder.compile()
