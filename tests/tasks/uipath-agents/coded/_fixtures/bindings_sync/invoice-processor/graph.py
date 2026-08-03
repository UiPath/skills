from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt
from uipath.platform import UiPath
from uipath.platform.common import InvokeProcess
from storage import BUCKET_NAME

SCRAPER_PROCESS = "data-scraper"

def fetch_data(state):
    response = interrupt(InvokeProcess(name=SCRAPER_PROCESS, input_arguments={}))
    return {"data": response}

def save_results(state):
    sdk = UiPath()
    sdk.buckets.upload(name=BUCKET_NAME, blob_file_path="results.json", content="{}")
    return state

def get_config(state):
    sdk = UiPath()
    api_key = sdk.assets.retrieve("api-key", folder_path="Shared")
    return {"config": api_key}
