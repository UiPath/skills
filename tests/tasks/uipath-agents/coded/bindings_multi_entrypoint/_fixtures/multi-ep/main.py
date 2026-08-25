from uipath.platform import UiPath

async def main(input):
    sdk = UiPath()
    bucket = await sdk.buckets.retrieve_async(name="reports-bucket", folder_path="Reports")
    return {"ok": True, "bucket": str(bucket)}
