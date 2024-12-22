"""
AlGame-MRIMADHA - Algorithmic Trading Framework
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

AlGame is a flexible backtesting framework supporting multiple assets,
timeframes and engines with an easy-to-use GUI interface.

Basic usage:
    >>> from algame import Backtester
    >>> from algame.strategies import SMACrossover
    >>>
    >>> # Create backtester
    >>> bt = Backtester()
    >>>
    >>> # Run backtest
    >>> results = bt.run(
    ...     strategy=SMACrossover,
    ...     symbols=['AAPL', 'GOOGL'],
    ...     start='2020-01-01'
    ... )
    >>>
    >>> # Show results
    >>> results.plot()
"""

__version__ = '0.1.0'

from .core.engine import EngineManager
from .core.engine.interface import (
    BacktestResult,
    OptimizationResult,
    EngineConfig
)

# Create default engine manager
_engine_manager = EngineManager()

class Backtester:
    """
    Main interface for running backtests.

    This class provides a simplified interface to the engine system.
    Most users should use this rather than working with engines directly.
    """

    def __init__(self, engine: str = None, **config):
        """
        Initialize backtester.

        Args:
            engine: Engine to use ('custom' or 'backtesting.py')
            **config: Engine configuration parameters
        """
        self._manager = EngineManager()
        if engine:
            self._manager.set_engine(engine)

        # Update configuration
        if config:
            self._manager.config = EngineConfig(**config)

    def run(self,
            strategy: Any,
            data: Union[str, pd.DataFrame, Dict[str, pd.DataFrame]],
            parameters: Dict[str, Any] = None,
            **kwargs) -> BacktestResult:
        """
        Run backtest.

        Args:
            strategy: Strategy to test
            data: Market data (symbol, DataFrame, or dict of DataFrames)
            parameters: Strategy parameters
            **kwargs: Additional parameters

        Returns:
            BacktestResult: Backtest results
        """
        # Load data if string provided
        if isinstance(data, str):
            from .data import load_data
            data = load_data(data, **kwargs)

        return self._manager.run_backtest(strategy, data, parameters)

    def optimize(self,
                strategy: Any,
                data: Union[str, pd.DataFrame],
                parameter_space: Dict[str, List[Any]],
                **kwargs) -> OptimizationResult:
        """
        Optimize strategy parameters.

        Args:
            strategy: Strategy to optimize
            data: Market data
            parameter_space: Parameter ranges to test
            **kwargs: Additional optimization parameters

        Returns:
            OptimizationResult: Optimization results
        """
        if isinstance(data, str):
            from .data import load_data
            data = load_data(data, **kwargs)

        return self._manager.optimize_strategy(
            strategy,
            data,
            parameter_space,
            **kwargs
        )
