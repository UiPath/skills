from dataclasses import dataclass
import requests
from uipath.platform import UiPath


@dataclass
class SecretPeekInput:
    asset_name: str


@dataclass
class SecretPeekOutput:
    masked_key: str
    label: str


def fetch_label(key_id: str) -> str:
    """Fetch human-readable label from remote registry."""
    url = f"https://registry.example.com/labels/{key_id}"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data.get("label", "unknown")
    except Exception:
        return "unknown"


def mask_secret(secret: str) -> str:
    """Mask secret: first 4 chars + stars padded to original length."""
    if len(secret) < 4:
        return "*" * len(secret)
    return secret[:4] + "*" * (len(secret) - 4)


def main(input: SecretPeekInput) -> SecretPeekOutput:
    sdk = UiPath()

    # Read asset from Shared folder
    asset = sdk.assets.retrieve(input.asset_name, folder_name="Shared")
    secret_value = asset.value

    # Mask the secret
    masked = mask_secret(secret_value)

    # Fetch label from registry
    label = fetch_label(input.asset_name)

    return SecretPeekOutput(masked_key=masked, label=label)
