"""
Strategy builder module.

This module provides tools for building trading strategies:
1. GUI-based strategy creation
2. Rule building and parsing
3. Strategy code generation
4. Parameter configuration

The builder follows a component-based design where:
- Each strategy part is a separate component
- Components can be added/removed/modified
- Components are validated independently
- Code is generated from components
"""

from .base import BuilderComponent, ComponentRegistry
from .strategy import StrategyBuilder
from .rules import RuleBuilder, RuleParser
from .indicators import IndicatorBuilder
from .parameters import ParameterBuilder
from .gui import StrategyEditor

__all__ = [
    'BuilderComponent',
    'ComponentRegistry',
    'StrategyBuilder',
    'RuleBuilder',
    'RuleParser',
    'IndicatorBuilder',
    'ParameterBuilder',
    'StrategyEditor'
]
