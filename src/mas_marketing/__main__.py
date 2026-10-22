"""Command-line entry point: ``python -m mas_marketing --scenario S2 --runs 30``."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from .experiment import SCENARIOS, run_paired_experiment
from .model import ModelConfig


def parse_args(argv=None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Multi-agent simulation of marketing situations")
    ap.add_argument("--scenario", nargs="+", default=["S1", "S2", "S3"], choices=sorted(SCENARIOS))
    ap.add_argument("--runs", type=int, default=30)
    ap.add_argument("--agents", type=int, default=500)
    ap.add_argument("--steps", type=int, default=40)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", type=Path, default=Path("results"))
    return ap.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    base = ModelConfig(n_agents=args.agents, steps=args.steps)
    summary = []
    for code in args.scenario:
        res = run_paired_experiment(code, runs=args.runs, base=base, seed=args.seed)
        with open(args.out / f"{code}_runs.csv", "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["run", "treatment_share", "control_share"])
            for i, (t, c) in enumerate(zip(res["treatment"], res["control"]), 1):
                w.writerow([i, f"{t:.4f}", f"{c:.4f}"])
        row = {k: v for k, v in res.items() if k not in ("treatment", "control")}
        summary.append(row)
        print(f"{code}: delta={row['delta_pp']:+.2f} p.p.  t={row['t_stat']:.2f}  "
              f"p={row['p_value']:.4g}  -> {'significant' if row['significant_0_05'] else 'n.s.'}")
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
