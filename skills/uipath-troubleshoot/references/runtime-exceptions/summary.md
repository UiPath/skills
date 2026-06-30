# Runtime Exceptions Playbooks

**Investigation guide:** [investigation_guide.md](./investigation_guide.md) — scope check, data correlation rules, local log paths, and source code analysis for runtime exception investigations

| Issue | Confidence | Description | Playbook |
|-------|:---:|-------------|----------|
| Null Reference Exception | Medium | `System.NullReferenceException` in workflow code — uninitialized variable, null activity output, missing data, or unguarded conditional path | [null-reference-exception.md](./playbooks/null-reference-exception.md) |
| Argument Null Exception | Medium | `System.ArgumentNullException` in workflow code — null value passed to activity or method that requires non-null | [argument-null-exception.md](./playbooks/argument-null-exception.md) |
| Invalid Operation Exception | Medium | `System.InvalidOperationException` in workflow code — LINQ `First`/`Single` with no/too-many matches, `Nullable.Value` with no value, collection modified during enumeration | [invalid-operation-exception.md](./playbooks/invalid-operation-exception.md) |
| Argument Exception | Medium | `System.ArgumentException` in workflow code — invalid (non-null, in-range) argument: undefined `Enum.Parse` name, duplicate dictionary/column key, bad format/culture | [argument-exception.md](./playbooks/argument-exception.md) |
| Directory Not Found Exception | Medium | `System.IO.DirectoryNotFoundException` in workflow code — I/O on a path whose directory is missing: hardcoded dev path, wrong config, unmapped drive on unattended | [directory-not-found-exception.md](./playbooks/directory-not-found-exception.md) |
| Index Out Of Range Exception | Medium | `System.IndexOutOfRangeException` in workflow code — array/string indexed past bounds: short `Split` result, off-by-one, fixed index on variable data | [index-out-of-range-exception.md](./playbooks/index-out-of-range-exception.md) |
| Key Not Found Exception | Medium | `System.Collections.Generic.KeyNotFoundException` in workflow code — dictionary/config indexed with an absent key: missing config row, typo, case mismatch | [key-not-found-exception.md](./playbooks/key-not-found-exception.md) |
| Argument Out Of Range Exception | Medium | `System.ArgumentOutOfRangeException` in workflow code — `Substring` past end, `List<T>` index past `Count`, invalid date/time component | [argument-out-of-range-exception.md](./playbooks/argument-out-of-range-exception.md) |
