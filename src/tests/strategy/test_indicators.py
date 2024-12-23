import pytest
import numpy as np
import pandas as pd

from algame.strategy.indicators import (
    Indicator,
    SMA,
    EMA,
    RSI,
    MACD,
    Bollinger,
    ATR
)

@pytest.fixture
def prices():
    """Generate sample price data."""
    return pd.Series(np.random.randn(100).cumsum() + 100)

@pytest.fixture
def ohlcv_data():
    """Generate sample OHLCV data."""
    return pd.DataFrame({
        'Open': np.random.randn(100).cumsum() + 100,
        'High': np.random.randn(100).cumsum() + 102,
        'Low': np.random.randn(100).cumsum() + 98,
        'Close': np.random.randn(100).cumsum() + 100,
        'Volume': np.random.randint(1000000, 10000000, 100)
    })

def test_indicator_base_class():
    """Test basic Indicator functionality."""
    class TestIndicator(Indicator):
        def calculate(self, data):
            return data

    indicator = TestIndicator()
    assert isinstance(indicator, Indicator)

    # Test data validation
    valid_data = pd.Series([1, 2, 3])
    indicator.validate_data(valid_data)

    invalid_data = pd.Series(['a', 'b', 'c'])
    with pytest.raises(ValueError):
        indicator.validate_data(invalid_data)

def test_sma_indicator(prices):
    """Test Simple Moving Average."""
    sma = SMA(period=20)
    result = sma.calculate(prices)

    assert isinstance(result, np.ndarray)
    assert len(result) == len(prices)
    assert np.isnan(result[0])  # First value should be NaN
    assert not np.isnan(result[-1])  # Last value should be valid

    # Verify calculation
    expected = prices.rolling(window=20).mean().values
    np.testing.assert_array_almost_equal(result, expected)

def test_ema_indicator(prices):
    """Test Exponential Moving Average."""
    ema = EMA(period=20)
    result = ema.calculate(prices)

    assert isinstance(result, np.ndarray)
    assert len(result) == len(prices)

    # Verify calculation
    expected = prices.ewm(span=20, adjust=False).mean().values
    np.testing.assert_array_almost_equal(result, expected)

def test_rsi_indicator(prices):
    """Test Relative Strength Index."""
    rsi = RSI(period=14)
    result = rsi.calculate(prices)

    assert isinstance(result, np.ndarray)
    assert len(result) == len(prices)
    assert np.all((result >= 0) & (result <= 100))  # RSI should be between 0 and 100

def test_macd_indicator(prices):
    """Test MACD indicator."""
    macd = MACD(fast_period=12, slow_period=26, signal_period=9)
    macd_line, signal_line, histogram = macd.calculate(prices)

    assert isinstance(macd_line, np.ndarray)
    assert isinstance(signal_line, np.ndarray)
    assert isinstance(histogram, np.ndarray)
    assert len(macd_line) == len(prices)

    # Verify calculation
    assert np.all(histogram == macd_line - signal_line)

def test_bollinger_indicator(prices):
    """Test Bollinger Bands."""
    bb = Bollinger(period=20, std_dev=2.0)
    middle, upper, lower = bb.calculate(prices)

    assert isinstance(middle, np.ndarray)
    assert isinstance(upper, np.ndarray)
    assert isinstance(lower, np.ndarray)

    # Verify bands
    assert np.all(upper >= middle)
    assert np.all(lower <= middle)

def test_atr_indicator(ohlcv_data):
    """Test Average True Range."""
    atr = ATR(period=14)
    result = atr.calculate(ohlcv_data)

    assert isinstance(result, np.ndarray)
    assert len(result) == len(ohlcv_data)
    assert np.all(result >= 0)  # ATR should be non-negative

def test_indicator_validation():
    """Test indicator input validation."""
    sma = SMA(period=20)

    # Test invalid data type
    with pytest.raises(ValueError):
        sma.calculate([1, 2, 3])  # List instead of pandas Series/numpy array

    # Test invalid parameter
    with pytest.raises(ValueError):
        SMA(period=-1)  # Negative period

    # Test missing data
    with pytest.raises(ValueError):
        sma.calculate(pd.Series([]))  # Empty series

def test_indicator_metadata():
    """Test indicator metadata."""
    sma = SMA(period=20)
    metadata = sma.get_metadata()

    assert metadata.name == "SMA"
    assert metadata.category == "Trend"
    assert isinstance(metadata.description, str)

    params = sma.get_parameters()
    assert 'period' in params
    assert params['period']['type'] == 'int'

def test_indicator_chaining():
    """Test using one indicator's output as another's input."""
    prices = pd.Series(np.random.randn(100).cumsum() + 100)

    # Calculate SMA of RSI
    rsi = RSI(period=14)
    rsi_values = rsi.calculate(prices)

    sma = SMA(period=10)
    sma_of_rsi = sma.calculate(rsi_values)

    assert isinstance(sma_of_rsi, np.ndarray)
    assert len(sma_of_rsi) == len(prices)

def test_indicator_performance(prices):
    """Test indicator calculation performance."""
    import time

    # Test SMA performance
    sma = SMA(period=20)
    start_time = time.time()
    _ = sma.calculate(prices)
    sma_time = time.time() - start_time

    # Test EMA performance
    ema = EMA(period=20)
    start_time = time.time()
    _ = ema.calculate(prices)
    ema_time = time.time() - start_time

    # Both should calculate reasonably quickly
    assert sma_time < 0.1
    assert ema_time < 0.1

def test_indicator_serialization():
    """Test indicator serialization."""
    sma = SMA(period=20)

    # Convert to dict
    state = sma.__dict__

    # Create new indicator from state
    new_sma = SMA(period=state['period'])

    # Compare indicators
    assert new_sma.period == sma.period

def test_custom_indicator(prices):
    """Test creating custom indicator."""
    class CustomMA(Indicator):
        def __init__(self, period=20, weight=0.5):
            self.period = period
            self.weight = weight

        def calculate(self, data):
            """Weighted combination of SMA and EMA."""
            sma = SMA(self.period).calculate(data)
            ema = EMA(self.period).calculate(data)
            return self.weight * sma + (1 - self.weight) * ema

    custom = CustomMA(period=20, weight=0.5)
    result = custom.calculate(prices)

    assert isinstance(result, np.ndarray)
    assert len(result) == len(prices)

if __name__ == '__main__':
    pytest.main([__file__])
