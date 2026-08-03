from uipath.platform import UiPath

async def main(input):
    sdk = UiPath()
    # queue
    await sdk.queues.create_item_async(item={"Name": "OrderQueue", "SpecificContent": {"id": "1"}})
    # app (Action Center)
    await sdk.tasks.create_async(title="Review", data={"id": "1"}, app_name="ReviewApp", app_folder_path="Ops")
    # index (Context Grounding)
    await sdk.context_grounding.retrieve_async(name="kb_index", folder_path="Shared")
    # connection (Integration Service)
    await sdk.connections.retrieve_async("salesforce-prod-conn")
    # mcpServer
    await sdk.mcp.retrieve_async(slug="weather-mcp", folder_path="Tools")
    return {"ok": True}
