# algame/core/engine/interface.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Union, Any, Tuple
import pandas as pd
import numpy as np

@dataclass
class EngineConfig:
    """
    Configuration for backtest engine.

    This class encapsulates all settings needed to run a backtest,
    ensuring consistent configuration across different engines.

    Attributes:
        initial_capital (float): Starting capital for backtest
        commission (float): Commission rate as decimal (e.g., 0.001 for 0.1%)
        margin_requirement (float): Required margin as ratio (e.g., 0.1 for 10x leverage)
        trade_on_close (bool): Whether to execute trades at bar close (True) or next bar open (False)
        hedging (bool): Whether to allow simultaneous long/short positions
        slippage (float): Slippage rate as decimal
        lot_size (float): Minimum trade size
        position_limit (float): Maximum position size as ratio of capital
        enable_fractional (bool): Whether to allow fractional position sizes
    """
    initial_capital: float = 100_000
    commission: float = 0.001
    margin_requirement: float = 1.0
    trade_on_close: bool = False
    hedging: bool = False
    slippage: float = 0.0
    lot_size: float = 1.0
    position_limit: float = 1.0
    enable_fractional: bool = False

@dataclass
class TradeStats:
    """
    Statistics for a single trade.

    Provides detailed metrics for trade analysis and performance tracking.

    Attributes:
        entry_time (datetime): Trade entry timestamp
        exit_time (Optional[datetime]): Trade exit timestamp (None if open)
        entry_price (float): Entry price
        exit_price (Optional[float]): Exit price (None if open)
        size (float): Position size (positive for long, negative for short)
        pnl (float): Realized profit/loss
        return_pct (float): Return percentage
        bars_held (int): Number of bars position was held
        fees (float): Total fees/commissions paid
        slippage (float): Total slippage cost
        mae (float): Maximum adverse excursion
        mfe (float): Maximum favorable excursion
        tag (Optional[str]): Custom trade tag/label
    """
    entry_time: datetime
    entry_price: float
    size: float
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    pnl: float = 0.0
    return_pct: float = 0.0
    bars_held: int = 0
    fees: float = 0.0
    slippage: float = 0.0
    mae: float = 0.0
    mfe: float = 0.0
    tag: Optional[str] = None

@dataclass
class BacktestResult:
    """
    Complete backtest results.

    Provides comprehensive results data for analysis and reporting.

    Attributes:
        equity_curve (pd.Series): Equity curve over time
        trades (List[TradeStats]): List of all trades
        positions (pd.DataFrame): Historical positions
        metrics (Dict[str, float]): Performance metrics
        drawdowns (pd.Series): Drawdown series
        returns (pd.Series): Return series
        exposure (float): Time in market percentage
        start_date (datetime): Backtest start date
        end_date (datetime): Backtest end date
        config (EngineConfig): Engine configuration used
    """
    equity_curve: pd.Series
    trades: List[TradeStats]
    positions: pd.DataFrame
    metrics: Dict[str, float]
    drawdowns: pd.Series
    returns: pd.Series
    exposure: float
    start_date: datetime
    end_date: datetime
    config: EngineConfig

@dataclass
class OptimizationResult:
    """
    Strategy optimization results.

    Contains optimization results and parameter analysis.

    Attributes:
        best_params (Dict[str, Any]): Best parameters found
        best_metrics (Dict[str, float]): Metrics with best parameters
        all_results (pd.DataFrame): Results for all parameter combinations
        param_importance (Dict[str, float]): Parameter importance scores
        optimization_path (List[Dict]): Optimization algorithm path
    """
    best_params: Dict[str, Any]
    best_metrics: Dict[str, float]
    all_results: pd.DataFrame
    param_importance: Dict[str, float]
    optimization_path: List[Dict]

class BacktestEngineInterface(ABC):
    """
    Abstract base class for backtest engines.

    This interface defines the standard contract that all backtest engines must implement.
    It ensures consistent behavior across different engine implementations while allowing
    for engine-specific optimizations and features.

    Key aspects:
    1. Data handling - Standardized data format and validation
    2. Strategy execution - Common strategy lifecycle management
    3. Position tracking - Consistent position and risk management
    4. Results generation - Standardized metrics and analysis

    Implementing classes should focus on optimizing the actual backtesting logic
    while maintaining this consistent interface.
    """

    @abstractmethod
    def __init__(self, config: Optional[EngineConfig] = None):
        """
        Initialize backtest engine.

        Args:
            config: Engine configuration. If None, uses default settings.
        """
        self.config = config or EngineConfig()

        # Initialize tracking variables
        self._data = None
        self._position = 0
        self._equity = self.config.initial_capital
        self._trades = []

    @abstractmethod
    def set_data(self,
                 data: Union[pd.DataFrame, Dict[str, pd.DataFrame]],
                 validate: bool = True) -> None:
        """
        Set data for backtesting.

        The engine supports both single-asset and multi-asset backtesting.
        For single asset, pass a DataFrame with OHLCV data.
        For multiple assets, pass a dict of DataFrames keyed by symbol.

        Args:
            data: Market data for backtesting
            validate: Whether to validate data format and quality

        Raises:
            ValueError: If data format is invalid
        """
        pass

    @abstractmethod
    def run_backtest(self,
                    strategy: Any,
                    parameters: Dict[str, Any] ) -> BacktestResult:
        """
        Run backtest with given strategy and parameters.

        This is the main entry point for running a backtest. It:
        1. Validates inputs and configuration
        2. Initializes strategy with parameters
        3. Runs strategy over historical data
        4. Tracks positions and equity
        5. Generates comprehensive results

        Args:
            strategy: Strategy class or instance
            parameters: Strategy parameters

        Returns:
            BacktestResult: Complete backtest results

        Raises:
            ValueError: If strategy or parameters are invalid
        """
        pass

    @abstractmethod
    def optimize_strategy(self,
                        strategy: Any,
                        parameter_space: Dict[str, List[Any]],
                        metric: str = 'sharpe_ratio',
                        method: str = 'grid',
                        max_evals: Optional[int] = None,
                        constraints: Optional[List[Dict]] = None) -> OptimizationResult:
        """
        Optimize strategy parameters.

        Performs parameter optimization using specified method:
        - grid: Exhaustive grid search
        - random: Random search
        - bayesian: Bayesian optimization
        - genetic: Genetic algorithm

        Args:
            strategy: Strategy to optimize
            parameter_space: Parameters and their possible values
            metric: Metric to optimize
            method: Optimization method
            max_evals: Maximum evaluations
            constraints: Parameter constraints

        Returns:
            OptimizationResult: Optimization results

        Raises:
            ValueError: If optimization parameters are invalid
        """
        pass

    @abstractmethod
    def validate_data(self, data: Union[pd.DataFrame, Dict[str, pd.DataFrame]]) -> bool:
        """
        Validate market data format and quality.

        Checks:
        1. Required columns (OHLCV)
        2. Data types
        3. Missing values
        4. Price anomalies
        5. Chronological order
        6. Forward-looking bias

        Args:
            data: Market data to validate

        Returns:
            bool: True if valid

        Raises:
            ValueError: With detailed validation errors
        """
        pass

    @abstractmethod
    def calculate_metrics(self,
                         equity_curve: pd.Series,
                         trades: List[TradeStats],
                         risk_free_rate: float = 0.0) -> Dict[str, float]:
        """
        Calculate comprehensive performance metrics.

        Calculates standard metrics including:
        - Returns (Total, Annual, Risk-adjusted)
        - Risk metrics (Volatility, Drawdown, VaR)
        - Ratios (Sharpe, Sortino, Calmar)
        - Trade statistics (Win rate, Profit factor)

        Args:
            equity_curve: Equity curve
            trades: List of trades
            risk_free_rate: Annual risk-free rate

        Returns:
            Dict[str, float]: Performance metrics
        """
        pass

    def get_position_value(self) -> float:
        """Get current position value."""
        return self._position * self._get_last_price()

    def get_equity(self) -> float:
        """Get current equity."""
        return self._equity + self.get_position_value()

    def _get_last_price(self) -> float:
        """Get most recent price."""
        if self._data is None:
            raise ValueError("No data loaded")
        return self._data['Close'].iloc[-1]

    @property
    def trades(self) -> List[TradeStats]:
        """Get list of completed trades."""
        return self._trades

# Example concrete implementation for testing
# class DemoEngine(BacktestEngineInterface):
#     """
#     Simple engine implementation for demonstration.

#     This implements the bare minimum to show how the interface works.
#     Real engines would be more sophisticated.
#     """

#     def set_data(self, data, validate=True):
#         if validate:
#             self.validate_data(data)
#         self._data = data

#     def run_backtest(self, strategy, parameters=None):
#         # Simplified backtest implementation
#         equity_curve = pd.Series(index=self._data.index)
#         equity_curve.iloc[0] = self.config.initial_capital

#         for i in range(1, len(self._data)):
#             equity_curve.iloc[i] = equity_curve.iloc[i-1]

#         return BacktestResult(
#             equity_curve=equity_curve,
#             trades=[],
#             positions=pd.DataFrame(),
#             metrics={},
#             drawdowns=pd.Series(),
#             returns=pd.Series(),
#             exposure=0.0,
#             start_date=self._data.index[0],
#             end_date=self._data.index[-1],
#             config=self.config
#         )

#     def optimize_strategy(self, strategy, parameter_space, metric='sharpe_ratio',
#                         method='grid', max_evals=None, constraints=None):
#         return OptimizationResult(
#             best_params={},
#             best_metrics={},
#             all_results=pd.DataFrame(),
#             param_importance={},
#             optimization_path=[]
#         )

#     def validate_data(self, data):
#         if isinstance(data, pd.DataFrame):
#             required_cols = ['Open', 'High', 'Low', 'Close']
#             if not all(col in data.columns for col in required_cols):
#                 raise ValueError(f"Data must contain columns: {required_cols}")
#         return True

#     def calculate_metrics(self, equity_curve, trades, risk_free_rate=0.0):
#         return {
#             'total_return': 0.0,
#             'sharpe_ratio': 0.0,
#             'max_drawdown': 0.0
#         }
