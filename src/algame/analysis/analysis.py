"""
Analysis module for performance metrics and risk analysis.

This module provides:
1. Performance metric calculations
2. Risk analysis tools
3. Strategy optimization analysis
4. Report generation
"""

from typing import Dict, List, Optional, Union, Any
import pandas as pd
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class PerformanceMetrics:
    """
    Performance metric calculations.

    Calculates standard trading metrics:
    - Returns (total, annual, risk-adjusted)
    - Risk metrics (volatility, drawdown, VaR)
    - Trade statistics (win rate, profit factor)
    """

    def __init__(self,
                 equity: pd.Series,
                 trades: List[Any],
                 risk_free_rate: float = 0.0):
        """Initialize metrics calculator."""
        self.equity = equity
        self.trades = trades
        self.risk_free_rate = risk_free_rate

        # Calculate key metrics
        self._calculate_returns()
        self._calculate_drawdowns()
        self._calculate_trade_stats()
        self._calculate_risk_metrics()

    def _calculate_returns(self):
        """Calculate return metrics."""
        # Return series
        self.returns = self.equity.pct_change()

        # Total return
        self.total_return = (self.equity[-1] / self.equity[0] - 1) * 100

        # Annual return
        years = (self.equity.index[-1] - self.equity.index[0]).days / 365
        self.annual_return = (1 + self.total_return/100) ** (1/years) - 1

        # Excess returns
        excess_returns = self.returns - self.risk_free_rate/252

        # Sharpe ratio
        return_std = self.returns.std() * np.sqrt(252)
        self.sharpe_ratio = (self.annual_return - self.risk_free_rate) / return_std if return_std > 0 else 0

        # Sortino ratio
        downside_std = self.returns[self.returns < 0].std() * np.sqrt(252)
        self.sortino_ratio = (self.annual_return - self.risk_free_rate) / downside_std if downside_std > 0 else 0

    def _calculate_drawdowns(self):
        """Calculate drawdown metrics."""
        # Running maximum
        running_max = self.equity.expanding().max()

        # Drawdown series
        drawdowns = (self.equity - running_max) / running_max * 100
        self.drawdowns = drawdowns

        # Maximum drawdown
        self.max_drawdown = drawdowns.min()

        # Average drawdown
        self.avg_drawdown = drawdowns[drawdowns < 0].mean()

        # Drawdown duration
        in_drawdown = drawdowns < 0
        dur_starts = in_drawdown.ne(in_drawdown.shift()).cumsum()
        durations = in_drawdown.groupby(dur_starts).cumsum()
        self.max_drawdown_duration = durations.max()

    def _calculate_trade_stats(self):
        """Calculate trade statistics."""
        if not self.trades:
            self._set_default_trade_stats()
            return

        # Profitable trades
        profits = [t for t in self.trades if t.pnl > 0]
        losses = [t for t in self.trades if t.pnl < 0]

        # Win rate
        self.win_rate = len(profits) / len(self.trades) * 100

        # Profit factor
        total_profit = sum(t.pnl for t in profits)
        total_loss = abs(sum(t.pnl for t in losses))
        self.profit_factor = total_profit / total_loss if total_loss else float('inf')

        # Average trade
        self.avg_trade = sum(t.pnl for t in self.trades) / len(self.trades)
        self.avg_win = sum(t.pnl for t in profits) / len(profits) if profits else 0
        self.avg_loss = sum(t.pnl for t in losses) / len(losses) if losses else 0

        # Largest trades
        self.largest_win = max(t.pnl for t in self.trades)
        self.largest_loss = min(t.pnl for t in self.trades)

        # Trade duration
        durations = [(t.exit_time - t.entry_time).total_seconds()/86400
                    for t in self.trades if t.exit_time]
        self.avg_duration = np.mean(durations) if durations else 0

    def _calculate_risk_metrics(self):
        """Calculate risk metrics."""
        # Volatility
        self.volatility = self.returns.std() * np.sqrt(252)

        # Value at Risk
        self.var_95 = np.percentile(self.returns, 5)
        self.var_99 = np.percentile(self.returns, 1)

        # Maximum consecutive losses
        signs = np.sign(self.returns)
        neg_runs = [len(list(g)) for k, g in itertools.groupby(signs) if k < 0]
        self.max_consecutive_losses = max(neg_runs) if neg_runs else 0

        # Beta (if benchmark provided)
        if hasattr(self, 'benchmark_returns'):
            cov = np.cov(self.returns, self.benchmark_returns)[0,1]
            benchmark_var = np.var(self.benchmark_returns)
            self.beta = cov / benchmark_var if benchmark_var > 0 else 1

    def _set_default_trade_stats(self):
        """Set default values for trade statistics."""
        self.win_rate = 0
        self.profit_factor = 0
        self.avg_trade = 0
        self.avg_win = 0
        self.avg_loss = 0
        self.largest_win = 0
        self.largest_loss = 0
        self.avg_duration = 0

    def get_metrics(self) -> Dict[str, float]:
        """Get all metrics as dictionary."""
        return {
            'total_return': self.total_return,
            'annual_return': self.annual_return * 100,
            'sharpe_ratio': self.sharpe_ratio,
            'sortino_ratio': self.sortino_ratio,
            'max_drawdown': self.max_drawdown,
            'avg_drawdown': self.avg_drawdown,
            'volatility': self.volatility * 100,
            'win_rate': self.win_rate,
            'profit_factor': self.profit_factor,
            'avg_trade': self.avg_trade,
            'largest_win': self.largest_win,
            'largest_loss': self.largest_loss,
            'avg_duration': self.avg_duration,
            'max_consecutive_losses': self.max_consecutive_losses,
            'var_95': self.var_95 * 100,
            'var_99': self.var_99 * 100
        }

class RiskAnalysis:
    """
    Risk analysis tools.

    Provides:
    - Position sizing calculations
    - Risk allocation
    - Portfolio optimization
    - Stress testing
    """

    def __init__(self,
                 returns: pd.Series,
                 positions: pd.DataFrame,
                 capital: float):
        """Initialize risk analyzer."""
        self.returns = returns
        self.positions = positions
        self.capital = capital

    def calculate_position_size(self,
                              risk_per_trade: float,
                              stop_loss: float) -> float:
        """
        Calculate position size based on risk.

        Args:
            risk_per_trade: Amount to risk as % of capital
            stop_loss: Stop loss distance in %

        Returns:
            Position size in units
        """
        risk_amount = self.capital * (risk_per_trade / 100)
        unit_risk = stop_loss / 100
        return risk_amount / unit_risk

    def stress_test(self,
                    scenarios: Dict[str, Dict[str, float]]) -> pd.DataFrame:
        """
        Perform stress testing.

        Args:
            scenarios: Dictionary of scenarios and their parameters

        Returns:
            DataFrame with scenario results
        """
        results = []

        for name, params in scenarios.items():
            # Adjust returns based on scenario
            adjusted_returns = self._adjust_returns(params)

            # Calculate scenario metrics
            metrics = PerformanceMetrics(
                self._calculate_equity(adjusted_returns),
                self.positions,
                params.get('risk_free', 0)
            )

            results.append({
                'scenario': name,
                'return': metrics.total_return,
                'drawdown': metrics.max_drawdown,
                'var_99': metrics.var_99
            })

        return pd.DataFrame(results)

    def _adjust_returns(self, params: Dict[str, float]) -> pd.Series:
        """Adjust returns based on scenario parameters."""
        returns = self.returns.copy()

        # Apply volatility adjustment
        if 'vol_mult' in params:
            returns *= params['vol_mult']

        # Apply shock
        if 'shock' in params:
            shock_idx = np.random.choice(
                len(returns),
                size=int(len(returns) * params['shock_prob']),
                replace=False
            )
            returns.iloc[shock_idx] = params['shock']

        return returns

    def _calculate_equity(self, returns: pd.Series) -> pd.Series:
        """Calculate equity curve from returns."""
        return (1 + returns).cumprod() * self.capital

class OptimizationAnalysis:
    """
    Optimization result analysis.

    Features:
    - Parameter importance analysis
    - Overfitting detection
    - Walk-forward analysis
    - Parameter stability
    """

    def __init__(self, results: pd.DataFrame):
        """
        Initialize analyzer.

        Args:
            results: DataFrame with optimization results
            Columns should include parameters and metrics
        """
        self.results = results

        # Calculate statistics
        self._analyze_parameters()
        self._analyze_stability()

    def _analyze_parameters(self):
        """Analyze parameter importance."""
        # Get parameter columns
        param_cols = [c for c in self.results.columns
                     if c not in ['fitness', 'sharpe', 'return']]

        # Calculate correlation with fitness
        correlations = {}
        for param in param_cols:
            corr = np.corrcoef(
                self.results[param],
                self.results['fitness']
            )[0,1]
            correlations[param] = abs(corr)

        # Normalize to percentages
        total = sum(correlations.values())
        self.param_importance = {
            k: v/total * 100
            for k, v in correlations.items()
        }

    def _analyze_stability(self):
        """Analyze parameter stability."""
        # Get top N% of results
        top_n = int(len(self.results) * 0.1)
        top_results = self.results.nlargest(top_n, 'fitness')

        # Calculate parameter ranges
        param_ranges = {}
        for param in self.param_importance.keys():
            param_range = top_results[param].max() - top_results[param].min()
            param_ranges[param] = param_range

        self.param_stability = param_ranges

    def get_optimal_params(self) -> Dict[str, float]:
        """Get optimal parameters."""
        best_idx = self.results['fitness'].idxmax()

        params = {}
        for param in self.param_importance.keys():
            params[param] = self.results.loc[best_idx, param]

        return params

    def plot_parameter_impact(self, param: str):
        """Plot parameter impact on fitness."""
        import matplotlib.pyplot as plt

        plt.figure(figsize=(10, 6))
        plt.scatter(self.results[param], self.results['fitness'])
        plt.xlabel(param)
        plt.ylabel('Fitness')
        plt.title(f'Impact of {param} on Performance')
        plt.grid(True)
        return plt.gcf()

def analyze_strategy(equity: pd.Series,
                    trades: List[Any],
                    benchmark: Optional[pd.Series] = None) -> Dict[str, Any]:
    """
    Analyze strategy performance.

    Convenience function that runs standard analysis.

    Args:
        equity: Strategy equity curve
        trades: List of completed trades
        benchmark: Optional benchmark returns

    Returns:
        Dictionary with analysis results
    """
    # Calculate metrics
    metrics = PerformanceMetrics(equity, trades)

    # Add benchmark comparison if provided
    if benchmark is not None:
        metrics.benchmark_returns = benchmark.pct_change()

    # Get all metrics
    results = metrics.get_metrics()

    # Add drawdown series
    results['drawdowns'] = metrics.drawdowns

    return results
