from typing import Optional, Union, Tuple
import numpy as np
import pandas as pd

from .base import Indicator

class RSI(Indicator):
    """
    Relative Strength Index (RSI).

    Formula: RSI = 100 - (100 / (1 + RS))
    where RS = avg_gain / avg_loss
    """

    def __init__(self, period: int = 14):
        self.period = period

    def calculate(self, data: Union[pd.Series, np.ndarray]) -> np.ndarray:
        """Calculate RSI values."""
        if isinstance(data, pd.Series):
            data = data.values

        # Calculate price changes
        changes = np.diff(data)

        # Calculate gains and losses
        gains = np.where(changes > 0, changes, 0)
        losses = np.where(changes < 0, -changes, 0)

        # Calculate average gains and losses
        avg_gains = pd.Series(gains).rolling(window=self.period).mean()
        avg_losses = pd.Series(losses).rolling(window=self.period).mean()

        # Calculate RS and RSI
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))

        # Add nan for first value
        return np.append(np.nan, rsi.values)

class MACD(Indicator):
    """
    Moving Average Convergence Divergence (MACD).

    Returns (MACD line, Signal line, Histogram)

    Formula:
    MACD Line = FastEMA - SlowEMA
    Signal Line = EMA(MACD Line)
    Histogram = MACD Line - Signal Line
    """

    def __init__(self,
                fast_period: int = 12,
                slow_period: int = 26,
                signal_period: int = 9):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period

    def calculate(self, data: Union[pd.Series, np.ndarray]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Calculate MACD values."""
        if isinstance(data, pd.Series):
            data = data.values

        # Calculate fast and slow EMAs
        fast_ema = pd.Series(data).ewm(span=self.fast_period, adjust=False).mean()
        slow_ema = pd.Series(data).ewm(span=self.slow_period, adjust=False).mean()

        # Calculate MACD line
        macd_line = fast_ema - slow_ema

        # Calculate signal line
        signal_line = macd_line.ewm(span=self.signal_period, adjust=False).mean()

        # Calculate histogram
        histogram = macd_line - signal_line

        return macd_line.values, signal_line.values, histogram.values

class Stochastic(Indicator):
    """
    Stochastic Oscillator.

    Returns (%K, %D)

    Formula:
    %K = (Close - Lowest Low) / (Highest High - Lowest Low) * 100
    %D = SMA(%K)
    """

    def __init__(self,
                k_period: int = 14,
                d_period: int = 3,
                slowing: int = 3):
        self.k_period = k_period
        self.d_period = d_period
        self.slowing = slowing

    def calculate(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Calculate Stochastic values."""
        # Get high, low, close
        high = data['High'].values
        low = data['Low'].values
        close = data['Close'].values

        # Calculate %K
        low_min = pd.Series(low).rolling(window=self.k_period).min()
        high_max = pd.Series(high).rolling(window=self.k_period).max()

        k = ((close - low_min) / (high_max - low_min)) * 100

        # Apply slowing period
        if self.slowing > 1:
            k = pd.Series(k).rolling(window=self.slowing).mean()

        # Calculate %D
        d = pd.Series(k).rolling(window=self.d_period).mean()

        return k.values, d.values

class ROC(Indicator):
    """
    Rate of Change (ROC).

    Formula: ROC = ((Close - Close[period]) / Close[period]) * 100
    """

    def __init__(self, period: int = 14):
        self.period = period

    def calculate(self, data: Union[pd.Series, np.ndarray]) -> np.ndarray:
        """Calculate ROC values."""
        if isinstance(data, pd.Series):
            data = data.values

        # Calculate ROC
        roc = ((data - np.roll(data, self.period)) / np.roll(data, self.period)) * 100

        # Replace inf and -inf with nan
        roc = np.where(np.isinf(roc), np.nan, roc)

        # Set initial values to nan
        roc[:self.period] = np.nan

        return roc

class MFI(Indicator):
    """
    Money Flow Index (MFI).

    Formula:
    Typical Price = (High + Low + Close) / 3
    Money Flow = Typical Price * Volume
    MFI = 100 - (100 / (1 + Money Flow Ratio))
    where Money Flow Ratio = Positive Money Flow / Negative Money Flow
    """

    def __init__(self, period: int = 14):
        self.period = period

    def calculate(self, data: pd.DataFrame) -> np.ndarray:
        """Calculate MFI values."""
        # Calculate typical price
        tp = (data['High'] + data['Low'] + data['Close']) / 3

        # Calculate money flow
        mf = tp * data['Volume']

        # Get positive and negative money flow
        pmf = pd.Series(np.where(tp > tp.shift(1), mf, 0)).rolling(window=self.period).sum()
        nmf = pd.Series(np.where(tp < tp.shift(1), mf, 0)).rolling(window=self.period).sum()

        # Calculate money flow ratio and MFI
        mfr = pmf / nmf
        mfi = 100 - (100 / (1 + mfr))

        return mfi.values
