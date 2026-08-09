# Behavioral twin: guard-case-plan.sh
& node (Join-Path $PSScriptRoot 'guard-case-plan.js')
exit $LASTEXITCODE
