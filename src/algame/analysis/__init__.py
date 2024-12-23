"""
Analysis module for performance metrics and risk analysis.

This module provides tools for:
1. Performance measurement
2. Risk analysis
3. Portfolio optimization
4. Report generation
"""

from .analysis import (
    PerformanceMetrics,
    RiskAnalysis,
    OptimizationAnalysis,
    analyze_strategy
)

# Supported metrics
PERFORMANCE_METRICS = [
    'total_return',
    'annual_return',
    'sharpe_ratio',
    'sortino_ratio',
    'max_drawdown',
    'avg_drawdown',
    'volatility',
    'win_rate',
    'profit_factor',
    'avg_trade',
    'max_consecutive_losses',
    'var_95',
    'var_99'
]

RISK_METRICS = [
    'volatility',
    'max_drawdown',
    'var',
    'expected_shortfall',
    'beta',
    'correlation',
    'tail_ratio'
]

TRADE_METRICS = [
    'win_rate',
    'profit_factor',
    'avg_win',
    'avg_loss',
    'largest_win',
    'largest_loss',
    'avg_duration',
    'max_drawdown'
]

# Report templates
REPORT_TEMPLATES = {
    'basic': [
        'total_return',
        'sharpe_ratio',
        'max_drawdown',
        'win_rate'
    ],
    'extended': PERFORMANCE_METRICS,
    'risk': RISK_METRICS,
    'trades': TRADE_METRICS
}

__all__ = [
    # Classes
    'PerformanceMetrics',
    'RiskAnalysis',
    'OptimizationAnalysis',

    # Functions
    'analyze_strategy',

    # Metrics lists
    'PERFORMANCE_METRICS',
    'RISK_METRICS',
    'TRADE_METRICS',

    # Report templates
    'REPORT_TEMPLATES'
]

# Version
__version__ = "0.1.0"

# Default settings
DEFAULT_RISK_FREE_RATE = 0.02  # 2% annual risk-free rate
DEFAULT_REQUIRED_RETURN = 0.10  # 10% required annual return
