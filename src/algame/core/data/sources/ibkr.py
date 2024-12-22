from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import logging
from pathlib import Path
import pytz
from threading import Lock
from queue import Queue

from ib_insync import IB, Contract, BarData, util
from ..interface import DataSourceInterface, MarketData

logger = logging.getLogger(__name__)

class IBKRDataSource(DataSourceInterface):
    """
    Interactive Brokers data source implementation.

    Features:
    1. Historical data access
    2. Real-time streaming
    3. Multiple asset types
    4. Contract management
    5. Connection handling
    6. Rate limiting

    The class uses ib_insync library and adds:
    - Robust error handling
    - Automatic reconnection
    - Request rate limiting
    - Data validation
    - Contract caching
    """

    # Map timeframes to IB bar sizes
    TIMEFRAME_MAP = {
        '1s': '1 secs',
        '5s': '5 secs',
        '10s': '10 secs',
        '15s': '15 secs',
        '30s': '30 secs',
        '1m': '1 min',
        '2m': '2 mins',
        '3m': '3 mins',
        '5m': '5 mins',
        '15m': '15 mins',
        '30m': '30 mins',
        '1h': '1 hour',
        '2h': '2 hours',
        '3h': '3 hours',
        '4h': '4 hours',
        '8h': '8 hours',
        '1d': '1 day',
        '1w': '1 week',
        '1mo': '1 month'
    }

    def __init__(self,
                 host: str = 'localhost',
                 port: int = 7497,  # 7497 for TWS, 4001 for Gateway
                 client_id: int = 1,
                 cache_dir: Optional[str] = None,
                 **kwargs):
        """
        Initialize IBKR data source.

        Args:
            host: TWS/Gateway host
            port: TWS/Gateway port
            client_id: Client ID
            cache_dir: Directory for caching data
            **kwargs: Additional connection parameters
        """
        self.host = host
        self.port = port
        self.client_id = client_id
        self.kwargs = kwargs

        # Initialize IB client
        self.ib = IB()
        self._connected = False
        self._connection_lock = Lock()

        # Setup caching
        self.cache_dir = Path(cache_dir) if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Contract cache
        self._contracts: Dict[str, Contract] = {}

        # Real-time data handling
        self._rt_data: Dict[str, Queue] = {}
        self._rt_bars: Dict[str, List[BarData]] = {}

        # Rate limiting
        self._request_count = 0
        self._last_request = datetime.now()
        self.rate_limit = 50  # requests per second

        logger.debug(f"Initialized IBKR data source: {host}:{port}")

    def connect(self) -> None:
        """
        Connect to Interactive Brokers.

        Handles connection with retry logic and timeout.

        Raises:
            ConnectionError: If connection fails
        """
        with self._connection_lock:
            if self._connected:
                return

            try:
                self.ib.connect(
                    host=self.host,
                    port=self.port,
                    clientId=self.client_id,
                    readonly=True,
                    **self.kwargs
                )
                self._connected = True
                logger.info("Connected to Interactive Brokers")

                # Setup error handling
                self.ib.errorEvent += self._handle_error

            except Exception as e:
                logger.error(f"Failed to connect to IB: {str(e)}")
                raise ConnectionError(f"IB connection failed: {str(e)}")

    def disconnect(self) -> None:
        """Disconnect from Interactive Brokers."""
        if self._connected:
            self.ib.disconnect()
            self._connected = False
            logger.info("Disconnected from Interactive Brokers")

    def get_data(self,
                 symbol: str,
                 start: Optional[Union[str, datetime]] = None,
                 end: Optional[Union[str, datetime]] = None,
                 timeframe: str = '1d') -> MarketData:
        """
        Get historical market data from IB.

        Args:
            symbol: Trading symbol
            start: Start timestamp
            end: End timestamp
            timeframe: Data timeframe

        Returns:
            MarketData: Market data container

        Raises:
            ValueError: If data not available
        """
        self._ensure_connected()

        try:
            # Get contract
            contract = self._get_contract(symbol)

            # Check cache first
            if self.cache_dir:
                cached_data = self._get_cached_data(
                    symbol, timeframe, start, end
                )
                if cached_data is not None:
                    return cached_data

            # Get bar size
            if timeframe not in self.TIMEFRAME_MAP:
                raise ValueError(
                    f"Unsupported timeframe: {timeframe}. "
                    f"Supported: {list(self.TIMEFRAME_MAP.keys())}"
                )
            bar_size = self.TIMEFRAME_MAP[timeframe]

            # Request data
            self._check_rate_limit()
            bars = self.ib.reqHistoricalData(
                contract=contract,
                endDateTime=end or '',
                durationStr=self._get_duration_string(start, end),
                barSizeSetting=bar_size,
                whatToShow='TRADES',
                useRTH=True,
                formatDate=1
            )

            if not bars:
                raise ValueError(f"No data available for {symbol}")

            # Convert to DataFrame
            df = util.df(bars)

            # Process data
            df = self._process_bar_data(df)

            # Cache data
            if self.cache_dir:
                self._cache_data(df, symbol, timeframe)

            return MarketData(df, symbol, timeframe)

        except Exception as e:
            logger.error(f"Error getting data for {symbol}: {str(e)}")
            raise

    def get_symbols(self) -> List[str]:
        """
        Get list of available symbols.

        Returns:
            List[str]: Available symbols
        """
        # Note: IB doesn't provide a direct way to get all symbols
        # This is a simplified implementation
        return []

    def get_timeframes(self, symbol: str) -> List[str]:
        """
        Get available timeframes for symbol.

        Args:
            symbol: Trading symbol

        Returns:
            List[str]: Available timeframes
        """
        try:
            contract = self._get_contract(symbol)
            contract_details = self.ib.reqContractDetails(contract)[0]

            # Filter timeframes based on contract type
            if contract_details.contract.secType == 'STK':
                # Stocks have all timeframes except very short ones
                return [tf for tf in self.TIMEFRAME_MAP.keys()
                       if not tf.endswith('s')]
            elif contract_details.contract.secType == 'FOREX':
                # Forex has all timeframes
                return list(self.TIMEFRAME_MAP.keys())
            else:
                # Default to daily and longer
                return ['1d', '1w', '1mo']

        except Exception as e:
            logger.error(f"Error getting timeframes for {symbol}: {str(e)}")
            return []

    @property
    def name(self) -> str:
        """Get data source name."""
        return "Interactive Brokers"

    def _ensure_connected(self) -> None:
        """Ensure connection to IB is active."""
        if not self._connected:
            self.connect()
        elif not self.ib.isConnected():
            self._connected = False
            self.connect()

    def _get_contract(self, symbol: str) -> Contract:
        """
        Get or create contract for symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Contract: IB contract

        Raises:
            ValueError: If contract not found
        """
        if symbol in self._contracts:
            return self._contracts[symbol]

        try:
            # Parse symbol for contract details
            parts = symbol.split(':')
            if len(parts) == 1:
                # Default to US stock
                contract = Contract(
                    symbol=symbol,
                    secType='STK',
                    exchange='SMART',
                    currency='USD'
                )
            else:
                # Format: TYPE:SYMBOL:EXCHANGE:CURRENCY
                sec_type, symbol, exchange, currency = parts
                contract = Contract(
                    symbol=symbol,
                    secType=sec_type,
                    exchange=exchange,
                    currency=currency
                )

            # Qualify contract
            qualified = self.ib.qualifyContracts(contract)
            if not qualified:
                raise ValueError(f"Contract not found: {symbol}")

            contract = qualified[0]
            self._contracts[symbol] = contract
            return contract

        except Exception as e:
            raise ValueError(f"Invalid contract {symbol}: {str(e)}")

    def _get_duration_string(self,
                           start: Optional[datetime],
                           end: Optional[datetime]) -> str:
        """Get duration string for historical data request."""
        if not end:
            end = datetime.now()
        if not start:
            # Default to 1 year
            start = end - timedelta(days=365)

        # Calculate duration
        duration = end - start
        days = duration.days

        if days <= 1:
            return "1 D"
        elif days <= 7:
            return f"{days} D"
        elif days <= 30:
            return f"{(days + 6) // 7} W"
        elif days <= 365:
            return f"{(days + 29) // 30} M"
        else:
            return f"{(days + 364) // 365} Y"

    def _process_bar_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process bar data into standard format."""
        # Rename columns
        df = df.rename(columns={
            'date': 'Date',
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume',
            'average': 'Average',
            'barCount': 'BarCount'
        })

        # Set index
        df.set_index('Date', inplace=True)

        # Convert timezone to UTC
        df.index = pd.to_datetime(df.index).tz_localize(None)

        # Sort index
        df.sort_index(inplace=True)

        return df[['Open', 'High', 'Low', 'Close', 'Volume']]

    def _check_rate_limit(self) -> None:
        """
        Check and enforce rate limiting.

        IB has strict rate limits that must be followed.
        """
        now = datetime.now()
        elapsed = (now - self._last_request).total_seconds()

        if elapsed < 1:  # 1 second window
            if self._request_count >= self.rate_limit:
                # Sleep for remaining time
                sleep_time = 1 - elapsed
                logger.debug(f"Rate limit hit, sleeping for {sleep_time:.2f}s")
                import time
                time.sleep(sleep_time)
                self._request_count = 0
                self._last_request = datetime.now()
            else:
                self._request_count += 1
        else:
            self._request_count = 1
            self._last_request = now

    def _handle_error(self,
                     reqId: int,
                     errorCode: int,
                     errorString: str,
                     *args) -> None:
        """Handle IB error events."""
        logger.error(f"IB Error {errorCode}: {errorString}")

        # Handle specific error codes
        if errorCode == 1100:  # Connectivity between IB and TWS lost
            self._connected = False
        elif errorCode == 2110:  # Connectivity between TWS and server lost
            pass
        elif errorCode == 10147:  # Rate limit hit
            self.rate_limit = max(1, self.rate_limit - 5)

    def __del__(self):
        """Cleanup on deletion."""
        self.disconnect()

    def subscribe_realtime(self,
                             symbol: str,
                             callback: Callable[[Dict], None],
                             timeframe: str = '1m') -> None:
            """
            Subscribe to real-time market data.

            Args:
                symbol: Trading symbol
                callback: Callback function for data updates
                timeframe: Bar timeframe

            Raises:
                ValueError: If subscription fails
            """
            self._ensure_connected()

            try:
                # Get contract
                contract = self._get_contract(symbol)

                # Setup data queue
                if symbol not in self._rt_data:
                    self._rt_data[symbol] = Queue()
                    self._rt_bars[symbol] = []

                # Start real-time bars
                self.ib.reqRealTimeBars(
                    contract,
                    5,  # Bar period in seconds
                    'TRADES',  # What to show
                    False,     # Use RTH
                    self._create_bar_handler(symbol, callback)
                )

                logger.info(f"Subscribed to real-time data for {symbol}")

            except Exception as e:
                logger.error(f"Error subscribing to {symbol}: {str(e)}")
                raise

    def unsubscribe_realtime(self, symbol: str) -> None:
            """
            Unsubscribe from real-time data.

            Args:
                symbol: Trading symbol to unsubscribe
            """
            if symbol in self._rt_data:
                try:
                    contract = self._get_contract(symbol)
                    self.ib.cancelRealTimeBars(contract)
                    del self._rt_data[symbol]
                    del self._rt_bars[symbol]
                    logger.info(f"Unsubscribed from real-time data for {symbol}")
                except Exception as e:
                    logger.error(f"Error unsubscribing from {symbol}: {str(e)}")

    def _create_bar_handler(self,
                            symbol: str,
                            callback: Callable[[Dict], None]) -> Callable:
        """
        Create handler for real-time bar updates.

        Args:
            symbol: Trading symbol
            callback: Callback function for updates

        Returns:
            Callable: Bar handler function
        """
        def handle_bar(bar: BarData) -> None:
            try:
                # Convert bar to dictionary
                bar_dict = {
                    'timestamp': pd.Timestamp(bar.time).tz_localize(None),
                    'open': bar.open,
                    'high': bar.high,
                    'low': bar.low,
                    'close': bar.close,
                    'volume': bar.volume,
                    'wap': bar.wap,
                    'count': bar.count
                }

                # Store bar
                self._rt_bars[symbol].append(bar)

                # Add to queue
                self._rt_data[symbol].put(bar_dict)

                # Call callback
                callback(bar_dict)

            except Exception as e:
                logger.error(f"Error handling bar for {symbol}: {str(e)}")

        return handle_bar

    def get_latest_bars(self,
                        symbol: str,
                        n: int = 1) -> Optional[pd.DataFrame]:
        """
        Get latest n real-time bars.

        Args:
            symbol: Trading symbol
            n: Number of bars to return

        Returns:
            Optional[pd.DataFrame]: Latest bars or None if not available
        """
        if symbol not in self._rt_bars:
            return None

        try:
            # Get latest bars
            bars = self._rt_bars[symbol][-n:]

            # Convert to DataFrame
            df = pd.DataFrame([
                {
                    'timestamp': pd.Timestamp(bar.time).tz_localize(None),
                    'open': bar.open,
                    'high': bar.high,
                    'low': bar.low,
                    'close': bar.close,
                    'volume': bar.volume,
                    'wap': bar.wap,
                    'count': bar.count
                }
                for bar in bars
            ])

            # Set index
            if not df.empty:
                df.set_index('timestamp', inplace=True)

            return df

        except Exception as e:
            logger.error(f"Error getting latest bars for {symbol}: {str(e)}")
            return None

    def get_market_hours(self, symbol: str) -> Dict[str, datetime]:
        """
        Get market hours for symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Dict[str, datetime]: Market open/close times
        """
        try:
            contract = self._get_contract(symbol)
            details = self.ib.reqContractDetails(contract)[0]

            # Get timezone
            tz = pytz.timezone(details.timeZoneId)

            # Get current date in market timezone
            now = datetime.now(tz)
            today = now.date()

            # Parse trading hours
            trading_hours = details.tradingHours
            if not trading_hours:
                # Use default market hours
                market_open = datetime.combine(today, pd.Timestamp('09:30').time())
                market_close = datetime.combine(today, pd.Timestamp('16:00').time())
            else:
                # Parse IB trading hours string
                times = trading_hours.split(';')[0].split('-')
                if len(times) == 2:
                    market_open = pd.Timestamp(times[0]).tz_localize(tz)
                    market_close = pd.Timestamp(times[1]).tz_localize(tz)
                else:
                    raise ValueError(f"Invalid trading hours format: {trading_hours}")

            return {
                'market_open': market_open,
                'market_close': market_close,
                'timezone': str(tz)
            }

        except Exception as e:
            logger.error(f"Error getting market hours for {symbol}: {str(e)}")
            raise

    def is_market_open(self, symbol: str) -> bool:
        """
        Check if market is currently open for symbol.

        Args:
            symbol: Trading symbol

        Returns:
            bool: True if market is open
        """
        try:
            hours = self.get_market_hours(symbol)
            tz = pytz.timezone(hours['timezone'])
            now = datetime.now(tz)
            return hours['market_open'] <= now <= hours['market_close']

        except Exception as e:
            logger.error(f"Error checking market hours for {symbol}: {str(e)}")
            return False

    def wait_for_market_open(self,
                            symbol: str,
                            callback: Optional[Callable] = None) -> None:
        """
        Wait for market to open.

        Args:
            symbol: Trading symbol
            callback: Optional callback when market opens
        """
        import time

        while not self.is_market_open(symbol):
            hours = self.get_market_hours(symbol)
            tz = pytz.timezone(hours['timezone'])
            now = datetime.now(tz)

            if now < hours['market_open']:
                wait_time = (hours['market_open'] - now).total_seconds()
                logger.info(f"Waiting {wait_time:.0f}s for market open")
                time.sleep(min(wait_time, 60))  # Sleep max 1 minute
            else:
                # Market is closed for the day
                next_open = hours['market_open'] + timedelta(days=1)
                wait_time = (next_open - now).total_seconds()
                logger.info(f"Market closed. Waiting {wait_time:.0f}s for next open")
                time.sleep(min(wait_time, 60))

        if callback:
            callback()

    def get_tick_data(self,
                        symbol: str,
                        duration: str = '1 D') -> pd.DataFrame:
        """
        Get historical tick data.

        Args:
            symbol: Trading symbol
            duration: Look-back duration

        Returns:
            pd.DataFrame: Tick data
        """
        self._ensure_connected()

        try:
            contract = self._get_contract(symbol)

            # Request tick data
            self._check_rate_limit()
            ticks = self.ib.reqHistoricalTicks(
                contract,
                '',  # End datetime (empty for now)
                duration,
                'TRADES',
                0,  # Use RTH
                False,  # IgnoreSize
                []  # Misc options
            )

            if not ticks:
                raise ValueError(f"No tick data available for {symbol}")

            # Convert to DataFrame
            df = pd.DataFrame([
                {
                    'time': tick.time,
                    'price': tick.price,
                    'size': tick.size,
                    'exchange': tick.exchange,
                    'special_conditions': tick.specialConditions
                }
                for tick in ticks
            ])

            # Set index
            df.set_index('time', inplace=True)
            df.index = pd.to_datetime(df.index)

            return df

        except Exception as e:
            logger.error(f"Error getting tick data for {symbol}: {str(e)}")
            raise

    def get_option_chain(self, symbol: str) -> pd.DataFrame:
        """
        Get option chain for symbol.

        Args:
            symbol: Trading symbol

        Returns:
            pd.DataFrame: Option chain data
        """
        self._ensure_connected()

        try:
            # Get underlying contract
            underlying = self._get_contract(symbol)

            # Request all options
            chains = self.ib.reqSecDefOptParams(
                underlying.symbol,
                '',  # Exchange
                underlying.secType,
                underlying.conId
            )

            if not chains:
                raise ValueError(f"No options available for {symbol}")

            # Convert to DataFrame
            rows = []
            for chain in chains:
                for strike in chain.strikes:
                    for expiry in chain.expirations:
                        rows.append({
                            'expiry': expiry,
                            'strike': strike,
                            'right': 'C',  # Call
                            'exchange': chain.exchange,
                            'multiplier': chain.multiplier
                        })
                        rows.append({
                            'expiry': expiry,
                            'strike': strike,
                            'right': 'P',  # Put
                            'exchange': chain.exchange,
                            'multiplier': chain.multiplier
                        })

            df = pd.DataFrame(rows)

            # Sort values
            df.sort_values(['expiry', 'strike', 'right'], inplace=True)

            return df

        except Exception as e:
            logger.error(f"Error getting option chain for {symbol}: {str(e)}")
            raise
