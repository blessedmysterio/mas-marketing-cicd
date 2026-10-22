"""Paired-run marketing experiments (common random numbers + paired t-test)."""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np
from scipy import stats

from .model import MarketModel, ModelConfig
from .network import build_network, top_hubs

FOCAL = 0  # brand A receives the intervention


@dataclass(frozen=True)
class Scenario:
    code: str
    title: str
    budget: int = 10  # number of seeded agents (or its advertising equivalent)


SCENARIOS = {
    "S1": Scenario("S1", "Price war: A and B both raise advertising pressure vs. status quo"),
    "S2": Scenario("S2", "Hub seeding vs. random seeding of brand A"),
    "S3": Scenario("S3", "Hub seeding vs. mass advertising of equal budget"),
}


def _arms(code: str, adj, base: ModelConfig, budget: int, rng: np.random.Generator):
    """Return (treatment_config, control_config) for a scenario."""
    n = base.n_agents
    if code == "S1":
        boost = {0: 0.004, 1: 0.004}
        return replace(base, p_boost=boost), base
    if code == "S2":
        hubs = top_hubs(adj, budget).tolist()
        rand = rng.choice(n, size=budget, replace=False).tolist()
        return replace(base, seed_agents={FOCAL: hubs}), replace(base, seed_agents={FOCAL: rand})
    if code == "S3":
        hubs = top_hubs(adj, budget).tolist()
        mass_boost = budget / (n * base.steps)  # same expected number of "touches"
        return replace(base, seed_agents={FOCAL: hubs}), replace(base, p_boost={FOCAL: mass_boost})
    raise KeyError(f"unknown scenario {code!r}; choose from {sorted(SCENARIOS)}")


def run_paired_experiment(code: str, runs: int = 30, base: ModelConfig | None = None, seed: int = 42) -> dict:
    """Run ``runs`` paired replications of a scenario.

    Each replication builds one network and runs treatment and control with
    the same random stream (common random numbers), so the difference in the
    focal brand's final share isolates the intervention effect.
    """
    if runs < 2:
        raise ValueError("runs must be >= 2 for a paired t-test")
    base = base or ModelConfig()
    scen = SCENARIOS[code] if code in SCENARIOS else None
    budget = scen.budget if scen else 10
    master = np.random.default_rng(seed)
    treat, ctrl = [], []
    for _ in range(runs):
        run_seed = int(master.integers(0, 2**31 - 1))
        adj = build_network(base.n_agents, base.m, seed=run_seed)
        cfg_t, cfg_c = _arms(code, adj, base, budget, np.random.default_rng(run_seed + 1))
        treat.append(MarketModel(adj, cfg_t, np.random.default_rng(run_seed + 2)).run()[-1, FOCAL])
        ctrl.append(MarketModel(adj, cfg_c, np.random.default_rng(run_seed + 2)).run()[-1, FOCAL])
    treat_a, ctrl_a = np.array(treat), np.array(ctrl)
    diff = treat_a - ctrl_a
    t_stat, p_val = stats.ttest_rel(treat_a, ctrl_a)
    if np.isnan(t_stat):  # identical arms
        t_stat, p_val = 0.0, 1.0
    return {
        "scenario": code,
        "title": SCENARIOS[code].title,
        "runs": runs,
        "treatment_mean_share": float(treat_a.mean()),
        "control_mean_share": float(ctrl_a.mean()),
        "delta_pp": float(diff.mean() * 100),
        "t_stat": float(t_stat),
        "p_value": float(p_val),
        "significant_0_05": bool(p_val < 0.05),
        "treatment": treat_a.tolist(),
        "control": ctrl_a.tolist(),
    }
