#!/usr/bin/env python3
"""Report accuracy, run-to-run stability and paraphrase invariance for a
strategy-selection run.

Accuracy alone hides two failure strategies this eval exists to catch:

  stability  — the same prompt answered differently on different runs
  invariance — the same workload answered differently when reworded

A row can sit at 60% accuracy because the model is genuinely uncertain, or
because it is stable-but-wrong. Those need different fixes, and only the
per-replicate breakdown tells them apart.

Usage:
    python3 analyze_consistency.py <RUN_DIR> [--jsonl strategy_selection.jsonl]

<RUN_DIR> is a coder-eval run directory. The script walks it for per-replicate
strategy.txt artifacts; it does not care about the surrounding layout, only that a
replicate directory contains one.
"""
import argparse
import collections
import json
import pathlib
import re
import sys

# Share the contract with the checker rather than reimplementing it — two parsers
# for one format will drift, and the drift shows up as a mysterious disagreement
# between this report and the gate.
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from check_strategy import KEY, STRATEGY_ANSWERS  # noqa: E402

STRATEGIES = ("AH", "AF", "CS", "SU", "PS", "EX", "BT")


def read_answer(path):
    """The strategy from the first non-empty line, or None. Only the first line is
    read, matching check_strategy.py."""
    try:
        lines = [l for l in path.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()]
    except OSError:
        return None
    if not lines:
        return None
    m = KEY.match(lines[0])
    token = m.group(1).upper() if m else ""
    return token if token in STRATEGY_ANSWERS else None


REPLICATE = re.compile(r"^\d{2}$")


def collect(run_dir):
    """row id -> [strategy per replicate]. A replicate that produced no usable
    artifact is recorded as None rather than dropped — a row that
    fails to answer is not the same as a row that answers wrongly.

    The real layout is
        <run>/<variant>/<task>/<row>/<NN>/artifacts/<task>/<row>/routing.txt
    so neither the parent nor the grandparent of routing.txt is the row id. The
    stable landmark is the two-digit replicate directory: its parent is the row.
    `strategy.txt` is still read so pre-migration run directories remain
    comparable."""
    out = collections.defaultdict(list)
    for name in ("routing.txt", "strategy.txt"):   # strategy.txt: pre-rename runs
        for p in sorted(pathlib.Path(run_dir).rglob(name)):
            rep = next((a for a in p.parents if REPLICATE.match(a.name)), None)
            if rep is None:
                continue
            out[rep.parent.name].append(read_answer(p))
    return out


def modal(values):
    real = [v for v in values if v]
    if not real:
        return None
    return collections.Counter(real).most_common(1)[0][0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--jsonl", default=str(pathlib.Path(__file__).with_name("strategy_selection.jsonl")))
    args = ap.parse_args()

    spec = {}
    for line in open(args.jsonl, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            spec[r["id"]] = r
            # Tolerated if a row ever carries one: run directories named with an
            # older id still match instead of dropping out of the denominator.
            if r.get("legacy_id"):
                spec[r["legacy_id"]] = r

    observed = collect(args.run_dir)
    if not observed:
        sys.exit(f"no routing.txt or strategy.txt artifacts found under {args.run_dir}")

    matched = {k: v for k, v in observed.items() if k in spec}
    if not matched:
        sys.exit(
            f"found {len(observed)} artifact dirs but none matched a row id in {args.jsonl}. "
            f"Sample dir name: {next(iter(observed))!r}"
        )

    reps = max(len(v) for v in matched.values())
    # spec may alias a row under more than one id, so len(spec) can overcount.
    n_rows = len({id(r) for r in spec.values()})
    print(f"{len(matched)} of {n_rows} rows observed · up to {reps} replicate(s)\n")

    # ---- accuracy + stability, per row
    unstable, wrong = [], []
    per_mode = collections.defaultdict(lambda: [0, 0])
    for rid, seen in sorted(matched.items()):
        want = spec[rid]["expected_strategy"]
        got = modal(seen)
        # Agreement is computed over replicates that actually answered. Dividing by
        # len(seen) counted unanswered replicates as agreeing with each other: when
        # every replicate failed to produce an artifact, seen is [None, None, ...],
        # modal returns None, None == None holds for each, and the row reported 100%
        # agreement and never appeared as unstable — a total failure read as perfect
        # stability.
        answered = [t for t in seen if t is not None]
        agree = (sum(1 for t in answered if t == got) / len(answered)) if answered else 0.0
        per_mode[want][1] += 1
        if got == want:
            per_mode[want][0] += 1
        else:
            wrong.append((rid, want, got, seen))
        if agree < 1.0 or len(answered) < len(seen):
            unstable.append((rid, agree, seen, len(answered), len(seen)))

    print("accuracy by strategy (modal answer vs ground truth)")
    for m in STRATEGIES:
        if per_mode[m][1]:
            ok, n = per_mode[m]
            print(f"  {m:5} {ok}/{n}")
    tot_ok = sum(v[0] for v in per_mode.values())
    tot_n = sum(v[1] for v in per_mode.values())
    print(f"  {'ALL':5} {tot_ok}/{tot_n}  ({tot_ok/tot_n:.0%})\n")

    # ---- paraphrase invariance, per pair
    pairs = collections.defaultdict(dict)
    for rid, seen in matched.items():
        row = spec[rid]
        if "pair" in row:
            pairs[row["pair"]][row["variant"]] = (modal(seen), row["expected_strategy"])

    complete = {k: v for k, v in pairs.items() if {"a", "b"} <= set(v)}
    flipped = [(k, v["a"][0], v["b"][0], v["a"][1]) for k, v in complete.items() if v["a"][0] != v["b"][0]]
    print(f"paraphrase invariance — pairs answered differently when reworded: "
          f"{len(flipped)}/{len(complete)}")
    for k, a, b, want in flipped:
        print(f"  {k:34} a={a} b={b}  (expected {want})")
    if complete and not flipped:
        print("  none — every workload got the same strategy under both phrasings")

    # A flip where one side is correct is the most actionable signal in the run:
    # the routing copy works for one framing of the workload and not the other.
    half = [f for f in flipped if want_correct(f)]
    if half:
        print(f"\n  of those, {len(half)} had one phrasing correct and the other wrong — "
              "the routing signal is phrasing-dependent, not absent:")
        for k, a, b, want in half:
            print(f"    {k:32} expected {want}, got a={a} b={b}")

    print()
    if wrong:
        print(f"wrong (modal answer != ground truth): {len(wrong)}")
        for rid, want, got, seen in wrong:
            print(f"  {rid:34} expected {want:5} got {got}  {seen}")
    return 0


def want_correct(f):
    _, a, b, want = f
    return (a == want) != (b == want)


if __name__ == "__main__":
    sys.exit(main())
