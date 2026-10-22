"""Consumer social network generation (Barabási–Albert scale-free graph)."""

from __future__ import annotations

import networkx as nx
import numpy as np
from scipy import sparse


def build_network(n_agents: int = 500, m: int = 3, seed: int | None = None) -> sparse.csr_matrix:
    """Return the adjacency matrix of a Barabási–Albert network.

    Each new node attaches to ``m`` existing nodes with probability
    proportional to their degree, which yields the heavy-tailed degree
    distribution (a few "hubs") typical of real social networks.
    """
    if n_agents <= m:
        raise ValueError("n_agents must be greater than m")
    if m < 1:
        raise ValueError("m must be >= 1")
    graph = nx.barabasi_albert_graph(n_agents, m, seed=seed)
    return nx.to_scipy_sparse_array(graph, format="csr", dtype=np.int8).tocsr()


def degrees(adj: sparse.csr_matrix) -> np.ndarray:
    """Degree of every node."""
    return np.asarray(adj.sum(axis=1)).ravel().astype(int)


def top_hubs(adj: sparse.csr_matrix, k: int) -> np.ndarray:
    """Indices of the ``k`` highest-degree nodes (ties broken by index)."""
    deg = degrees(adj)
    order = np.lexsort((np.arange(deg.size), -deg))
    return order[:k]
