<!--skill-flavor:assign-roundtrip-runtime-comparison:start-->
- Multi-key `set` (for example, `"set": { "userName": "...", "count": 0 }`) — Studio Web's designer keeps one key on save. Use one Assign activity per variable.
<!--skill-flavor:assign-roundtrip-runtime-comparison:end-->

<!--skill-flavor:assign-literal-roundtrip:start-->
**String literals MUST be wrapped:** `"${'literal'}"` (a JS string inside an expression). Studio Web preserves the wrapped form and rewrites a plain literal to `${literal}` on save. See SKILL.md critical rule 5.
<!--skill-flavor:assign-literal-roundtrip:end-->

<!--skill-flavor:response-object-roundtrip:start-->
- **Use a single-expression `${{ ... }}` for object payloads.** Studio Web preserves that form across designer saves.
<!--skill-flavor:response-object-roundtrip:end-->
