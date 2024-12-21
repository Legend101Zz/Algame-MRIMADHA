from typing import Dict, List, Optional, Union, Any
from datetime import datetime
import pandas as pd
import logging
from pathlib import Path

from .interface import DataSourceInterface, MarketData
from .sources.yahoo import YahooDataSource
from .sources.csv import CSVDataSource

logger = logging.getLogger(__name__)

class DataManager:
    """
    Central manager for market data.

    This class provides a unified interface for accessing market data
    from multiple sources. It handles:
    1. Source registration and management
    2. Data caching and preprocessing
    3. Cross-source data merging
    4. Data validation and quality checks

    Features:
    - Multiple data source support
    - Smart caching
    - Data validation
    - Cross-source data merging
    - Parallel data loading
    """

    def __init__(self,
                data_dir: Optional[str] = None,
                enable_cache: bool = True):
        """
        Initialize data manager.

        Args:
            data_dir: Base directory for data storage
            enable_cache: Whether to enable data caching
        """
        self.data_dir = Path(data_dir) if data_dir else Path.home() / '.algame' / 'data'
        self.enable_cache = enable_cache

        # Initialize data sources
        self._sources: Dict[str, DataSourceInterface] = {}

        # Initialize cache
        if enable_cache:
            self.data_dir.mkdir(parents=True, exist_ok=True)

        # Register default sources
        self._register_default_sources()

        logger.debug("Initialized DataManager")

    def get_data(self,
                 symbol: str,
                 start: Optional[Union[str, datetime]] = None,
                 end: Optional[Union[str, datetime]] = None,
                 timeframe: str = '1d',
                 source: Optional[str] = None) -> MarketData:
        """
        Get market data.

        If source is specified, get data from that source.
        Otherwise, try sources in order until data is found.

        Args:
            symbol: Trading symbol
            start: Start timestamp
            end: End timestamp
            timeframe: Data timeframe
            source: Specific source to use

        Returns:
            MarketData: Market data

        Raises:
            ValueError: If data not found
        """
        # Check cache first
        if self.enable_cache:
            cached_data = self._get_cached_data(
                symbol, timeframe, start, end
            )
            if cached_data is not None:
                return cached_data

        try:
            # Try specified source
            if source:
                if source not in self._sources:
                    raise ValueError(f"Unknown data source: {source}")

                data = self._sources[source].get_data(
                    symbol, start, end, timeframe
                )

            else:
                # Try all sources
                errors = []
                for src_name, src in self._sources.items():
                    try:
                        data = src.get_data(
                            symbol, start, end, timeframe
                        )
                        source = src_name  # Remember successful source
                        break
                    except Exception as e:
                        errors.append(f"{src_name}: {str(e)}")
                else:
                    # No source had the data
                    raise ValueError(
                        f"Data not found in any source:\n" +
                        "\n".join(errors)
                    )

            # Cache data if enabled
            if self.enable_cache:
                self._cache_data(data, source)

            return data

        except Exception as e:
            logger.error(f"Error getting data for {symbol}: {str(e)}")
            raise

    def add_source(self,
                  name: str,
                  source: DataSourceInterface) -> None:
        """
        Register new data source.

        Args:
            name: Source name
            source: Data source instance

        Raises:
            ValueError: If source already registered
        """
        if name in self._sources:
            raise ValueError(f"Source '{name}' already registered")

        self._sources[name] = source
        logger.info(f"Registered data source: {name}")

    def remove_source(self, name: str) -> None:
        """
        Remove data source.

        Args:
            name: Source name to remove

        Raises:
            KeyError: If source not found
        """
        if name not in self._sources:
            raise KeyError(f"Source '{name}' not found")

        del self._sources[name]
        logger.info(f"Removed data source: {name}")

    def get_available_symbols(self,
                            source: Optional[str] = None) -> List[str]:
        """
        Get available symbols.

        Args:
            source: Specific source to check (None for all)

        Returns:
            List[str]: Available symbols
        """
        symbols = set()
        sources = ([self._sources[source]] if source
                  else self._sources.values())

        for src in sources:
            try:
                symbols.update(src.get_symbols())
            except Exception as e:
                logger.warning(f"Error getting symbols from {src.name}: {str(e)}")

        return sorted(symbols)

    def get_available_timeframes(self,
                               symbol: str,
                               source: Optional[str] = None) -> List[str]:
        """
        Get available timeframes for symbol.

        Args:
            symbol: Trading symbol
            source: Specific source to check (None for all)

        Returns:
            List[str]: Available timeframes
        """
        timeframes = set()
        sources = ([self._sources[source]] if source
                  else self._sources.values())

        for src in sources:
            try:
                timeframes.update(src.get_timeframes(symbol))
            except Exception as e:
                logger.warning(
                    f"Error getting timeframes from {src.name}: {str(e)}"
                )

        return sorted(timeframes)

    def clear_cache(self, older_than: Optional[int] = None) -> None:
        """
        Clear cached data.

        Args:
            older_than: Clear data older than days (None for all)
        """
        if not self.enable_cache:
            return

        try:
            if older_than:
                logger.info(f"Clearing cache older than {older_than} days")
                cutoff = datetime.now() - timedelta(days=older_than)
                for file in self.data_dir.glob('**/*.parquet'):
                    if file.stat().st_mtime < cutoff.timestamp():
                        file.unlink()
            else:
                logger.info("Clearing all cache")
                for file in self.data_dir.glob('**/*.parquet'):
                    file.unlink()

        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            raise

    def _register_default_sources(self) -> None:
        """Register default data sources."""
        # Register Yahoo Finance source
        self.add_source('yahoo', YahooDataSource(
            cache_dir=str(self.data_dir / 'yahoo')
        ))

        # Register CSV source if data directory exists
        csv_dir = self.data_dir / 'csv'
        if csv_dir.exists():
            self.add_source('csv', CSVDataSource(
                base_dir=str(csv_dir)
            ))

    def _get_cached_data(self,
                        symbol: str,
                        timeframe: str,
                        start: Optional[datetime],
                        end: Optional[datetime]) -> Optional[MarketData]:
        """
        Get data from cache if available.

        Args:
            symbol: Trading symbol
            timeframe: Data timeframe
            start: Start timestamp
            end: End timestamp

        Returns:
            Optional[MarketData]: Cached data if available
        """
        if not self.enable_cache:
            return None

        try:
            # Construct cache path
            cache_path = self.data_dir / 'cache' / symbol / timeframe

            if not cache_path.exists():
                return None

            # Find relevant cache files
            cached_data = []
            for file in cache_path.glob('*.parquet'):
                df = pd.read_parquet(file)

                # Filter date range
                if start:
                    df = df[df.index >= pd.Timestamp(start)]
                if end:
                    df = df[df.index <= pd.Timestamp(end)]

                if not df.empty:
                    cached_data.append(df)

            if not cached_data:
                return None

            # Combine cached data
            data = pd.concat(cached_data).sort_index()
            return MarketData(data, symbol, timeframe)

        except Exception as e:
            logger.warning(f"Error reading cache: {str(e)}")
            return None

    def _cache_data(self,
                    data: MarketData,
                    source: str) -> None:
        """
        Cache market data.

        Args:
            data: Data to cache
            source: Source that provided the data
        """
        if not self.enable_cache:
            return

        try:
            # Construct cache path
            cache_path = (self.data_dir / 'cache' /
                         data.symbol / data.timeframe)
            cache_path.mkdir(parents=True, exist_ok=True)

            # Split by month and save
            for name, group in data._data.groupby(pd.Grouper(freq='M')):
                if not group.empty:
                    # Create filename with source info
                    filename = (f"{name.strftime('%Y-%m')}_"
                              f"{source}.parquet")
                    file_path = cache_path / filename

                    # Save data
                    group.to_parquet(file_path)

        except Exception as e:
            logger.warning(f"Error caching data: {str(e)}")

    def update_data(self,
                    symbols: Union[str, List[str]],
                    timeframe: str = '1d',
                    source: Optional[str] = None,
                    **kwargs) -> Dict[str, MarketData]:
        """
        Update data for multiple symbols.

        Downloads latest data and updates cache.

        Args:
            symbols: Symbol(s) to update
            timeframe: Data timeframe
            source: Specific source to use
            **kwargs: Additional parameters for data source

        Returns:
            Dict[str, MarketData]: Updated data by symbol
        """
        if isinstance(symbols, str):
            symbols = [symbols]

        results = {}
        errors = []

        for symbol in symbols:
            try:
                # Get existing data
                try:
                    existing = self.get_data(
                        symbol,
                        timeframe=timeframe,
                        source=source
                    )
                    start = existing.end_date
                except ValueError:
                    start = None

                # Get new data
                new_data = self.get_data(
                    symbol,
                    start=start,
                    timeframe=timeframe,
                    source=source,
                    **kwargs
                )

                results[symbol] = new_data
                logger.info(f"Updated data for {symbol}")

            except Exception as e:
                errors.append(f"{symbol}: {str(e)}")

        if errors:
            logger.warning(
                "Errors updating symbols:\n" +
                "\n".join(errors)
            )

        return results

    def validate_data(self,
                     data: Union[MarketData, pd.DataFrame],
                     symbol: Optional[str] = None,
                     timeframe: Optional[str] = None) -> bool:
        """
        Validate market data.

        Args:
            data: Data to validate
            symbol: Symbol (required if DataFrame)
            timeframe: Timeframe (required if DataFrame)

        Returns:
            bool: True if valid

        Raises:
            ValueError: If validation fails
        """
        if isinstance(data, pd.DataFrame):
            if not symbol or not timeframe:
                raise ValueError(
                    "symbol and timeframe required for DataFrame"
                )
            data = MarketData(data, symbol, timeframe)

        # Data is already validated by MarketData class
        return True

    def merge_data(self,
                   sources: List[str],
                   symbol: str,
                   timeframe: str = '1d',
                   priority: Optional[List[str]] = None) -> MarketData:
        """
        Merge data from multiple sources.

        Args:
            sources: Sources to merge
            symbol: Trading symbol
            timeframe: Data timeframe
            priority: Source priority for conflicts

        Returns:
            MarketData: Merged data

        Raises:
            ValueError: If no data found
        """
        if not sources:
            raise ValueError("No sources specified")

        data_frames = []
        errors = []

        # Get data from each source
        for source in sources:
            try:
                data = self.get_data(
                    symbol,
                    timeframe=timeframe,
                    source=source
                )
                data_frames.append(data._data)
            except Exception as e:
                errors.append(f"{source}: {str(e)}")

        if not data_frames:
            raise ValueError(
                "No data found from any source:\n" +
                "\n".join(errors)
            )

        # Merge data frames
        if priority:
            # Use priority order
            merged = data_frames[0].copy()
            for df in data_frames[1:]:
                # Fill missing values from next source
                merged = merged.combine_first(df)
        else:
            # Use mean for overlapping values
            merged = pd.concat(data_frames).groupby(level=0).mean()

        return MarketData(merged, symbol, timeframe)
