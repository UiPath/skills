from pydantic import BaseModel
from uipath.tracing import traced

class Input(BaseModel):
    message: str

class Output(BaseModel):
    echoed: str

@traced()
async def main(input: Input) -> Output:
    return Output(echoed=input.message)
