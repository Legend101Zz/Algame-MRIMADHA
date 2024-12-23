import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from algame.core.engine import (
    BacktestEngineInterface,
    BacktestResult,
    TradeStats,
    EngineConfig,
    Position,
    Order,
    CustomEngine
)

# Helper function to create sample data
def create_sample_data(periods=100):
    dates = pd.date_range(start='2020-01-01', periods=periods, freq='D')
    data = pd.DataFrame({
        'Open': np.random.randn(periods).cumsum() + 100,
        'High': np.random.randn(periods).cumsum() + 102,
        'Low': np.random.randn(periods).cumsum() + 98,
        'Close': np.random.randn(periods).cumsum() + 100,
        'Volume': np.random.randint(1000000, 10000000, periods)
    }, index=dates)
    return data

# Test basic engine configuration
def test_engine_config():
    config = EngineConfig()
    assert config.initial_capital == 100000.0
    assert config.commission == 0.001
    assert config.slippage == 0.0001
    assert config.position_limit == 1.0

# Test Position class
def test_position():
    position = Position()
    assert position.size == 0.0
    assert not position.is_open
    assert not position.is_long
    assert not position.is_short

    # Test long position
    position.size = 100
    assert position.is_open
    assert position.is_long
    assert not position.is_short

    # Test short position
    position.size = -100
    assert position.is_open
    assert not position.is_long
    assert position.is_short

# Test Order class
def test_order():
    order = Order(
        type='buy',
        size=100,
        price=50.0,
        stop_loss=45.0,
        take_profit=55.0
    )
    assert order.type == 'buy'
    assert order.size == 100
    assert order.price == 50.0
    assert order.stop_loss == 45.0
    assert order.take_profit == 55.0
    assert order.status == 'pending'

# Test CustomEngine basic functionality
def test_custom_engine_basics():
    engine = CustomEngine()
    data = create_sample_data()
    engine.set_data(data)
    assert engine._data is not None

# Test engine position management
def test_engine_position_management():
    engine = CustomEngine()
    data = create_sample_data()
    engine.set_data(data)

    # Test buy order
    engine.buy(size=100, price=50.0)
    assert engine.position.size == 100
    assert engine.position.is_long

    # Test sell order
    engine.sell(size=100, price=51.0)
    assert engine.position.size == -100
    assert engine.position.is_short

    # Test close position
    engine.close()
    assert engine.position.size == 0
    assert not engine.position.is_open

# Test trade tracking
def test_trade_tracking():
    engine = CustomEngine()
    data = create_sample_data()
    engine.set_data(data)

    # Execute a complete trade
    entry_time = datetime.now()
    engine.buy(size=100, price=50.0)

    exit_time = entry_time + timedelta(days=1)
    engine.sell(size=100, price=51.0)

    # Verify trade was recorded
    assert len(engine.trades) == 1
    trade = engine.trades[0]
    assert trade.size == 100
    assert trade.entry_price == 50.0
    assert trade.exit_price == 51.0
    assert trade.pnl == 100.0  # (51 - 50) * 100

# Test engine metrics calculation
def test_engine_metrics():
    engine = CustomEngine()
    data = create_sample_data()
    engine.set_data(data)

    # Execute multiple trades
    engine.buy(size=100, price=50.0)
    engine.sell(size=100, price=51.0)
    engine.buy(size=100, price=51.0)
    engine.sell(size=100, price=50.0)

    # Calculate metrics
    metrics = engine.calculate_metrics(
        equity_curve=pd.Series([100000, 100100, 100000]),
        trades=engine.trades
    )

    assert 'total_return' in metrics
    assert 'sharpe_ratio' in metrics
    assert 'max_drawdown' in metrics
    assert 'win_rate' in metrics

# Test risk management
def test_risk_management():
    engine = CustomEngine()
    data = create_sample_data()
    engine.set_data(data)

    # Test stop loss
    engine.buy(size=100, price=50.0, stop_loss=49.0)
    engine.update_position(current_price=48.0)
    assert not engine.position.is_open  # Position should be closed by stop loss

    # Test take profit
    engine.buy(size=100, price=50.0, take_profit=51.0)
    engine.update_position(current_price=52.0)
    assert not engine.position.is_open  # Position should be closed by take profit

# Test portfolio constraints
def test_portfolio_constraints():
    engine = CustomEngine()
    data = create_sample_data()
    engine.set_data(data)

    # Test position limit
    engine.config.position_limit = 0.5  # 50% of capital
    capital = engine.config.initial_capital
    price = 100.0

    # Try to take position larger than limit
    max_size = (capital * engine.config.position_limit) / price
    engine.buy(size=max_size * 2, price=price)  # Should be limited
    assert engine.position.size <= max_size

# Test error handling
def test_engine_error_handling():
    engine = CustomEngine()

    # Test setting invalid data
    with pytest.raises(ValueError):
        engine.set_data(None)

    # Test trading without data
    with pytest.raises(ValueError):
        engine.buy(size=100, price=50.0)

    # Test invalid position size
    with pytest.raises(ValueError):
        engine.buy(size=-100, price=50.0)  # Negative size for buy

# Integration test
def test_complete_backtest():
    engine = CustomEngine()
    data = create_sample_data()
    engine.set_data(data)

    # Execute multiple trades
    for i in range(0, len(data)-1, 10):
        if i % 20 == 0:
            engine.buy(size=100, price=data['Close'][i])
        else:
            engine.sell(size=100, price=data['Close'][i])
            engine.close()

    # Get backtest results
    results = engine.get_results()

    assert isinstance(results, BacktestResult)
    assert len(results.trades) > 0
    assert isinstance(results.equity_curve, pd.Series)
    assert isinstance(results.metrics, dict)
    assert 'total_return' in results.metrics
    assert 'sharpe_ratio' in results.metrics

if __name__ == '__main__':
    pytest.main([__file__])
