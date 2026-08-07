#!/bin/sh
# Seeds the two reviewer write-ups traces_feedback_comment_file_smoke.yaml expects
# in the sandbox: one already on disk, one printed on stdout by a script.
set -eu

printf '%s\n' \
  'The agent summarised the wrong invoice line and omitted the total.' \
  'Reviewer: monthly output-quality sweep.' \
  > review-note.md

printf '%s\n' \
  '#!/bin/sh' \
  'echo "Latency spike: the agent retried the extraction tool four times before answering."' \
  > gen-note.sh
chmod +x gen-note.sh

echo "OK: seeded review-note.md and gen-note.sh"
