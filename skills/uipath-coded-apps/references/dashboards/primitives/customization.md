# Customization & Ownership — hand-edited dashboards

The generated project is a **standard Vite + React + Tailwind + Recharts app with no skill dependency**. The skill's job is the first draft; the user owns the result. This file tells you how to act when the user customizes it — the build script does NOT handle this, you do.

## Ownership map — what the build script overwrites

| File | Regenerated when | Safe to hand-edit? |
|------|------------------|--------------------|
| `src/dashboard/Dashboard.tsx` | **Every** build and incremental op (ADD/REMOVE/CHANGE/REBUILD) | Only if you re-apply edits after (see protocol) |
| `src/dashboard/widgets/index.ts` | Every build and incremental op | No — regenerated from state.json widgets only |
| `src/dashboard/widgets/<Widget>.tsx` | CHANGE/REBUILD of that widget | Hash-guarded on CHANGE/REMOVE (`HAND_EDIT_DETECTED`); **REBUILD overwrites silently** |
| `src/dashboard/views/<Widget>View.tsx` | ADD/CHANGE of its chart widget | Same caveat |
| `src/App.tsx` | Only inside `GENERATED_IMPORTS/ROUTES` markers | Yes, outside the markers |
| `src/index.css`, `tailwind.config.*`, `src/dashboard/chrome/*`, `src/hooks/*`, `src/lib/*` | Never | **Yes — fully safe** |
| Any new file the user adds | Never touched, but `index.ts` regen drops its export | Yes (see custom-widget rule) |

## Rules

1. **Look-and-feel requests → edit the project directly. Never run the build script for presentation-only changes.** Restyle via `index.css` CSS variables (`--chart-1..5`, `--background`, …), Tailwind config, `chrome/` components, or by editing `Dashboard.tsx` yourself with file-edit tools. You are a coding agent — the script is for data/widget generation, not the only way to change the app.
2. **Before running ANY edit-intent on a customized project, protect `Dashboard.tsx`:** read it first; run the script; if the user had customized it, re-apply their layout afterwards and merge the change in by hand (e.g. add the new widget's import + JSX where it fits their design). The script always rewrites `Dashboard.tsx` + `widgets/index.ts` from state.
3. **Detect customization before assuming.** Signals: the user says they edited; `HAND_EDIT_DETECTED` fires; `Dashboard.tsx` clearly diverges from the generated shape (custom sections, different grid). When detected, prefer hand-editing over the script for the whole change.
4. **Never run REBUILD on a customized project without explicit consent** — it regenerates every widget from stored intent and silently overwrites hand-edited widget files.
5. **`HAND_EDIT_DETECTED` means stop.** Never overwrite; show the user what would be lost and ask: keep their version (apply the change by hand) or regenerate.
6. **Custom (user-written) widgets: import them directly in `Dashboard.tsx`** (`import { Foo } from './widgets/Foo'`), NOT via `./widgets` index — `index.ts` regeneration drops unknown exports. If the user already routes through the index, re-add the export line after any script run.
7. **Custom routes/views go outside the `GENERATED_*` markers in `App.tsx`** — content inside the markers is regenerated.
8. **Full takeover is legitimate.** A pro user can stop using build/edit entirely and develop the app by hand; everything keeps working (`npm run dev/build`), and the deploy flow still works — it only reads `.dashboard/state.json`. Tell them this when they ask "can I extend this myself?": yes, it's their app.

## Anti-patterns

- Running `edit-intent` (or a fresh build) over a customized `Dashboard.tsx` without re-applying the user's layout — their design is wiped
- Telling the user a styling request "isn't supported" because `displayAs`/registry has no option for it — edit the code instead
- Re-running the build script to change a title, color, or spacing
- Regenerating a hand-edited widget after `HAND_EDIT_DETECTED` without asking
