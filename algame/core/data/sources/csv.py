from typing import Dict, List, Optional, Union, Any
from datetime import datetime
import pandas as pd
from pathlib import Path
import logging
import re

from ..interface import DataSourceInterface, MarketData

logger = logging.getLogger(__name__)

class CSVDataSource(DataSourceInterface):
    """
    CSV file data source implementation.

    Features:
    1. Flexible directory structure
    2. Multiple file formats
    3. Column mapping
    4. Data validation

    The class supports multiple directory structures:
    1. Flat: all files in one directory
    2. Hierarchical: symbol/timeframe/files
    3. Combined: symbol_timeframe_date.csv
    """

    def __init__(self,
                base_dir: Union[str, Path],
                structure: str = 'flat',
                file_pattern: str = '{symbol}_{timeframe}_{date}.csv',
                column_map: Optional[Dict[str, str]] = None):
        """
        Initialize CSV data source.

        Args:
            base_dir: Base directory for data files
            structure: Directory structure ('flat', 'hierarchical', 'combined')
            file_pattern: Pattern for file names
            column_map: Mapping of file columns to standard names

        Example patterns:
            - "AAPL_1d_2023.csv"
            - "daily/AAPL_2023.csv"
            - "AAPL/1d/data.csv"
        """
        self.base_dir = Path(base_dir)
        self.structure = structure
        self.file_pattern = file_pattern

        # Default column mapping
        self.column_map = column_map or {
            'Open': 'Open',
            'High': 'High',
            'Low': 'Low',
            'Close': 'Close',
            'Volume': 'Volume',
            'Date': 'Date',
            'Timestamp': 'Timestamp'
        }

        # Compile file pattern regex
        self._pattern_regex = self._compile_pattern(file_pattern)

        # Cache for available symbols/timeframes
        self._available_data: Optional[Dict[str, List[str]]] = None

        logger.debug(f"Initialized CSV data source at: {self.base_dir}")

    def get_data(self,
                 symbol: str,
                 start: Optional[Union[str, datetime]] = None,
                 end: Optional[Union[str, datetime]] = None,
                 timeframe: str = '1d') -> MarketData:
        """
        Get market data from CSV files.

        Args:
            symbol: Trading symbol
            start: Start timestamp
            end: End timestamp
            timeframe: Data timeframe

        Returns:
            MarketData: Market data container

        Raises:
            ValueError: If data not found or invalid
        """
        # Find relevant files
        files = self._find_data_files(symbol, timeframe)
        if not files:
            raise ValueError(f"No data found for {symbol} ({timeframe})")

        try:
            # Read and combine files
            data = []
            for file in files:
                df = self._read_csv_file(file)
                data.append(df)

            # Combine data
            combined = pd.concat(data).sort_index()

            # Filter date range
            if start:
                combined = combined[combined.index >= pd.Timestamp(start)]
            if end:
                combined = combined[combined.index <= pd.Timestamp(end)]

            return MarketData(combined, symbol, timeframe)

        except Exception as e:
            logger.error(f"Error reading data for {symbol}: {str(e)}")
            raise

    def get_symbols(self) -> List[str]:
        """
        Get list of available symbols.

        Scans directory structure to find all available symbols.

        Returns:
            List[str]: Available symbols
        """
        self._scan_available_data()
        return list(self._available_data.keys())

    def get_timeframes(self, symbol: str) -> List[str]:
        """
        Get available timeframes for symbol.

        Args:
            symbol: Trading symbol

        Returns:
            List[str]: Available timeframes
        """
        self._scan_available_data()
        return self._available_data.get(symbol, [])

    @property
    def name(self) -> str:
        """Get data source name."""
        return "CSV Files"

    def _compile_pattern(self, pattern: str) -> re.Pattern:
        """
        Compile file pattern into regex.

        Converts pattern with placeholders to regex pattern.
        E.g., "{symbol}_{timeframe}.csv" -> "([^_]+)_([^_]+)\.csv"

        Args:
            pattern: File name pattern

        Returns:
            re.Pattern: Compiled regex pattern
        """
        # Escape special characters
        regex = re.escape(pattern)

        # Replace placeholders with capture groups
        replacements = {
            r'\{symbol\}': r'(?P<symbol>[^_]+)',
            r'\{timeframe\}': r'(?P<timeframe>[^_]+)',
            r'\{date\}': r'(?P<date>\d{4}(?:-\d{2})?(?:-\d{2})?)'
        }

        for placeholder, group in replacements.items():
            regex = regex.replace(placeholder, group)

        return re.compile(regex)

    def _find_data_files(self, symbol: str, timeframe: str) -> List[Path]:
        """
        Find all data files for symbol and timeframe.

        Handles different directory structures:
        - Flat: search all files in base directory
        - Hierarchical: look in symbol/timeframe directory
        - Combined: search for specific pattern

        Args:
            symbol: Trading symbol
            timeframe: Data timeframe

        Returns:
            List[Path]: Found data files
        """
        if self.structure == 'flat':
            # Search in base directory
            return sorted(
                f for f in self.base_dir.glob('*.csv')
                if self._matches_pattern(f.name, symbol, timeframe)
            )

        elif self.structure == 'hierarchical':
            # Look in symbol/timeframe directory
            data_dir = self.base_dir / symbol / timeframe
            return sorted(data_dir.glob('*.csv')) if data_dir.exists() else []

        else:  # combined
            # Search for specific pattern
            pattern = self.file_pattern.format(
                symbol=symbol,
                timeframe=timeframe,
                date='*'
            )
            return sorted(self.base_dir.glob(pattern))

    def _matches_pattern(self,
                        filename: str,
                        symbol: str,
                        timeframe: str) -> bool:
        """Check if filename matches pattern for symbol/timeframe."""
        match = self._pattern_regex.match(filename)
        if not match:
            return False

        return (
            match.group('symbol') == symbol and
            match.group('timeframe') == timeframe
        )


    def _read_csv_file(self, file_path: Path) -> pd.DataFrame:
        """
        Read and process CSV file.

        Handles:
        1. Column mapping
        2. Date parsing
        3. Data validation
        4. Type conversion

        Args:
            file_path: Path to CSV file

        Returns:
            pd.DataFrame: Processed data

        Raises:
            ValueError: If file format is invalid
        """
        try:
            # Detect CSV format
            sep = self._detect_separator(file_path)

            # Read CSV
            df = pd.read_csv(
                file_path,
                sep=sep,
                parse_dates=True,
                infer_datetime_format=True
            )

            # Map columns
            df = self._map_columns(df)

            # Set index
            df = self._set_datetime_index(df)

            # Convert types
            df = self._convert_types(df)

            return df

        except Exception as e:
            logger.error(f"Error reading {file_path}: {str(e)}")
            raise

    def _detect_separator(self, file_path: Path) -> str:
        """
        Detect CSV separator character.

        Reads first few lines of file to detect separator.

        Args:
            file_path: Path to CSV file

        Returns:
            str: Detected separator
        """
        # Read first few lines
        with file_path.open('r') as f:
            sample = ''.join(f.readline() for _ in range(5))

        # Count potential separators
        separators = {
            ',': sample.count(','),
            ';': sample.count(';'),
            '\t': sample.count('\t'),
            '|': sample.count('|')
        }

        # Return most common separator
        sep = max(separators.items(), key=lambda x: x[1])[0]
        return sep if separators[sep] > 0 else ','

    def _map_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Map CSV columns to standard names.

        Args:
            df: Raw DataFrame

        Returns:
            pd.DataFrame: DataFrame with mapped columns

        Raises:
            ValueError: If required columns missing
        """
        # Create reverse mapping
        rev_map = {v: k for k, v in self.column_map.items()}

        # Find matching columns (case insensitive)
        mapped_cols = {}
        for col in df.columns:
            # Try exact match
            if col in rev_map:
                mapped_cols[col] = rev_map[col]
            else:
                # Try case-insensitive match
                col_lower = col.lower()
                for file_col, std_col in rev_map.items():
                    if file_col.lower() == col_lower:
                        mapped_cols[col] = std_col
                        break

        # Rename columns
        df = df.rename(columns=mapped_cols)

        # Check required columns
        required = ['Open', 'High', 'Low', 'Close']
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        return df

    def _set_datetime_index(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Set DataFrame datetime index.

        Tries different date/time columns by priority:
        1. 'Timestamp' column
        2. 'Date' column
        3. Existing index if datetime

        Args:
            df: DataFrame to process

        Returns:
            pd.DataFrame: DataFrame with datetime index

        Raises:
            ValueError: If no valid datetime found
        """
        # Try Timestamp column
        if 'Timestamp' in df.columns:
            df.set_index('Timestamp', inplace=True)

        # Try Date column
        elif 'Date' in df.columns:
            df.set_index('Date', inplace=True)

        # Verify/convert index
        if not isinstance(df.index, pd.DatetimeIndex):
            try:
                df.index = pd.to_datetime(df.index)
            except Exception as e:
                raise ValueError(f"No valid datetime index found: {str(e)}")

        # Ensure index is sorted
        if not df.index.is_monotonic_increasing:
            df.sort_index(inplace=True)

        return df

    def _convert_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert DataFrame columns to appropriate types.

        Args:
            df: DataFrame to process

        Returns:
            pd.DataFrame: Processed DataFrame
        """
        # Price columns should be float
        price_cols = ['Open', 'High', 'Low', 'Close']
        for col in price_cols:
            if col in df:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Volume should be int
        if 'Volume' in df:
            df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce')
            df['Volume'] = df['Volume'].fillna(0).astype(int)

        return df

    def _scan_available_data(self) -> None:
        """
        Scan directory for available data.

        Updates _available_data cache with found symbols
        and timeframes.
        """
        if self._available_data is not None:
            return

        self._available_data = {}

        try:
            if self.structure == 'flat':
                # Scan all CSV files
                for file in self.base_dir.glob('*.csv'):
                    match = self._pattern_regex.match(file.name)
                    if match:
                        symbol = match.group('symbol')
                        timeframe = match.group('timeframe')
                        if symbol not in self._available_data:
                            self._available_data[symbol] = []
                        if timeframe not in self._available_data[symbol]:
                            self._available_data[symbol].append(timeframe)

            elif self.structure == 'hierarchical':
                # Scan symbol directories
                for symbol_dir in self.base_dir.glob('*/'):
                    if symbol_dir.is_dir():
                        symbol = symbol_dir.name
                        self._available_data[symbol] = []
                        # Scan timeframe directories
                        for tf_dir in symbol_dir.glob('*/'):
                            if tf_dir.is_dir() and any(tf_dir.glob('*.csv')):
                                self._available_data[symbol].append(tf_dir.name)

            else:  # combined
                # Scan all matching files
                for file in self.base_dir.glob('*.csv'):
                    match = self._pattern_regex.match(file.name)
                    if match:
                        symbol = match.group('symbol')
                        timeframe = match.group('timeframe')
                        if symbol not in self._available_data:
                            self._available_data[symbol] = []
                        if timeframe not in self._available_data[symbol]:
                            self._available_data[symbol].append(timeframe)

            logger.debug(f"Found {len(self._available_data)} symbols with data")

        except Exception as e:
            logger.error(f"Error scanning data directory: {str(e)}")
            self._available_data = {}
            raise

    def add_data(self,
                symbol: str,
                timeframe: str,
                data: pd.DataFrame,
                filename: Optional[str] = None) -> None:
        """
        Add new data file.

        Args:
            symbol: Trading symbol
            timeframe: Data timeframe
            data: Data to save
            filename: Optional filename (default: auto-generated)
        """
        try:
            # Prepare data
            df = data.copy()

            # Ensure datetime index
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)

            # Generate filename
            if filename is None:
                date_str = df.index[0].strftime('%Y-%m')
                filename = self.file_pattern.format(
                    symbol=symbol,
                    timeframe=timeframe,
                    date=date_str
                )

            # Determine save path
            if self.structure == 'hierarchical':
                save_path = self.base_dir / symbol / timeframe / filename
                save_path.parent.mkdir(parents=True, exist_ok=True)
            else:
                save_path = self.base_dir / filename

            # Save data
            df.to_csv(save_path)
            logger.info(f"Saved data to {save_path}")

            # Update cache
            if self._available_data is not None:
                if symbol not in self._available_data:
                    self._available_data[symbol] = []
                if timeframe not in self._available_data[symbol]:
                    self._available_data[symbol].append(timeframe)

        except Exception as e:
            logger.error(f"Error saving data: {str(e)}")
            raise
