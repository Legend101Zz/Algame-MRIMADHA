from typing import Dict, Any, List, Union,Optional
import pandas as pd
from datetime import datetime
from backtesting import Backtest
from backtesting import Strategy as BaseStrategy

from .interface import (
    BacktestEngineInterface,
    BacktestResult,
    OptimizationResult,
    TradeStats,
    EngineConfig
)

class StrategyAdapter(BaseStrategy):
    """
    Adapter class to convert AlGame strategies to backtesting.py format.

    This adapter translates between our strategy interface and backtesting.py's
    requirements. It handles:
    1. Strategy initialization
    2. Parameter management
    3. Signal generation
    4. Position management

    The adapter pattern allows us to use backtesting.py without modifying
    our core strategy interface.
    """

    def __init__(self, broker, data, params):
        super().__init__(broker, data, params)
        # Store original strategy instance
        strategy_class = params.pop('_strategy_class')
        self._strategy = strategy_class(params)

    def init(self):
        """Initialize strategy (backtesting.py requirement)."""
        # Initialize original strategy
        self._strategy.initialize(self.data.df)

        # Register indicators
        for name, indicator in self._strategy.indicators.items():
            setattr(self, name, self.I(lambda x: indicator, name=name))

    def next(self):
        """Generate trading signals (backtesting.py requirement)."""
        # Get current data slice
        current_data = self.data.df.iloc[:len(self.data)]

        # Get signals from original strategy
        signals = self._strategy.next(current_data)

        # Process signals
        if signals:
            for signal in signals:
                self._process_signal(signal)

    def _process_signal(self, signal: Dict[str, Any]):
        """Process trading signal from original strategy."""
        action = signal.get('action')
        if action == 'buy':
            if signal.get('close_existing', True):
                self.position.close()
            size = signal.get('size', 1.0)
            stop_loss = signal.get('stop_loss')
            take_profit = signal.get('take_profit')
            self.buy(size=size, sl=stop_loss, tp=take_profit)

        elif action == 'sell':
            if signal.get('close_existing', True):
                self.position.close()
            size = signal.get('size', 1.0)
            stop_loss = signal.get('stop_loss')
            take_profit = signal.get('take_profit')
            self.sell(size=size, sl=stop_loss, tp=take_profit)

        elif action == 'close':
            self.position.close()

class BacktestingPyEngine(BacktestEngineInterface):
    """
    Adapter for backtesting.py library.

    This engine implements our interface using backtesting.py as the
    underlying execution engine. It provides:
    1. Data validation
    2. Strategy adaptation
    3. Results conversion
    4. Optimization support
    """

    def __init__(self, config: Optional[EngineConfig] = None):
        """Initialize engine with config."""
        super().__init__(config)
        self._backtest = None

    def set_data(self,
                 data: Union[pd.DataFrame, Dict[str, pd.DataFrame]],
                 validate: bool = True):
        """Set data for backtesting."""
        if validate:
            self.validate_data(data)

        # backtesting.py only supports single asset
        if isinstance(data, dict):
            if len(data) > 1:
                raise ValueError("backtesting.py engine only supports single asset")
            data = next(iter(data.values()))

        self._data = data

    def run_backtest(self,
                    strategy: Any,
                    parameters: Dict[str, Any] = None) -> BacktestResult:
        """Run backtest using backtesting.py."""
        parameters = parameters or {}

        # Add strategy class to parameters
        parameters['_strategy_class'] = strategy

        # Create backtesting.py Backtest instance
        self._backtest = Backtest(
            self._data,
            StrategyAdapter,
            cash=self.config.initial_capital,
            commission=self.config.commission,
            margin=1/self.config.margin_requirement,
            trade_on_close=self.config.trade_on_close,
            hedging=self.config.hedging,
        )

        # Run backtest
        results = self._backtest.run(**parameters)

        # Convert results to our format
        return self._convert_results(results)

    def optimize_strategy(self,
                        strategy: Any,
                        parameter_space: Dict[str, List[Any]],
                        metric: str = 'sharpe_ratio',
                        method: str = 'grid',
                        max_evals: int = None,
                        constraints: List[Dict] = None) -> OptimizationResult:
        """Run optimization using backtesting.py."""
        if self._backtest is None:
            raise ValueError("Must run backtest before optimization")

        # Add strategy class to parameters
        parameter_space['_strategy_class'] = [strategy]

        # Run optimization
        results = self._backtest.optimize(
            maximize=metric,
            method=method,
            max_tries=max_evals,
            constraint=constraints,
            **parameter_space
        )

        # Convert results to our format
        return self._convert_optimization_results(results)

    def _convert_results(self, results) -> BacktestResult:
        """Convert backtesting.py results to our format."""
        # Convert trades
        trades = []
        for t in results._trades:
            trades.append(TradeStats(
                entry_time=t.entry_time,
                exit_time=t.exit_time,
                entry_price=t.entry_price,
                exit_price=t.exit_price,
                size=t.size,
                pnl=t.pl,
                return_pct=t.pl_pct,
                bars_held=t.bars,
                tag=t.tag
            ))

        # Create result
        return BacktestResult(
            equity_curve=results._equity_curve['Equity'],
            trades=trades,
            positions=pd.DataFrame(results._trades),
            metrics=results._stats,
            drawdowns=results._equity_curve['DrawdownPct'],
            returns=results._equity_curve['Equity'].pct_change(),
            exposure=results._stats['Exposure Time [%]'] / 100,
            start_date=results._equity_curve.index[0],
            end_date=results._equity_curve.index[-1],
            config=self.config
        )

    def _convert_optimization_results(self, results) -> OptimizationResult:
        """Convert backtesting.py optimization results to our format."""
        return OptimizationResult(
            best_params=results._strategy.params,
            best_metrics=results._stats,
            all_results=pd.DataFrame(results._heatmap),
            param_importance={},  # Not provided by backtesting.py
            optimization_path=[]   # Not provided by backtesting.py
        )

    def validate_data(self, data: Union[pd.DataFrame, Dict[str, pd.DataFrame]]) -> bool:
        """Validate data format for backtesting.py."""
        if isinstance(data, dict):
            if len(data) > 1:
                raise ValueError("backtesting.py engine only supports single asset")
            data = next(iter(data.values()))

        required_cols = ['Open', 'High', 'Low', 'Close']
        if not all(col in data.columns for col in required_cols):
            raise ValueError(f"Data must contain columns: {required_cols}")

        if not isinstance(data.index, pd.DatetimeIndex):
            raise ValueError("Data index must be DatetimeIndex")

        return True
