#!/usr/bin/env python3
"""Inventory an Automation Anywhere Automation 360 bot export - for reading it at genome extraction and for deriving
the migration catalogs at genome execution.

Usage:
  a360-export-inventory.py profile <EXPORT_DIR> [--out DIR]   # identity, packages, vocabulary, call graph, roots, credentials, windows, evidence
  a360-export-inventory.py cards   <EXPORT_DIR> [--out DIR]   # one compact card per bot
  a360-export-inventory.py dump    <EXPORT_DIR> <BOT>         # one bot, line by line, in execution order (name or repository path)
  a360-export-inventory.py targets <EXPORT_DIR> [--out DIR]   # UI target catalog: windows + captured controls with decoded object properties and the action applied
  a360-export-inventory.py data    <EXPORT_DIR> [--out DIR]   # bot inventory (call edges with argument bindings) + data sources the bots read and write

<EXPORT_DIR> is the export root (the folder holding `Bots/`), the `Bots/` folder itself, or any folder above it that
contains exactly one `Bots/` tree. Bot files are extension-less JSON documents with `nodes`, `variables` and
`packages`; `<Bot>Metadata/` folders hold the recorder's screenshots and are never read for logic.

Which mode runs which command, and where the output goes: references/sources/automation-anywhere-source-guide.md
(command block at the top); why nothing is written beside the genome: references/genome-format-guide.md § Source Map;
execution-time derivation: references/source-migration-guide.md § Migration preflight.
Writes a360-profile.txt / a360-cards.txt / a360-targets.{json,md} / a360-process-data.json / a360-data-sources.{json,md}
into --out (default: current directory); dump prints to stdout.
Never prints a literal typed into a password field, a variable whose name contains password/pwd/secret/token, or a
value of an attribute so named. Credential Vault references (locker/credential.attribute) are identity, not secrets, and
are kept - references/genome-format-guide.md § Platform Dependencies.

Bot identity: Automation 360 exports carry no numeric object ids; a bot is identified by its repository path below
`Bots/`. The script derives a stable six-digit id from that path (CRC-32, folded into 100000-999999) so Source Map rows
can carry `Name` (id) and genome-step-map.py can resolve them; the same export always yields the same ids.
"""
import argparse
import base64
import collections
import json
import os
import re
import sys
import urllib.parse
import zlib
import xml.etree.ElementTree as ET

SENSITIVE = re.compile(r'passw|pwd|secret|token', re.I)
BRANCH_COMMANDS = ('else', 'elseIf', 'catch', 'finally')
# Not steps: authoring notes, the run's own log and screenshots, timing, debugging leftovers, migration plumbing.
NOISE = {('Comment', 'Comment'), ('LogToFile', 'logToFile'), ('Delay', 'delay'), ('LegacyAutomation', 'getKeystrokesDelay'),
         ('MessageBox', 'messageBox'), ('Screen', 'captureDesktop'), ('Step', 'step')}
SEPARATOR = re.compile(r'^[=\-\*\|#_~\s]*$')
REPO_PREFIX = re.compile(r'^(repository:///)?(automation anywhere/)?bots/', re.I)
GLOBAL_VALUE = re.compile(r'\$@([A-Za-z0-9_]+)\$')
SYSTEM_VAR = re.compile(r'\$System:([A-Za-z0-9_]+)')
VAR_REF = re.compile(r'\$([A-Za-z0-9_\-]+)')
DATA_FILE_EXT = ('.xml', '.xlsx', '.xls', '.xlsm', '.csv', '.txt', '.json', '.vbs', '.ps1', '.bat', '.config', '.ini')

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def stable_id(key):
    """Six-digit id derived from a repository path or data-source identity; same input, same id."""
    return 100000 + zlib.crc32(key.encode('utf-8')) % 900000


def repo_path(s):
    """`repository:///Automation%20Anywhere/Bots/My%20Tasks/X/Y` -> `My Tasks/X/Y`."""
    s = urllib.parse.unquote(s or '').replace('\\', '/')
    return REPO_PREFIX.sub('', s).strip('/')


def fmt_window(w):
    if not w:
        return None
    exe = os.path.basename((w.get('path') or '').replace('\\', '/')) or None
    parts = [json.dumps(w.get('name') or '', ensure_ascii=False)]
    if w.get('class'):
        parts.append(w['class'])
    if exe:
        parts.append(exe)
    return 'win(' + ' '.join(parts) + ')'


def decode_blob(blob):
    """The recorder stores the captured object tree as base64 JSON; strip the protobuf memo fields it carries."""
    if not blob:
        return {}
    try:
        d = json.loads(base64.b64decode(blob).decode('utf-8'))
    except Exception as e:  # noqa: BLE001 - a bad blob is reported, not fatal
        return {'error': str(e)}

    def prune(o):
        if isinstance(o, dict):
            return {k: prune(v) for k, v in o.items() if k not in ('memoizedIsInitialized', 'unknownFields', 'memoizedSize', 'memoizedHashCode', 'actionsMemoizedSerializedSize', 'searchCriteriaMemoizedSerializedSize')}
        if isinstance(o, list):
            return [prune(x) for x in o]
        return o
    return prune(d)


class Bot:
    def __init__(self, export, abs_path, rel_path):
        self.export = export
        self.abs = abs_path
        self.path = rel_path
        self.name = os.path.basename(rel_path)
        self.folder = os.path.dirname(rel_path)
        self.id = stable_id(rel_path)
        with open(abs_path, encoding='utf-8-sig') as fh:
            self.doc = json.load(fh)
        self.vars = {v.get('name'): v for v in self.doc.get('variables', [])}
        self.lines = []  # (line, depth, node, is_branch) in editor order
        self._number(self.doc.get('nodes', []), 0)
        self.metadata_dir = abs_path + 'Metadata'

    def _number(self, nodes, depth):
        for n in nodes:
            self.lines.append((len(self.lines) + 1, depth, n, False))
            self._number(n.get('children', []), depth + 1)
            for b in n.get('branches', []):
                self.lines.append((len(self.lines) + 1, depth, b, True))
                self._number(b.get('children', []), depth + 1)

    def line_of(self, node):
        for ln, _, n, _ in self.lines:
            if n is node:
                return ln
        return None

    def nodes(self, enabled_only=False):
        for ln, depth, n, is_branch in self.lines:
            if enabled_only and n.get('disabled'):
                continue
            yield ln, depth, n, is_branch

    def window(self, expr):
        """`$window-1$` -> the WINDOW variable's recorded title/class/executable."""
        m = re.fullmatch(r'\$([^$]+)\$', expr or '')
        v = self.vars.get(m.group(1)) if m else None
        w = ((v or {}).get('defaultValue') or {}).get('window') if v else None
        if not w:
            return None
        return {'variable': m.group(1), 'title': w.get('name'), 'class': w.get('class') or None,
                'exe': os.path.basename((w.get('path') or '').replace('\\', '/')) or None}

    # ----- variables -----
    def var_groups(self):
        g = {'in': [], 'out': [], 'inout': [], 'const': [], 'local': []}
        for v in self.doc.get('variables', []):
            i, o = v.get('input'), v.get('output')
            k = 'inout' if i and o else 'in' if i else 'out' if o else 'const' if v.get('readOnly') else 'local'
            g[k].append(v['name'])
        return g

    def description(self):
        """The author's description: the first comment that starts with 'Description', else the first real comment."""
        first = None
        for _, _, n, _ in self.lines:
            if n.get('commandName') != 'Comment':
                continue
            t = (self._attr_string(n, 'comment') or '').strip()
            if not t or SEPARATOR.match(t):
                continue
            if t.lower().startswith('description'):
                return t.split(':', 1)[-1].strip()
            first = first or t
        return first

    @staticmethod
    def _attr_string(n, name):
        for a in n.get('attributes', []):
            if a.get('name') == name:
                v = a.get('value') or {}
                return v.get('expression') or v.get('string')
        return None


class Export:
    def __init__(self, root):
        self.given = root
        self.bots_dir = self._find_bots(root)
        self.root = os.path.dirname(self.bots_dir)
        self.bots = []
        self.data_files = []  # files under My Docs / MyDocs and any non-bot, non-metadata file
        for dp, dns, fns in os.walk(self.bots_dir):
            dns[:] = [d for d in dns if not d.endswith('Metadata')]
            for f in sorted(fns):
                p = os.path.join(dp, f)
                rel = os.path.relpath(p, self.bots_dir).replace('\\', '/')
                if self._is_bot(p):
                    self.bots.append(Bot(self, p, rel))
                elif f.lower().endswith(DATA_FILE_EXT):
                    self.data_files.append((rel, p))
        self.bots.sort(key=lambda b: b.path)
        self.by_path = {b.path: b for b in self.bots}
        self.by_path_ci = {b.path.lower(): b for b in self.bots}
        self.secrets = self._secrets()
        self.edges = [e for b in self.bots for e in self._edges(b)]
        self.called = {e['calleeId'] for e in self.edges if e['calleeId'] and not e['disabled']}
        self.called_any = {e['calleeId'] for e in self.edges if e['calleeId']}

    @staticmethod
    def _find_bots(root):
        root = os.path.abspath(root)
        if os.path.basename(root).lower() == 'bots' and os.path.isdir(root):
            return root
        cand = os.path.join(root, 'Bots')
        if os.path.isdir(cand):
            return cand
        hits = []
        for dp, dns, _ in os.walk(root):
            if dp[len(root):].count(os.sep) > 3:
                dns[:] = []
                continue
            for d in dns:
                if d.lower() == 'bots':
                    hits.append(os.path.join(dp, d))
        if len(hits) == 1:
            return hits[0]
        sys.exit(f"{root}: expected an Automation 360 export with one Bots/ folder, found {len(hits)}")

    @staticmethod
    def _is_bot(p):
        if os.path.splitext(p)[1]:
            return False
        try:
            with open(p, 'rb') as fh:
                head = fh.read(4096)
            return head.lstrip(b'\xef\xbb\xbf').startswith(b'{') and b'"nodes"' in head or b'"packages"' in head
        except OSError:
            return False

    def resolve(self, ref):
        p = repo_path(ref)
        return self.by_path.get(p) or self.by_path_ci.get(p.lower())

    def _secrets(self):
        """Literal secret values: defaults of password-named variables, literals typed into password fields, literal
        values of password-named attributes. Redacted wherever they appear afterwards."""
        out = set()

        def take(v):
            if isinstance(v, str) and len(v) > 3 and not v.startswith('$') and v not in ('True', 'False', 'None'):
                out.add(v)
        for b in self.bots:
            for v in b.doc.get('variables', []):
                if SENSITIVE.search(v.get('name') or ''):
                    take(((v.get('defaultValue') or {}).get('string')))
            for _, _, n, _ in b.lines:
                attrs = {a.get('name'): a.get('value') or {} for a in n.get('attributes', [])}
                if n.get('commandName') == 'capture' and 'passwordtextAction' in attrs:
                    take((attrs.get('value') or {}).get('string'))
                for name, v in attrs.items():
                    if SENSITIVE.search(name or '') and v.get('type') != 'CREDENTIAL':
                        take(v.get('string'))
                # a literal assigned into a password-named variable (String.assign -> $StrLaraPassword$) is the
                # commonest way a secret ends up in a bot; the attribute is called sourceString, so only the target tells
                if SENSITIVE.search((n.get('returnTo') or {}).get('variableName') or ''):
                    for v in attrs.values():
                        if v.get('type') == 'STRING' and not v.get('expression'):
                            take(v.get('string'))
        return out

    def _edges(self, bot):
        out = []
        for ln, _, n, _ in bot.lines:
            if n.get('commandName') != 'runTask':
                continue
            attrs = {a.get('name'): a.get('value') or {} for a in n.get('attributes', [])}
            tb = attrs.get('taskbot') or {}
            ref = (tb.get('taskbotFile') or {}).get('string') or (tb.get('taskbotFile') or {}).get('expression') or ''
            callee = self.resolve(ref)
            out.append({'caller': bot.name, 'callerId': bot.id, 'line': ln, 'disabled': bool(n.get('disabled')),
                        'continueOnError': bool((attrs.get('continueOnError') or {}).get('boolean')),
                        'calleePath': repo_path(ref), 'callee': callee.name if callee else None, 'calleeId': callee.id if callee else None,
                        'inputs': {d['key']: d.get('value') for d in (tb.get('taskbotInput') or {}).get('dictionary', [])},
                        'outputs': {d['key']: d.get('value') for d in (tb.get('taskbotOutput') or {}).get('dictionary', [])}})
        return out

    # ----- rendering -----
    def V(self, v, bot, aname=''):
        """One attribute value as text. Expressions win over literals (they carry the variable names)."""
        if not v:
            return ''
        t = v.get('type')
        if t == 'CREDENTIAL':
            c = v.get('credential') or {}
            return f"vault:{c.get('lockerName')}/{c.get('name')}.{c.get('attributeName')}"
        if t == 'WINDOW':
            if v.get('expression'):
                w = bot.window(v['expression'])
                return f"{v['expression']}=" + (fmt_window({'name': w['title'], 'class': w['class'], 'path': w['exe']}) if w else '?')
            return fmt_window(v.get('window')) or '?'
        if t == 'SESSION':
            sn = v.get('sessionName') or {}
            return 'session:' + str(sn.get('string') or sn.get('expression') or v.get('expression') or '?')
        if t == 'UIOBJECT':
            return self.fmt_uiobject(v, bot)
        if t == 'EXCEPTION':
            return str(v.get('exceptionName'))
        if t == 'LIST':
            return '[' + ', '.join(self.V(x, bot, aname) for x in v.get('list', [])) + ']'
        if t == 'DICTIONARY':
            return '{' + ', '.join(f"{d.get('key')}: {self.V(d.get('value'), bot, d.get('key'))}" for d in v.get('dictionary', [])) + '}'
        if t == 'REGION':
            r = v.get('region') or {}
            return f"region({','.join(self.V(r.get(k), bot) for k in ('x', 'y', 'width', 'height'))})"
        if t == 'VARIABLE':
            return f"${v.get('variableName')}$"
        if t == 'TASKBOT':
            return self.fmt_taskbot(v, bot)
        if t == 'FILE':
            s = urllib.parse.unquote(v.get('expression') or v.get('string') or '')
            s = re.sub(r'^file://', '', s)
            return json.dumps(self.safe(aname, s), ensure_ascii=False)
        if v.get('expression') not in (None, ''):
            s = v['expression']
        elif 'string' in v:
            s = v['string']
        elif 'number' in v:
            return str(v['number'])
        elif 'boolean' in v:
            return str(v['boolean']).lower()
        else:
            return json.dumps(v, ensure_ascii=False)[:100]
        return json.dumps(self.safe(aname, s), ensure_ascii=False)

    def safe(self, aname, s):
        if not isinstance(s, str):
            return s
        if SENSITIVE.search(aname or '') and not s.startswith('$'):
            return '***'
        for sec in self.secrets:
            if sec in s:
                s = s.replace(sec, '***')
        return s

    def fmt_taskbot(self, v, bot):
        ref = (v.get('taskbotFile') or {}).get('string') or (v.get('taskbotFile') or {}).get('expression') or ''
        callee = self.resolve(ref)
        head = f"`{callee.name}` ({callee.id})" if callee else f"UNRESOLVED `{repo_path(ref) or '?'}`"
        ins = ', '.join(f"{d.get('key')}={self.V(d.get('value'), bot, d.get('key'))}" for d in (v.get('taskbotInput') or {}).get('dictionary', []))
        outs = ', '.join(f"{d.get('key')}={self.V(d.get('value'), bot, d.get('key'))}" for d in (v.get('taskbotOutput') or {}).get('dictionary', []))
        return f"{head} in{{{ins}}} out{{{outs}}}"

    def capture_summary(self, v, bot):
        """UIOBJECT value -> normalized control description (also the row shape of the target catalog)."""
        uo = v.get('uiObject') or {}
        win_expr = (v.get('uiObjectWindow') or {}).get('expression')
        crit = {}
        for k, c in (uo.get('criteria') or {}).items():
            if c.get('enabled'):
                cv = c.get('value') or {}
                crit[k] = cv.get('expression') or cv.get('string') or cv.get('number') or ''
        d = decode_blob(uo.get('blob'))
        on = d.get('objNode') or {}
        tech = on.get('technology') or {}
        shots = sorted({m for m in re.findall(r'"\w*MetadataPath":\s*"([^"]+\.png)"', json.dumps(v))})
        return {'technology': uo.get('technologyType'), 'controlType': uo.get('controlType'), 'window': bot.window(win_expr) if win_expr else None,
                'windowExpr': win_expr, 'criteria': crit,
                'object': {'name': on.get('name') or None, 'role': on.get('role'), 'description': on.get('description') or None,
                           'className': on.get('className') or on.get('class') or None, 'id': on.get('id') or None, 'value': on.get('value') or None,
                           'windowTitle': on.get('windowTitle') or None, 'defaultAction': on.get('defaultAction') or None,
                           'states': on.get('states') or None, 'index': on.get('index'),
                           'path': [p.get('index') for p in ((on.get('path') or {}).get('objPath') or [])],
                           'bounds': {k: on.get(k) for k in ('left', 'top', 'width', 'height') if on.get(k) is not None},
                           'attributes': {a.get('name'): a.get('value') for a in on.get('attributes', []) if a.get('value') not in ('', None)},
                           'techType': tech.get('techType'), 'platformType': tech.get('platformType')},
                'parent': ((d.get('objParent') or {}).get('name') if isinstance(d.get('objParent'), dict) else None),
                'browserFramework': d.get('browserFramework'), 'captureVersion': d.get('captureVersion'),
                'searchCriteria': d.get('searchCriteria') or None, 'screenshots': shots, 'blobError': d.get('error')}

    def fmt_uiobject(self, v, bot):
        c = self.capture_summary(v, bot)
        w = c['window']
        wtxt = f"{c['windowExpr']}=" + (fmt_window({'name': w['title'], 'class': w['class'], 'path': w['exe']}) if w else '?') if c['windowExpr'] else ''
        crit = ', '.join(f"{k}={json.dumps(self.safe(k, str(val)), ensure_ascii=False)}" for k, val in c['criteria'].items())
        name = c['object']['name'] or c['object']['description']
        return f"ui[{c['technology']}/{c['controlType']}] {wtxt} {{{crit}}}" + (f" obj={json.dumps(name, ensure_ascii=False)}" if name else '')

    def fmt_condition(self, a, bot):
        v = a.get('value') or {}
        cname = v.get('conditionalName') or '?'
        sub = {x.get('name'): x.get('value') or {} for x in a.get('attributes', [])}
        r = lambda k: self.V(sub.get(k), bot, k)
        if cname in ('legacyConditionVariable', 'stringVariable', 'numberVariable', 'booleanVariable'):
            s = f"{r('variable')} {(sub.get('operator') or {}).get('string') or '?'} {r('value')}"
            if (sub.get('matchCase') or {}).get('boolean'):
                s += ' [matchCase]'
            return s
        if cname == 'capture':
            return f"uiObjectExists({self.fmt_uiobject(sub.get('uiObject') or {}, bot)}, wait {r('wait')}s)"
        if cname == 'hasExtension':
            return f"hasExtension({r('sourceFilePath')} {(sub.get('operator') or {}).get('string')} {r('extensions')})"
        parts = [f"{k}={self.V(val, bot, k)}" for k, val in sub.items()]
        return f"{cname}({', '.join(parts)})"

    def fmt_iterator(self, a, bot):
        v = a.get('value') or {}
        iname = (v.get('iteratorName') or '?').split('.')[-1]
        sub = ', '.join(f"{x.get('name')}={self.V(x.get('value'), bot, x.get('name'))}" for x in a.get('attributes', []))
        ret = a.get('returnTo') or {}
        rs = f" -> ${ret.get('variableName')}$" if ret.get('variableName') else ''
        return f"for {iname}({sub}){rs}"

    def render(self, n, bot, is_branch=False):
        pk, cmd = n.get('packageName'), n.get('commandName')
        off = '[off] ' if n.get('disabled') else ''
        if cmd == 'Comment':
            t = (bot._attr_string(n, 'comment') or '').strip()
            if not t or SEPARATOR.match(t):
                return None
            return f"{off}# {t.replace(chr(10), ' / ')}"
        conds, others, op = [], [], None
        for a in n.get('attributes', []):
            v = a.get('value') or {}
            t = v.get('type')
            if t == 'CONDITIONAL':
                conds.append(self.fmt_condition(a, bot))
            elif a.get('name') == 'operator' and cmd in ('if', 'elseIf'):
                op = v.get('string')
            elif t == 'ITERATOR':
                others.append(self.fmt_iterator(a, bot))
            elif t == 'TASKBOT':
                others.append(self.fmt_taskbot(v, bot))
            else:
                others.append(f"{a.get('name')}={self.V(v, bot, a.get('name'))}")
        text = ''
        if conds:
            text = f" {op or 'AND'} ".join(conds) if len(conds) > 1 else conds[0]
        if others:
            text = (text + ' ' if text else '') + ' '.join(others)
        ret = n.get('returnTo') or {}
        if ret:
            text += ' -> ' + (f"${ret.get('variableName')}$" if ret.get('type') == 'VARIABLE' else self.V(ret, bot))
        if n.get('returns'):
            text += ' -> ' + ', '.join(f"{k}=${(val or {}).get('variableName')}$" for k, val in n['returns'].items())
        label = cmd if is_branch or cmd in ('if', 'elseIf', 'try', 'throw') else f"{pk}.{cmd}"
        if cmd == 'loop.commands.start':
            label = 'loop'
        elif cmd in ('loop.commands.break', 'loop.commands.continue'):
            label = cmd.split('.')[-1]
        return f"{off}{label} {text}".rstrip()


# ----------------------------------------------------------------------------------------------------------------------
def dump(x: Export, which, compact=False):
    """compact: a disabled node is one line with its subtree folded, a log line shows only its message, delays and
    keystroke-delay lookups shrink to a word - the logic stays, the plumbing goes."""
    bot = x.by_path.get(repo_path(which)) or next((b for b in x.bots if b.name == which), None) \
        or next((b for b in x.bots if b.name.lower() == which.lower()), None)
    if not bot:
        return f"no bot named {which!r}; bots: {[b.name for b in x.bots]}"
    L = []
    pr = L.append
    props = bot.doc.get('properties') or {}
    pr(f"# `{bot.name}` ({bot.id})  path={bot.path}  priority={props.get('automationPriority')} botCodeVersion={props.get('botCodeVersion')} "
       f"migrationJournal={bot.doc.get('migrationJournalReviewIds') or []} lines={len(bot.lines)} disabled={sum(1 for _, _, n, _ in bot.lines if n.get('disabled'))}")
    pr(f"PACKAGES: {', '.join(f'{p.get('name')} {p.get('version')}' for p in bot.doc.get('packages', []))}")
    d = bot.description()
    if d:
        pr(f"DESCRIPTION: {d}")
    g = bot.var_groups()
    for k, label in (('in', 'INPUTS'), ('out', 'OUTPUTS'), ('inout', 'IN/OUT'), ('const', 'CONSTANTS')):
        if g[k]:
            pr(f"{label}: {', '.join(g[k])}")
    pr(f"LOCALS: {len(g['local'])}")
    wins = collections.OrderedDict()
    for v in bot.doc.get('variables', []):
        if v.get('type') == 'WINDOW':
            w = bot.window(f"${v['name']}$")
            if w:
                wins[v['name']] = f"{json.dumps(w['title'], ensure_ascii=False)} {w['class'] or ''} {w['exe'] or ''}".strip()
    if wins:
        pr("WINDOWS: " + '; '.join(f"${k}$={val}" for k, val in wins.items()))
    consts = []
    for v in bot.doc.get('variables', []):
        dv = v.get('defaultValue') or {}
        lit = dv.get('string') if 'string' in dv else dv.get('number') if 'number' in dv else None
        if lit not in (None, '') and v.get('type') != 'WINDOW' and not v['name'].startswith('window-'):
            consts.append(f"{v['name']}={json.dumps(x.safe(v['name'], str(lit)), ensure_ascii=False)[:80]}")
    if consts:
        pr("DEFAULTS: " + '; '.join(consts[:40]) + (' …' if len(consts) > 40 else ''))
    pr('')
    fold_below = None  # depth of a disabled node whose subtree is being folded (compact mode)
    folded = 0
    for ln, depth, n, is_branch in bot.lines:
        if fold_below is not None:
            if depth > fold_below or (depth == fold_below and is_branch):
                folded += 1
                continue
            if folded:
                L[-1] += f" (+{folded} lines folded)"
            fold_below, folded = None, 0
        cmd = n.get('commandName')
        if compact:
            if n.get('disabled'):
                label = cmd if is_branch or cmd in ('if', 'elseIf', 'try', 'throw') else f"{n.get('packageName')}.{cmd}"
                if cmd == 'Comment':
                    t = x.render(n, bot, is_branch)
                    if t is None:
                        continue
                    pr(f"{ln:>4} {'  ' * depth}{t}")
                    continue
                pr(f"{ln:>4} {'  ' * depth}[off] {label}")
                fold_below = depth
                continue
            if cmd == 'getKeystrokesDelay':
                continue
            if cmd == 'logToFile':
                pr(f"{ln:>4} {'  ' * depth}log {x.V(next((a.get('value') for a in n.get('attributes', []) if a.get('name') == 'logContent'), None), bot)}")
                continue
            if cmd == 'delay':
                a = {a.get('name'): a.get('value') or {} for a in n.get('attributes', [])}
                pr(f"{ln:>4} {'  ' * depth}delay {x.V(a.get('delayTime'), bot)} {(a.get('timeUnit') or {}).get('string', '').lower()}")
                continue
        t = x.render(n, bot, is_branch)
        if t is None:
            continue
        pr(f"{ln:>4} {'  ' * depth}{t}")
    if folded:
        L[-1] += f" (+{folded} lines folded)"
    return '\n'.join(L)


def profile(x: Export):
    L = []
    pr = L.append
    all_nodes = [(b, ln, n) for b in x.bots for ln, _, n, _ in b.lines]
    enabled = [(b, ln, n) for b, ln, n in all_nodes if not n.get('disabled')]
    pr(f"## EXPORT {x.root}")
    pr(f"bots={len(x.bots)} lines={len(all_nodes)} disabled={len(all_nodes) - len(enabled)} data files={len(x.data_files)} "
       f"metadata folders={sum(1 for b in x.bots if os.path.isdir(b.metadata_dir))}")
    migrated = [b.name for b in x.bots if b.doc.get('migrationJournalReviewIds')]
    pr(f"migration journal (Enterprise 11 -> Automation 360 Bot Migration): {len(migrated)} bots carry review ids: {migrated}")
    pk = collections.defaultdict(set)
    for b in x.bots:
        for p in b.doc.get('packages', []):
            pk[p.get('name')].add(p.get('version'))
    pr("\n## PACKAGES (name: versions)")
    for k in sorted(pk):
        pr(f"  {k}: {sorted(pk[k])}")
    pr("\n## FOLDERS (path: bots)")
    byf = collections.defaultdict(list)
    for b in x.bots:
        byf[b.folder].append(b)
    for f in sorted(byf):
        pr(f"  {f}: {[b.name for b in byf[f]]}")
    pr("\n## DATA FILES in the export (My Docs)")
    for rel, p in x.data_files:
        pr(f"  {rel} ({os.path.getsize(p)} bytes)")
    pr("\n## COMMAND VOCABULARY (package.command: enabled / disabled)")
    voc_on = collections.Counter((n.get('packageName'), n.get('commandName')) for _, _, n in enabled)
    voc_off = collections.Counter((n.get('packageName'), n.get('commandName')) for _, _, n in all_nodes if n.get('disabled'))
    for (p, c), cnt in sorted(voc_on.items(), key=lambda kv: -kv[1]):
        pr(f"  {p}.{c}: {cnt} / {voc_off.get((p, c), 0)}")
    for (p, c), cnt in sorted(voc_off.items()):
        if (p, c) not in voc_on:
            pr(f"  {p}.{c}: 0 / {cnt}")
    pr("\n## BOTS (name (id) | folder | lines on/off | in | out | in/out | windows | captures on/off | calls | screenshots | logs | messageboxes on/off | description)")
    for b in x.bots:
        g = b.var_groups()
        caps = [n for _, _, n, _ in b.lines if n.get('commandName') == 'capture']
        pr(f"  `{b.name}` ({b.id}) | {b.folder} | {sum(1 for _, _, n, _ in b.lines if not n.get('disabled'))}/{sum(1 for _, _, n, _ in b.lines if n.get('disabled'))}"
           f" | in={len(g['in'])} out={len(g['out'])} inout={len(g['inout'])} | windows={sum(1 for v in b.doc.get('variables', []) if v.get('type') == 'WINDOW')}"
           f" | captures={sum(1 for n in caps if not n.get('disabled'))}/{sum(1 for n in caps if n.get('disabled'))}"
           f" | calls={sum(1 for e in x.edges if e['caller'] == b.name and not e['disabled'])}"
           f" | shots={sum(1 for _, _, n, _ in b.lines if n.get('commandName') == 'captureDesktop' and not n.get('disabled'))}"
           f" | logs={sum(1 for _, _, n, _ in b.lines if n.get('commandName') == 'logToFile' and not n.get('disabled'))}"
           f" | msgbox={sum(1 for _, _, n, _ in b.lines if n.get('commandName') == 'messageBox' and not n.get('disabled'))}/{sum(1 for _, _, n, _ in b.lines if n.get('commandName') == 'messageBox' and n.get('disabled'))}"
           f" | {(b.description() or '')[:110]}")
    pr("\n## CALL GRAPH (caller -> callee: uses [disabled uses] {continueOnError uses})")
    agg = collections.defaultdict(lambda: [0, 0, 0])
    for e in x.edges:
        k = (e['caller'], e['callee'] or f"UNRESOLVED {e['calleePath']}")
        agg[k][1 if e['disabled'] else 0] += 1
        if e['continueOnError'] and not e['disabled']:
            agg[k][2] += 1
    for (c, t), (on, off, coe) in sorted(agg.items()):
        pr(f"  {c} -> {t}: {on} [{off}] {{{coe}}}")
    roots = [b for b in x.bots if b.id not in x.called]
    leaves = [b for b in x.bots if not any(e['caller'] == b.name and not e['disabled'] for e in x.edges)]
    pr(f"\n## ROOTS (never called by an enabled Run Task): {[f'`{b.name}` ({b.id})' for b in roots]}")
    pr(f"## LEAVES (call nothing): {[b.name for b in leaves]}")
    pr(f"## UNRESOLVED callees: {sorted({e['calleePath'] for e in x.edges if not e['callee']})}")
    pr(f"## DEAD CALLS (disabled Run Task only): {sorted({(e['caller'], e['callee'] or e['calleePath']) for e in x.edges if e['disabled']} - {(e['caller'], e['callee']) for e in x.edges if not e['disabled']})}")
    pr("\n## CREDENTIAL VAULT REFERENCES (locker/credential.attribute: attribute of command, uses)")
    creds = collections.Counter()
    globs, sysv = collections.Counter(), collections.Counter()
    for b, ln, n in all_nodes:
        for a in n.get('attributes', []):
            s = json.dumps(a.get('value') or {})
            for m in GLOBAL_VALUE.findall(s):
                globs[m] += 1
            for m in SYSTEM_VAR.findall(s):
                sysv[m] += 1
            for c in re.findall(r'"credential":\s*(\{[^}]*\})', s):
                cd = json.loads(c)
                creds[(f"{cd.get('lockerName')}/{cd.get('name')}.{cd.get('attributeName')}", a.get('name'), n.get('commandName'), bool(n.get('disabled')))] += 1
    for (ref, an, cmd, off), cnt in sorted(creds.items()):
        pr(f"  {ref}: {an} of {cmd}{' [off]' if off else ''}, {cnt}")
    pr(f"\n## GLOBAL VALUES ($@name$): {dict(globs)}")
    pr(f"## SYSTEM VARIABLES ($System:name): {dict(sysv)}")
    pr("\n## LEGACY CREDENTIAL NOTES (migration comments naming the Enterprise 11 credential each action used)")
    for b, ln, n in all_nodes:
        if n.get('commandName') == 'Comment':
            t = b._attr_string(n, 'comment') or ''
            if 'legacy bot referred' in t:
                pr(f"  {b.name}:{ln} {' '.join(re.findall(r'Credential name=([^,]+), attribute name=([^\s/]+)', t).__repr__().split())}")
    pr("\n## WINDOWS (title | class | executable): bots")
    wins = collections.defaultdict(set)
    for b in x.bots:
        for v in b.doc.get('variables', []):
            if v.get('type') == 'WINDOW':
                w = bot_window = b.window(f"${v['name']}$")
                if w:
                    wins[(w['title'], w['class'], w['exe'])].add(b.name)
    for (t, c, e), bs in sorted(wins.items(), key=lambda kv: str(kv[0])):
        pr(f"  {json.dumps(t, ensure_ascii=False)} | {c} | {e}: {sorted(bs)}")
    pr("\n## UI CAPTURES (technology/control/action: enabled / disabled)")
    capc = collections.Counter()
    for b, ln, n in all_nodes:
        if n.get('commandName') != 'capture':
            continue
        attrs = {a.get('name'): a.get('value') or {} for a in n.get('attributes', [])}
        uo = (attrs.get('uiObject') or {}).get('uiObject') or {}
        act = next((attrs[k].get('string') for k in ('textboxAction', 'buttonAction', 'clientAction', 'labelAction', 'passwordtextAction') if k in attrs), None)
        capc[(uo.get('technologyType'), uo.get('controlType'), act, bool(n.get('disabled')))] += 1
    for (t, c, a, off), cnt in sorted(capc.items(), key=lambda kv: (str(kv[0][0]), str(kv[0][1]), str(kv[0][2]), kv[0][3])):
        pr(f"  {t}/{c}/{a}: {'0 / ' + str(cnt) if off else str(cnt)}")
    pr("\n## APPLICATIONS, BROWSERS, SCRIPTS (command: attributes)")
    for b, ln, n in enabled + [(b, ln, n) for b, ln, n in all_nodes if n.get('disabled') and n.get('commandName') in ('openbrowser', 'runApp', 'RunScript')]:
        if n.get('commandName') in ('openbrowser', 'runApp', 'RunScript'):
            pr(f"  {b.name}:{ln} {x.render(n, b)}")
    pr("\n## EMAIL (command: attributes)")
    for b, ln, n in all_nodes:
        if n.get('packageName') == 'Email' and n.get('commandName') in ('emailConnect', 'sendMail', 'moveEmail', 'saveAttachment'):
            t = x.render(n, b)
            t = re.sub(r' message="[^"]{60,}"', ' message="…"', t)
            pr(f"  {b.name}:{ln} {t[:600]}")
        for a in n.get('attributes', []):
            if (a.get('value') or {}).get('type') == 'ITERATOR' and 'email' in ((a.get('value') or {}).get('iteratorName') or ''):
                pr(f"  {b.name}:{ln} {x.render(n, b)}")
    pr("\n## DATABASE / EXCEL / XML (command: attributes)")
    for b, ln, n in all_nodes:
        if n.get('packageName') in ('Database', 'Excel_MS', 'XML') and n.get('commandName') not in ('disconnect', 'CloseSpreadsheet', 'endSession', 'GoToCell'):
            pr(f"  {b.name}:{ln} {x.render(n, b)[:400]}")
    pr("\n## FILES AND FOLDERS (enabled commands)")
    for b, ln, n in enabled:
        if n.get('packageName') in ('File', 'Folder'):
            pr(f"  {b.name}:{ln} {x.render(n, b)[:300]}")
    pr("\n## EVIDENCE AND NOISE per bot (logToFile / captureDesktop / delay total s / messageBox on+off / comments / getKeystrokesDelay) - enabled only unless noted")
    for b in x.bots:
        c = collections.Counter(n.get('commandName') for _, _, n, _ in b.lines if not n.get('disabled'))
        delay_s = 0.0
        for _, _, n, _ in b.lines:
            if n.get('commandName') == 'delay' and not n.get('disabled'):
                a = {a.get('name'): a.get('value') or {} for a in n.get('attributes', [])}
                try:
                    v = float((a.get('delayTime') or {}).get('number'))
                    delay_s += v / 1000 if (a.get('timeUnit') or {}).get('string') == 'MILLISECONDS' else v
                except (TypeError, ValueError):
                    pass
        mb_off = sum(1 for _, _, n, _ in b.lines if n.get('commandName') == 'messageBox' and n.get('disabled'))
        pr(f"  {b.name}: logs={c.get('logToFile', 0)} shots={c.get('captureDesktop', 0)} delays={c.get('delay', 0)} (~{delay_s:.0f}s fixed) msgbox={c.get('messageBox', 0)}+{mb_off}off comments={c.get('Comment', 0)} keydelay={c.get('getKeystrokesDelay', 0)}")
    pr("\n## MIGRATION PLUMBING (variables the Bot Migration generated: m-*, M-*, Loop-*, Error-*)")
    for b in x.bots:
        gen = [v['name'] for v in b.doc.get('variables', []) if re.match(r'^(m-|M-|Loop-|Error-|window-|Prompt-Assignment|my-list-variable)', v['name'])]
        pr(f"  {b.name}: {len(gen)} of {len(b.doc.get('variables', []))} variables")
    return '\n'.join(L)


def cards(x: Export):
    L = []
    pr = L.append
    callers = collections.defaultdict(set)
    for e in x.edges:
        if e['callee'] and not e['disabled']:
            callers[e['callee']].add(e['caller'])
    for b in x.bots:
        g = b.var_groups()
        on = [(ln, n) for ln, _, n, _ in b.lines if not n.get('disabled')]
        pr(f"### `{b.name}` ({b.id})  [{b.folder}] lines={len(b.lines)} enabled={len(on)} steps={sum(1 for _, n in on if (n.get('packageName'), n.get('commandName')) not in NOISE and n.get('commandName') not in BRANCH_COMMANDS)}")
        d = b.description()
        if d:
            pr(f"  description: {d[:300]}")
        pr(f"  inputs: {g['in'] + g['inout']}")
        pr(f"  outputs: {g['out'] + g['inout']}" if g['out'] or g['inout'] else "  outputs: []")
        pr(f"  callers: {sorted(callers.get(b.name, []))}")
        calls = []
        for e in x.edges:
            if e['caller'] == b.name and not e['disabled']:
                t = f"`{e['callee']}` ({e['calleeId']})" if e['callee'] else f"UNRESOLVED {e['calleePath']}"
                if not calls or calls[-1] != t:
                    calls.append(t)
        pr(f"  calls (in order): {calls}")
        wins = []
        for v in b.doc.get('variables', []):
            if v.get('type') == 'WINDOW':
                w = b.window(f"${v['name']}$")
                if w:
                    t = f"{w['title']} [{w['class'] or '?'} {w['exe'] or '?'}]"
                    if t not in wins:
                        wins.append(t)
        if wins:
            pr(f"  windows: {wins}")
        caps = collections.Counter()
        for ln, n in on:
            if n.get('commandName') == 'capture':
                attrs = {a.get('name'): a.get('value') or {} for a in n.get('attributes', [])}
                uo = (attrs.get('uiObject') or {}).get('uiObject') or {}
                act = next((attrs[k].get('string') for k in ('textboxAction', 'buttonAction', 'clientAction', 'labelAction', 'passwordtextAction') if k in attrs), None)
                caps[f"{uo.get('technologyType')}/{uo.get('controlType')}/{act}"] += 1
        if caps:
            pr(f"  ui captures: {dict(caps)}")
        conds, loops, tries, throws, stops, emails, dbs, excel, files, keys, apps, runs = [], [], 0, 0, 0, [], [], [], [], [], [], []
        for ln, n in on:
            cmd = n.get('commandName')
            if cmd in ('if', 'elseIf'):
                conds.append(f"{ln}:{x.render(n, b, cmd == 'elseIf')[:110]}")
            elif cmd == 'loop.commands.start':
                loops.append(f"{ln}:{x.render(n, b)[:110]}")
            elif cmd == 'try':
                tries += 1
            elif cmd == 'throw':
                throws += 1
            elif cmd == 'stopTask':
                stops += 1
            elif n.get('packageName') == 'Email' and cmd in ('sendMail', 'emailConnect', 'moveEmail', 'saveAttachment'):
                emails.append(f"{ln}:{cmd}")
            elif n.get('packageName') == 'Database' and cmd in ('connect', 'sqlQuery', 'insertUpdateDelete'):
                dbs.append(f"{ln}:{x.render(n, b)[:140]}")
            elif n.get('packageName') == 'Excel_MS':
                excel.append(f"{ln}:{cmd}")
            elif n.get('packageName') in ('File', 'Folder'):
                files.append(f"{ln}:{cmd}")
            elif cmd == 'Keystrokes':
                keys.append(f"{ln}:{x.render(n, b)[:120]}")
            elif cmd in ('runApp', 'openbrowser', 'RunScript'):
                apps.append(f"{ln}:{x.render(n, b)[:160]}")
        for label, items, cap in (('conditions', conds, 40), ('loops', loops, 12), ('database', dbs, 12), ('keystrokes', keys, 12), ('apps', apps, 8), ('email', emails, 12), ('excel', excel, 12), ('files', files, 12)):
            if items:
                pr(f"  {label} ({len(items)}): {items[:cap]}{' …' if len(items) > cap else ''}")
        pr(f"  error handling: try={tries} throw={throws} stopTask={stops} catch-returns={sum(1 for _, _, n, _ in b.lines if n.get('commandName') == 'catch' and n.get('returns'))}")
        pr(f"  evidence: logs={sum(1 for _, n in on if n.get('commandName') == 'logToFile')} screenshots={sum(1 for _, n in on if n.get('commandName') == 'captureDesktop')} "
           f"delays={sum(1 for _, n in on if n.get('commandName') == 'delay')} messageboxes={sum(1 for _, n in on if n.get('commandName') == 'messageBox')} (+{sum(1 for _, _, n, _ in b.lines if n.get('commandName') == 'messageBox' and n.get('disabled'))} disabled)")
        pr('')
    return '\n'.join(L)


def targets(x: Export):
    cat = []
    for b in x.bots:
        wins = []
        for v in b.doc.get('variables', []):
            if v.get('type') == 'WINDOW':
                w = b.window(f"${v['name']}$")
                if w:
                    wins.append(w)
        controls, keystrokes, window_ops = [], [], []
        for ln, _, n, _ in b.lines:
            cmd = n.get('commandName')
            attrs = {a.get('name'): a.get('value') or {} for a in n.get('attributes', [])}
            if cmd == 'capture' or any((a.get('value') or {}).get('conditionalName') == 'capture' for a in n.get('attributes', [])):
                uiv = attrs.get('uiObject')
                if not uiv:  # capture used as an If condition: the UIOBJECT sits under the condition attribute
                    for a in n.get('attributes', []):
                        for s in a.get('attributes', []):
                            if (s.get('value') or {}).get('type') == 'UIOBJECT':
                                uiv = s['value']
                if not uiv:
                    continue
                c = x.capture_summary(uiv, b)
                act = next((attrs[k].get('string') for k in ('textboxAction', 'buttonAction', 'clientAction', 'labelAction', 'passwordtextAction') if k in attrs), 'EXISTS' if cmd != 'capture' else None)
                val = attrs.get('value') or {}
                value = val.get('expression') or val.get('string')
                if 'passwordtextAction' in attrs and value and not str(value).startswith('$'):
                    value = '***'
                cred = (attrs.get('valueCV') or {}).get('credential')
                c.update({'bot': b.name, 'botId': b.id, 'line': ln, 'uid': n.get('uid'), 'disabled': bool(n.get('disabled')), 'action': act,
                          'value': x.safe('value', value) if value else None,
                          'credential': f"{cred.get('lockerName')}/{cred.get('name')}.{cred.get('attributeName')}" if cred else None,
                          'typeOfInput': (attrs.get('typeOfInput') or {}).get('string'), 'runInBackground': (attrs.get('runInBackground') or {}).get('boolean'),
                          'wait': (attrs.get('wait') or {}).get('number') or (attrs.get('wait') or {}).get('expression'),
                          'returnTo': (n.get('returnTo') or {}).get('variableName')})
                controls.append(c)
            elif cmd == 'Keystrokes':
                keystrokes.append({'line': ln, 'disabled': bool(n.get('disabled')), 'window': b.window((attrs.get('windowValue') or {}).get('expression')),
                                   'keys': x.safe('keys', (attrs.get('stringToType') or {}).get('expression') or (attrs.get('stringToType') or {}).get('string'))})
            elif n.get('packageName') in ('Window', 'Wait') or cmd in ('windowExists', 'windowTitleExists'):
                wv = next((v for v in attrs.values() if v.get('type') == 'WINDOW'), None)
                window_ops.append({'line': ln, 'disabled': bool(n.get('disabled')), 'command': cmd, 'window': b.window(wv.get('expression')) if wv else None,
                                   'newTitle': (attrs.get('newTitle') or {}).get('expression') or (attrs.get('newTitle') or {}).get('string')})
        cat.append({'bot': b.name, 'botId': b.id, 'path': b.path, 'windows': wins, 'controls': controls, 'keystrokes': keystrokes, 'windowOps': window_ops,
                    'metadataFolder': os.path.relpath(b.metadata_dir, x.bots_dir).replace('\\', '/') if os.path.isdir(b.metadata_dir) else None})
    techs = collections.Counter(c['technology'] for e in cat for c in e['controls'])
    crit = collections.Counter(f"{c['technology']}:{k}" for e in cat for c in e['controls'] for k in c['criteria'])
    md = ["# Automation 360 UI target catalog\n",
          f"{len(cat)} bots, {sum(len(e['windows']) for e in cat)} window variables, {sum(len(e['controls']) for e in cat)} captured controls "
          f"({sum(1 for e in cat for c in e['controls'] if c['disabled'])} disabled), {sum(len(e['keystrokes']) for e in cat)} keystroke commands. "
          f"Technologies: {', '.join(f'{k} ({v})' for k, v in techs.most_common())}. Enabled criteria: {', '.join(f'{k} ({v})' for k, v in crit.most_common())}\n"]
    for e in cat:
        if not (e['windows'] or e['controls'] or e['keystrokes']):
            continue
        md.append(f"\n## `{e['bot']}` ({e['botId']}) — {e['path']}\n")
        if e['windows']:
            md.append("Windows: " + '; '.join(f"${w['variable']}$ = {json.dumps(w['title'], ensure_ascii=False)} [{w['class'] or '?'} {w['exe'] or '?'}]" for w in e['windows']))
        for c in e['controls']:
            w = c['window'] or {}
            o = c['object']
            md.append(f"- line {c['line']}{' [off]' if c['disabled'] else ''} {c['technology']}/{c['controlType']} **{c['action']}**"
                      + (f" value={json.dumps(c['value'], ensure_ascii=False)}" if c['value'] else '') + (f" credential={c['credential']}" if c['credential'] else '')
                      + f" — window {json.dumps(w.get('title'), ensure_ascii=False)} [{w.get('class') or '?'} {w.get('exe') or '?'}]"
                      + f" — criteria {json.dumps(c['criteria'], ensure_ascii=False)[:300]}"
                      + f" — object name={json.dumps(o['name'], ensure_ascii=False)} role={o['role']} class={o['className']} id={o['id']} path={o['path']}"
                      + (f" parent={c['parent']!r}" if c['parent'] else '') + (f" shots={c['screenshots']}" if c['screenshots'] else ''))
        for k in e['keystrokes']:
            w = k['window'] or {}
            md.append(f"- line {k['line']}{' [off]' if k['disabled'] else ''} KEYSTROKES to {json.dumps(w.get('title'), ensure_ascii=False)} [{w.get('class') or '?'}]: {json.dumps(k['keys'], ensure_ascii=False)}")
    return cat, '\n'.join(md)


def data(x: Export):
    pd = []
    for b in x.bots:
        calls = []
        for e in x.edges:
            if e['caller'] != b.name:
                continue
            calls.append({'line': e['line'], 'calleeId': e['calleeId'], 'callee': e['callee'], 'calleePath': e['calleePath'], 'disabled': e['disabled'],
                          'continueOnError': e['continueOnError'], 'recordset': None,
                          'inputs': {k: x.V(v, b, k) for k, v in e['inputs'].items()}, 'outputs': {k: x.V(v, b, k) for k, v in e['outputs'].items()}})
        g = b.var_groups()
        pd.append({'id': b.id, 'name': b.name, 'path': b.path, 'folder': b.folder, 'recordset': None,
                   'priority': (b.doc.get('properties') or {}).get('automationPriority'), 'migrationJournalReviewIds': b.doc.get('migrationJournalReviewIds') or [],
                   'inputs': g['in'] + g['inout'], 'outputs': g['out'] + g['inout'],
                   'screenshots': sum(1 for _, _, n, _ in b.lines if n.get('commandName') == 'captureDesktop' and not n.get('disabled')),
                   'logs': sum(1 for _, _, n, _ in b.lines if n.get('commandName') == 'logToFile' and not n.get('disabled')),
                   'calls': calls})
    # Data sources: what the bots read and write outside the UI. Automation 360 has no recordsets; these are the
    # counterpart the step map lists per step.
    src = collections.OrderedDict()

    def add(kind, name, bot, ln, **extra):
        key = f"{kind}|{name}"
        s = src.setdefault(key, {'id': stable_id(key), 'name': name, 'kind': kind, 'usedBy': [], **extra})
        u = f"{bot}:{ln}"
        if u not in s['usedBy']:
            s['usedBy'].append(u)
    for rel, p in x.data_files:
        entry = {'inExport': True, 'path': rel}
        if rel.lower().endswith('.xml'):
            try:
                with open(p, 'rb') as fh:
                    raw = fh.read(1_000_000)  # config files are small; a DTD or entity declaration is not a config file
                if b'<!DOCTYPE' in raw or b'<!ENTITY' in raw:
                    entry['error'] = 'skipped: document carries a DTD or entity declaration'
                else:
                    entry['values'] = {el.tag: (el.text or '').strip() for el in ET.fromstring(raw)}
            except ET.ParseError as e:
                entry['error'] = str(e)
        add('config-file', os.path.basename(rel), '-', 0, **entry)
    for b in x.bots:
        sess_url = {}
        for ln, _, n, _ in b.lines:
            if n.get('disabled'):
                continue
            cmd, pk = n.get('commandName'), n.get('packageName')
            attrs = {a.get('name'): a.get('value') or {} for a in n.get('attributes', [])}
            r = lambda k: json.loads(x.V(attrs.get(k), b, k)) if attrs.get(k) and (attrs[k].get('type') in ('STRING', 'FILE')) else x.V(attrs.get(k), b, k)
            if pk == 'Excel_MS' and cmd in ('OpenSpreadsheet', 'CreateSpreadsheet'):
                add('workbook', r('filePath'), b.name, ln, mode=(attrs.get('fileAccessMode') or {}).get('string'), sheet=(attrs.get('sheetName') or {}).get('string'))
            elif pk == 'Database' and cmd == 'connect':
                url = r('connectionURL')
                sess = ((n.get('returnTo') or {}).get('sessionName') or {}).get('string') or 'Default'
                sess_url[sess] = url
                add('database-connection', url, b.name, ln, session=sess)
            elif pk == 'Database' and cmd in ('sqlQuery', 'insertUpdateDelete'):
                q = r('query')
                sess = ((attrs.get('session') or {}).get('sessionName') or {}).get('string') or 'Default'
                tables = re.findall(r'\[([^\]]+?)\$*\]', q)
                add('database-connection', sess_url.get(sess, f"session {sess}"), b.name, ln)
                key = f"query|{b.name}:{ln}"
                src[key] = {'id': stable_id(key), 'name': q[:200], 'kind': 'query', 'session': sess, 'connection': sess_url.get(sess), 'tables': tables[:6], 'usedBy': [f"{b.name}:{ln}"],
                            'export': (attrs.get('doExport') or {}).get('boolean'), 'exportTo': r('filePath') if attrs.get('filePath') else None}
            elif pk == 'XML' and cmd == 'startSession':
                add('xml-file', r('filePath'), b.name, ln)
            elif pk == 'XML' and cmd == 'getSingleNodeV2':
                add('xml-node', r('xPath'), b.name, ln)
            elif cmd == 'RunScript':
                add('script', r('scriptPath'), b.name, ln)
            elif cmd == 'saveAttachment':
                add('folder', r('folderPath'), b.name, ln, role='attachment download')
            elif cmd == 'moveEmail':
                add('mailbox-folder', f"{r('sourceFolder')} -> {r('destinationfolderPath')}", b.name, ln, filter={'readStatus': (attrs.get('readStatus') or {}).get('string'), 'subject': r('subject'), 'from': r('from')})
            elif cmd == 'emailConnect':
                add('mailbox', f"{(attrs.get('serverType') or {}).get('string')} {(attrs.get('protocol') or {}).get('string') or (attrs.get('exchangeService') or {}).get('string') or ''} {r('serverHost') if attrs.get('serverHost') else ''}".strip(),
                    b.name, ln, account=x.V(attrs.get('ewsUsernameInteractive') or attrs.get('username'), b), auth=(attrs.get('authType') or {}).get('string'), session=r('session'))
            elif cmd == 'logToFile':
                add('log-file', r('filePath'), b.name, ln)
            elif cmd == 'captureDesktop':
                add('screenshot-file', r('filePath'), b.name, ln)
            elif pk in ('File', 'Folder') and cmd in ('createFolder', 'copyFiles', 'deleteFiles', 'renameFiles', 'createFile'):
                for k in ('folderPath', 'sourceFilePath', 'destinationPath', 'filePath'):
                    if attrs.get(k):
                        add('file-operation', f"{cmd} {k}={r(k)}", b.name, ln)
            for a in n.get('attributes', []):
                v = a.get('value') or {}
                if v.get('type') == 'ITERATOR' and 'email' in (v.get('iteratorName') or ''):
                    sub = {s.get('name'): s.get('value') or {} for s in a.get('attributes', [])}
                    add('mailbox-folder', f"read {(sub.get('folder') or {}).get('string') or '?'} ({(sub.get('readStatus') or {}).get('string')})", b.name, ln,
                        filter={'from': x.V(sub.get('from'), b), 'subject': x.V(sub.get('subject'), b)})
                if v.get('type') == 'ITERATOR' and 'files' in (v.get('iteratorName') or ''):
                    sub = {s.get('name'): s.get('value') or {} for s in a.get('attributes', [])}
                    add('folder', json.loads(x.V(sub.get('folderPath'), b)) if sub.get('folderPath') else '?', b.name, ln, role='file loop')
    rs = list(src.values())
    md = ["# Automation 360 data sources (secrets redacted)\n", f"{len(rs)} sources across {len(x.bots)} bots. Kinds: {dict(collections.Counter(s['kind'] for s in rs))}\n"]
    for kind in sorted({s['kind'] for s in rs}):
        md.append(f"\n## {kind}\n")
        for s in rs:
            if s['kind'] != kind:
                continue
            extra = {k: v for k, v in s.items() if k not in ('id', 'name', 'kind', 'usedBy')}
            md.append(f"- ({s['id']}) `{s['name'][:160]}` — used by {', '.join(s['usedBy'][:8])}{' …' if len(s['usedBy']) > 8 else ''}"
                      + (f" — {json.dumps(extra, ensure_ascii=False)[:300]}" if extra else ''))
    return pd, rs, '\n'.join(md)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('command', choices=['profile', 'cards', 'dump', 'targets', 'data'])
    ap.add_argument('export_dir')
    ap.add_argument('bot', nargs='?')
    ap.add_argument('--out', default='.')
    ap.add_argument('--compact', action='store_true', help='dump: fold disabled subtrees, shorten log/delay lines')
    a = ap.parse_args()
    x = Export(a.export_dir)
    if a.command == 'dump':
        if not a.bot:
            ap.error('dump requires BOT (name or repository path)')
        print(dump(x, a.bot, a.compact))
        return 0
    os.makedirs(a.out, exist_ok=True)

    def W(name, content):
        p = os.path.join(a.out, name)
        with open(p, 'w', encoding='utf-8') as fh:
            fh.write(content)
        print(f"written {p}")
    if a.command == 'targets':
        cat, md = targets(x)
        W('a360-targets.json', json.dumps(cat, indent=1, ensure_ascii=False))
        W('a360-targets.md', md)
        return 0
    if a.command == 'data':
        pd, rs, md = data(x)
        W('a360-process-data.json', json.dumps(pd, indent=1, ensure_ascii=False))
        W('a360-data-sources.json', json.dumps(rs, indent=1, ensure_ascii=False))
        W('a360-data-sources.md', md)
        return 0
    text = profile(x) if a.command == 'profile' else cards(x)
    W(f'a360-{a.command}.txt', text)
    return 0


if __name__ == '__main__':
    sys.exit(main())
