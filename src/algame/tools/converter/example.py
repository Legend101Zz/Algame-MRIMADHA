"""
Template for Converting Common PineScript Patterns.

This template provides conversions for:
1. Common indicator setups
2. Standard entry/exit patterns
3. Risk management rules
"""

# Strategy Class Template
STRATEGY_TEMPLATE = '''
from algame.strategy import StrategyBase
from algame.indicators import *
import numpy as np

class {strategy_name}(StrategyBase):
    """
    {strategy_description}

    Converted from PineScript {version}
    Original Author: {author}
    """

    def __init__(self, parameters=None):
        super().__init__(parameters)

        # Default parameters
        self.parameters = parameters or {default_params}

    def initialize(self):
        """Initialize indicators."""
        {initialize_code}

    def next(self):
        """Generate trading signals."""
        {next_code}
'''

# Common Indicator Patterns
INDICATOR_PATTERNS = {
    # Moving Averages
    'ta.sma': 'self.{name} = self.add_indicator(SMA, self.data.Close, period={period})',
    'ta.ema': 'self.{name} = self.add_indicator(EMA, self.data.Close, period={period})',
    'ta.wma': 'self.{name} = self.add_indicator(WMA, self.data.Close, period={period})',

    # Oscillators
    'ta.rsi': 'self.{name} = self.add_indicator(RSI, self.data.Close, period={period})',
    'ta.macd': '''self.{name}_line, self.{name}_signal, self.{name}_hist = self.add_indicator(
            MACD, self.data.Close,
            fast_period={fast}, slow_period={slow}, signal_period={signal}
        )''',
    'ta.bbands': '''self.{name}_middle, self.{name}_upper, self.{name}_lower = self.add_indicator(
            Bollinger, self.data.Close,
            period={period}, std_dev={mult}
        )''',

    # Volume
    'ta.obv': 'self.{name} = self.add_indicator(OBV, self.data.Close, self.data.Volume)',
    'ta.mfi': 'self.{name} = self.add_indicator(MFI, self.data.Close, self.data.Volume, period={period})',
}

# Entry/Exit Patterns
ENTRY_PATTERNS = {
    # Simple Crossover
    'cross_above': '''
        if self.data.Close[-1] > self.{indicator}[-1] and \\
           self.data.Close[-2] <= self.{indicator}[-2]:
            self.buy()
    ''',

    'cross_below': '''
        if self.data.Close[-1] < self.{indicator}[-1] and \\
           self.data.Close[-2] >= self.{indicator}[-2]:
            self.sell()
    ''',

    # Oscillator Overbought/Oversold
    'oscillator_entry': '''
        if self.{indicator}[-1] < {oversold} and self.{indicator}[-2] >= {oversold}:
            self.buy()
        elif self.{indicator}[-1] > {overbought} and self.{indicator}[-2] <= {overbought}:
            self.sell()
    ''',

    # Multiple Condition
    'multi_condition': '''
        long_condition = {long_conditions}
        short_condition = {short_conditions}

        if long_condition:
            self.buy()
        elif short_condition:
            self.sell()
    '''
}

# Risk Management Patterns
RISK_PATTERNS = {
    # Fixed Stop Loss/Take Profit
    'fixed_risk': '''
        if self.position.is_long:
            stop_price = self.entry_price * (1 - {stop_loss})
            target_price = self.entry_price * (1 + {take_profit})

            if self.data.Close[-1] <= stop_price or self.data.Close[-1] >= target_price:
                self.close()
    ''',

    # Trailing Stop
    'trailing_stop': '''
        if self.position.is_long:
            stop_price = max([
                self.entry_price * (1 - {initial_stop}),
                self.data.Close[-1] * (1 - {trail_percent})
            ])

            if self.data.Close[-1] <= stop_price:
                self.close()
    ''',

    # Time-Based Exit
    'time_exit': '''
        if self.position.is_open:
            bars_since_entry = len(self.data) - self.entry_bar
            if bars_since_entry >= {max_bars}:
                self.close()
    '''
}

# Example Strategy Using Template
EXAMPLE_STRATEGY = '''
//@version=5
strategy("Dual MA Crossover", overlay=true)

// Parameters
fastLength = input(10, "Fast MA Length")
slowLength = input(20, "Slow MA Length")
rsiLength = input(14, "RSI Length")
rsiOverbought = input(70, "RSI Overbought")
rsiOversold = input(30, "RSI Oversold")

// Indicators
fastMA = ta.sma(close, fastLength)
slowMA = ta.sma(close, slowLength)
rsi = ta.rsi(close, rsiLength)

// Entry conditions
longCondition = ta.crossover(fastMA, slowMA) and rsi < rsiOversold
shortCondition = ta.crossunder(fastMA, slowMA) and rsi > rsiOverbought

// Trading logic
if longCondition
    strategy.entry("Long", strategy.long)

if shortCondition
    strategy.entry("Short", strategy.short)

// Risk management
strategy.exit("SL/TP", "Long", stop=strategy.position_avg_price * 0.95, limit=strategy.position_avg_price * 1.05)
strategy.exit("SL/TP", "Short", stop=strategy.position_avg_price * 1.05, limit=strategy.position_avg_price * 0.95)
'''

# Expected Python Conversion
EXPECTED_CONVERSION = '''
from algame.strategy import StrategyBase
from algame.indicators import *
import numpy as np

class DualMACrossover(StrategyBase):
    """
    Dual Moving Average Crossover with RSI Filter

    Uses SMA crossovers with RSI oversold/overbought conditions
    for entry signals. Includes fixed stop loss and take profit.
    """

    def __init__(self, parameters=None):
        super().__init__(parameters)

        # Default parameters
        self.parameters = parameters or {
            'fastLength': 10,
            'slowLength': 20,
            'rsiLength': 14,
            'rsiOverbought': 70,
            'rsiOversold': 30,
            'stopLoss': 0.05,
            'takeProfit': 0.05
        }

    def initialize(self):
        """Initialize indicators."""
        # Moving averages
        self.fastMA = self.add_indicator(SMA, self.data.Close,
                                       period=self.parameters['fastLength'])
        self.slowMA = self.add_indicator(SMA, self.data.Close,
                                       period=self.parameters['slowLength'])

        # RSI
        self.rsi = self.add_indicator(RSI, self.data.Close,
                                    period=self.parameters['rsiLength'])

    def next(self):
        """Generate trading signals."""
        # Entry conditions
        long_condition = (
            self.fastMA[-1] > self.slowMA[-1] and
            self.fastMA[-2] <= self.slowMA[-2] and
            self.rsi[-1] < self.parameters['rsiOversold']
        )

        short_condition = (
            self.fastMA[-1] < self.slowMA[-1] and
            self.fastMA[-2] >= self.slowMA[-2] and
            self.rsi[-1] > self.parameters['rsiOverbought']
        )

        # Trading logic
        if long_condition:
            self.buy(
                sl=self.data.Close[-1] * (1 - self.parameters['stopLoss']),
                tp=self.data.Close[-1] * (1 + self.parameters['takeProfit'])
            )

        elif short_condition:
            self.sell(
                sl=self.data.Close[-1] * (1 + self.parameters['stopLoss']),
                tp=self.data.Close[-1] * (1 - self.parameters['takeProfit'])
            )
'''
