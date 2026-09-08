<!--skill-flavor:sw-eval-variable-add-example:start-->
uip maestro flow variable add /solution/<Project>/new.flow name \
<!--skill-flavor:sw-eval-variable-add-example:end-->

<!--skill-flavor:sw-eval-input-file-note:start-->
`--input-file <key>=<path>` is repeatable and attaches a staged file under the specified key for runtime use, including PDFs, CSVs, and images. Stage the file inside `/solution/<Project>/` (not `/tmp`, which is scratch and does not survive the turn) and leave it in place until `run start` has uploaded it.
<!--skill-flavor:sw-eval-input-file-note:end-->

<!--skill-flavor:sw-eval-variable-list-example:start-->
uip maestro flow variable list /solution/<Project>/new.flow --output json
<!--skill-flavor:sw-eval-variable-list-example:end-->

<!--skill-flavor:sw-eval-input-file-antipattern:start-->
- Do not move or overwrite attached input files before `run start` has uploaded them; the eval set references their paths under `/solution/<Project>/` (and files under `/solution` cannot be deleted anyway).
<!--skill-flavor:sw-eval-input-file-antipattern:end-->
