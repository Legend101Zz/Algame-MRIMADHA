import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
from datetime import datetime, timedelta

from algame.core.data import (
    DataManager,
    MarketData,
    DataSourceInterface,
    YahooDataSource,
    CSVDataSource
)

# Sample data source for testing
class MockDataSource(DataSourceInterface):
    def __init__(self):
        self._data = {}

    def get_data(self, symbol, start=None, end=None, timeframe='1d'):
        if symbol not in self._data:
            raise ValueError(f"Symbol not found: {symbol}")
        data = self._data[symbol]

        if start:
            data = data[data.index >= pd.Timestamp(start)]
        if end:
            data = data[data.index <= pd.Timestamp(end)]

        return MarketData(data, symbol, timeframe)

    def get_symbols(self):
        return list(self._data.keys())

    def get_timeframes(self, symbol):
        return ['1d']

    @property
    def name(self):
        return "MockSource"

# Helper function to create sample data
def create_sample_data(symbol='AAPL', periods=100):
    dates = pd.date_range(start='2020-01-01', periods=periods, freq='D')
    data = pd.DataFrame({
        'Open': np.random.randn(periods).cumsum() + 100,
        'High': np.random.randn(periods).cumsum() + 102,
        'Low': np.random.randn(periods).cumsum() + 98,
        'Close': np.random.randn(periods).cumsum() + 100,
        'Volume': np.random.randint(1000000, 10000000, periods)
    }, index=dates)
    return data

# Test MarketData class
def test_market_data():
    data = create_sample_data()
    market_data = MarketData(data, 'AAPL', '1d')

    assert market_data.symbol == 'AAPL'
    assert market_data.timeframe == '1d'
    assert isinstance(market_data.start_date, pd.Timestamp)
    assert isinstance(market_data.end_date, pd.Timestamp)
    assert len(market_data.columns) == 5

    # Test data validation
    with pytest.raises(ValueError):
        # Missing required columns
        bad_data = pd.DataFrame({'A': [1, 2, 3]})
        MarketData(bad_data, 'AAPL', '1d')

# Test DataManager initialization and configuration
def test_data_manager_init():
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = DataManager(data_dir=tmpdir)
        assert manager.data_dir == Path(tmpdir)
        assert manager.enable_cache

        # Test source registration
        source = MockDataSource()
        manager.add_source('mock', source)
        assert 'mock' in manager._sources

# Test data loading and caching
def test_data_loading():
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = DataManager(data_dir=tmpdir)
        source = MockDataSource()

        # Add sample data to mock source
        source._data['AAPL'] = create_sample_data('AAPL')
        manager.add_source('mock', source)

        # Load data
        data = manager.get_data('AAPL', source='mock')
        assert isinstance(data, MarketData)
        assert data.symbol == 'AAPL'

        # Test caching
        cached_file = Path(tmpdir) / 'cache' / 'AAPL' / '1d' / '2020-01.parquet'
        assert cached_file.exists()

        # Load from cache
        cached_data = manager.get_data('AAPL', source='mock')
        pd.testing.assert_frame_equal(data._data, cached_data._data)

# Test data validation
def test_data_validation():
    manager = DataManager()

    # Valid data
    valid_data = create_sample_data()
    assert manager.validate_data(valid_data)

    # Invalid data
    invalid_data = pd.DataFrame({
        'A': [1, 2, 3],
        'B': [4, 5, 6]
    })
    with pytest.raises(ValueError):
        manager.validate_data(invalid_data)

# Test timeframe conversion
def test_timeframe_conversion():
    data = create_sample_data(periods=100)
    market_data = MarketData(data, 'AAPL', '1d')

    # Convert to higher timeframe
    weekly = market_data.resample('1w')
    assert weekly.timeframe == '1w'
    assert len(weekly._data) < len(data)

    # Verify OHLCV aggregation
    assert (weekly._data['High'] >= weekly._data['Open']).all()
    assert (weekly._data['High'] >= weekly._data['Close']).all()
    assert (weekly._data['Low'] <= weekly._data['Open']).all()
    assert (weekly._data['Low'] <= weekly._data['Close']).all()

# Test data source management
def test_data_source_management():
    manager = DataManager()

    # Add source
    source = MockDataSource()
    manager.add_source('mock', source)
    assert 'mock' in manager._sources

    # Remove source
    manager.remove_source('mock')
    assert 'mock' not in manager._sources

    # Get available symbols
    source._data['AAPL'] = create_sample_data('AAPL')
    source._data['GOOGL'] = create_sample_data('GOOGL')
    manager.add_source('mock', source)

    symbols = manager.get_available_symbols(source='mock')
    assert set(symbols) == {'AAPL', 'GOOGL'}

# Test CSV data source
def test_csv_data_source():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create sample CSV
        data = create_sample_data('AAPL')
        csv_file = Path(tmpdir) / 'AAPL.csv'
        data.to_csv(csv_file)

        # Initialize source
        source = CSVDataSource(base_dir=tmpdir)

        # Load data
        loaded_data = source.get_data('AAPL')
        pd.testing.assert_frame_
