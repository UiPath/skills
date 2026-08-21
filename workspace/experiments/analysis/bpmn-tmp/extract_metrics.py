"""Extract per-task metrics from OPT and BASE runs. Outputs per_task_rows.json."""
import json, glob, os, re

OPT_DIR  = '/home/azureuser/projects/skills/tmp/coder_eval/runs/maestro-bpmn-optimized-sonnet-5'
BASE_DIR = '/home/azureuser/projects/skills/tmp/coder_eval/runs/maestro-bpmn-baseline-sonnet-5'
OUT_DIR  = '/home/azureuser/projects/skills/tmp/experiments/analysis/bpmn-tmp'

SCRIPT_PAT = re.compile(r'python3\s+.*?\.py', re.IGNORECASE)

def is_script_call(cmd):
    return cmd.get('tool_name') == 'Bash' and bool(SCRIPT_PAT.search((cmd.get('parameters') or {}).get('command', '')))

def extract_script_name(cmd):
    m = re.search(r'python3\s+(.+?\.py)', (cmd.get('parameters') or {}).get('command', ''))
    return os.path.basename(m.group(1)) if m else None

def task_metrics(d):
    tu = d.get('total_token_usage') or {}
    thinking_tok = tool_result_tok = tool_calls = turns = 0
    script_calls = {}
    trace = []
    for it in d.get('iterations', []):
        turns += it.get('num_turns', 0) or 0
        for msg in it.get('messages', []):
            rt = msg.get('reasoning_tokens', 0) or 0
            thinking_tok += rt
            if rt >= 1500:
                trace.append(('THINK', rt))
        for cmd in it.get('commands', []):
            tool_calls += 1
            tr = cmd.get('result_tokens', 0) or 0
            tool_result_tok += tr
            trace.append((cmd.get('tool_name', ''), tr))
            if is_script_call(cmd):
                sn = extract_script_name(cmd) or 'unknown.py'
                script_calls[sn] = script_calls.get(sn, 0) + 1
    return {
        'thinking_tok': thinking_tok, 'tool_result_tok': tool_result_tok,
        'tool_calls': tool_calls, 'script_calls': script_calls, 'turns': turns,
        'cost': tu.get('total_cost_usd', 0), 'cache_read': tu.get('cache_read_input_tokens', 0),
        'cache_create': tu.get('cache_creation_input_tokens', 0),
        'output_tok': tu.get('output_tokens', 0), 'uncached': tu.get('uncached_input_tokens', 0),
        'time': d.get('duration_seconds', 0), 'task_desc': d.get('task_description', ''),
        'status': d.get('final_status', ''), 'trace': trace[:50],
    }

def get_all_tasks(run_dir):
    tasks = {}
    for tj in sorted(glob.glob(f'{run_dir}/default/*/*/task.json')):
        parts = tj.split('/default/')[1].split('/')
        task_id, rep = parts[0], parts[1]
        with open(tj) as f:
            d = json.load(f)
        tasks.setdefault(task_id, []).append({'rep': rep, 'data': d, 'metrics': task_metrics(d)})
    return tasks

print("Loading OPT..."); opt_tasks = get_all_tasks(OPT_DIR)
print("Loading BASE..."); base_tasks = get_all_tasks(BASE_DIR)

both_solved = sorted(
    t for t in opt_tasks if t in base_tasks
    and any(r['data'].get('final_status') == 'SUCCESS' for r in opt_tasks[t])
    and any(r['data'].get('final_status') == 'SUCCESS' for r in base_tasks[t])
)
print(f"Both solved: {len(both_solved)}")

rows = []
for task_id in both_solved:
    opt_r = [r for r in opt_tasks[task_id] if r['data'].get('final_status') == 'SUCCESS']
    base_r = [r for r in base_tasks[task_id] if r['data'].get('final_status') == 'SUCCESS']
    om, bm = opt_r[0]['metrics'], base_r[0]['metrics']
    rows.append({
        'task': task_id, 'n_opt': len(opt_r), 'n_base': len(base_r),
        'task_desc': bm['task_desc'][:120],
        'b_thinking': bm['thinking_tok'], 'b_tool_result': bm['tool_result_tok'],
        'b_tool_calls': bm['tool_calls'], 'b_turns': bm['turns'], 'b_cost': bm['cost'],
        'b_cache_read': bm['cache_read'], 'b_cache_create': bm['cache_create'],
        'b_output': bm['output_tok'], 'b_uncached': bm['uncached'], 'b_time': bm['time'],
        'b_scripts': bm['script_calls'], 'b_trace': bm['trace'],
        'o_thinking': om['thinking_tok'], 'o_tool_result': om['tool_result_tok'],
        'o_tool_calls': om['tool_calls'], 'o_turns': om['turns'], 'o_cost': om['cost'],
        'o_cache_read': om['cache_read'], 'o_cache_create': om['cache_create'],
        'o_output': om['output_tok'], 'o_uncached': om['uncached'], 'o_time': om['time'],
        'o_scripts': om['script_calls'], 'o_trace': om['trace'],
        'd_thinking': om['thinking_tok'] - bm['thinking_tok'],
        'd_tool_result': om['tool_result_tok'] - bm['tool_result_tok'],
        'd_tool_calls': om['tool_calls'] - bm['tool_calls'],
        'd_turns': om['turns'] - bm['turns'],
        'd_cost': om['cost'] - bm['cost'],
        'd_time': om['time'] - bm['time'],
    })

rows.sort(key=lambda r: r['d_cost'])
with open(f'{OUT_DIR}/per_task_rows.json', 'w') as f:
    json.dump({'both_solved': both_solved, 'rows': rows}, f, indent=2)

print(f"Written {len(rows)} rows")
tb = sum(r['b_cost'] for r in rows); to = sum(r['o_cost'] for r in rows)
print(f"BASE total: ${tb:.4f}  OPT total: ${to:.4f}  saving: ${tb-to:.4f} ({(tb-to)/tb*100:.1f}%)")
print(f"cache_read  Δ: {sum(r['o_cache_read']-r['b_cache_read'] for r in rows):+,}")
print(f"cache_create Δ: {sum(r['o_cache_create']-r['b_cache_create'] for r in rows):+,}")
print(f"output Δ: {sum(r['o_output']-r['b_output'] for r in rows):+,}")
print(f"tool_calls Δ: {sum(r['d_tool_calls'] for r in rows):+}")
print(f"turns Δ: {sum(r['d_turns'] for r in rows):+}")
