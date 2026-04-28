# MCP Server Resource

MCP (Model Context Protocol) server resources are a distinct resource type — they use `$resourceType: "mcp"`, not `$resourceType: "tool"`.

For Orchestrator process tools, see [../process/process.md](../process/process.md). For Integration Service tools, see [../integration-service/integration-service.md](../integration-service/integration-service.md).

## When to Use

- Agent needs to invoke tools exposed by an MCP server

## Agent-Level Resource Shape

**Path:** `<AgentName>/resources/{McpServerName}/resource.json`

```jsonc
{
  "$resourceType": "mcp",
  "id": "<uuid>",
  "name": "MyMcpServer",
  "description": "What this MCP server provides",
  "isEnabled": true,
  "tools": []  // MCP tool definitions — populated at runtime
}
```

## Solution-Level Files

Not yet documented for this skill. End-to-end MCP authoring is sparse — there is no scenario walkthrough today.

## Gotchas

See [../../critical-rules.md](../../critical-rules.md) general rules. No MCP-specific gotchas captured at this time.

## References

- [../../agent-definition.md](../../agent-definition.md) § Resources Convention
