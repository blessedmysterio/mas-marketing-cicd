import numpy as np
import pytest

from mas_marketing.model import UNDECIDED, MarketModel, ModelConfig
from mas_marketing.network import build_network


def make(cfg=None, seed=0):
    cfg = cfg or ModelConfig(n_agents=200, steps=20)
    adj = build_network(cfg.n_agents, cfg.m, seed=seed)
    return MarketModel(adj, cfg, np.random.default_rng(seed))


def test_shares_are_valid_probabilities():
    hist = make().run()
    assert hist.shape == (21, 3)
    assert np.all(hist >= 0)
    assert np.all(hist.sum(axis=1) <= 1.0 + 1e-12)


def test_adoption_is_monotone():
    hist = make().run()
    assert np.all(np.diff(hist.sum(axis=1)) >= 0)


def test_seeded_agents_start_adopted():
    cfg = ModelConfig(n_agents=200, steps=5, seed_agents={0: [1, 2, 3]})
    model = make(cfg)
    assert list(model.state[[1, 2, 3]]) == [0, 0, 0]
    assert (model.state == UNDECIDED).sum() == 197


def test_same_seed_same_result():
    a = make(seed=9).run()
    b = make(seed=9).run()
    np.testing.assert_array_equal(a, b)


def test_no_influence_means_no_adoption():
    cfg = ModelConfig(n_agents=100, steps=30, p=(0.0, 0.0, 0.0), q=0.0)
    assert make(cfg).run()[-1].sum() == 0


def test_word_of_mouth_spreads_from_seed():
    cfg = ModelConfig(n_agents=200, steps=40, p=(0.0, 0.0, 0.0), q=0.2, seed_agents={1: [0]})
    final = make(cfg).run()[-1]
    assert final[1] > 0.5 and final[0] == 0 and final[2] == 0


def test_advertising_boost_increases_share():
    base = ModelConfig(n_agents=300, steps=30)
    boosted = ModelConfig(n_agents=300, steps=30, p_boost={0: 0.05})
    assert make(boosted, seed=4).run()[-1, 0] > make(base, seed=4).run()[-1, 0]


def test_invalid_config_rejected():
    with pytest.raises(ValueError):
        make(ModelConfig(n_agents=50, p=(0.1, 0.1)))
