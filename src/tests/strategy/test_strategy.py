# tests/strategy/test_strategy.py

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from algame.strategy import (
    StrategyBase,
    Position,
    Order,
    Trade
)

class TestStrategy(StrategyBase):
    """Simple test strategy."""
    def initialize(self):
        self.sma = self.add_indicator('SMA', self.data.Close, period=20)

    def next(self):
        if len(self.data) < 20:
            return

        if self.data.Close[-1] > self.sma[-1]:
            self.buy()
        elif self.data.Close[-1] < self.sma[-1]:
            self.sell()

@pytest.fixture
def strategy():
    """Create test strategy instance."""
    return TestStrategy()

@pytest.fixture
def sample_data():
    """Create sample market data."""
    dates = pd.date_range(start='2020-01-01', periods=100, freq='D')
    data = pd.DataFrame({
        'Open': np.random.randn(100).cumsum() + 100,
        'High': np.random.randn(100).cumsum() + 102,
        'Low': np.random.randn(100).cumsum() + 98,
        'Close': np.random.randn(100).cumsum() + 100,
        'Volume': np.random.randint(1000000, 10000000, 100)
    }, index=dates)
    return data

def test_strategy_initialization(strategy, sample_data):
    """Test strategy initialization."""
    strategy.set_data(sample_data)
    assert strategy.data is not None
    assert hasattr(strategy, 'sma')
    assert strategy.position is not None
    assert len(strategy.trades) == 0

def test_strategy_position_management(strategy, sample_data):
    """Test position management."""
    strategy.set_data(sample_data)

    # Test buy
    strategy.buy(size=100)
    assert strategy.position.size == 100
    assert strategy.position.is_long

    # Test sell
    strategy.sell(size=100)
    assert strategy.position.size == -100
    assert strategy.position.is_short

    # Test close
    strategy.close()
    assert strategy.position.size == 0
    assert not strategy.position.is_open

def test_strategy_order_execution(strategy, sample_data):
    """Test order execution."""
    strategy.set_data(sample_data)

    # Create order
    order = strategy.buy(
        size=100,
        stop_loss=95.0,
        take_profit=105.0
    )

    assert isinstance(order, Order)
    assert order.size == 100
    assert order.stop_loss == 95.0
    assert order.take_profit == 105.0
    assert order.status == 'pending'

def test_strategy_trade_tracking(strategy, sample_data):
    """Test trade tracking."""
    strategy.set_data(sample_data)

    # Execute trades
    strategy.buy(size=100, price=100.0)
    strategy.sell(size=100, price=105.0)

    assert len(strategy.trades) == 1
    trade = strategy.trades[0]
    assert isinstance(trade, Trade)
    assert trade.size == 100
    assert trade.pnl == 500.0  # (105 - 100) * 100

def test_strategy_indicators(strategy, sample_data):
    """Test indicator management."""
    strategy.set_data(sample_data)

    # Add indicators
    sma = strategy.add_indicator('SMA', sample_data['Close'], period=20)
    rsi = strategy.add_indicator('RSI', sample_data['Close'], period=14)

    assert 'sma' in strategy.indicators
    assert 'rsi' in strategy.indicators
    assert len(sma) == len(sample_data)
    assert len(rsi) == len(sample_data)

def test_strategy_parameters(sample_data):
    """Test strategy parameter handling."""
    class ParameterizedStrategy(StrategyBase):
        def __init__(self, parameters=None):
            super().__init__(parameters)
            self.sma_period = self.parameters.get('sma_period', 20)
            self.rsi_period = self.parameters.get('rsi_period', 14)

        def initialize(self):
            self.sma = self.add_indicator('SMA', self.data.Close, period=self.sma_period)
            self.rsi = self.add_indicator('RSI', self.data.Close, period=self.rsi_period)

    params = {'sma_period': 10, 'rsi_period': 7}
    strategy = ParameterizedStrategy(parameters=params)
    strategy.set_data(sample_data)

    assert strategy.sma_period == 10
    assert strategy.rsi_period == 7

def test_strategy_validation(strategy, sample_data):
    """Test strategy validation."""
    # Test missing data
    with pytest.raises(ValueError):
        strategy.next()

    # Test invalid position size
    with pytest.raises(ValueError):
        strategy.buy(size=-100)

def test_strategy_risk_management(strategy, sample_data):
    """Test risk management features."""
    strategy.set_data(sample_data)

    # Set position limits
    strategy.position_limit = 0.5  # 50% of capital
    strategy.risk_per_trade = 0.02  # 2% risk per trade

    # Test position sizing
    size = strategy.calculate_position_size(
        price=100.0,
        stop_loss=95.0
    )
    assert size > 0
    assert size <= strategy.position_limit * strategy.capital

def test_strategy_optimization(sample_data):
    """Test strategy optimization capabilities."""
    class OptimizableStrategy(StrategyBase):
        def __init__(self, parameters=None):
            super().__init__(parameters)
            self.period = self.parameters.get('period', 20)

        def initialize(self):
            self.sma = self.add_indicator('SMA', self.data.Close, period=self.period)

        @classmethod
        def get_parameter_space(cls):
            return {
                'period': range(10, 50, 5)
            }

    strategy = OptimizableStrategy()
    param_space = strategy.get_parameter_space()

    assert 'period' in param_space
    assert len(list(param_space['period'])) == 8

def test_strategy_persistence(strategy, sample_data):
    """Test strategy state persistence."""
    strategy.set_data(sample_data)

    # Execute some trades
    strategy.buy(size=100, price=100.0)
    strategy.sell(size=100, price=105.0)

    # Save state
    state = strategy.get_state()

    # Create new strategy instance
    new_strategy = TestStrategy()
    new_strategy.set_data(sample_data)
    new_strategy.set_state(state)

    # Verify state was restored
    assert new_strategy.position.size == 0
    assert len(new_strategy.trades) == 1
    assert new_strategy.trades[0].pnl == 500.0

def test_strategy_event_handling(strategy, sample_data):
    """Test strategy event handling."""
    events = []

    def on_order(order):
        events.append(('order', order))

    def on_trade(trade):
        events.append(('trade', trade))

    strategy.set_data(sample_data)
    strategy.on_order = on_order
    strategy.on_trade = on_trade

    # Execute trade
    strategy.buy(size=100, price=100.0)
    strategy.sell(size=100, price=105.0)

    assert len(events) == 4  # 2 orders + 2 trades
    assert events[0][0] == 'order'  # First event should be order
    assert events[-1][0] == 'trade'  # Last event should be trade

def test_strategy_multiple_assets():
    """Test strategy with multiple assets."""
    class MultiAssetStrategy(StrategyBase):
        def initialize(self):
            for symbol in self.data:
                self.sma[symbol] = self.add_indicator(
                    'SMA',
                    self.data[symbol].Close,
                    period=20
                )

        def next(self):
            for symbol in self.data:
                if self.data[symbol].Close[-1] > self.sma[symbol][-1]:
                    self.buy(symbol)
                else:
                    self.sell(symbol)

    # Create sample data for multiple assets
    dates = pd.date_range(start='2020-01-01', periods=100, freq='D')
    data = {
        'AAPL': pd.DataFrame({
            'Close': np.random.randn(100).cumsum() + 100
        }, index=dates),
        'GOOGL': pd.DataFrame({
            'Close': np.random.randn(100).cumsum() + 200
        }, index=dates)
    }

    strategy = MultiAssetStrategy()
    strategy.set_data(data)

    assert len(strategy.data) == 2
    assert 'AAPL' in strategy.sma
    assert 'GOOGL' in strategy.sma

def test_strategy_portfolio_management(strategy, sample_data):
    """Test portfolio management capabilities."""
    strategy.set_data(sample_data)

    # Set portfolio constraints
    strategy.max_positions = 5
    strategy.max_exposure = 0.8  # 80% max exposure

    # Test position sizing
    size = strategy.calculate_position_size(
        price=100.0,
        weight=0.2  # 20% position weight
    )

    assert size > 0
    assert size <= (strategy.capital * strategy.max_exposure) / 100.0

def test_strategy_metrics(strategy, sample_data):
    """Test strategy performance metrics calculation."""
    strategy.set_data(sample_data)

    # Execute some trades
    strategy.buy(size=100, price=100.0)
    strategy.sell(size=100, price=105.0)
    strategy.buy(size=100, price=103.0)
    strategy.sell(size=100, price=101.0)

    metrics = strategy.calculate_metrics()

    assert 'total_return' in metrics
    assert 'win_rate' in metrics
    assert 'max_drawdown' in metrics
    assert metrics['win_rate'] == 50.0  # One winning trade, one losing trade

def test_strategy_custom_indicators(sample_data):
    """Test using custom indicators in strategy."""
    class CustomIndicator:
        def __init__(self, period):
            self.period = period

        def calculate(self, data):
            return pd.Series(data).rolling(self.period).mean().values

    class CustomStrategy(StrategyBase):
        def initialize(self):
            self.custom = self.add_indicator(
                CustomIndicator,
                self.data.Close,
                period=20
            )

    strategy = CustomStrategy()
    strategy.set_data(sample_data)

    assert hasattr(strategy, 'custom')
    assert len(strategy.custom) == len(sample_data)

def test_strategy_templates():
    """Test strategy template functionality."""
    from algame.strategy import TrendStrategy, MeanReversionStrategy

    # Test trend following template
    trend = TrendStrategy({'trend_period': 20})
    assert hasattr(trend, 'trend_period')

    # Test mean reversion template
    mean_rev = MeanReversionStrategy({'lookback': 20})
    assert hasattr(mean_rev, 'lookback')

def test_strategy_optimization_results(strategy, sample_data):
    """Test handling optimization results."""
    # Create optimization results
    opt_results = {
        'parameters': {'period': 15},
        'metrics': {
            'sharpe_ratio': 1.5,
            'total_return': 0.25
        }
    }

    # Apply optimized parameters
    strategy.update_parameters(opt_results['parameters'])
    strategy.set_data(sample_data)

    assert strategy.parameters['period'] == 15

def test_strategy_position_analysis(strategy, sample_data):
    """Test position analysis tools."""
    strategy.set_data(sample_data)

    # Execute trades
    strategy.buy(size=100, price=100.0)
    strategy.sell(size=50, price=105.0)  # Partial close

    position_info = strategy.analyze_position()

    assert position_info['size'] == 50
    assert position_info['cost_basis'] == 100.0
    assert position_info['market_value'] == position_info['size'] * sample_data['Close'][-1]

if __name__ == '__main__':
    pytest.main([__file__])
