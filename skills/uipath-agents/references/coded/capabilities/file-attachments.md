# File Attachments

How to work with files in a coded agent — as input, as output, or created mid-run.

For the low-code equivalent, see `../../lowcode/capabilities/built-in-tools/analyze-attachments.md`.

## File as Input

Use `Attachment` on the `Input` model. `uip codedagent init` emits the `job-attachment` schema in `entry-points.json` so Studio Web and Orchestrator render a file picker at runtime.

```python
from pydantic import BaseModel
from uipath.platform.attachments import Attachment

class Input(BaseModel):
    attachment: Attachment
```

Run `uip codedagent init` after the edit to refresh `entry-points.json`.

Access fields as snake_case, e.g. `input.attachment.full_name`.

`Attachment` carries metadata only. Fetch bytes via `sdk.attachments` (instantiate inside the function, never at module level):

```python
from uipath.platform import UiPath

async def main(input: Input) -> Output:
    uipath = UiPath()
    async with uipath.attachments.open_async(attachment=input.attachment) as (att, response):
        async for raw_bytes in response.aiter_raw():
            ...
```

Sync equivalent: `sdk.attachments.open(...)`.

## Creating Attachments

Produce a file from the agent and attach it to the current job:

```python
from uipath.platform.common import UiPathConfig

await uipath.jobs.create_attachment_async(
    name="report.txt",
    content=str(result),
    folder_key=UiPathConfig.folder_key,
    job_key=UiPathConfig.job_key,
)
```

Standalone uploads (not tied to a job) go through `sdk.attachments` — see the SDK reference.

## Local Testing

`uip codedagent run` / `invoke` cannot upload attachments — the platform file picker only exists in Studio Web / Orchestrator. To exercise attachment logic locally without making `Input.attachment` optional, detect the run context via `UiPathConfig.job_key` (`None` outside a platform job, populated inside Orchestrator / Studio Web) and load bytes from an environment variable. Pass a placeholder `Attachment` in the CLI input just to satisfy validation — the agent ignores its fields on the local branch.

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

Invoke locally — placeholder `Attachment` satisfies the schema, env var provides the real file:

```bash
UIPATH_LOCAL_ATTACHMENT=C:/tmp/sample.pdf uip codedagent run main '{"attachment": {"ID": "00000000-0000-0000-0000-000000000000", "FullName": "placeholder", "MimeType": "application/octet-stream"}}'
```

Same pattern for **creating** attachments — when `job_key is None`, write to disk instead of calling `jobs.create_attachment_async`:

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

## Gotchas

- `uip codedagent run` / `invoke` cannot upload attachments — use the env-var fallback above, or test the platform path via Studio Web / Orchestrator.

## References

- `sdk-services.md` § Attachments, § Jobs
