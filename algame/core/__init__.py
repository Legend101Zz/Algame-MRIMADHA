
"""
Core backtesting engine module.

This module provides the foundational components for:
1. Engine management and execution
2. Data handling and processing
3. Configuration management
4. Performance analysis

The core module is designed to be:
- Modular: Components are loosely coupled
- Extensible: Easy to add new functionality
- Configurable: Highly customizable behavior
- Reliable: Robust error handling and validation

Key Components:
--------------
Engine System:
    - Multiple engine support (custom, backtesting.py)
    - Parallel execution
    - Performance optimization

Data Management:
    - Multiple data sources
    - Data validation
    - Efficient caching
    - Real-time support

Configuration:
    - Comprehensive settings
    - Configuration validation
    - Save/load support
    - Templates and defaults

Example usage:
    >>> from algame.core import Backtest, Strategy
    >>> from algame.core.config import BacktestConfig
    >>>
    >>> # Create configuration
    >>> config = BacktestConfig(
    ...     name="My Backtest",
    ...     symbols=["AAPL", "GOOGL"]
    ... )
    >>>
    >>> # Create and run backtest
    >>> bt = Backtest(config)
    >>> results = bt.run(MyStrategy)
"""

from typing import Dict, Any
import logging
import platform
import sys

# Setup logging
logger = logging.getLogger(__name__)

# Version information
__version__ = "0.1.0"
__author__ = "Mrigesh Thakur"
__license__ = "MIT"

# Platform information
PLATFORM_INFO = {
    'python': sys.version,
    'platform': platform.platform(),
    'machine': platform.machine()
}

# Import core components
from .engine import (
    Backtest,
    Strategy,
    Position,
    Order,
    Trade
)

from .data import (
    DataManager,
    DataSource,
    MarketData
)

from .config import (
    ConfigManager,
    BacktestConfig,
    EngineConfig,
    StrategyConfig
)

# Feature flags and capabilities
FEATURES = {
    'parallel_execution': True,
    'real_time_data': True,
    'gpu_acceleration': False,
    'live_trading': False,
    'optimization': True,
    'multi_asset': True,
    'caching': True
}

# Default settings
DEFAULTS = {
    'engine': 'custom',
    'data_source': 'yahoo',
    'timeframe': '1d',
    'cache_dir': '~/.algame/cache',
    'max_workers': None  # Auto-detect
}

# Configuration validation settings
VALIDATION = {
    'strict_mode': True,
    'validate_data': True,
    'validate_config': True,
    'validate_results': True
}

class AlGameCore:
    """
    Core system configuration and management.

    This class provides central configuration and management of:
    - Feature flags
    - System settings
    - Component initialization
    - Resource management
    """

    def __init__(self, **settings):
        """
        Initialize core system.

        Args:
            **settings: Override default settings
        """
        self.settings = {**DEFAULTS, **settings}
        self.features = FEATURES.copy()
        self.validation = VALIDATION.copy()

        # Initialize managers
        self._init_managers()

        logger.info(f"Initialized AlGame Core v{__version__}")

    def _init_managers(self):
        """Initialize system managers."""
        # Create config manager
        self.config_manager = ConfigManager(
            config_dir=self.settings['cache_dir']
        )

        # Create data manager
        self.data_manager = DataManager(
            data_dir=self.settings['cache_dir'],
            max_workers=self.settings['max_workers']
        )

        # Register default data sources
        self._register_data_sources()

    def _register_data_sources(self):
        """Register default data sources."""
        from .data.sources import (
            YahooDataSource,
            CSVDataSource,
            IBKRDataSource
        )

        # Register built-in sources
        sources = {
            'yahoo': YahooDataSource,
            'csv': CSVDataSource,
            'ibkr': IBKRDataSource
        }

        for name, source_class in sources.items():
            try:
                self.data_manager.register_source(name, source_class)
                logger.debug(f"Registered data source: {name}")
            except Exception as e:
                logger.warning(f"Failed to register {name}: {str(e)}")

    def create_backtest(self,
                       config: Union[str, Dict, BacktestConfig],
                       **kwargs) -> 'Backtest':
        """
        Create backtest instance.

        Args:
            config: Backtest configuration
            **kwargs: Additional settings

        Returns:
            Backtest: Configured backtest instance
        """
        # Load config if string
        if isinstance(config, str):
            config = self.config_manager.load_config(config)
        # Create config if dict
        elif isinstance(config, dict):
            config = BacktestConfig(**config)

        # Create backtest
        return Backtest(config, **kwargs)

    def optimize_strategy(self,
                        strategy: Type[Strategy],
                        param_grid: Dict[str, Any],
                        **kwargs) -> Dict[str, Any]:
        """
        Optimize strategy parameters.

        Args:
            strategy: Strategy to optimize
            param_grid: Parameter ranges
            **kwargs: Additional settings

        Returns:
            Dict[str, Any]: Optimization results
        """
        # Create optimizer
        from .optimization import Optimizer
        optimizer = Optimizer(**kwargs)

        # Run optimization
        return optimizer.optimize(strategy, param_grid)

    def validate_strategy(self,
                        strategy: Type[Strategy],
                        **kwargs) -> Dict[str, Any]:
        """
        Validate trading strategy.

        Args:
            strategy: Strategy to validate
            **kwargs: Validation settings

        Returns:
            Dict[str, Any]: Validation results
        """
        # Create validator
        from .validation import StrategyValidator
        validator = StrategyValidator(**kwargs)

        # Run validation
        return validator.validate(strategy)

    @property
    def version(self) -> str:
        """Get version information."""
        return __version__

    @property
    def platform_info(self) -> Dict[str, str]:
        """Get platform information."""
        return PLATFORM_INFO.copy()

    def enable_feature(self, feature: str) -> None:
        """Enable system feature."""
        if feature not in self.features:
            raise ValueError(f"Unknown feature: {feature}")
        self.features[feature] = True
        logger.info(f"Enabled feature: {feature}")

    def disable_feature(self, feature: str) -> None:
        """Disable system feature."""
        if feature not in self.features:
            raise ValueError(f"Unknown feature: {feature}")
        self.features[feature] = False
        logger.info(f"Disabled feature: {feature}")

    def is_feature_enabled(self, feature: str) -> bool:
        """Check if feature is enabled."""
        return self.features.get(feature, False)

    def enable_strict_mode(self) -> None:
        """Enable strict validation mode."""
        self.validation['strict_mode'] = True
        logger.info("Enabled strict validation mode")

    def disable_strict_mode(self) -> None:
        """Disable strict validation mode."""
        self.validation['strict_mode'] = False
        logger.info("Disabled strict validation mode")

# Create global instance
core = AlGameCore()

# Export components
__all__ = [
    # Core classes
    'Backtest',
    'Strategy',
    'Position',
    'Order',
    'Trade',

    # Managers
    'DataManager',
    'DataSource',
    'MarketData',
    'ConfigManager',

    # Configuration
    'BacktestConfig',
    'EngineConfig',
    'StrategyConfig',

    # Global instance
    'core',

    # Version
    '__version__',
    '__author__',
    '__license__'
]
