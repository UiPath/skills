#!/usr/bin/env python3
"""Report accuracy, run-to-run stability and paraphrase invariance for a
mode-selection run.

Accuracy alone hides two failure modes this eval exists to catch:

  stability  — the same prompt answered differently on different runs
  invariance — the same workload answered differently when reworded

A row can sit at 60% accuracy because the model is genuinely uncertain, or
because it is stable-but-wrong. Those need different fixes, and only the
per-replicate breakdown tells them apart.

Usage:
    python3 analyze_consistency.py <RUN_DIR> [--jsonl mode_selection.jsonl]

<RUN_DIR> is a coder-eval run directory. The script walks it for per-replicate
mode.txt artifacts; it does not care about the surrounding layout, only that a
replicate directory contains one.
"""
import argparse
import collections
import json
import pathlib
import re
import sys

MODES = ("AH", "AF", "CS", "SU", "PS", "PA", "EX", "BT", "NONE")


def read_mode(path):
    try:
        first = path.read_text(encoding="utf-8", errors="replace").strip().splitlines()[0]
    except (OSError, IndexError):
        return None
    token = re.sub(r"[^A-Za-z]", "", first).upper()
    return token if token in MODES else None


REPLICATE = re.compile(r"^\d{2}$")


def collect(run_dir):
    """row id -> [mode per replicate]. A replicate that produced no usable
    mode.txt is recorded as None rather than dropped — a row that fails to
    answer is not the same as a row that answers wrongly.

    The real layout is
        <run>/<variant>/<task>/<row>/<NN>/artifacts/<task>/<row>/mode.txt
    so neither the parent nor the grandparent of mode.txt is the row id. The
    stable landmark is the two-digit replicate directory: its parent is the
    row. Anchoring on that survives changes to how the sandbox is preserved
    underneath it."""
    out = collections.defaultdict(list)
    for p in sorted(pathlib.Path(run_dir).rglob("mode.txt")):
        rep = next((a for a in p.parents if REPLICATE.match(a.name)), None)
        if rep is None:
            continue
        out[rep.parent.name].append(read_mode(p))
    return out


def modal(values):
    real = [v for v in values if v]
    if not real:
        return None
    return collections.Counter(real).most_common(1)[0][0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--jsonl", default=str(pathlib.Path(__file__).with_name("mode_selection.jsonl")))
    args = ap.parse_args()

    spec = {}
    for line in open(args.jsonl, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            spec[r["id"]] = r

    observed = collect(args.run_dir)
    if not observed:
        sys.exit(f"no mode.txt artifacts found under {args.run_dir}")

    matched = {k: v for k, v in observed.items() if k in spec}
    if not matched:
        sys.exit(
            f"found {len(observed)} artifact dirs but none matched a row id in {args.jsonl}. "
            f"Sample dir name: {next(iter(observed))!r}"
        )

    reps = max(len(v) for v in matched.values())
    print(f"{len(matched)} of {len(spec)} rows observed · up to {reps} replicate(s)\n")

    # ---- accuracy + stability, per row
    unstable, wrong = [], []
    per_mode = collections.defaultdict(lambda: [0, 0])
    for rid, seen in sorted(matched.items()):
        want = spec[rid]["expected_mode"]
        got = modal(seen)
        agree = sum(1 for s in seen if s == got) / len(seen) if seen else 0
        per_mode[want][1] += 1
        if got == want:
            per_mode[want][0] += 1
        else:
            wrong.append((rid, want, got, seen))
        if agree < 1.0:
            unstable.append((rid, agree, seen))

    print("accuracy by mode (modal answer vs ground truth)")
    for m in MODES:
        if per_mode[m][1]:
            ok, n = per_mode[m]
            print(f"  {m:5} {ok}/{n}")
    tot_ok = sum(v[0] for v in per_mode.values())
    tot_n = sum(v[1] for v in per_mode.values())
    print(f"  {'ALL':5} {tot_ok}/{tot_n}  ({tot_ok/tot_n:.0%})\n")

    if reps > 1:
        print(f"stability — rows whose replicates disagreed: {len(unstable)}/{len(matched)}")
        for rid, agree, seen in unstable:
            print(f"  {rid:34} {agree:.0%} agreement  {seen}")
        if not unstable:
            print("  none — every row answered identically across replicates")
        print()
    else:
        print("stability — not measurable at 1 replicate; rerun with --repeats N (N>=3)\n")

    # ---- paraphrase invariance, per pair
    pairs = collections.defaultdict(dict)
    for rid, seen in matched.items():
        s = spec[rid]
        if "pair" in s:
            pairs[s["pair"]][s["variant"]] = (modal(seen), s["expected_mode"])

    complete = {k: v for k, v in pairs.items() if {"a", "b"} <= set(v)}
    flipped = [(k, v["a"][0], v["b"][0], v["a"][1]) for k, v in complete.items() if v["a"][0] != v["b"][0]]
    print(f"paraphrase invariance — pairs answered differently when reworded: "
          f"{len(flipped)}/{len(complete)}")
    for k, a, b, want in flipped:
        print(f"  {k:34} a={a} b={b}  (expected {want})")
    if complete and not flipped:
        print("  none — every workload got the same mode under both phrasings")

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
