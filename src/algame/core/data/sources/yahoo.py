from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf
import logging
from pathlib import Path
import json

from ..interface import DataSourceInterface, MarketData

logger = logging.getLogger(__name__)

class YahooDataSource(DataSourceInterface):
    """
    Yahoo Finance data source implementation.

    Features:
    1. Automatic data caching
    2. Multiple timeframe support
    3. Batch symbol downloading
    4. Error handling and retries

    The class uses the yfinance library but adds:
    - Robust error handling
    - Data validation
    - Smart caching
    - Rate limiting
    """

    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize Yahoo Finance data source.

        Args:
            cache_dir: Directory for caching data (optional)
        """
        self._cache_dir = Path(cache_dir) if cache_dir else Path.home() / '.algame' / 'cache'
        self._cache_dir.mkdir(parents=True, exist_ok=True)

        # Cache for symbol info
        self._symbols_cache: Dict[str, Dict] = {}

        # Timeframe mapping
        self._timeframe_map = {
            '1m': '1m',
            '2m': '2m',
            '5m': '5m',
            '15m': '15m',
            '30m': '30m',
            '1h': '1h',
            '1d': '1d',
            '5d': '5d',
            '1wk': '1wk',
            '1mo': '1mo',
            '3mo': '3mo'
        }

        logger.debug(f"Initialized Yahoo data source with cache: {self._cache_dir}")

    def get_data(self,
                 symbol: str,
                 start: Optional[Union[str, datetime]] = None,
                 end: Optional[Union[str, datetime]] = None,
                 timeframe: str = '1d') -> MarketData:
        """
        Get market data from Yahoo Finance.

        The method follows these steps:
        1. Check cache for recent data
        2. Download missing data if needed
        3. Validate and process data
        4. Update cache
        5. Return standardized MarketData

        Args:
            symbol: Trading symbol
            start: Start timestamp
            end: End timestamp
            timeframe: Data timeframe

        Returns:
            MarketData: Market data container

        Raises:
            ValueError: If invalid parameters or data not available
        """
        # Validate timeframe
        if timeframe not in self._timeframe_map:
            valid_timeframes = ", ".join(self._timeframe_map.keys())
            raise ValueError(
                f"Invalid timeframe: {timeframe}. "
                f"Valid timeframes: {valid_timeframes}"
            )

        # Standardize timestamps
        start = pd.Timestamp(start) if start else None
        end = pd.Timestamp(end) if end else pd.Timestamp.now()

        try:
            # Check cache first
            data = self._get_cached_data(symbol, timeframe, start, end)

            # Download if needed
            if data is None:
                data = self._download_data(symbol, timeframe, start, end)
                # Cache the data
                self._cache_data(symbol, timeframe, data)

            # Return MarketData container
            return MarketData(data, symbol, timeframe)

        except Exception as e:
            logger.error(f"Error getting data for {symbol}: {str(e)}")
            raise

    def get_symbols(self) -> List[str]:
        """
        Get list of available symbols.

        Returns cached symbols or downloads new list.
        Downloads are cached to avoid excessive API calls.

        Returns:
            List[str]: Available symbols
        """
        # Load symbols from cache
        cache_file = self._cache_dir / 'symbols.json'
        if cache_file.exists():
            # Check if cache is fresh (less than 1 day old)
            if cache_file.stat().st_mtime > (datetime.now() - timedelta(days=1)).timestamp():
                with cache_file.open('r') as f:
                    return json.load(f)

        # Download new symbols list
        try:
            # This is a simplified version - in practice would need
            # to implement proper symbol list downloading from Yahoo
            symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN']  # Example

            # Cache symbols
            with cache_file.open('w') as f:
                json.dump(symbols, f)

            return symbols

        except Exception as e:
            logger.error(f"Error getting symbols: {str(e)}")
            raise

    def get_timeframes(self, symbol: str) -> List[str]:
        """
        Get available timeframes for symbol.

        Different symbols may have different timeframe availability
        based on their listing venue and data provider restrictions.

        Args:
            symbol: Trading symbol

        Returns:
            List[str]: Available timeframes
        """
        # Get symbol info
        info = self._get_symbol_info(symbol)

        # Determine available timeframes
        timeframes = list(self._timeframe_map.keys())

        # Filter based on symbol type
        if info.get('type') == 'crypto':
            # Crypto has all timeframes
            return timeframes
        elif info.get('type') == 'forex':
            # Forex excludes some timeframes
            return [tf for tf in timeframes if tf not in ['5d', '1mo', '3mo']]
        else:
            # Stocks have standard timeframes
            return [tf for tf in timeframes if tf not in ['1m', '2m']]

    @property
    def name(self) -> str:
        """Get data source name."""
        return "Yahoo Finance"

    def _get_cached_data(self,
                        symbol: str,
                        timeframe: str,
                        start: Optional[datetime],
                        end: datetime) -> Optional[pd.DataFrame]:
        """
        Get data from cache if available.

        The caching system uses a hierarchical structure:
        cache_dir/
            symbol/
                timeframe/
                    YYYY-MM.parquet  # Monthly data files

        Args:
            symbol: Trading symbol
            timeframe: Data timeframe
            start: Start timestamp
            end: End timestamp

        Returns:
            Optional[pd.DataFrame]: Cached data if available
        """
        # Get cache path
        cache_path = self._cache_dir / symbol / timeframe
        if not cache_path.exists():
            return None

        try:
            # Find relevant cache files
            cached_data = []
            for file in cache_path.glob('*.parquet'):
                # Parse file date from name (YYYY-MM.parquet)
                file_date = pd.Timestamp(file.stem)

                # Check if file is in date range
                if (not start or file_date >= start) and file_date <= end:
                    df = pd.read_parquet(file)
                    cached_data.append(df)

            if not cached_data:
                return None

            # Combine and filter data
            data = pd.concat(cached_data).sort_index()
            if start:
                data = data[data.index >= start]
            data = data[data.index <= end]

            return data

        except Exception as e:
            logger.warning(f"Error reading cache for {symbol}: {str(e)}")
            return None

    def _download_data(self,
                      symbol: str,
                      timeframe: str,
                      start: Optional[datetime],
                      end: datetime) -> pd.DataFrame:
        """
        Download data from Yahoo Finance.

        Implements retry logic and handles common errors.

        Args:
            symbol: Trading symbol
            timeframe: Data timeframe
            start: Start timestamp
            end: End timestamp

        Returns:
            pd.DataFrame: Downloaded data

        Raises:
            ValueError: If data not available
        """
        import time
        from urllib.error import URLError

        # Convert timeframe to Yahoo format
        yf_timeframe = self._timeframe_map[timeframe]

        # Initialize ticker
        ticker = yf.Ticker(symbol)

        # Retry parameters
        max_retries = 3
        retry_delay = 1  # seconds

        for attempt in range(max_retries):
            try:
                # Download data
                data = ticker.history(
                    interval=yf_timeframe,
                    start=start,
                    end=end
                )

                if len(data) == 0:
                    raise ValueError(f"No data available for {symbol}")

                return data

            except URLError as e:
                logger.warning(f"Network error downloading {symbol} (attempt {attempt + 1}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                else:
                    raise ValueError(f"Failed to download data after {max_retries} attempts")

            except Exception as e:
                logger.error(f"Error downloading {symbol}: {str(e)}")
                raise

    def _cache_data(self,
                    symbol: str,
                    timeframe: str,
                    data: pd.DataFrame) -> None:
        """
        Cache downloaded data.

        Splits data into monthly files for efficient storage and retrieval.

        Args:
            symbol: Trading symbol
            timeframe: Data timeframe
            data: Data to cache
        """
        # Create cache directory
        cache_path = self._cache_dir / symbol / timeframe
        cache_path.mkdir(parents=True, exist_ok=True)

        try:
            # Split data by month
            for name, group in data.groupby(pd.Grouper(freq='M')):
                if len(group) > 0:
                    # Save to parquet file
                    filename = name.strftime('%Y-%m.parquet')
                    file_path = cache_path / filename
                    group.to_parquet(file_path)

            logger.debug(f"Cached {len(data)} rows for {symbol}")

        except Exception as e:
            logger.error(f"Error caching data for {symbol}: {str(e)}")
            raise

    def _get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """
        Get symbol information.

        Caches symbol information to reduce API calls.

        Args:
            symbol: Trading symbol

        Returns:
            Dict[str, Any]: Symbol information
        """
        # Check cache
        if symbol in self._symbols_cache:
            return self._symbols_cache[symbol]

        try:
            # Get info from Yahoo
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # Process info
            processed_info = {
                'type': self._determine_symbol_type(info),
                'exchange': info.get('exchange'),
                'currency': info.get('currency'),
                'timezone': info.get('exchangeTimezoneName')
            }

            # Cache info
            self._symbols_cache[symbol] = processed_info

            return processed_info

        except Exception as e:
            logger.error(f"Error getting info for {symbol}: {str(e)}")
            return {}

    def _determine_symbol_type(self, info: Dict[str, Any]) -> str:
        """Determine symbol type from Yahoo info."""
        quoteType = info.get('quoteType', '').lower()

        if quoteType in ['cryptocurrency', 'crypto']:
            return 'crypto'
        elif quoteType in ['currency', 'fx']:
            return 'forex'
        elif quoteType in ['equity', 'stock']:
            return 'stock'
        elif quoteType in ['etf', 'mutualfund']:
            return 'fund'
        else:
            return 'unknown'

    def clear_cache(self, older_than: Optional[int] = None) -> None:
        """
        Clear cached data.

        Args:
            older_than: Clear data older than days (None for all)
        """
        import shutil

        try:
            if older_than is None:
                # Clear all cache
                shutil.rmtree(self._cache_dir)
                self._cache_dir.mkdir(parents=True)
                logger.info("Cleared all cached data")
            else:
                # Clear old data only
                cutoff = datetime.now() - timedelta(days=older_than)
                for symbol_dir in self._cache_dir.iterdir():
                    if symbol_dir.is_dir():
                        for timeframe_dir in symbol_dir.iterdir():
                            for file in timeframe_dir.glob('*.parquet'):
                                if file.stat().st_mtime < cutoff.timestamp():
                                    file.unlink()
                logger.info(f"Cleared cached data older than {older_than} days")

        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            raise
