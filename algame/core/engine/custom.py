# algame/core/engine/custom.py

from typing import Dict, Any, List, Optional, Union
import pandas as pd
import numpy as np
from datetime import datetime
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import logging

from .interface import (
    BacktestEngineInterface,
    BacktestResult,
    OptimizationResult,
    TradeStats,
    EngineConfig
)

logger = logging.getLogger(__name__)

class Position:
    """
    Represents an open position.

    This class tracks:
    - Position size and direction
    - Entry price and time
    - Stop loss and take profit levels
    - Unrealized P&L
    """

    def __init__(self,
                 size: float,
                 entry_price: float,
                 entry_time: datetime,
                 stop_loss: Optional[float] = None,
                 take_profit: Optional[float] = None):
        self.size = size  # Positive for long, negative for short
        self.entry_price = entry_price
        self.entry_time = entry_time
        self.stop_loss = stop_loss
        self.take_profit = take_profit

    def update(self, current_price: float) -> None:
        """Update position with new price."""
        self.unrealized_pnl = (current_price - self.entry_price) * self.size

    def should_exit(self, current_price: float) -> bool:
        """Check if position should be closed."""
        if self.stop_loss and self.size > 0:
            if current_price <= self.stop_loss:
                return True
        elif self.stop_loss and self.size < 0:
            if current_price >= self.stop_loss:
                return True

        if self.take_profit and self.size > 0:
            if current_price >= self.take_profit:
                return True
        elif self.take_profit and self.size < 0:
            if current_price <= self.take_profit:
                return True

        return False

class AssetProcessor:
    """
    Processes single asset data.

    This class handles:
    - Data preprocessing
    - Signal generation
    - Position management
    - Trade execution
    - Performance tracking
    """

    def __init__(self,
                 symbol: str,
                 data: pd.DataFrame,
                 strategy: Any,
                 config: EngineConfig):
        self.symbol = symbol
        self.data = data
        self.strategy = strategy
        self.config = config

        # Initialize tracking
        self.position: Optional[Position] = None
        self.equity = [config.initial_capital]
        self.trades: List[TradeStats] = []

    def run(self) -> Dict[str, Any]:
        """Run backtest for this asset."""
        try:
            # Initialize strategy
            self.strategy.initialize(self.data)

            # Process each bar
            for i in range(len(self.data)):
                self._process_bar(i)

            # Close any open position
            if self.position:
                self._close_position(
                    self.data.iloc[-1]['Close'],
                    self.data.index[-1]
                )

            return {
                'symbol': self.symbol,
                'equity': pd.Series(self.equity, index=self.data.index),
                'trades': self.trades
            }

        except Exception as e:
            logger.error(f"Error processing {self.symbol}: {str(e)}")
            raise

    def _process_bar(self, index: int) -> None:
        """Process single price bar."""
        current_bar = self.data.iloc[index]

        # Update position if exists
        if self.position:
            self.position.update(current_bar['Close'])

            # Check stops
            if self.position.should_exit(current_bar['Close']):
                self._close_position(current_bar['Close'], current_bar.name)

        # Get strategy signals
        try:
            signals = self.strategy.next(self.data.iloc[:index+1])
            if signals:
                self._process_signals(signals, current_bar)
        except Exception as e:
            logger.error(f"Error getting signals for {self.symbol}: {str(e)}")

        # Update equity
        self.equity.append(self._calculate_equity(current_bar['Close']))

    def _process_signals(self,
                        signals: List[Dict[str, Any]],
                        current_bar: pd.Series) -> None:
        """Process trading signals."""
        for signal in signals:
            action = signal.get('action')

            if action == 'buy':
                if self.position and signal.get('close_existing', True):
                    self._close_position(current_bar['Close'], current_bar.name)
                self._open_long(
                    size=signal.get('size', 1.0),
                    price=current_bar['Close'],
                    time=current_bar.name,
                    stop_loss=signal.get('stop_loss'),
                    take_profit=signal.get('take_profit')
                )

            elif action == 'sell':
                if self.position and signal.get('close_existing', True):
                    self._close_position(current_bar['Close'], current_bar.name)
                self._open_short(
                    size=signal.get('size', 1.0),
                    price=current_bar['Close'],
                    time=current_bar.name,
                    stop_loss=signal.get('stop_loss'),
                    take_profit=signal.get('take_profit')
                )

            elif action == 'close':
                if self.position:
                    self._close_position(current_bar['Close'], current_bar.name)

    def _open_long(self,
                   size: float,
                   price: float,
                   time: datetime,
                   stop_loss: Optional[float] = None,
                   take_profit: Optional[float] = None) -> None:
        """Open long position."""
        self.position = Position(
            size=size,
            entry_price=price,
            entry_time=time,
            stop_loss=stop_loss,
            take_profit=take_profit
        )

    def _open_short(self,
                    size: float,
                    price: float,
                    time: datetime,
                    stop_loss: Optional[float] = None,
                    take_profit: Optional[float] = None) -> None:
        """Open short position."""
        self.position = Position(
            size=-size,
            entry_price=price,
            entry_time=time,
            stop_loss=stop_loss,
            take_profit=take_profit
        )

    def _close_position(self,
                       price: float,
                       time: datetime) -> None:
        """Close current position."""
        if self.position:
            # Calculate trade statistics
            pnl = (price - self.position.entry_price) * self.position.size
            return_pct = (price / self.position.entry_price - 1) * 100

            # Record trade
            self.trades.append(
                TradeStats(
                    entry_time=self.position.entry_time,
                    exit_time=time,
                    entry_price=self.position.entry_price,
                    exit_price=price,
                    size=self.position.size,
                    pnl=pnl,
                    return_pct=return_pct,
                    fees=self._calculate_fees(price, self.position.size)
                )
            )

            self.position = None

    def _calculate_equity(self, current_price: float) -> float:
        """Calculate current equity."""
        equity = self.equity[-1]
        if self.position:
            equity += self.position.unrealized_pnl
        return equity

    def _calculate_fees(self, price: float, size: float) -> float:
        """Calculate trading fees."""
        return abs(price * size * self.config.commission)

class CustomEngine(BacktestEngineInterface):
    """
    Custom parallel backtesting engine.

    Features:
    - Multi-asset support
    - Parallel processing
    - Advanced risk management
    - Detailed performance tracking
    """

    def __init__(self, config: EngineConfig = None):
        super().__init__(config)
        self._workers = mp.cpu_count()

    def set_data(self,
                 data: Union[pd.DataFrame, Dict[str, pd.DataFrame]],
                 validate: bool = True) -> None:
        """Set data for backtesting."""
        if validate:
            self.validate_data(data)

        # Convert single dataframe to dict
        if isinstance(data, pd.DataFrame):
            data = {'default': data}

        self._data = data

    def run_backtest(self,
                    strategy: Any,
                    parameters: Dict[str, Any] = None) -> BacktestResult:
        """Run parallel backtest."""
        parameters = parameters or {}

        # Create processors for each asset
        processors = [
            AssetProcessor(symbol, data, strategy(parameters), self.config)
            for symbol, data in self._data.items()
        ]

        # Run processors in parallel
        with ProcessPoolExecutor(max_workers=self._workers) as executor:
            results = list(executor.map(lambda p: p.run(), processors))

        # Combine results
        combined_results = self._combine_results(results)

        return combined_results

    def optimize_strategy(self,
                        strategy: Any,
                        parameter_space: Dict[str, List[Any]],
                        metric: str = 'sharpe_ratio',
                        method: str = 'grid',
                        max_evals: Optional[int] = None,
                        constraints: Optional[List[Dict]] = None) -> OptimizationResult:
        """Run parallel optimization."""
        # Generate parameter combinations
        param_combos = self._generate_param_combos(
            parameter_space,
            method,
            max_evals,
            constraints
        )

        # Run backtests in parallel
        results = []
        with ProcessPoolExecutor(max_workers=self._workers) as executor:
            futures = []
            for params in param_combos:
                future = executor.submit(
                    self.run_backtest,
                    strategy,
                    params
                )
                futures.append((params, future))

            # Collect results
            for params, future in futures:
                try:
                    result = future.result()
                    results.append({
                        'parameters': params,
                        'metrics': result.metrics,
                        'value': result.metrics[metric]
                    })
                except Exception as e:
                    logger.error(f"Optimization error with params {params}: {str(e)}")

        # Find best result
        best = max(results, key=lambda x: x['value'])

        return OptimizationResult(
            best_params=best['parameters'],
            best_metrics=best['metrics'],
            all_results=pd.DataFrame(results),
            param_importance=self._calculate_param_importance(results),
            optimization_path=results
        )

    def _combine_results(self,
                        results: List[Dict[str, Any]]) -> BacktestResult:
        """Combine results from multiple assets."""
        # Combine equity curves
        equity = pd.concat([r['equity'] for r in results], axis=1)
        total_equity = equity.sum(axis=1)

        # Combine trades
        all_trades = []
        for r in results:
            all_trades.extend(r['trades'])

        # Sort trades by time
        all_trades.sort(key=lambda x: x.entry_time)

        return BacktestResult(
            equity_curve=total_equity,
            trades=all_trades,
            positions=pd.DataFrame([vars(t) for t in all_trades]),
            metrics=self.calculate_metrics(total_equity, all_trades),
            drawdowns=self._calculate_drawdowns(total_equity),
            returns=total_equity.pct_change(),
            exposure=self._calculate_exposure(all_trades),
            start_date=total_equity.index[0],
            end_date=total_equity.index[-1],
            config=self.config
        )

    def _calculate_drawdowns(self, equity: pd.Series) -> pd.Series:
        """Calculate drawdown series."""
        peak = equity.expanding().max()
        drawdown = (equity - peak) / peak * 100
        return drawdown

    def _calculate_exposure(self, trades: List[TradeStats]) -> float:
        """Calculate market exposure percentage."""
        if not trades:
            return 0.0

        total_time = (trades[-1].exit_time - trades[0].entry_time).total_seconds()
        exposure_time = sum(
            (t.exit_time - t.entry_time).total_seconds()
            for t in trades
        )
        return exposure_time / total_time

    def _generate_param_combos(self,
                             parameter_space: Dict[str, List[Any]],
                             method: str,
                             max_evals: Optional[int],
                             constraints: Optional[List[Dict]]) -> List[Dict[str, Any]]:
        """Generate parameter combinations for optimization."""
        if method == 'grid':
            # Generate grid of parameters
            import itertools
            keys = parameter_space.keys()
            values = parameter_space.values()
            combinations = list(itertools.product(*values))

            # Apply constraints
            if constraints:
                combinations = [
                    combo for combo in combinations
                    if all(self._check_constraint(dict(zip(keys, combo)), c)
                          for c in constraints)
                ]

            # Limit evaluations
            if max_evals and len(combinations) > max_evals:
                import random
                combinations = random.sample(combinations, max_evals)

            return [dict(zip(keys, combo)) for combo in combinations]

        elif method == 'random':
            # Random search
            import random
            combinations = []
            while len(combinations) < (max_evals or 100):
                combo = {
                    key: random.choice(values)
                    for key, values in parameter_space.items()
                }
                if not constraints or all(self._check_constraint(combo, c) for c in constraints):
                    combinations.append(combo)
            return combinations

        else:
            raise ValueError(f"Unsupported optimization method: {method}")

    def _check_constraint(self, params: Dict[str, Any], constraint: Dict) -> bool:
        """Check if parameters satisfy constraint."""
        operator = constraint['operator']
        left = self._evaluate_expression(constraint['left'], params)
        right = self._evaluate_expression(constraint['right'], params)

        if operator == '>':
            return left > right
        elif operator == '<':
            return left < right
        elif operator == '>=':
            return left >= right
        elif operator == '<=':
            return left <= right
        elif operator == '==':
            return left == right
        else:
            raise ValueError(f"Unsupported operator: {operator}")

    def _evaluate_expression(self, expr: Union[str, float], params: Dict[str, Any]) -> float:
        """Evaluate parameter expression."""
        if isinstance(expr, (int, float)):
            return float(expr)
        return float(params[expr])

    def _calculate_param_importance(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate parameter importance scores."""
        if not results:
            return {}

        # Convert results to DataFrame
        import pandas as pd
        df = pd.DataFrame([
            {**r['parameters'], 'value': r['value']}
            for r in results
        ])

        # Calculate correlation with performance
        importance = {}
        for param in df.columns:
            if param != 'value':
                correlation = df[param].corr(df['value'])
                importance[param] = abs(correlation)

        # Normalize to percentages
        total = sum(importance.values())
        if total > 0:
            importance = {k: v/total * 100 for k, v in importance.items()}

        return importance
