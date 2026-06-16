from uipath.platform import UiPath

async def main(input):
    sdk = UiPath()
    asset = await sdk.assets.retrieve_async("report_email", folder_path="Reports")
    return {"ok": True, "email": str(asset)}
