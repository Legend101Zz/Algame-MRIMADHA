from typing import Dict, Type, Optional, List
import logging
from .interface import BacktestEngineInterface

logger = logging.getLogger(__name__)

class EngineRegistry:
    """
    Central registry for backtest engines.

    This class manages the registration and retrieval of backtest engines.
    It ensures type safety and provides helpful error messages for developers.

    The registry pattern provides several benefits:
    1. Centralized engine management
    2. Dynamic engine loading
    3. Runtime engine switching
    4. Plugin support for new engines

    Example usage:
        # Register engines
        registry = EngineRegistry()
        registry.register("custom", CustomEngine)
        registry.register("backtest.py", BacktestingPyEngine)

        # Get engine
        engine = registry.get_engine("custom")
    """

    def __init__(self):
        """Initialize registry."""
        # Dictionary to store registered engines
        self._engines: Dict[str, Type[BacktestEngineInterface]] = {}

        # Track the default engine
        self._default_engine: Optional[str] = None

        # Store engine metadata
        self._engine_metadata: Dict[str, Dict] = {}

        logger.debug("Initialized EngineRegistry")

    def register(self,
                name: str,
                engine_class: Type[BacktestEngineInterface],
                make_default: bool = False,
                metadata: Optional[Dict] = None) -> None:
        """
        Register a new backtest engine.

        Args:
            name: Unique name for the engine
            engine_class: Engine class (must implement BacktestEngineInterface)
            make_default: Whether to make this the default engine
            metadata: Optional engine metadata

        Raises:
            TypeError: If engine_class doesn't implement BacktestEngineInterface
            ValueError: If engine name already registered
        """
        # Validate engine class
        if not issubclass(engine_class, BacktestEngineInterface):
            raise TypeError(
                f"Engine class must implement BacktestEngineInterface. "
                f"Got {engine_class.__name__}"
            )

        # Check for name collision
        if name in self._engines:
            raise ValueError(f"Engine '{name}' already registered")

        # Register engine
        self._engines[name] = engine_class
        self._engine_metadata[name] = metadata or {}
        logger.info(f"Registered engine: {name} ({engine_class.__name__})")

        # Set as default if requested or first engine
        if make_default or self._default_engine is None:
            self._default_engine = name
            logger.info(f"Set {name} as default engine")

    def unregister(self, name: str) -> None:
        """
        Unregister an engine.

        Args:
            name: Name of engine to unregister

        Raises:
            KeyError: If engine not found
        """
        if name not in self._engines:
            raise KeyError(f"Engine '{name}' not found")

        # Remove engine
        del self._engines[name]
        del self._engine_metadata[name]
        logger.info(f"Unregistered engine: {name}")

        # Update default engine if needed
        if name == self._default_engine:
            self._default_engine = next(iter(self._engines.keys())) if self._engines else None
            if self._default_engine:
                logger.info(f"New default engine: {self._default_engine}")
            else:
                logger.warning("No engines registered - no default engine set")

    def get_engine(self,
                  name: Optional[str] = None,
                  **config) -> BacktestEngineInterface:
        """
        Get engine instance by name.

        Args:
            name: Engine name (uses default if None)
            **config: Engine configuration parameters

        Returns:
            BacktestEngineInterface: Engine instance

        Raises:
            KeyError: If engine not found
            ValueError: If no engines registered
        """
        # Use default if no name provided
        if name is None:
            if self._default_engine is None:
                raise ValueError("No engines registered")
            name = self._default_engine

        # Get engine class
        if name not in self._engines:
            available = ", ".join(self._engines.keys())
            raise KeyError(
                f"Engine '{name}' not found. "
                f"Available engines: {available}"
            )

        # Create and return instance
        engine_class = self._engines[name]
        try:
            engine = engine_class(**config)
            logger.debug(f"Created engine instance: {name}")
            return engine
        except Exception as e:
            logger.error(f"Failed to create engine '{name}': {str(e)}")
            raise

    def get_engine_metadata(self, name: str) -> Dict:
        """
        Get metadata for registered engine.

        Args:
            name: Engine name

        Returns:
            Dict: Engine metadata

        Raises:
            KeyError: If engine not found
        """
        if name not in self._engines:
            raise KeyError(f"Engine '{name}' not found")
        return self._engine_metadata[name].copy()

    def list_engines(self) -> List[Dict]:
        """
        Get list of registered engines and their metadata.

        Returns:
            List[Dict]: List of engine information dictionaries
        """
        engines = []
        for name, engine_class in self._engines.items():
            engines.append({
                'name': name,
                'class': engine_class.__name__,
                'is_default': name == self._default_engine,
                'metadata': self._engine_metadata[name],
                'supports': {
                    'multi_asset': hasattr(engine_class, 'supports_multi_asset'),
                    'optimization': hasattr(engine_class, 'optimize_strategy'),
                    'live_trading': hasattr(engine_class, 'supports_live_trading'),
                }
            })
        return engines

    def set_default_engine(self, name: str) -> None:
        """
        Set default engine.

        Args:
            name: Name of engine to set as default

        Raises:
            KeyError: If engine not found
        """
        if name not in self._engines:
            raise KeyError(f"Engine '{name}' not found")

        self._default_engine = name
        logger.info(f"Set default engine to: {name}")

    @property
    def default_engine(self) -> Optional[str]:
        """Get name of current default engine."""
        return self._default_engine

    def update_metadata(self, name: str, metadata: Dict) -> None:
        """
        Update metadata for registered engine.

        Args:
            name: Engine name
            metadata: New metadata to update

        Raises:
            KeyError: If engine not found
        """
        if name not in self._engines:
            raise KeyError(f"Engine '{name}' not found")

        self._engine_metadata[name].update(metadata)
        logger.debug(f"Updated metadata for engine: {name}")

    def clear(self) -> None:
        """Clear all registered engines."""
        self._engines.clear()
        self._engine_metadata.clear()
        self._default_engine = None
        logger.info("Cleared engine registry")

    def __contains__(self, name: str) -> bool:
        """Check if engine is registered."""
        return name in self._engines

    def __len__(self) -> int:
        """Get number of registered engines."""
        return len(self._engines)

    def __repr__(self) -> str:
        """Get string representation."""
        engines = [f"{name} ({cls.__name__})"
                  for name, cls in self._engines.items()]
        return f"EngineRegistry(engines=[{', '.join(engines)}])"


# Example usage in __init__.py:
"""
# Create global registry instance
registry = EngineRegistry()

# Register built-in engines
from .custom import CustomEngine
from .backtesting_py import BacktestingPyEngine

registry.register("custom", CustomEngine, make_default=True)
registry.register("backtesting.py", BacktestingPyEngine)
"""
