"""Core engine system providing backtesting capabilities."""

from .interface import (
    BacktestEngineInterface,
    BacktestResult,
    OptimizationResult,
    TradeStats,
    EngineConfig
)
from .manager import EngineManager
from .registry import EngineRegistry
from .algame_engine import CustomEngine
from .backtesting_py import BacktestingPyEngine

__all__ = [
    'BacktestEngineInterface',
    'BacktestResult',
    'OptimizationResult',
    'TradeStats',
    'EngineConfig',
    'EngineManager',
    'EngineRegistry',
    'CustomEngine',
    'BacktestingPyEngine'
]

# Create global registry
registry = EngineRegistry()

# Register built-in engines
registry.register('custom', CustomEngine, make_default=True)
registry.register('backtesting.py', BacktestingPyEngine)
