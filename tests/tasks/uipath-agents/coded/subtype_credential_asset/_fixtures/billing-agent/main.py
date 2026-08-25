from uipath.platform import UiPath

async def main(input):
    sdk = UiPath()
    api_key = await sdk.assets.retrieve_credential_async(
        "billing_api_key", folder_path="Finance"
    )
    return {"ok": True}
