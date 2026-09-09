<!--skill-flavor:voice-topology-testing:start-->
Only a real inbound call can raise a `core.trigger.voice`, so **an inbound flow cannot be debugged** — `uip flow debug` has no call to answer and the run never advances. Testing it means the full publish path — `uip solution publish --location "<FolderPathOrKey>"`, bind a number, then dial it — while an outbound flow runs under `uip flow debug` directly and places its call from the host debug.
<!--skill-flavor:voice-topology-testing:end-->

<!--skill-flavor:voice-topology-testing-2:start-->
| | Inbound | Outbound |
| --- | --- | --- |
| Trigger | `core.trigger.voice` | `core.trigger.manual` (or any other trigger) |
| `uip flow debug` | **Not usable** — publish + bind + dial the number | Runs, and places a real call |
| Phone number | Bound to the published release ([impl.md § Bind an Inbound Phone Number](impl.md#bind-an-inbound-phone-number)) | Named directly in `inputs.from` |
| Needs a publish to test at all | Yes | No |

Outbound is the only shape with a debug loop; inbound cannot be exercised at all until it is published and a number is bound to it.
<!--skill-flavor:voice-topology-testing-2:end-->

<!--skill-flavor:voice-scaffold-command:start-->

`<FlowProjectDir>` = `/solution/<FlowProject>` = `CurrentProject.AbsolutePath`; this form runs the real CLI in Studio Web and `--conversational` is honoured.
<!--skill-flavor:voice-scaffold-command:end-->
