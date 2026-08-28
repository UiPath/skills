# File Attachments

How to use files as input, output, or artifacts created during a coded-agent run.

For the low-code equivalent, see `../../lowcode/capabilities/built-in-tools/analyze-attachments.md`.

## File as Input

Declare an `Attachment` on the `Input` model. After editing, run `uip codedagent init` to refresh `entry-points.json`; it emits the `job-attachment` schema so Studio Web and Orchestrator render a file picker.

```python
from pydantic import BaseModel
from uipath.platform.attachments import Attachment

class Input(BaseModel):
    attachment: Attachment
```

`Attachment` contains metadata only. Use snake_case fields such as `input.attachment.full_name`, and fetch bytes through `sdk.attachments`. Instantiate `UiPath` inside the function, never at module level:

```python
from uipath.platform import UiPath

async def main(input: Input) -> Output:
    uipath = UiPath()
    async with uipath.attachments.open_async(attachment=input.attachment) as (att, response):
        async for raw_bytes in response.aiter_raw():
            ...
```

Use `sdk.attachments.open(...)` for synchronous code.

## Creating Attachments

Attach generated files to the current job:

```python
from uipath.platform.common import UiPathConfig

await uipath.jobs.create_attachment_async(
    name="report.txt",
    content=str(result),
    folder_key=UiPathConfig.folder_key,
    job_key=UiPathConfig.job_key,
)
```

For standalone uploads not tied to a job, use `sdk.attachments`; see the SDK reference.

## Local Testing

`uip codedagent run` and `invoke` cannot upload attachments because the file picker exists only in Studio Web / Orchestrator. To test locally without making `Input.attachment` optional, check `UiPathConfig.job_key`: it is `None` outside a platform job and populated inside Orchestrator / Studio Web. Locally, read bytes from `UIPATH_LOCAL_ATTACHMENT`; pass a placeholder `Attachment` only for validation and ignore its fields.

```python
import os
from pathlib import Path
from uipath.platform import UiPath
from uipath.platform.common import UiPathConfig

async def read_attachment_bytes(input: Input) -> bytes:
    if UiPathConfig.job_key is None:
        return Path(os.environ["UIPATH_LOCAL_ATTACHMENT"]).read_bytes()

    uipath = UiPath()
    async with uipath.attachments.open_async(attachment=input.attachment) as (_att, response):
        return b"".join([chunk async for chunk in response.aiter_raw()])
```

Run locally with a placeholder attachment and an environment variable containing the real file:

```bash
UIPATH_LOCAL_ATTACHMENT=C:/tmp/sample.pdf uip codedagent run main '{"attachment": {"ID": "00000000-0000-0000-0000-000000000000", "FullName": "placeholder", "MimeType": "application/octet-stream"}}'
```

For created attachments, write locally to `UIPATH_LOCAL_OUTPUT_DIR` (or `.`); in a platform job, call `jobs.create_attachment_async`:

```python
if UiPathConfig.job_key is None:
    Path(os.environ.get("UIPATH_LOCAL_OUTPUT_DIR", ".")).joinpath("report.txt").write_text(str(result))
else:
    await uipath.jobs.create_attachment_async(
        name="report.txt",
        content=str(result),
        folder_key=UiPathConfig.folder_key,
        job_key=UiPathConfig.job_key,
    )
```

## References

- `sdk-services.md` § Attachments, § Jobs
