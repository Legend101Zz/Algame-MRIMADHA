from typing import Dict, Any, Optional, Union
import pandas as pd
from pathlib import Path
import json
import logging
import datetime

from .interface import BacktestResult, EngineConfig,OptimizationResult
from .registry import EngineRegistry
from ..strategy import StrategyBase

logger = logging.getLogger(__name__)

class EngineManager:
    """
    High-level interface for managing and running backtests.

    This class provides a user-friendly interface to:
    1. Switch between engines
    2. Run backtests
    3. Save/load configurations
    4. Handle results

    It abstracts away the complexity of engine management while
    providing access to advanced features when needed.

    Example usage:
        manager = EngineManager()

        # Run with default engine
        results = manager.run_backtest(strategy, data)

        # Switch engine
        manager.set_engine("backtesting.py")
        results = manager.run_backtest(strategy, data)
    """

    def __init__(self,
                 config_path: Optional[str] = None,
                 engine: Optional[str] = None):
        """
        Initialize engine manager.

        Args:
            config_path: Path to config file (optional)
            engine: Name of engine to use (optional)
        """
        # Initialize registry
        self.registry = EngineRegistry()

        # Load configuration
        self.config = EngineConfig()
        if config_path:
            self.load_config(config_path)

        # Set engine
        self._engine = None
        self.set_engine(engine)


        # Track strategy and results
        self._last_strategy: Optional[StrategyBase] = None
        self._last_results: Optional[BacktestResult] = None
        self._strategy_history: Dict[str, Dict[str, Any]] = {}


    def set_engine(self, engine: Optional[str] = None) -> None:
        """
        Set active engine.

        Args:
            engine: Engine name (uses default if None)
        """
        self._engine = self.registry.get_engine(engine, config=self.config)
        logger.info(f"Set active engine to: {type(self._engine).__name__}")

    def run_backtest(self,
                    strategy: Union[Type[StrategyBase], StrategyBase],
                    data: Union[pd.DataFrame, Dict[str, pd.DataFrame]],
                    parameters: Optional[Dict[str, Any]] = None,
                    engine: Optional[str] = None) -> BacktestResult:
        """Run backtest with current engine."""
        # Use temporary engine if specified
        if engine:
            orig_engine = self._engine
            self.set_engine(engine)

        try:
            # Create strategy instance if needed
            if isinstance(strategy, type):
                strategy_instance = strategy(parameters)
            else:
                strategy_instance = strategy
                if parameters:
                    strategy_instance.set_parameters(parameters)

            # Store as last strategy
            self._last_strategy = strategy_instance
            self._record_strategy_usage(strategy_instance)

            # Prepare backtest
            self._engine.set_data(data)

            # Run backtest
            results = self._engine.run_backtest(strategy_instance, parameters)

            # Store results
            self._last_results = results
            logger.info(f"Completed backtest with {len(results.trades)} trades")

            return results

        finally:
            # Restore original engine
            if engine:
                self._engine = orig_engine

    def optimize_strategy(self,
                        strategy: Union[Type[StrategyBase], StrategyBase],
                        data: Union[pd.DataFrame, Dict[str, pd.DataFrame]],
                        parameter_space: Dict[str, Any],
                        **kwargs) -> OptimizationResult:
        """Optimize strategy parameters."""
        # Create strategy instance if needed
        if isinstance(strategy, type):
            strategy_instance = strategy()
        else:
            strategy_instance = strategy

        # Store as last strategy
        self._last_strategy = strategy_instance
        self._record_strategy_usage(strategy_instance)

        # Prepare optimization
        self._engine.set_data(data)

        # Run optimization
        results = self._engine.optimize_strategy(
            strategy_instance,
            parameter_space,
            **kwargs
        )

        logger.info("Completed strategy optimization")
        return results


    def save_config(self, path: Union[str,Path]) -> None:
        """
        Save current configuration.

        Args:
            path: Path to save config file

        Raises:
            IOError: If unable to save config
        """
        config = {
            'engine': self._engine.__class__.__name__,
            'settings': self.config.__dict__,
            'version': '1.0.0',  # Config format version
            'saved_at': pd.Timestamp.now().isoformat(),
            'metadata': {
                'description': 'AlGame engine configuration',
                'engine_info': {
                    'name': self._engine.__class__.__name__,
                    'supported_features': self._get_engine_features()
                }
            }
        }

        try:
            # Create directory if needed
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)

            # Save config
            with path.open('w') as f:
                json.dump(config, f, indent=4, sort_keys=True)

            logger.info(f"Saved configuration to: {path}")

        except Exception as e:
            logger.error(f"Failed to save config: {str(e)}")
            raise IOError(f"Unable to save config: {str(e)}")

    def load_config(self, path: Union[str,Path]) -> None:
        """
        Load configuration from file.

        Args:
            path: Path to config file

        Raises:
            IOError: If unable to load config
            ValueError: If config format is invalid
        """
        try:
            # Load config
            path = Path(path)
            with path.open('r') as f:
                config = json.load(f)

            # Validate config format
            self._validate_config(config)

            # Update settings
            self.config = EngineConfig(**config['settings'])

            # Set engine if specified
            if 'engine' in config:
                self.set_engine(config['engine'])

            logger.info(f"Loaded configuration from: {path}")

        except Exception as e:
            logger.error(f"Failed to load config: {str(e)}")
            raise IOError(f"Unable to load config: {str(e)}")

    def _validate_config(self, config: Dict) -> None:
        """
        Validate configuration format.

        Args:
            config: Configuration dictionary

        Raises:
            ValueError: If config is invalid
        """
        # Check required fields
        required_fields = ['engine', 'settings', 'version']
        missing = [field for field in required_fields if field not in config]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")

        # Check settings format
        if not isinstance(config['settings'], dict):
            raise ValueError("Settings must be a dictionary")

        # Validate version
        try:
            major, minor, patch = config['version'].split('.')
            if int(major) != 1:  # Only support major version 1 for now
                raise ValueError(f"Unsupported config version: {config['version']}")
        except Exception:
            raise ValueError(f"Invalid version format: {config['version']}")

    def _get_engine_features(self) -> Dict[str, bool]:
        """Get supported features of current engine."""
        features = {
            'multi_asset': hasattr(self._engine, 'supports_multi_asset'),
            'optimization': hasattr(self._engine, 'optimize_strategy'),
            'live_trading': hasattr(self._engine, 'supports_live_trading'),
            'parallel_execution': hasattr(self._engine, '_workers'),
        }
        return features

    def export_config(self, path: Union[str,Path], include_results: bool = False) -> None:
        """
        Export complete configuration including strategy details.

        This creates a standalone config that can be shared and replicated.

        Args:
            path: Path to save config
            include_results: Whether to include last results

        Raises:
            IOError: If unable to export config
        """
        # Get base config
        config = {
            'engine': self._engine.__class__.__name__,
            'settings': self.config.__dict__,
            'version': '1.0.0',
            'exported_at': pd.Timestamp.now().isoformat(),
        }

        # Add strategy info if available
        if hasattr(self, '_last_strategy'):
            config['strategy'] = {
                'class': self._last_strategy.__class__.__name__,
                'parameters': getattr(self._last_strategy, 'parameters', {}),
                'indicators': self._get_strategy_indicators(),
            }

        # Add results if requested
        if include_results and hasattr(self, '_last_results'):
            config['results'] = {
                'summary': self._last_results.metrics,
                'trades_summary': self._get_trades_summary(),
            }

        try:
            # Save as YAML for better readability
            import yaml
            path = Path(path)
            with path.open('w') as f:
                yaml.dump(config, f, default_flow_style=False)

            logger.info(f"Exported configuration to: {path}")

        except Exception as e:
            logger.error(f"Failed to export config: {str(e)}")
            raise IOError(f"Unable to export config: {str(e)}")

    def _get_strategy_indicators(self) -> Dict[str, Dict]:
        """Get strategy indicator configurations."""
        if not hasattr(self, '_last_strategy'):
            return {}

        indicators = {}
        for name, ind in getattr(self._last_strategy, 'indicators', {}).items():
            indicators[name] = {
                'type': ind.__class__.__name__,
                'parameters': getattr(ind, 'parameters', {}),
            }
        return indicators

    def _get_trades_summary(self) -> Dict[str, Any]:
        """Get summary of trading results."""
        if not hasattr(self, '_last_results'):
            return {}

        trades = self._last_results.trades
        return {
            'total_trades': len(trades),
            'winning_trades': len([t for t in trades if t.pnl > 0]),
            'losing_trades': len([t for t in trades if t.pnl < 0]),
            'total_pnl': sum(t.pnl for t in trades),
            'largest_win': max((t.pnl for t in trades), default=0),
            'largest_loss': min((t.pnl for t in trades), default=0),
        }

    def _record_strategy_usage(self, strategy: StrategyBase) -> None:
        """Record strategy usage history."""
        strategy_name = strategy.__class__.__name__
        if strategy_name not in self._strategy_history:
            self._strategy_history[strategy_name] = {
                'first_used': datetime.now(),
                'usage_count': 0,
                'parameters': [],
                'results': []
            }

        history = self._strategy_history[strategy_name]
        history['usage_count'] += 1
        history['last_used'] = datetime.now()
        history['parameters'].append(strategy.get_parameters())

    def get_strategy_history(self, strategy_name: Optional[str] = None) -> Dict:
        """Get strategy usage history."""
        if strategy_name:
            return self._strategy_history.get(strategy_name, {})
        return self._strategy_history

    def get_last_strategy(self) -> Optional[StrategyBase]:
        """Get last used strategy."""
        return self._last_strategy

    def get_last_results(self) -> Optional[BacktestResult]:
        """Get last backtest results."""
        return self._last_results

    def clear_history(self) -> None:
        """Clear strategy history."""
        self._strategy_history.clear()
        self._last_strategy = None
        self._last_results = None
