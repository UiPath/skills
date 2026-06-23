from datetime import datetime
from pydantic import BaseModel
from uipath.tracing import traced

class Input(BaseModel):
    label: str = "digest"

class Output(BaseModel):
    digest: str

@traced()
async def main(input: Input) -> Output:
    today = datetime.utcnow().strftime("%Y-%m-%d")
    return Output(digest=f"{input.label}: {today}")
