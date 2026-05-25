from pydantic import BaseModel


class Input(BaseModel):
    message: str


class Output(BaseModel):
    echoed: str


async def main(payload: Input) -> Output:
    return Output(echoed=payload.message)
