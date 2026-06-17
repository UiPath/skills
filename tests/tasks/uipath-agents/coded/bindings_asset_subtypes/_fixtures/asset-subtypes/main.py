from uipath.platform import UiPath

async def main(input):
    sdk = UiPath()
    api_key: str = await sdk.assets.retrieve_async("api_key", folder_path="Shared")
    max_retries: int = await sdk.assets.retrieve_async("max_retries", folder_path="Shared")
    feature_enabled: bool = await sdk.assets.retrieve_async("feature_enabled", folder_path="Shared")
    return {"ok": True, "api_key": api_key, "max_retries": max_retries, "feature_enabled": feature_enabled}
