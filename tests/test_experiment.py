import json

import pytest

from mas_marketing.__main__ import main
from mas_marketing.experiment import run_paired_experiment
from mas_marketing.model import ModelConfig

SMALL = ModelConfig(n_agents=150, steps=20)


@pytest.mark.parametrize("code", ["S1", "S2", "S3"])
def test_experiment_output_schema(code):
    res = run_paired_experiment(code, runs=5, base=SMALL, seed=1)
    assert res["runs"] == 5 and len(res["treatment"]) == 5
    assert 0.0 <= res["p_value"] <= 1.0
    assert abs(res["delta_pp"] - 100 * (res["treatment_mean_share"] - res["control_mean_share"])) < 1e-9


def test_experiment_is_reproducible():
    a = run_paired_experiment("S2", runs=4, base=SMALL, seed=123)
    b = run_paired_experiment("S2", runs=4, base=SMALL, seed=123)
    assert a == b


def test_hub_seeding_beats_random_seeding():
    res = run_paired_experiment("S2", runs=20, base=ModelConfig(n_agents=300, steps=30), seed=7)
    assert res["delta_pp"] > 0


def test_unknown_scenario():
    with pytest.raises(KeyError):
        run_paired_experiment("S9", runs=3, base=SMALL)


def test_too_few_runs():
    with pytest.raises(ValueError):
        run_paired_experiment("S2", runs=1, base=SMALL)


def test_cli_writes_results(tmp_path):
    rc = main(["--scenario", "S2", "--runs", "3", "--agents", "120", "--steps", "10", "--out", str(tmp_path)])
    assert rc == 0
    summary = json.loads((tmp_path / "summary.json").read_text())
    assert summary[0]["scenario"] == "S2"
    lines = (tmp_path / "S2_runs.csv").read_text().strip().splitlines()
    assert len(lines) == 4
