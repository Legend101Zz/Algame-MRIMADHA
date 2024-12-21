"""
Strategy module for Algame framework.

This module provides a complete strategy development framework:
1. Base Strategy Interface
2. Pre-built Templates
3. Technical Indicators
4. Strategy Builder
5. Validation Tools

Module Structure:
    base.py: Core strategy classes and interfaces
    templates/: Ready-to-use strategy templates
    builder/: GUI-based strategy construction
    indicators/: Technical analysis indicators
    validator.py: Strategy validation tools

Usage Examples:
    # Using base strategy
    from algame.strategy import Strategy

    class MyStrategy(Strategy):
        def initialize(self):
            self.sma = self.add_indicator('SMA', self.data.Close, 20)

    # Using template
    from algame.strategy.templates import TrendStrategy

    class MyTrend(TrendStrategy):
        def __init__(self):
            super().__init__({'period': 20})

    # Using builder
    from algame.strategy.builder import StrategyBuilder

    builder = StrategyBuilder()
    MyStrategy = builder.build()
"""

# Version info
__version__ = '0.1.0'

# Import core components
from .base import (
    StrategyBase,
    Position,
    Order,
    Trade
)

# Import template components
from .template import (
    TrendStrategy,
    MeanReversionStrategy,
    BreakoutStrategy,
)

# Import builder components
from .builder import (
    StrategyBuilder,
    RuleBuilder,
    IndicatorBuilder,
    StrategyEditor
)

# Import indicator components
from .indicators import (
    Indicator,
    SMA,
    EMA,
    RSI,
    MACD,
    Bollinger,
    ATR,
    register_indicator
)

# Import validation
from .validator import (
    StrategyValidator,
    ValidationReport,
    validate_strategy
)

# Default strategy configuration
DEFAULT_CONFIG = {
    'initial_capital': 100000,
    'commission': 0.001,
    'slippage': 0.0001,
    'position_size': 1.0
}

# Strategy registry
_strategy_registry = {}

def register_strategy(name: str, strategy_class: type) -> None:
    """Register strategy class."""
    global _strategy_registry
    _strategy_registry[name] = strategy_class

def get_strategy(name: str) -> type:
    """Get registered strategy class."""
    if name not in _strategy_registry:
        raise ValueError(f"Strategy not found: {name}")
    return _strategy_registry[name]

def list_strategies() -> list:
    """Get list of registered strategies."""
    return list(_strategy_registry.keys())

# Export public interface
__all__ = [
    # Base classes
    'StrategyBase',
    'Position',
    'Order',
    'Trade',

    # Templates
    'TrendStrategy',
    'MeanReversionStrategy',
    'BreakoutStrategy',


    # Builder
    'StrategyBuilder',
    'RuleBuilder',
    'IndicatorBuilder',
    'StrategyEditor',

    # Indicators
    'Indicator',
    'SMA',
    'EMA',
    'RSI',
    'MACD',
    'Bollinger',
    'ATR',
    'register_indicator',

    # Validation
    'StrategyValidator',
    'ValidationReport',
    'validate_strategy',

    # Registration
    'register_strategy',
    'get_strategy',
    'list_strategies',

    # Version
    '__version__'
]
