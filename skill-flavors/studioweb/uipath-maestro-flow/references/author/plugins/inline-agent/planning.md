<!--skill-flavor:inline-agent-resource-kinds:start-->
- **External tool** (`tool` port) — agent calls a deployed automation. Four kinds; discover via the registry below. The referenced process must be on the open solution's Resources panel (`uip solution resources list --kind Process`; `uip solution resources add` if missing) — `uip solution resources refresh` is unavailable in Studio Web.
- **Built-in tool** (`tool` port) — platform-shipped tool, e.g. analyze-attachments. `registry get uipath.agent.resource.tool.builtin.<toolType>`. Self-contained — no bindings, no solution resource.
- **Context** (`context` port) — RAG retrieval from a Context Grounding index. `registry search "uipath.agent.resource.context"`, then `get` the matching `NodeType`. Needs the index on the open solution's Resources panel.
- **Escalation** (`escalation` port) — human-in-the-loop approval/review mid-run via a deployed Action Center app. `registry get uipath.agent.resource.escalation`. Needs the app on the open solution's Resources panel.
<!--skill-flavor:inline-agent-resource-kinds:end-->

<!--skill-flavor:inline-agent-tool-folderpath:start-->
For the tool's `resource.json` format and solution-level resource setup, see the `uipath-agents` skill (`lowcode/capabilities/process/`). Set `location` based on the discovery `Source` field: `"solution"` when `Source: "Local"`, `"external"` when `Source: "Remote"` (same rule as standalone agents — see `critical-rules.md` Rule 12). Set `properties.folderPath` to the **literal folder path from discovery** — parse it from the registry `Description` field (e.g., `(Shared/Sales)` → `"Shared/Sales"`) or from `uip solution resources get`. Do **not** leave `folderPath` empty — an empty `folderPath` prevents the tool binding from resolving at runtime.
<!--skill-flavor:inline-agent-tool-folderpath:end-->

<!--skill-flavor:inline-agent-tool-add-antipattern:start-->
Do not use `uip agent tool add` to attach the tool to an inline-in-flow agent. That command is designed for standalone agent projects. For inline-in-flow agents, hand-author the tool's `resource.json`, run `uip agent refresh --inline-in-flow --bindings-target` to write the binding, and make sure the referenced resource is on the open solution's Resources panel (`uip solution resources list --kind <Kind> --output json`; `uip solution resources add` if missing).
<!--skill-flavor:inline-agent-tool-add-antipattern:end-->
