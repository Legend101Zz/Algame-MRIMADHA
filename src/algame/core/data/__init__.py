"""
Core data management module.

This module provides:
1. Data source management
2. Market data containers
3. Data validation and preprocessing
4. Caching and persistence
"""

from .interface import DataSourceInterface, MarketData
from .manager import DataManager
from .factory import DataSourceFactory, create_data_source
from .sources.yahoo import YahooDataSource
from .sources.csv import CSVDataSource
from .sources.ibkr import IBKRDataSource
from .utils import (
    parse_timeframe,
    timeframe_to_seconds,
    convert_timeframe,
    validate_ohlcv,
    fill_missing_data,
    calculate_returns,
    detect_outliers
)

# Version info
__version__ = "0.1.0"

# Default data sources
DEFAULT_SOURCES = {
    'yahoo': YahooDataSource,
    'csv': CSVDataSource,
    'ibkr': IBKRDataSource
}

__all__ = [
    # Classes
    'DataSourceInterface',
    'MarketData',
    'DataManager',
    'DataSourceFactory',

    # Data sources
    'YahooDataSource',
    'CSVDataSource',
    'IBKRDataSource',

    # Functions
    'create_data_source',
    'parse_timeframe',
    'timeframe_to_seconds',
    'convert_timeframe',
    'validate_ohlcv',
    'fill_missing_data',
    'calculate_returns',
    'detect_outliers',

    # Constants
    'DEFAULT_SOURCES'
]
