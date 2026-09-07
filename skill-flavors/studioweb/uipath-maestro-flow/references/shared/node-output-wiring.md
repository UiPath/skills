<!--skill-flavor:validation-steps:start-->
1. Open `/solution/<ProjectName>/new.flow`.
2. Search for the token: `grep '"vars\.' /solution/<ProjectName>/new.flow` or `grep '"\$vars\.' /solution/<ProjectName>/new.flow`.
3. In `bodyParameters`, `queryParameters`, `pathParameters`, end-node `source`, and other value fields, prepend `=js:` to each variable reference.
4. Run `uip maestro flow validate` and re-run `uip flow debug`.
<!--skill-flavor:validation-steps:end-->
