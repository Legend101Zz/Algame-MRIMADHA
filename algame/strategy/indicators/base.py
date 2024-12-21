from abc import ABC, abstractmethod
from typing import Dict, Optional, Union, Any
from dataclasses import dataclass
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

@dataclass
class IndicatorMetadata:
    """Metadata for technical indicators."""
    name: str
    category: str
    version: str
    description: str
    inputs: Optional[Dict[str, str]] = None
    parameters: Optional[Dict[str, Dict[str, Any]]] = None

class Indicator(ABC):
    """
    Base class for technical indicators.

    This abstract class defines the interface that all indicators
    must implement. It provides:

    1. Standardized Calculation:
        - Input validation
        - Output formatting
        - Error handling

    2. Metadata:
        - Indicator information
        - Input descriptions
        - Parameter definitions

    3. Utilities:
        - Data type conversion
        - Missing data handling
        - Data validation

    Example:
        class SMA(Indicator):
            def __init__(self, period: int = 14):
                self.period = period

            def calculate(self, data):
                return pd.Series(data).rolling(period=self.period).mean()
    """

    @abstractmethod
    def calculate(self, data: Union[pd.Series, pd.DataFrame, np.ndarray]) -> Union[np.ndarray, tuple]:
        """
        Calculate indicator values.

        Args:
            data: Input data (Series, DataFrame, or ndarray)

        Returns:
            Calculated indicator values

        Raises:
            ValueError: If input data is invalid
        """
        pass

    def validate_data(self,
                     data: Union[pd.Series, pd.DataFrame, np.ndarray],
                     required_columns: Optional[list] = None) -> None:
        """
        Validate input data.

        Args:
            data: Input data to validate
            required_columns: Required column names for DataFrame

        Raises:
            ValueError: If data validation fails
        """
        # Check data is not empty
        if data is None or (isinstance(data, (pd.Series, pd.DataFrame)) and data.empty):
            raise ValueError("Input data is empty")

        # Check required columns
        if required_columns and isinstance(data, pd.DataFrame):
            missing = [col for col in required_columns if col not in data.columns]
            if missing:
                raise ValueError(f"Missing required columns: {missing}")

        # Check for numeric data
        if isinstance(data, pd.DataFrame):
            non_numeric = [col for col in data.columns
                         if not np.issubdtype(data[col].dtype, np.number)]
            if non_numeric:
                raise ValueError(f"Non-numeric columns: {non_numeric}")

        elif isinstance(data, pd.Series):
            if not np.issubdtype(data.dtype, np.number):
                raise ValueError("Series must be numeric")

        elif isinstance(data, np.ndarray):
            if not np.issubdtype(data.dtype, np.number):
                raise ValueError("Array must be numeric")

    def prepare_data(self,
                    data: Union[pd.Series, pd.DataFrame, np.ndarray],
                    required_columns: Optional[list] = None) -> Union[pd.Series, pd.DataFrame, np.ndarray]:
        """
        Prepare data for calculation.

        Args:
            data: Input data
            required_columns: Required column names

        Returns:
            Prepared data

        Raises:
            ValueError: If data preparation fails
        """
        # Validate data
        self.validate_data(data, required_columns)

        # Convert Series to ndarray if needed
        if isinstance(data, pd.Series):
            data = data.values

        # Extract required columns if needed
        if required_columns and isinstance(data, pd.DataFrame):
            data = data[required_columns]

        return data

    def handle_missing_values(self,
                            data: Union[pd.Series, pd.DataFrame, np.ndarray],
                            method: str = 'fill',
                            value: Optional[float] = None) -> Union[pd.Series, pd.DataFrame, np.ndarray]:
        """
        Handle missing values in data.

        Args:
            data: Input data
            method: Handling method ('fill', 'drop', 'interpolate')
            value: Fill value for 'fill' method

        Returns:
            Data with missing values handled
        """
        if isinstance(data, (pd.Series, pd.DataFrame)):
            if method == 'fill':
                return data.fillna(value if value is not None else method)
            elif method == 'drop':
                return data.dropna()
            elif method == 'interpolate':
                return data.interpolate()
        else:
            # Handle numpy array
            if method == 'fill':
                return np.nan_to_num(data, nan=value if value is not None else 0)
            elif method == 'drop':
                return data[~np.isnan(data)]
            elif method == 'interpolate':
                return pd.Series(data).interpolate().values

        return data

    @classmethod
    def get_metadata(cls) -> IndicatorMetadata:
        """Get indicator metadata."""
        return IndicatorMetadata(
            name=cls.__name__,
            category='Unknown',
            version='1.0.0',
            description=cls.__doc__ or 'No description'
        )

    @classmethod
    def get_parameters(cls) -> Dict[str, Dict[str, Any]]:
        """
        Get indicator parameters.

        Returns dict of parameters with metadata for GUI:
        - type: Parameter type for input validation
        - default: Default value
        - range: Valid range for numeric parameters
        - description: Parameter description
        """
        return {}

def register_indicator(name: str,
                      indicator_class: type,
                      metadata: Optional[IndicatorMetadata] = None) -> None:
    """
    Register indicator in global registry.

    Args:
        name: Indicator name
        indicator_class: Indicator class
        metadata: Optional metadata
    """
    from . import _indicator_registry

    # Validate class
    if not issubclass(indicator_class, Indicator):
        raise TypeError(f"Class must inherit from Indicator: {indicator_class}")

    # Get metadata
    if metadata is None:
        metadata = indicator_class.get_metadata()

    # Add to registry
    _indicator_registry[name] = {
        'class': indicator_class,
        'metadata': metadata
    }

    logger.debug(f"Registered indicator: {name}")

def get_indicator(name: str) -> type:
    """
    Get indicator class by name.

    Args:
        name: Indicator name

    Returns:
        Indicator class

    Raises:
        ValueError: If indicator not found
    """
    from . import _indicator_registry

    if name not in _indicator_registry:
        raise ValueError(f"Indicator not found: {name}")

    return _indicator_registry[name]['class']

def list_indicators() -> Dict[str, IndicatorMetadata]:
    """
    Get dictionary of registered indicators.

    Returns:
        Dict of indicator name to metadata
    """
    from . import _indicator_registry

    return {
        name: meta['metadata']
        for name, meta in _indicator_registry.items()
    }
