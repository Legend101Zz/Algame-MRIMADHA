from typing import Optional, Union, Tuple
import numpy as np
import pandas as pd

from .base import Indicator

class ATR(Indicator):
    """
    Average True Range (ATR).

    Formula:
    TR = max(high - low, abs(high - prev_close), abs(low - prev_close))
    ATR = EMA(TR)
    """

    def __init__(self, period: int = 14):
        self.period = period

    def calculate(self, data: pd.DataFrame) -> np.ndarray:
        """Calculate ATR values."""
        high = data['High'].values
        low = data['Low'].values
        close = data['Close'].values

        # Calculate True Range
        tr1 = high - low
        tr2 = np.abs(high - np.roll(close, 1))
        tr3 = np.abs(low - np.roll(close, 1))

        tr = np.maximum(tr1, np.maximum(tr2, tr3))

        # Calculate ATR
        atr = pd.Series(tr).ewm(span=self.period, adjust=False).mean()

        # Set first value to nan
        atr.iloc[0] = np.nan

        return atr.values

class Bollinger(Indicator):
    """
    Bollinger Bands.

    Returns (Middle Band, Upper Band, Lower Band)

    Formula:
    Middle = SMA(Close)
    Upper = Middle + (StdDev * multiplier)
    Lower = Middle - (StdDev * multiplier)
    """

    def __init__(self, period: int = 20, multiplier: float = 2.0):
        self.period = period
        self.multiplier = multiplier

    def calculate(self, data: Union[pd.Series, np.ndarray]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Calculate Bollinger Bands values."""
        if isinstance(data, pd.Series):
            data = data.values

        # Calculate middle band (SMA)
        middle = pd.Series(data).rolling(window=self.period).mean()

        # Calculate standard deviation
        std = pd.Series(data).rolling(window=self.period).std()

        # Calculate upper and lower bands
        upper = middle + (std * self.multiplier)
        lower = middle - (std * self.multiplier)

        return middle.values, upper.values, lower.values


class Keltner(Indicator):
    """
    Keltner Channels.

    Returns (Middle Line, Upper Line, Lower Line)

    Formula:
    Middle = EMA(Close)
    Upper = Middle + (multiplier * ATR)
    Lower = Middle - (multiplier * ATR)
    """

    def __init__(self, period: int = 20, atr_period: int = 10, multiplier: float = 2.0):
        self.period = period
        self.atr_period = atr_period
        self.multiplier = multiplier


    def calculate(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Calculate Keltner Channels values."""
        close = data['Close'].values

        # Calculate middle line (EMA)
        middle = pd.Series(close).ewm(span=self.period, adjust=False).mean()

        # Calculate ATR
        atr = ATR(period=self.atr_period).calculate(data)

        # Calculate upper and lower lines
        upper = middle + (self.multiplier * atr)
        lower = middle - (self.multiplier * atr)

        return middle.values, upper.values, lower.values

class StandardDev(Indicator):
    """
    Standard Deviation.

    Formula:
    StdDev = sqrt(sum((x - mean)^2) / (n-1))
    where x is price and n is period.
    """

    def __init__(self, period: int = 20):
        self.period = period

    def calculate(self, data: Union[pd.Series, np.ndarray]) -> np.ndarray:
        """Calculate Standard Deviation values."""
        if isinstance(data, pd.Series):
            data = data.values

        return pd.Series(data).rolling(window=self.period).std().values

class ParabolicSAR(Indicator):
    """
    Parabolic Stop And Reverse (SAR).

    Formula:
    SAR(t+1) = SAR(t) + α * (EP - SAR(t))
    where:
    α is the acceleration factor
    EP is the extreme point
    """

    def __init__(self,
                initial_af: float = 0.02,
                max_af: float = 0.2,
                af_step: float = 0.02):
        self.initial_af = initial_af
        self.max_af = max_af
        self.af_step = af_step

    def calculate(self, data: pd.DataFrame) -> np.ndarray:
        """Calculate Parabolic SAR values."""
        high = data['High'].values
        low = data['Low'].values

        # Initialize arrays
        sar = np.zeros_like(high)
        trend = np.zeros_like(high)  # 1 for uptrend, -1 for downtrend
        ep = np.zeros_like(high)  # Extreme point
        af = np.zeros_like(high)  # Acceleration factor

        # Initialize first values
        trend[0] = 1 if high[1] > high[0] else -1
        ep[0] = high[0] if trend[0] == 1 else low[0]
        af[0] = self.initial_af
        sar[0] = low[0] if trend[0] == 1 else high[0]

        # Calculate SAR values
        for i in range(1, len(high)):
            # Previous values
            prev_sar = sar[i-1]
            prev_trend = trend[i-1]
            prev_ep = ep[i-1]
            prev_af = af[i-1]

            # Calculate SAR
            if prev_trend == 1:
                # Uptrend
                sar[i] = prev_sar + prev_af * (prev_ep - prev_sar)

                # Update trend if price crosses below SAR
                if low[i] < sar[i]:
                    trend[i] = -1
                    sar[i] = prev_ep
                    ep[i] = low[i]
                    af[i] = self.initial_af
                else:
                    trend[i] = 1
                    # Update extreme point and acceleration factor
                    if high[i] > prev_ep:
                        ep[i] = high[i]
                        af[i] = min(prev_af + self.af_step, self.max_af)
                    else:
                        ep[i] = prev_ep
                        af[i] = prev_af

            else:
                # Downtrend
                sar[i] = prev_sar - prev_af * (prev_sar - prev_ep)

                # Update trend if price crosses above SAR
                if high[i] > sar[i]:
                    trend[i] = 1
                    sar[i] = prev_ep
                    ep[i] = high[i]
                    af[i] = self.initial_af
                else:
                    trend[i] = -1
                    # Update extreme point and acceleration factor
                    if low[i] < prev_ep:
                        ep[i] = low[i]
                        af[i] = min(prev_af + self.af_step, self.max_af)
                    else:
                        ep[i] = prev_ep
                        af[i] = prev_af

        return sar
