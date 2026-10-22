"""Agent-based competitive diffusion model (network Bass model, several brands).

Every consumer agent is either undecided (-1) or has adopted one brand
(0..n_brands-1). At each step an undecided agent is exposed to

* external influence (advertising) with probability ``p[b]`` per brand, and
* word-of-mouth from every neighbour who already uses brand ``b``, each
  contact converting it with probability ``q``.

If several brands "fire" in the same step, the agent picks one of them
with probability proportional to the brand's hazard. Adoption is
permanent (no churn), so market shares are monotone in time.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy import sparse

UNDECIDED = -1


@dataclass
class ModelConfig:
    n_agents: int = 500
    m: int = 3
    n_brands: int = 3
    steps: int = 40
    p: tuple[float, ...] = (0.004, 0.004, 0.004)  # advertising (innovation) coefficients
    q: float = 0.03  # word-of-mouth (imitation) coefficient per adopting neighbour
    seed_agents: dict[int, list[int]] = field(default_factory=dict)  # brand -> agents seeded at t=0
    p_boost: dict[int, float] = field(default_factory=dict)  # brand -> extra advertising pressure

    def validate(self) -> None:
        if len(self.p) != self.n_brands:
            raise ValueError("len(p) must equal n_brands")
        if not all(0.0 <= x <= 1.0 for x in self.p) or not 0.0 <= self.q <= 1.0:
            raise ValueError("probabilities must lie in [0, 1]")
        if self.steps < 1:
            raise ValueError("steps must be >= 1")


class MarketModel:
    def __init__(self, adj: sparse.csr_matrix, config: ModelConfig, rng: np.random.Generator):
        config.validate()
        if adj.shape[0] != config.n_agents:
            raise ValueError("adjacency size does not match n_agents")
        self.adj = adj
        self.cfg = config
        self.rng = rng
        self.state = np.full(config.n_agents, UNDECIDED, dtype=np.int8)
        for brand, agents in config.seed_agents.items():
            self.state[np.asarray(agents, dtype=int)] = brand
        self.p = np.array(config.p, dtype=float)
        for brand, extra in config.p_boost.items():
            self.p[brand] = min(1.0, self.p[brand] + extra)
        self.history: list[np.ndarray] = [self.shares()]

    def shares(self) -> np.ndarray:
        counts = np.bincount(self.state[self.state >= 0], minlength=self.cfg.n_brands)
        return counts / self.cfg.n_agents

    def step(self) -> None:
        n, b = self.cfg.n_agents, self.cfg.n_brands
        onehot = np.zeros((n, b))
        adopted = self.state >= 0
        onehot[np.where(adopted)[0], self.state[adopted]] = 1.0
        neigh = self.adj @ onehot  # neighbours using each brand
        hazard = 1.0 - (1.0 - self.p) * (1.0 - self.cfg.q) ** neigh  # shape (n, b)
        fired = self.rng.random((n, b)) < hazard
        candidates = np.where((~adopted) & fired.any(axis=1))[0]
        if candidates.size:
            w = hazard[candidates] * fired[candidates]
            w /= w.sum(axis=1, keepdims=True)
            u = self.rng.random(candidates.size)[:, None]
            choice = (u > np.cumsum(w, axis=1)).sum(axis=1)
            self.state[candidates] = choice
        self.history.append(self.shares())

    def run(self) -> np.ndarray:
        for _ in range(self.cfg.steps):
            self.step()
        return np.vstack(self.history)
