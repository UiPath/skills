<!--skill-flavor:http-impl-node-add:start-->
```bash
uip maestro flow node add /solution/<FlowProject>/new.flow core.action.http.v2 \
  --label "<HTTP node label>" --output json
```
<!--skill-flavor:http-impl-node-add:end-->

<!--skill-flavor:http-impl-node-add-inputs:start-->
```bash
uip maestro flow node add /solution/<FlowProject>/new.flow core.action.http.v2 \
  --label "<HTTP node label>" \
  --input '{
    "timeout": "PT30M",
    "retryCount": 3,
    "branches": [
      { "id": "hasItems", "name": "Has Items", "conditionExpression": "$self.output.body.items.length > 0" },
      { "id": "empty",    "name": "Empty",    "conditionExpression": "$self.output.body.items.length == 0" }
    ]
  }' --output json
```
<!--skill-flavor:http-impl-node-add-inputs:end-->

<!--skill-flavor:http-impl-configure-dynamic:start-->
```bash
uip maestro flow node configure /solution/<FlowProject>/new.flow <nodeId> \
  --detail '{
    "authentication": "manual",
    "method": "GET",
    "url": "=js:`https://api.example.com/users/${$vars.userId}`"
  }' --output json
```
<!--skill-flavor:http-impl-configure-dynamic:end-->
