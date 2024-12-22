from typing import Dict, Type
import logging

from .interface import DataSourceInterface
from .sources.yahoo import YahooDataSource
from .sources.csv import CSVDataSource

logger = logging.getLogger(__name__)

class DataSourceFactory:
    """
    Factory for creating data sources.

    This class manages the creation and configuration of data sources.
    It provides a centralized way to:
    1. Register new data source types
    2. Create data source instances
    3. Configure data sources
    4. Manage source dependencies
    """

    # Registry of data source types
    _sources: Dict[str, Type[DataSourceInterface]] = {}

    @classmethod
    def register_source(cls,
                       name: str,
                       source_class: Type[DataSourceInterface]) -> None:
        """
        Register new data source type.

        Args:
            name: Source type name
            source_class: Source class

        Raises:
            ValueError: If source already registered
        """
        if name in cls._sources:
            raise ValueError(f"Source type '{name}' already registered")

        # Validate source class
        if not issubclass(source_class, DataSourceInterface):
            raise TypeError(
                f"Source class must implement DataSourceInterface"
            )

        cls._sources[name] = source_class
        logger.info(f"Registered data source type: {name}")

    @classmethod
    def create_source(cls,
                     source_type: str,
                     **config) -> DataSourceInterface:
        """
        Create data source instance.

        Args:
            source_type: Type of source to create
            **config: Source configuration

        Returns:
            DataSourceInterface: Data source instance

        Raises:
            ValueError: If source type not found
        """
        if source_type not in cls._sources:
            raise ValueError(
                f"Unknown source type: {source_type}. "
                f"Available types: {list(cls._sources.keys())}"
            )

        # Create instance
        source_class = cls._sources[source_type]
        return source_class(**config)

    @classmethod
    def get_source_types(cls) -> Dict[str, Type[DataSourceInterface]]:
        """Get registered source types."""
        return cls._sources.copy()

# Register built-in sources
DataSourceFactory.register_source('yahoo', YahooDataSource)
DataSourceFactory.register_source('csv', CSVDataSource)

def create_data_source(source_type: str, **config) -> DataSourceInterface:
    """
    Convenience function to create data source.

    Args:
        source_type: Type of source to create
        **config: Source configuration

    Returns:
        DataSourceInterface: Data source instance
    """
    return DataSourceFactory.create_source(source_type, **config)

# Example usage:
"""
# Create Yahoo Finance source
yahoo = create_data_source('yahoo', cache_dir='~/.algame/cache')

# Create CSV source
csv = create_data_source('csv',
                        base_dir='data/csv',
                        structure='hierarchical')

# Register custom source
class MyCustomSource(DataSourceInterface):
    ...

DataSourceFactory.register_source('custom', MyCustomSource)
custom = create_data_source('custom', **config)
"""
