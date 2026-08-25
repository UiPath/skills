from uipath import UiPath  # this import path does not exist
from pydantic import BaseModel

class Input(BaseModel):
    asset_name: str

class Output(BaseModel):
    value: str

async def main(input: Input) -> Output:
    sdk = UiPath()
    asset = await sdk.assets.retrieve_async(input.asset_name, folder_path="Shared")
    return Output(value=str(asset))
