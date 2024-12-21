from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Type
import pandas as pd
import numpy as np
from datetime import datetime
import logging

from .base import StrategyBase

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of a single validation check."""
    passed: bool
    message: str
    details: Optional[Dict[str, Any]] = None

@dataclass
class ValidationReport:
    """Complete strategy validation report."""
    strategy_name: str
    timestamp: datetime
    results: Dict[str, ValidationResult]

    @property
    def passed(self) -> bool:
        """Check if all validations passed."""
        return all(r.passed for r in self.results.values())

    @property
    def failed_checks(self) -> List[str]:
        """Get list of failed checks."""
        return [name for name, result in self.results.items()
                if not result.passed]

    def to_dict(self) -> Dict:
        """Convert report to dictionary."""
        return {
            'strategy_name': self.strategy_name,
            'timestamp': self.timestamp.isoformat(),
            'passed': self.passed,
            'results': {
                name: {
                    'passed': r.passed,
                    'message': r.message,
                    'details': r.details
                }
                for name, r in self.results.items()
            }
        }

class StrategyValidator:
    """
    Strategy validation system.

    This class provides comprehensive strategy validation:
    1. Code structure and implementation
    2. Data requirements and handling
    3. Parameter validation
    4. Risk management checks
    5. Performance simulation
    """

    def __init__(self,
                 sample_data: Optional[pd.DataFrame] = None,
                 strict_mode: bool = True):
        """
        Initialize validator.

        Args:
            sample_data: Sample market data for testing
            strict_mode: Whether to enforce all checks
        """
        self.sample_data = sample_data
        self.strict_mode = strict_mode

    def validate(self,
                strategy_class: Type[StrategyBase],
                **kwargs) -> ValidationReport:
        """
        Validate trading strategy.

        Args:
            strategy_class: Strategy class to validate
            **kwargs: Additional validation parameters

        Returns:
            ValidationReport: Validation results
        """
        results = {}

        # Run all validation checks
        checks = [
            self._validate_implementation,
            self._validate_data_handling,
            self._validate_parameters,
            self._validate_risk_management,
            self._validate_performance
        ]

        for check in checks:
            try:
                name = check.__name__.replace('_validate_', '')
                result = check(strategy_class, **kwargs)
                results[name] = result
            except Exception as e:
                logger.error(f"Validation error in {check.__name__}: {str(e)}")
                if self.strict_mode:
                    raise
                results[name] = ValidationResult(
                    passed=False,
                    message=f"Validation failed: {str(e)}"
                )

        return ValidationReport(
            strategy_name=strategy_class.__name__,
            timestamp=datetime.now(),
            results=results
        )

    def _validate_implementation(self,
                               strategy_class: Type[StrategyBase],
                               **kwargs) -> ValidationResult:
        """Validate strategy implementation."""
        try:
            # Check inheritance
            if not issubclass(strategy_class, StrategyBase):
                return ValidationResult(
                    passed=False,
                    message="Strategy must inherit from StrategyBase"
                )

            # Check required methods
            required_methods = ['initialize', 'next']
            missing = [m for m in required_methods
                      if not hasattr(strategy_class, m)]
            if missing:
                return ValidationResult(
                    passed=False,
                    message=f"Missing required methods: {missing}"
                )

            # Create instance
            strategy = strategy_class()

            return ValidationResult(
                passed=True,
                message="Implementation validated successfully"
            )

        except Exception as e:
            return ValidationResult(
                passed=False,
                message=f"Implementation validation failed: {str(e)}"
            )

    def _validate_data_handling(self,
                              strategy_class: Type[StrategyBase],
                              **kwargs) -> ValidationResult:
        """Validate data handling."""
        if self.sample_data is None:
            return ValidationResult(
                passed=True,
                message="Data validation skipped (no sample data)"
            )

        try:
            strategy = strategy_class()
            strategy.set_data(self.sample_data)

            # Check indicator calculations
            indicators = getattr(strategy, 'indicators', {})
            invalid = []
            for name, values in indicators.items():
                if np.isnan(values).any():
                    invalid.append(name)

            if invalid:
                return ValidationResult(
                    passed=False,
                    message=f"Invalid indicator calculations: {invalid}"
                )

            return ValidationResult(
                passed=True,
                message="Data handling validated successfully",
                details={'indicators': list(indicators.keys())}
            )

        except Exception as e:
            return ValidationResult(
                passed=False,
                message=f"Data validation failed: {str(e)}"
            )

    def _validate_parameters(self,
                           strategy_class: Type[StrategyBase],
                           **kwargs) -> ValidationResult:
        """Validate strategy parameters."""
        try:
            # Get parameter definitions
            params = strategy_class.get_parameters()

            # Check parameter metadata
            invalid = []
            for name, meta in params.items():
                if not all(k in meta for k in ['type', 'default']):
                    invalid.append(name)

            if invalid:
                return ValidationResult(
                    passed=False,
                    message=f"Invalid parameter definitions: {invalid}"
                )

            # Create with default parameters
            strategy = strategy_class()

            # Test parameter validation
            strategy.validate_parameters()

            return ValidationResult(
                passed=True,
                message="Parameters validated successfully",
                details={'parameters': params}
            )

        except Exception as e:
            return ValidationResult(
                passed=False,
                message=f"Parameter validation failed: {str(e)}"
            )

    def _validate_risk_management(self,
                                strategy_class: Type[StrategyBase],
                                **kwargs) -> ValidationResult:
        """Validate risk management."""
        try:
            strategy = strategy_class()

            # Check position sizing
            if not hasattr(strategy, 'position'):
                return ValidationResult(
                    passed=False,
                    message="Missing position management"
                )

            # Check stop loss / take profit
            risk_checks = {
                'stop_loss': False,
                'take_profit': False,
                'position_sizing': False
            }

            # Analyze source code
            import inspect
            source = inspect.getsource(strategy_class)
            risk_checks['stop_loss'] = 'stop_loss' in source
            risk_checks['take_profit'] = 'take_profit' in source
            risk_checks['position_sizing'] = 'position_size' in source

            missing = [k for k, v in risk_checks.items() if not v]

            if missing and self.strict_mode:
                return ValidationResult(
                    passed=False,
                    message=f"Missing risk management: {missing}"
                )

            return ValidationResult(
                passed=True,
                message="Risk management validated successfully",
                details={'implemented': risk_checks}
            )

        except Exception as e:
            return ValidationResult(
                passed=False,
                message=f"Risk validation failed: {str(e)}"
            )

    def _validate_performance(self,
                            strategy_class: Type[StrategyBase],
                            **kwargs) -> ValidationResult:
        """Validate strategy performance."""
        if self.sample_data is None:
            return ValidationResult(
                passed=True,
                message="Performance validation skipped (no sample data)"
            )

        try:
            from ..core import Backtest

            # Run backtest with sample data
            bt = Backtest(self.sample_data)
            results = bt.run(strategy_class)

            # Check basic metrics
            metrics = {
                'total_trades': len(results.trades) > 0,
                'sharpe_ratio': results.metrics['sharpe_ratio'] > 0,
                'max_drawdown': results.metrics['max_drawdown'] < 0.5
            }

            failed = [k for k, v in metrics.items() if not v]

            if failed and self.strict_mode:
                return ValidationResult(
                    passed=False,
                    message=f"Performance checks failed: {failed}",
                    details={'metrics': results.metrics}
                )

            return ValidationResult(
                passed=True,
                message="Performance validated successfully",
                details={'metrics': results.metrics}
            )

        except Exception as e:
            return ValidationResult(
                passed=False,
                message=f"Performance validation failed: {str(e)}"
            )

def validate_strategy(strategy_class: Type[StrategyBase],
                     **kwargs) -> ValidationReport:
    """
    Convenience function to validate strategy.

    Args:
        strategy_class: Strategy to validate
        **kwargs: Validation parameters

    Returns:
        ValidationReport: Validation results
    """
    validator = StrategyValidator(**kwargs)
    return validator.validate(strategy_class)
