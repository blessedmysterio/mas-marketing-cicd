"""Multi-agent simulation of marketing situations on scale-free consumer networks."""

from .model import MarketModel, ModelConfig
from .network import build_network, top_hubs
from .experiment import SCENARIOS, run_paired_experiment

__all__ = [
    "MarketModel",
    "ModelConfig",
    "build_network",
    "top_hubs",
    "SCENARIOS",
    "run_paired_experiment",
]
__version__ = "1.0.0"
