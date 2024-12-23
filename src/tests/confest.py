import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
from datetime import datetime, timedelta

from algame.core.data import MarketData
from algame.strategy import StrategyBase

@pytest.fixture
def sample_data():
    """Create sample OHLCV data."""
    dates = pd.date_range(start='2020-01-01', periods=100, freq='D')
    data = pd.DataFrame({
        'Open': np.random.randn(100).cumsum() + 100,
        'High': np.random.randn(100).cumsum() + 102,
        'Low': np.random.randn(100).cumsum() + 98,
        'Close': np.random.randn(100).cumsum() + 100,
        'Volume': np.random.randint(1000000, 10000000, 100)
    }, index=dates)
    return data

@pytest.fixture
def market_data(sample_data):
    """Create MarketData instance."""
    return MarketData(sample_data, 'AAPL', '1d')

@pytest.fixture
def temp_data_dir():
    """Create temporary directory for data files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def simple_strategy():
    """Create simple test strategy."""
    class TestStrategy(StrategyBase):
        def initialize(self):
            self.sma = self.add_indicator('SMA', self.data.Close, period=20)

        def next(self):
            if len(self.data) < 20:
                return

            if self.data.Close[-1] > self.sma[-1]:
                self.buy()
            elif self.data.Close[-1] < self.sma[-1]:
                self.sell()

    return TestStrategy

@pytest.fixture
def backtest_config():
    """Create test backtest configuration."""
    from algame.core.config import BacktestConfig, StrategyConfig

    return BacktestConfig(
        name="Test Backtest",
        description="Test configuration",
        symbols=['AAPL'],
        start_date=datetime(2020, 1, 1),
        end_date=datetime(2020, 12, 31),
        strategy=StrategyConfig(
            name="Test Strategy",
            parameters={'period': 20}
        )
    )
