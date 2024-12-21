from typing import Dict, List, Optional, Union, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import re

def parse_timeframe(timeframe: str) -> Tuple[int, str]:
    """
    Parse timeframe string into number and unit.

    Examples:
        "1m" -> (1, "minute")
        "4h" -> (4, "hour")
        "1d" -> (1, "day")

    Args:
        timeframe: Timeframe string

    Returns:
        Tuple[int, str]: Number and unit

    Raises:
        ValueError: If invalid format
    """
    # Parse timeframe
    match = re.match(r'(\d+)([mhdwMy])', timeframe)
    if not match:
        raise ValueError(
            f"Invalid timeframe format: {timeframe}. "
            "Must be number + unit (m,h,d,w,M,y)"
        )

    number = int(match.group(1))
    unit = match.group(2)

    # Map to full unit name
    unit_map = {
        'm': 'minute',
        'h': 'hour',
        'd': 'day',
        'w': 'week',
        'M': 'month',
        'y': 'year'
    }

    return number, unit_map[unit]

def timeframe_to_seconds(timeframe: str) -> int:
    """
    Convert timeframe to seconds.

    Args:
        timeframe: Timeframe string

    Returns:
        int: Number of seconds
    """
    number, unit = parse_timeframe(timeframe)

    # Convert to seconds
    unit_seconds = {
        'minute': 60,
        'hour': 3600,
        'day': 86400,
        'week': 604800,
        'month': 2592000,  # 30 days
        'year': 31536000   # 365 days
    }

    return number * unit_seconds[unit]

def convert_timeframe(data: pd.DataFrame,
                     target_timeframe: str,
                     method: str = 'ohlcv') -> pd.DataFrame:
    """
    Convert data to different timeframe.

    Args:
        data: OHLCV data
        target_timeframe: Target timeframe
        method: Aggregation method

    Returns:
        pd.DataFrame: Resampled data
    """
    # Convert timeframe to offset
    offset = timeframe_to_offset(target_timeframe)

    if method == 'ohlcv':
        # Standard OHLCV resampling
        resampled = data.resample(offset).agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum' if 'Volume' in data else None
        }).dropna()

    elif method == 'vwap':
        # Volume-weighted average price
        resampled = data.resample(offset).agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': lambda x: (x * data.loc[x.index, 'Volume']).sum() / data.loc[x.index, 'Volume'].sum(),
            'Volume': 'sum'
        }).dropna()

    else:
        raise ValueError(f"Unknown method: {method}")

    return resampled

def timeframe_to_offset(timeframe: str) -> str:
    """
    Convert timeframe to pandas offset string.

    Args:
        timeframe: Timeframe string

    Returns:
        str: Pandas offset string
    """
    number, unit = parse_timeframe(timeframe)

    # Map to pandas offset
    offset_map = {
        'minute': 'T',
        'hour': 'H',
        'day': 'D',
        'week': 'W',
        'month': 'M',
        'year': 'Y'
    }

    return f"{number}{offset_map[unit]}"

def validate_ohlcv(data: pd.DataFrame,
                  require_volume: bool = False) -> bool:
    """
    Validate OHLCV data format.

    Args:
        data: Data to validate
        require_volume: Whether Volume is required

    Returns:
        bool: True if valid

    Raises:
        ValueError: If validation fails
    """
    # Check required columns
    required = ['Open', 'High', 'Low', 'Close']
    if require_volume:
        required.append('Volume')

    missing = [col for col in required if col not in data.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    # Check numeric types
    for col in required:
        if not np.issubdtype(data[col].dtype, np.number):
            raise ValueError(f"Column {col} must be numeric")

    # Check for missing values
    if data[required].isnull().any().any():
        raise ValueError("Data contains missing values")

    # Validate price relationships
    if not (
        (data['High'] >= data['Low']).all() and
        (data['High'] >= data['Open']).all() and
        (data['High'] >= data['Close']).all() and
        (data['Low'] <= data['Open']).all() and
        (data['Low'] <= data['Close']).all()
    ):
        raise ValueError("Invalid price relationships")

    return True

def fill_missing_data(data: pd.DataFrame,
                     method: str = 'ffill',
                     limit: Optional[int] = None) -> pd.DataFrame:
    """
    Fill missing values in OHLCV data.

    Args:
        data: Data to fill
        method: Fill method ('ffill', 'bfill', 'interpolate', 'vwap')
        limit: Maximum fills

    Returns:
        pd.DataFrame: Filled data
    """
    filled = data.copy()

    if method == 'ffill':
        # Forward fill
        filled = filled.fillna(method='ffill', limit=limit)

    elif method == 'bfill':
        # Backward fill
        filled = filled.fillna(method='bfill', limit=limit)

    elif method == 'interpolate':
        # Linear interpolation
        for col in ['Open', 'High', 'Low', 'Close']:
            filled[col] = filled[col].interpolate(
                method='linear',
                limit=limit
            )
        if 'Volume' in filled:
            filled['Volume'] = filled['Volume'].fillna(0)

    elif method == 'vwap':
        # Fill using volume-weighted average price
        if 'Volume' not in filled:
            raise ValueError("Volume required for VWAP filling")

        price = ((filled['High'] + filled['Low'] + filled['Close']) / 3)
        vwap = (price * filled['Volume']).cumsum() / filled['Volume'].cumsum()

        for col in ['Open', 'High', 'Low', 'Close']:
            filled[col] = filled[col].fillna(vwap)
        filled['Volume'] = filled['Volume'].fillna(0)

    else:
        raise ValueError(f"Unknown fill method: {method}")

    return filled

def adjust_for_splits_dividends(data: pd.DataFrame,
                              splits: pd.Series,
                              dividends: pd.Series) -> pd.DataFrame:
    """
    Adjust OHLCV data for splits and dividends.

    Args:
        data: OHLCV data
        splits: Split ratios indexed by date
        dividends: Dividend amounts indexed by date

    Returns:
        pd.DataFrame: Adjusted data
    """
    adjusted = data.copy()

    # Process splits
    if not splits.empty:
        for date, ratio in splits.items():
            # Adjust prices before split
            mask = adjusted.index < date
            adjusted.loc[mask, 'Open'] /= ratio
            adjusted.loc[mask, 'High'] /= ratio
            adjusted.loc[mask, 'Low'] /= ratio
            adjusted.loc[mask, 'Close'] /= ratio
            # Adjust volume
            adjusted.loc[mask, 'Volume'] *= ratio

    # Process dividends
    if not dividends.empty:
        for date, amount in dividends.items():
            # Adjust prices before dividend
            mask = adjusted.index < date
            factor = 1 - (amount / adjusted.loc[date, 'Close'])
            adjusted.loc[mask, 'Open'] *= factor
            adjusted.loc[mask, 'High'] *= factor
            adjusted.loc[mask, 'Low'] *= factor
            adjusted.loc[mask, 'Close'] *= factor

    return adjusted

def calculate_returns(data: pd.DataFrame,
                     method: str = 'arithmetic') -> pd.Series:
    """
    Calculate returns from price data.

    Args:
        data: OHLCV data
        method: Return calculation method

    Returns:
        pd.Series: Returns series
    """
    if method == 'arithmetic':
        # Simple returns
        returns = data['Close'].pct_change()

    elif method == 'log':
        # Log returns
        returns = np.log(data['Close'] / data['Close'].shift(1))

    elif method == 'excess':
        # Excess returns over risk-free rate
        if 'RiskFree' not in data:
            raise ValueError("Risk-free rate required for excess returns")
        simple_returns = data['Close'].pct_change()
        returns = simple_returns - data['RiskFree']

    else:
        raise ValueError(f"Unknown return method: {method}")

    return returns

def detect_outliers(data: pd.DataFrame,
                   method: str = 'zscore',
                   threshold: float = 3.0) -> pd.Series:
    """
    Detect outliers in OHLCV data.

    Args:
        data: OHLCV data
        method: Detection method
        threshold: Detection threshold

    Returns:
        pd.Series: Boolean mask of outliers
    """
    if method == 'zscore':
        # Z-score method
        returns = data['Close'].pct_change()
        zscore = np.abs((returns - returns.mean()) / returns.std())
        return zscore > threshold

    elif method == 'mad':
        # Median Absolute Deviation
        returns = data['Close'].pct_change()
        median = returns.median()
        mad = np.median(np.abs(returns - median))
        modified_zscore = 0.6745 * np.abs(returns - median) / mad
        return modified_zscore > threshold

    elif method == 'iqr':
        # Interquartile Range
        returns = data['Close'].pct_change()
        Q1 = returns.quantile(0.25)
        Q3 = returns.quantile(0.75)
        IQR = Q3 - Q1
        return (returns < (Q1 - threshold * IQR)) | (returns > (Q3 + threshold * IQR))

    else:
        raise ValueError(f"Unknown outlier detection method: {method}")

def calculate_indicators(data: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate common technical indicators.

    Args:
        data: OHLCV data

    Returns:
        pd.DataFrame: Data with indicators
    """
    df = data.copy()

    # Moving averages
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()

    # Volatility
    df['ATR'] = calculate_atr(df)
    df['Volatility'] = df['Close'].rolling(window=20).std()

    # Momentum
    df['RSI'] = calculate_rsi(df['Close'])
    df['MACD'], df['MACD_Signal'], df['MACD_Hist'] = calculate_macd(df['Close'])

    # Volume
    if 'Volume' in df:
        df['VWAP'] = calculate_vwap(df)
        df['Volume_SMA'] = df['Volume'].rolling(window=20).mean()

    return df

def calculate_atr(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate Average True Range."""
    high = data['High']
    low = data['Low']
    close = data['Close']

    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    return tr.rolling(window=period).mean()

def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index."""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_macd(prices: pd.Series,
                  fast: int = 12,
                  slow: int = 26,
                  signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate MACD, Signal and Histogram."""
    exp1 = prices.ewm(span=fast, adjust=False).mean()
    exp2 = prices.ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    histogram = macd - signal_line

    return macd, signal_line, histogram

def calculate_vwap(data: pd.DataFrame) -> pd.Series:
    """Calculate Volume Weighted Average Price."""
    typical_price = (data['High'] + data['Low'] + data['Close']) / 3
    return (typical_price * data['Volume']).cumsum() / data['Volume'].cumsum()
