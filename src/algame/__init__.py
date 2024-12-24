"""
Algame: Algorithmic Trading Framework
===================================

Core Modules:
- strategy: Strategy development and management
- core: Core backtesting engine and utilities
- gui: Graphical user interface components
- tools: Utility tools and helpers
- analysis: Analysis and metrics
"""

__version__ = '0.1.0'

# Core components
from .core import (
    EngineManager,
    BacktestConfig,
    EngineConfig,
    MarketData
)

# Strategy components
from .strategy import (
    StrategyBase,
    Position,
    Order,
    Trade,
    TrendStrategy,
    MeanReversionStrategy,
    BreakoutStrategy
)

# GUI components
from .gui import (
    GUI,
    MainWindow,
    Chart,
    OptimizerPanel,
    DataPanel,
    StrategyPanel,
    ResultsPanel,
    ConverterPanel,
    app
)

# Analysis components
from .analysis import (
    PerformanceMetrics,
    RiskAnalysis,
    OptimizationAnalysis
)

# Tools and utilities
from .tools import (
    PineScriptConverter,
    convert_strategy
)

# Public API
__all__ = [
    # Core
    'EngineManager',
    'BacktestConfig',
    'EngineConfig',
    'MarketData',

    # Strategy
    'StrategyBase',
    'Position',
    'Order',
    'Trade',
    'TrendStrategy',
    'MeanReversionStrategy',
    'BreakoutStrategy',

    # GUI
    'GUI',
    'MainWindow',
    'Chart',
    'OptimizerPanel',
    'DataPanel',
    'StrategyPanel',
    'ResultsPanel',
    'ConverterPanel',
    'app',

    # Analysis
    'PerformanceMetrics',
    'RiskAnalysis',
    'OptimizationAnalysis',

    # Tools
    'PineScriptConverter',
    'convert_strategy',

    # Version
    '__version__'
]

# Make the default engine instance available
from .core import core
default_engine = core