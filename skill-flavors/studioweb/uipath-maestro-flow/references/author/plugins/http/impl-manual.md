<!--skill-flavor:http-manual-node-add:start-->
```bash
uip maestro flow node add /solution/<FlowProject>/new.flow core.action.http.v2 \
  --label "<HTTP node label>" --output json
```
<!--skill-flavor:http-manual-node-add:end-->

<!--skill-flavor:http-manual-configure:start-->
```bash
uip maestro flow node configure /solution/<FlowProject>/new.flow <nodeId> \
  --detail '{
    "authentication": "manual",
    "method": "GET",
    "url": "https://api.example.com/endpoint",
    "query": {"param1": "value1"}
  }' --output json
```
<!--skill-flavor:http-manual-configure:end-->

<!--skill-flavor:http-manual-configure-headers:start-->
```bash
uip maestro flow node configure /solution/<FlowProject>/new.flow <nodeId> \
  --detail '{
    "authentication": "manual",
    "method": "GET",
    "url": "https://api.example.com/me",
    "headers": {"Authorization": "=js:`Bearer ${$vars.apiToken}`"}
  }' --output json
```
<!--skill-flavor:http-manual-configure-headers:end-->
