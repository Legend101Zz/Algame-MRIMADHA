"""
Strategy templates module.

This module provides base templates for common strategy types:
1. Trend Following
2. Mean Reversion
3. Breakout
4. Pattern Recognition

These templates provide:
- Standard logic implementation
- Parameter management
- Risk management
- Position sizing

Users can extend these templates to create strategies faster.
"""

from typing import Dict, List, Optional, Union, Any
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from .base import StrategyBase, Order, Position
from ..core.data import MarketData
from ..indicators import SMA, RSI, ATR, MACD

class TrendStrategy(StrategyBase):
    """
    Base template for trend following strategies.

    Features:
    - Trend detection
    - Entry/exit signals
    - Position sizing
    - Risk management

    Parameters:
        trend_period: Period for trend calculation
        entry_threshold: Entry signal threshold
        exit_threshold: Exit signal threshold
        stop_loss: Stop loss percentage
        take_profit: Take profit percentage
    """

    def __init__(self, config: Optional[Dict] = None):
        """Initialize strategy."""
        default_params = {
            'trend_period': 20,
            'entry_threshold': 1.0,
            'exit_threshold': -1.0,
            'stop_loss': 0.02,
            'take_profit': 0.03
        }

        # Merge with provided config
        if config:
            default_params.update(config)

        super().__init__(default_params)

    def initialize(self) -> None:
        """Initialize indicators."""
        # Get parameters
        period = self.config.parameters['trend_period']

        # Calculate trend indicators
        self.sma = self.add_indicator('SMA', SMA, self.data.Close, period)
        self.atr = self.add_indicator('ATR', ATR, self.data, period)

        # Add visualization settings
        self.plot_settings = {
            'SMA': {'color': 'blue', 'width': 2},
            'ATR': {'panel': 'separate', 'color': 'orange'}
        }

    def next(self) -> None:
        """Generate trading signals."""
        if len(self.data) < self.config.parameters['trend_period']:
            return

        current_price = self.data.Close[-1]

        # Calculate trend signals
        trend_strength = (current_price - self.sma[-1]) / self.atr[-1]

        # Check entry conditions
        if not self.position.is_open:
            if trend_strength > self.config.parameters['entry_threshold']:
                self.buy(
                    sl=current_price * (1 - self.config.parameters['stop_loss']),
                    tp=current_price * (1 + self.config.parameters['take_profit'])
                )

        # Check exit conditions
        else:
            if trend_strength < self.config.parameters['exit_threshold']:
                self.close()

    @classmethod
    def get_parameters(cls) -> Dict[str, Dict]:
        """
        Get strategy parameters for GUI.

        Returns dict of parameters with metadata for GUI:
        - type: Parameter type for input validation
        - default: Default value
        - range: Valid range for numeric parameters
        - description: Parameter description
        """
        return {
            'trend_period': {
                'type': int,
                'default': 20,
                'range': (5, 100),
                'description': 'Period for trend calculation'
            },
            'entry_threshold': {
                'type': float,
                'default': 1.0,
                'range': (0, 5),
                'description': 'Trend strength required for entry'
            },
            'exit_threshold': {
                'type': float,
                'default': -1.0,
                'range': (-5, 0),
                'description': 'Trend strength for exit'
            },
            'stop_loss': {
                'type': float,
                'default': 0.02,
                'range': (0.01, 0.1),
                'description': 'Stop loss percentage'
            },
            'take_profit': {
                'type': float,
                'default': 0.03,
                'range': (0.01, 0.1),
                'description': 'Take profit percentage'
            }
        }

class MeanReversionStrategy(StrategyBase):
    """
    Base template for mean reversion strategies.

    Features:
    - Oversold/overbought detection
    - Dynamic entry/exit levels
    - Volatility-adjusted position sizing
    """

    def initialize(self) -> None:
        # Get parameters
        rsi_period = self.config.parameters.get('rsi_period', 14)
        bb_period = self.config.parameters.get('bb_period', 20)
        bb_std = self.config.parameters.get('bb_std', 2.0)

        # Calculate indicators
        self.rsi = self.add_indicator('RSI', RSI, self.data.Close, rsi_period)
        self.bb_upper, self.bb_lower = self.calculate_bands(bb_period, bb_std)

        # Add visualization
        self.plot_settings = {
            'RSI': {'panel': 'separate', 'color': 'purple'},
            'BB_Upper': {'color': 'gray', 'style': 'dashed'},
            'BB_Lower': {'color': 'gray', 'style': 'dashed'}
        }

    @classmethod
    def get_parameters(cls) -> Dict[str, Dict]:
        """Get strategy parameters for GUI."""
        return {
            'rsi_period': {
                'type': int,
                'default': 14,
                'range': (5, 30),
                'description': 'RSI calculation period'
            },
            'oversold': {
                'type': float,
                'default': 30,
                'range': (10, 40),
                'description': 'Oversold level'
            },
            'overbought': {
                'type': float,
                'default': 70,
                'range': (60, 90),
                'description': 'Overbought level'
            },
            'bb_period': {
                'type': int,
                'default': 20,
                'range': (10, 50),
                'description': 'Bollinger Bands period'
            },
            'bb_std': {
                'type': float,
                'default': 2.0,
                'range': (1.0, 3.0),
                'description': 'Bollinger Bands standard deviation'
            }
        }

class BreakoutStrategy(StrategyBase):
    """
    Base template for breakout strategies.

    Features:
    - Support/resistance detection
    - Volume confirmation
    - False breakout filtering
    """

    def initialize(self) -> None:
        period = self.config.parameters.get('period', 20)
        atr_period = self.config.parameters.get('atr_period', 14)

        # Calculate levels
        self.highs = self.add_indicator('Highs', pd.Series.rolling, self.data.High, period, lambda x: x.max())
        self.lows = self.add_indicator('Lows', pd.Series.rolling, self.data.Low, period, lambda x: x.min())
        self.atr = self.add_indicator('ATR', ATR, self.data, atr_period)

        self.plot_settings = {
            'Highs': {'color': 'green', 'style': 'dashed'},
            'Lows': {'color': 'red', 'style': 'dashed'},
            'ATR': {'panel': 'separate'}
        }

    @classmethod
    def get_parameters(cls) -> Dict[str, Dict]:
        """Get strategy parameters for GUI."""
        return {
            'period': {
                'type': int,
                'default': 20,
                'range': (10, 50),
                'description': 'Lookback period for levels'
            },
            'atr_period': {
                'type': int,
                'default': 14,
                'range': (5, 30),
                'description': 'ATR calculation period'
            },
            'breakout_threshold': {
                'type': float,
                'default': 1.0,
                'range': (0.5, 3.0),
                'description': 'Breakout threshold in ATR units'
            },
            'volume_multiple': {
                'type': float,
                'default': 2.0,
                'range': (1.0, 5.0),
                'description': 'Volume confirmation multiple'
            }
        }

# Engine Adapters - These allow strategies to work with different backtesting engines

class BacktestingPyAdapter:
    """Adapter for backtesting.py engine."""

    @staticmethod
    def adapt_strategy(strategy_class: type) -> type:
        """Convert strategy to backtesting.py format."""
        from backtesting import Strategy as BtStrategy

        class AdaptedStrategy(BtStrategy):
            """Strategy adapted for backtesting.py."""

            def init(self):
                # Create strategy instance
                self._strategy = strategy_class(self._params)

                # Initialize with data
                data = self.to_market_data(self.data)
                self._strategy.set_data(data)

            def next(self):
                # Update data
                data = self.to_market_data(self.data)
                self._strategy.set_data(data)

                # Generate signals
                self._strategy.next()

                # Process orders
                self.process_orders()

            def process_orders(self):
                """Process pending orders."""
                for order in self._strategy.position.orders:
                    if order.type == 'buy':
                        self.buy(size=order.size, sl=order.sl, tp=order.tp)
                    else:
                        self.sell(size=order.size, sl=order.sl, tp=order.tp)

            @staticmethod
            def to_market_data(data) -> MarketData:
                """Convert backtesting.py data to MarketData."""
                df = pd.DataFrame({
                    'Open': data.Open,
                    'High': data.High,
                    'Low': data.Low,
                    'Close': data.Close,
                    'Volume': data.Volume
                }, index=data.index)
                return MarketData(df, 'default')

        return AdaptedStrategy

class CustomEngineAdapter:
    """Adapter for custom engine."""

    @staticmethod
    def adapt_strategy(strategy_class: type) -> type:
        """Convert strategy to custom engine format."""
        # Our custom engine is already compatible
        return strategy_class
