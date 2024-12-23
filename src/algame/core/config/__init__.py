"""
Configuration management module.

This module handles:
1. Strategy configurations
2. Engine settings
3. Configuration persistence
4. Parameter validation
"""

from .types import BacktestConfig, StrategyConfig, EngineConfig
from .manager import ConfigManager

# Default configurations
DEFAULT_BACKTEST_CONFIG = {
    'name': 'Default Backtest',
    'description': 'Default backtest configuration',
    'engine': {
        'initial_capital': 100000,
        'commission': 0.001,
        'slippage': 0.0001
    },
    'strategy': {
        'name': 'Default Strategy'
    }
}

DEFAULT_ENGINE_CONFIG = {
    'initial_capital': 100000,
    'commission': 0.001,
    'slippage': 0.0001,
    'position_limit': 1.0,
    'enable_fractional': False,
    'lot_size': 1.0
}

DEFAULT_STRATEGY_CONFIG = {
    'name': 'Default Strategy',
    'version': '1.0.0',
    'parameters': {},
    'trading_hours': {
        'start': '09:30',
        'end': '16:00'
    },
    'trading_days': [0, 1, 2, 3, 4]  # Monday to Friday
}

__all__ = [
    # Classes
    'BacktestConfig',
    'StrategyConfig',
    'EngineConfig',
    'ConfigManager',

    # Default configurations
    'DEFAULT_BACKTEST_CONFIG',
    'DEFAULT_ENGINE_CONFIG',
    'DEFAULT_STRATEGY_CONFIG'
]
