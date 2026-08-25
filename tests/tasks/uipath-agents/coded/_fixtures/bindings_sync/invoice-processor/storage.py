from uipath.platform import UiPath

BUCKET_NAME = "invoice-data"

def download_template():
    sdk = UiPath()
    sdk.buckets.download(name=BUCKET_NAME, blob_file_path="template.xlsx", destination_path="/tmp/t.xlsx")
