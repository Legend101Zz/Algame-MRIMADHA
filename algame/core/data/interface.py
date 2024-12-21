from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
import pandas as pd
import numpy as np

class MarketData:
    """
    Container for market data with validation and preprocessing.

    This class provides a standardized interface for market data access
    and ensures data quality through validation and preprocessing.

    Key features:
    1. Data validation
    2. Automatic preprocessing
    3. Multiple timeframe support
    4. Efficient memory usage

    Attributes:
        symbol (str): Trading symbol
        timeframe (str): Data timeframe ('1m', '1h', '1d', etc.)
        start_date (datetime): First data point timestamp
        end_date (datetime): Last data point timestamp
        columns (List[str]): Available data columns
    """

    def __init__(self,
                 data: pd.DataFrame,
                 symbol: str,
                 timeframe: str,
                 validate: bool = True):
        """
        Initialize market data.

        Args:
            data: Raw market data DataFrame
            symbol: Trading symbol
            timeframe: Data timeframe
            validate: Whether to validate data

        Raises:
            ValueError: If data validation fails
        """
        self.symbol = symbol
        self.timeframe = timeframe

        # Store data
        self._data = data.copy()

        # Validate if requested
        if validate:
            self._validate_data()

        # Set attributes
        self.columns = list(self._data.columns)
        self.start_date = self._data.index[0]
        self.end_date = self._data.index[-1]

    def _validate_data(self) -> None:
        """
        Validate data format and quality.

        Checks:
        1. Required columns
        2. Index format
        3. Data types
        4. Missing values
        5. Price relationships

        Raises:
            ValueError: If validation fails
        """
        # Check index
        if not isinstance(self._data.index, pd.DatetimeIndex):
            raise ValueError("Data index must be DatetimeIndex")

        # Check required columns
        required = ['Open', 'High', 'Low', 'Close']
        missing = [col for col in required if col not in self._data.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        # Check data types
        for col in required:
            if not np.issubdtype(self._data[col].dtype, np.number):
                raise ValueError(f"Column {col} must be numeric")

        # Check for missing values
        if self._data[required].isnull().any().any():
            raise ValueError("Data contains missing values")

        # Check price relationships
        if not (
            (self._data['High'] >= self._data['Low']).all() and
            (self._data['High'] >= self._data['Open']).all() and
            (self._data['High'] >= self._data['Close']).all() and
            (self._data['Low'] <= self._data['Open']).all() and
            (self._data['Low'] <= self._data['Close']).all()
        ):
            raise ValueError("Invalid price relationships")

    def get_data(self,
                 columns: Optional[List[str]] = None,
                 start: Optional[Union[str, datetime]] = None,
                 end: Optional[Union[str, datetime]] = None) -> pd.DataFrame:
        """
        Get subset of market data.

        Args:
            columns: Columns to include (all if None)
            start: Start timestamp (earliest if None)
            end: End timestamp (latest if None)

        Returns:
            pd.DataFrame: Requested data subset
        """
        # Select columns
        data = self._data[columns] if columns else self._data

        # Select time range
        if start:
            data = data[data.index >= pd.Timestamp(start)]
        if end:
            data = data[data.index <= pd.Timestamp(end)]

        return data

    def add_column(self,
                   name: str,
                   data: Union[pd.Series, np.ndarray],
                   overwrite: bool = False) -> None:
        """
        Add new data column.

        Args:
            name: Column name
            data: Column data
            overwrite: Whether to overwrite existing column

        Raises:
            ValueError: If column exists and overwrite=False
        """
        if name in self._data and not overwrite:
            raise ValueError(f"Column '{name}' already exists")

        self._data[name] = data
        if name not in self.columns:
            self.columns.append(name)

    def remove_column(self, name: str) -> None:
        """
        Remove data column.

        Args:
            name: Column to remove

        Raises:
            ValueError: If column is required or doesn't exist
        """
        if name not in self._data:
            raise ValueError(f"Column '{name}' not found")

        if name in ['Open', 'High', 'Low', 'Close']:
            raise ValueError(f"Cannot remove required column: {name}")

        del self._data[name]
        self.columns.remove(name)

    def resample(self, timeframe: str) -> 'MarketData':
        """
        Resample data to new timeframe.

        Args:
            timeframe: Target timeframe

        Returns:
            MarketData: Resampled data

        Raises:
            ValueError: If invalid timeframe
        """
        # Convert timeframe to pandas offset
        try:
            offset = self._timeframe_to_offset(timeframe)
        except ValueError as e:
            raise ValueError(f"Invalid timeframe: {e}")

        # Resample OHLCV data
        resampled = self._data.resample(offset).agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum' if 'Volume' in self._data else None
        }).dropna()

        return MarketData(resampled, self.symbol, timeframe)

    @staticmethod
    def _timeframe_to_offset(timeframe: str) -> str:
        """Convert timeframe to pandas offset string."""
        # Map timeframes to pandas offsets
        mapping = {
            's': 'S',   # seconds
            'm': 'T',   # minutes
            'h': 'H',   # hours
            'd': 'D',   # days
            'w': 'W',   # weeks
            'M': 'M'    # months
        }

        # Parse timeframe
        try:
            number = int(timeframe[:-1])
            unit = timeframe[-1]
            if unit not in mapping:
                raise ValueError
            return f"{number}{mapping[unit]}"
        except (ValueError, IndexError):
            raise ValueError(
                f"Invalid timeframe format: {timeframe}. "
                "Must be number + unit (s,m,h,d,w,M)"
            )

    def __len__(self) -> int:
        """Get number of data points."""
        return len(self._data)

    def __getitem__(self, key: str) -> pd.Series:
        """Get data column."""
        return self._data[key]

    def __contains__(self, key: str) -> bool:
        """Check if column exists."""
        return key in self._data

class DataSourceInterface(ABC):
    """
    Interface for market data sources.

    This abstract class defines the standard interface that all
    data sources must implement. This ensures consistent behavior
    across different data sources while allowing source-specific
    optimizations.
    """

    @abstractmethod
    def get_data(self,
                 symbol: str,
                 start: Optional[Union[str, datetime]] = None,
                 end: Optional[Union[str, datetime]] = None,
                 timeframe: str = '1d') -> MarketData:
        """
        Get market data for symbol.

        Args:
            symbol: Trading symbol
            start: Start timestamp
            end: End timestamp
            timeframe: Data timeframe

        Returns:
            MarketData: Market data container
        """
        pass

    @abstractmethod
    def get_symbols(self) -> List[str]:
        """Get list of available symbols."""
        pass

    @abstractmethod
    def get_timeframes(self, symbol: str) -> List[str]:
        """Get available timeframes for symbol."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Get data source name."""
        pass
