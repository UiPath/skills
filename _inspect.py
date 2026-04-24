import json, sys, io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

task_json = sys.argv[1]
d = json.loads(Path(task_json).read_text(encoding='utf-8'))
lr = d.get('llm_review') or {}
print('task_id:', d.get('task_id'))
print('final_status:', d.get('final_status'))
print('weighted_score:', d.get('weighted_score'))
print('LLM REVIEW score:', lr.get('score'))
print('issues:', lr.get('issues'))
print()
print('next_steps:')
for s in lr.get('next_steps') or []:
    print(f'  - {s}')
print()
print('TOOL CALLS:')
for turn in d.get('turns') or []:
    for c in turn.get('commands') or []:
        tn = c.get('tool_name')
        status = c.get('result_status') or '-'
        params = c.get('parameters') or {}
        if tn == 'Skill':
            print(f'  [{status:<7}] Skill   -> {params.get("skill")}')
        elif tn == 'Bash':
            cmd = (params.get('command') or '').splitlines()[0][:140]
            print(f'  [{status:<7}] Bash    {cmd}')
        elif tn in ('Write', 'Edit', 'Read'):
            fp = params.get('file_path', '')
            base = fp.replace('\\', '/').split('/')[-1] or fp
            print(f'  [{status:<7}] {tn:<6} {base}')
        elif tn == 'Glob':
            print(f'  [{status:<7}] Glob    {params.get("pattern")}')
        else:
            print(f'  [{status:<7}] {tn}')
