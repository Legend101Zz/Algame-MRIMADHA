from typing import Optional, Union
import numpy as np
import pandas as pd

from .base import Indicator

class SMA(Indicator):
    """
    Simple Moving Average (SMA).

    Formula: SMA = sum(prices) / n
    where n is the period.
    """

    def __init__(self, period: int = 14):
        self.period = period

    def calculate(self, data: Union[pd.Series, np.ndarray]) -> np.ndarray:
        """Calculate SMA values."""
        if isinstance(data, pd.Series):
            data = data.values
        return pd.Series(data).rolling(window=self.period).mean().values

class EMA(Indicator):
    """
    Exponential Moving Average (EMA).

    Formula: EMA = (Price * k) + (EMA[previous] * (1-k))
    where k = 2 / (period + 1)
    """

    def __init__(self, period: int = 14):
        self.period = period

    def calculate(self, data: Union[pd.Series, np.ndarray]) -> np.ndarray:
        """Calculate EMA values."""
        if isinstance(data, pd.Series):
            data = data.values
        return pd.Series(data).ewm(span=self.period, adjust=False).mean().values

class TEMA(Indicator):
    """
    Triple Exponential Moving Average (TEMA).

    Formula: TEMA = (3×EMA1) - (3×EMA2) + EMA3
    where EMAn is the nth EMA of the previous EMA
    """

    def __init__(self, period: int = 14):
        self.period = period

    def calculate(self, data: Union[pd.Series, np.ndarray]) -> np.ndarray:
        """Calculate TEMA values."""
        if isinstance(data, pd.Series):
            data = data.values

        # Calculate first EMA
        ema1 = pd.Series(data).ewm(span=self.period, adjust=False).mean()

        # Calculate second EMA
        ema2 = ema1.ewm(span=self.period, adjust=False).mean()

        # Calculate third EMA
        ema3 = ema2.ewm(span=self.period, adjust=False).mean()

        # Calculate TEMA
        tema = 3 * ema1 - 3 * ema2 + ema3

        return tema.values

class DEMA(Indicator):
    """
    Double Exponential Moving Average (DEMA).

    Formula: DEMA = 2×EMA1 - EMA2
    where EMA2 is the EMA of EMA1
    """

    def __init__(self, period: int = 14):
        self.period = period

    def calculate(self, data: Union[pd.Series, np.ndarray]) -> np.ndarray:
        """Calculate DEMA values."""
        if isinstance(data, pd.Series):
            data = data.values

        # Calculate first EMA
        ema1 = pd.Series(data).ewm(span=self.period, adjust=False).mean()

        # Calculate second EMA
        ema2 = ema1.ewm(span=self.period, adjust=False).mean()

        # Calculate DEMA
        dema = 2 * ema1 - ema2

        return dema.values

class WMA(Indicator):
    """
    Weighted Moving Average (WMA).

    Formula: WMA = sum(price[i] * weight[i]) / sum(weights)
    where weight[i] = (period - i) for i in range(period)
    """

    def __init__(self, period: int = 14):
        self.period = period

    def calculate(self, data: Union[pd.Series, np.ndarray]) -> np.ndarray:
        """Calculate WMA values."""
        if isinstance(data, pd.Series):
            data = data.values

        # Create weights
        weights = np.arange(1, self.period + 1)

        # Calculate WMA
        wma = []
        for i in range(len(data)):
            if i < self.period - 1:
                wma.append(np.nan)
            else:
                window = data[i-self.period+1:i+1]
                wma.append(np.sum(window * weights) / np.sum(weights))

        return np.array(wma)
