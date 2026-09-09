<!-- when: adding a HITL escalation to a Low-Code Agent (agent.json) project -->
# HITL on a Low-Code Agent — Escalation Reference

The Low-Code Agent escalation CLI (`uip agent escalation add`) is currently in-flight. Until it ships, configure manually.

**`agent.json` escalation entry:**
```json
{
  "escalations": [
    {
      "name": "<escalation-name>",
      "inputSchema":  { "inputs": [...], "inOuts": [...] },
      "outputSchema": { "outputs": [...], "outcomes": [...] }
    }
  ]
}
```

**Agent source (Python):**
```python
from uipath.sdk import interrupt, CreateTask

response = interrupt(CreateTask(
    escalation_name="<escalation-name>",
    data={ "fieldName": value }
))
# response contains the human's outputs and chosen outcome
```
