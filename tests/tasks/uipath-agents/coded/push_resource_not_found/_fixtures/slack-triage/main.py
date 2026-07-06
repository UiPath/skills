from pydantic import BaseModel
from uipath import UiPath


class Input(BaseModel):
    message: str


class Output(BaseModel):
    posted: bool


async def main(payload: Input) -> Output:
    sdk = UiPath()
    connection = await sdk.connections.retrieve_async("slack-triage")
    # Activity invocation omitted — this fixture exercises the connection
    # binding resolution at push time, not the runtime call.
    return Output(posted=connection is not None)
