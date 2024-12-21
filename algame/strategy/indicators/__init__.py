"""
Technical indicators module.

This module provides:
1. Built-in technical indicators
2. Custom indicator support
3. Indicator validation
4. Optimization tools

Features:
- Efficient calculation
- Vectorized operations
- Numpy/Pandas integration
- Real-time updates
"""

from typing import Dict, List, Optional, Union, Any
import numpy as np
import pandas as pd

# Import base indicator
from .base import (
    Indicator,
    IndicatorMetadata,
    register_indicator
)

# Import built-in indicators
from .trend import (
    SMA,
    EMA,
    TEMA,
    DEMA,
    WMA
)

from .momentum import (
    RSI,
    MACD,
    Stochastic,
    ROC,
    MFI
)

from .volatility import (
    ATR,
    Bollinger,
    Keltner,
    StandardDev,
    ParabolicSAR
)

from .volume import (
    OBV,
    ADL,
    CMF,
    VWAP,
    VolumeProfile
)

from .pattern import (
    CandlePattern,
    PricePattern,
    ChartPattern
)

# Indicator registry
_indicator_registry: Dict[str, type] = {}

def register_built_in_indicators() -> None:
    """Register built-in indicators."""
    indicators = [
        # Trend
        ('SMA', SMA, 'Trend'),
        ('EMA', EMA, 'Trend'),
        ('TEMA', TEMA, 'Trend'),
        ('DEMA', DEMA, 'Trend'),
        ('WMA', WMA, 'Trend'),

        # Momentum
        ('RSI', RSI, 'Momentum'),
        ('MACD', MACD, 'Momentum'),
        ('Stochastic', Stochastic, 'Momentum'),
        ('ROC', ROC, 'Momentum'),
        ('MFI', MFI, 'Momentum'),

        # Volatility
        ('ATR', ATR, 'Volatility'),
        ('Bollinger', Bollinger, 'Volatility'),
        ('Keltner', Keltner, 'Volatility'),
        ('StandardDev', StandardDev, 'Volatility'),
        ('ParabolicSAR', ParabolicSAR, 'Volatility'),

        # Volume
        ('OBV', OBV, 'Volume'),
        ('ADL', ADL, 'Volume'),
        ('CMF', CMF, 'Volume'),
        ('VWAP', VWAP, 'Volume'),
        ('VolumeProfile', VolumeProfile, 'Volume'),

        # Pattern
        ('CandlePattern', CandlePattern, 'Pattern'),
        ('PricePattern', PricePattern, 'Pattern'),
        ('ChartPattern', ChartPattern, 'Pattern')
    ]

    for name, indicator_class, category in indicators:
        metadata = IndicatorMetadata(
            name=name,
            category=category,
            version='1.0.0',
            description=indicator_class.__doc__
        )
        register_indicator(name, indicator_class, metadata)

def get_indicator(name: str) -> type:
    """Get indicator class by name."""
    if name not in _indicator_registry:
        raise ValueError(f"Indicator not found: {name}")
    return _indicator_registry[name]['class']

def get_indicator_metadata(name: str) -> IndicatorMetadata:
    """Get indicator metadata."""
    if name not in _indicator_registry:
        raise ValueError(f"Indicator not found: {name}")
    return _indicator_registry[name]['metadata']

def list_indicators() -> List[Dict[str, Any]]:
    """Get list of registered indicators."""
    return [
        {
            'name': name,
            'category': meta['metadata'].category,
            'description': meta['metadata'].description
        }
        for name, meta in _indicator_registry.items()
    ]

def list_indicator_categories() -> List[str]:
    """Get list of indicator categories."""
    categories = set()
    for meta in _indicator_registry.values():
        categories.add(meta['metadata'].category)
    return sorted(categories)

# Register built-in indicators
register_built_in_indicators()

# Export public interface
__all__ = [
    # Base classes
    'Indicator',
    'IndicatorMetadata',
    'register_indicator',

    # Built-in indicators
    'SMA', 'EMA', 'TEMA', 'DEMA', 'WMA',  # Trend
    'RSI', 'MACD', 'Stochastic', 'ROC', 'MFI',  # Momentum
    'ATR', 'Bollinger', 'Keltner', 'StandardDev', 'ParabolicSAR',  # Volatility
    'OBV', 'ADL', 'CMF', 'VWAP', 'VolumeProfile',  # Volume
    'CandlePattern', 'PricePattern', 'ChartPattern',  # Pattern

    # Registry functions
    'get_indicator',
    'get_indicator_metadata',
    'list_indicators',
    'list_indicator_categories'
]
