"""Detailed token-usage + cost breakdown using SDK-reported numbers."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def per_replicate(rep_dir: Path) -> dict:
    data = json.loads((rep_dir / "task.json").read_text(encoding="utf-8"))
    ttu = data.get("total_token_usage", {}) or {}

    turns = data.get("turns", []) or []
    return {
        "rep": rep_dir.name,
        "score": data.get("weighted_score"),
        "duration_s": round(data.get("duration_seconds", 0), 1),
        "fresh": ttu.get("input_tokens", 0),
        "cache_c": ttu.get("cache_creation_input_tokens", 0),
        "cache_r": ttu.get("cache_read_input_tokens", 0),
        "out": ttu.get("output_tokens", 0),
        "cost": ttu.get("total_cost_usd", 0) or 0,
        "turns": len(turns),
    }


def main(run_dir_arg: str) -> int:
    run_dir = Path(run_dir_arg)
    rep_dirs = sorted([d for d in run_dir.iterdir() if d.is_dir() and d.name.isdigit()])
    results = [per_replicate(r) for r in rep_dirs]

    print(f"Token usage for {run_dir}\n")

    # Column legend:
    #   "NEW"     — input that costs full (or near-full) price = cache_create + uncached
    #               (cache_create is ~1.25x fresh rate; uncached is 1.0x fresh rate)
    #   "REUSED"  — input served from the prompt cache (cache_read_input_tokens),
    #               billed at ~0.1x fresh rate -- effectively "free" relative to NEW.
    #   "out"     — model-generated output (parent + sub-agents).
    # The bill is dominated by NEW + Output. REUSED is the cheap leg of the cost.
    print(f"{'rep':>3} {'sc':>4} {'sec':>6} | {'NEW':>7} {'(uncached/cached)':>19} {'REUSED':>10} {'out':>6} | {'$cost':>6}")
    print("-" * 80)
    sums = {"fresh": 0, "cache_c": 0, "cache_r": 0, "out": 0, "cost": 0.0, "dur": 0.0}
    for r in results:
        new_in = r["fresh"] + r["cache_c"]
        breakdown = f"({r['fresh']:>3,}/{r['cache_c']:>7,})"
        print(
            f"{r['rep']:>3} "
            f"{(r['score'] or 0):>4.2f} "
            f"{r['duration_s']:>6} | "
            f"{new_in:>7,} "
            f"{breakdown:>19} "
            f"{r['cache_r']:>10,} "
            f"{r['out']:>6,} | "
            f"{r['cost']:>5.3f}"
        )
        sums["fresh"] += r["fresh"]
        sums["cache_c"] += r["cache_c"]
        sums["cache_r"] += r["cache_r"]
        sums["out"] += r["out"]
        sums["cost"] += r["cost"]
        sums["dur"] += r["duration_s"]

    n = len(results)
    in_total_all = sums["fresh"] + sums["cache_c"] + sums["cache_r"]
    new_total = sums["fresh"] + sums["cache_c"]
    print("-" * 80)
    print(
        f"{'sum':>3} {'':>4} {sums['dur']:>6.1f} | "
        f"{new_total:>7,} ({sums['fresh']:>3,}/{sums['cache_c']:>7,}) "
        f"{sums['cache_r']:>10,} {sums['out']:>6,} | "
        f"{sums['cost']:>5.2f}"
    )
    if n:
        avg_new = new_total // n
        avg_fresh = sums['fresh'] // n
        avg_cc = sums['cache_c'] // n
        print(
            f"{'avg':>3} {'':>4} {sums['dur']/n:>6.1f} | "
            f"{avg_new:>7,} ({avg_fresh:>3,}/{avg_cc:>7,}) "
            f"{sums['cache_r']//n:>10,} {sums['out']//n:>6,} | "
            f"{sums['cost']/n:>5.3f}"
        )

    if not in_total_all:
        return 0

    print("\n=== Cost-driving tokens (NEW input + Output) ===")
    print(f"  NEW input (full price)   : {new_total:>10,}  -- this is what you actually pay full rate for")
    print(f"      uncached fresh tail  : {sums['fresh']:>10,}  ({100*sums['fresh']/new_total:>5.2f}% of NEW)  -- 1.0x fresh rate")
    print(f"      new->cache write     : {sums['cache_c']:>10,}  ({100*sums['cache_c']/new_total:>5.2f}% of NEW)  -- 1.25x fresh rate")
    print(f"  Output                   : {sums['out']:>10,}  -- billed at output rate (5x fresh)")
    print()
    print(f"  REUSED input (discounted): {sums['cache_r']:>10,}  -- 0.1x fresh rate; effectively the 'free' leg")
    print()
    print(f"Per-replicate avg of cost-driving content (NEW + Output):")
    print(f"  NEW input  : {new_total//n:>6,} tokens/rep")
    print(f"  Output     : {sums['out']//n:>6,} tokens/rep")
    print(f"  Sum        : {(new_total + sums['out'])//n:>6,} tokens/rep at full-or-output rate")

    print("\nDerived ratios:")
    if sums["out"]:
        print(f"  input  / output (in:out) : {in_total_all // sums['out']}:1")
    if sums["cache_c"]:
        print(f"  reads-per-cache-write    : {sums['cache_r'] / sums['cache_c']:.1f}x   (how many turns reuse each cache entry)")

    print(f"\nSDK-reported cost: ${sums['cost']:.2f} for {n} replicate(s)  =  ${sums['cost']/n:.3f}/rep")
    print("  These figures come straight from total_token_usage.total_cost_usd written by the Anthropic SDK")
    print("  and account for parent + all sub-agent inference. They are the authoritative cost.")

    # Per-rep variance
    if n > 1:
        costs = [r["cost"] for r in results]
        in_tot = [r["fresh"] + r["cache_c"] + r["cache_r"] for r in results]
        print(f"\nPer-rep variance:")
        print(f"  cost      min={min(costs):.3f}  max={max(costs):.3f}  range={max(costs)-min(costs):.3f}")
        print(f"  cache_r   min={min(r['cache_r'] for r in results):,}  max={max(r['cache_r'] for r in results):,}")
        print(f"  in_total  min={min(in_tot):,}  max={max(in_tot):,}")

    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python tmp/token_usage.py <run_dir>/default/<task_id>", file=sys.stderr)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
