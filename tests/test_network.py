import numpy as np
import pytest

from mas_marketing.network import build_network, degrees, top_hubs


def test_network_size_and_edges():
    n, m = 200, 3
    adj = build_network(n, m, seed=1)
    assert adj.shape == (n, n)
    # Barabási–Albert graph has m * (n - m) undirected edges
    assert adj.nnz // 2 == m * (n - m)


def test_network_is_symmetric_without_self_loops():
    adj = build_network(100, 2, seed=3)
    assert (adj != adj.T).nnz == 0
    assert adj.diagonal().sum() == 0


def test_network_is_reproducible():
    a = build_network(150, 3, seed=7)
    b = build_network(150, 3, seed=7)
    assert (a != b).nnz == 0


def test_scale_free_has_hubs():
    adj = build_network(500, 3, seed=11)
    deg = degrees(adj)
    assert deg.max() > 5 * np.median(deg)


def test_top_hubs_are_highest_degree():
    adj = build_network(300, 3, seed=5)
    deg = degrees(adj)
    hubs = top_hubs(adj, 10)
    assert len(set(hubs)) == 10
    assert deg[hubs].min() >= np.sort(deg)[-10]


@pytest.mark.parametrize("n,m", [(3, 3), (10, 0)])
def test_invalid_parameters(n, m):
    with pytest.raises(ValueError):
        build_network(n, m)
