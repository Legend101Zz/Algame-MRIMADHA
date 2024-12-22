import re
import ast
from typing import Dict, List, Set, Optional, Any, Union, Tuple
import logging
import pandas as pd

from .parser import PineParser

logger = logging.getLogger(__name__)


class PineConverter:
    """
    PineScript to Python converter.

    This class handles the actual conversion process:
    1. Uses PineParser to analyze code
    2. Generates equivalent Python code
    3. Creates Algame strategy class

    The converter maintains mappings for:
    - Variable translations
    - Function translations
    - State conversions

    Example:
        converter = PineConverter()
        python_code = converter.convert(pine_script)
    """

    # Built-in function mappings
    BUILT_IN_FUNCS = {
        'ta.sma': ('SMA', 'self.data.Close'),
        'ta.ema': ('EMA', 'self.data.Close'),
        'ta.rsi': ('RSI', 'self.data.Close'),
        'ta.macd': ('MACD', 'self.data.Close'),
        'ta.atr': ('ATR', 'self.data'),
        'ta.bb': ('Bollinger', 'self.data.Close'),
        'ta.supertrend': ('SuperTrend', 'self.data'),
        'ta.vwap': ('VWAP', 'self.data'),
        'ta.obv': ('OBV', 'self.data.Close', 'self.data.Volume'),
    }

    # Operator translations
    OPERATORS = {
        'and': 'and',
        'or': 'or',
        'not': 'not',
        '==': '==',
        '!=': '!=',
        '>': '>',
        '<': '<',
        '>=': '>=',
        '<=': '<=',
        '+': '+',
        '-': '-',
        '*': '*',
        '/': '/',
        '%': '%',
    }

    def __init__(self):
        """Initialize converter."""
        self.parser = PineParser()
        self.translations: Dict[str, str] = {}
        self.imported_modules: Set[str] = set()
        self.strategy_vars: Dict[str, Any] = {}
        self.indicators: Dict[str, Any] = {}

    def convert(self, pine_code: str) -> str:
        """
        Convert PineScript to Python strategy.

        Args:
            pine_code: Raw PineScript code

        Returns:
            Python strategy class code

        Raises:
            ValueError: If parsing fails
            SyntaxError: If conversion fails
        """
        try:
            # Parse PineScript
            self.parsed = self.parser.parse(pine_code)

            # Generate translations
            self._generate_translations(self.parsed)

            # Generate strategy code
            strategy_code = self._generate_strategy(self.parsed)

            # Validate generated code
            self._validate_code(strategy_code)

            return strategy_code

        except Exception as e:
            logger.error(f"Conversion failed: {str(e)}")
            raise

    def _generate_translations(self, parsed: Dict[str, Any]):
        """
        Generate translation mappings.

        Creates mappings for:
        - Variables (inputs, series, locals)
        - Functions (built-in, user defined)
        - Operators and expressions
        """
        # Reset translations
        self.translations.clear()

        # Variable translations
        for name, var in parsed['variables'].items():
            if var.is_input:
                # Convert to strategy parameter
                self.translations[name] = f"self.parameters['{name}']"
                self.strategy_vars[name] = var.value
            elif var.is_series:
                # Convert to indicator or data reference
                self.translations[name] = f"self.{name}"
                if var.type == 'series':
                    self.indicators[name] = var
            else:
                # Convert to instance variable
                self.translations[name] = f"self._{name}"

        # Function translations
        for name, func in parsed['functions'].items():
            if func.is_builtin:
                # Use builtin mapping if available
                if name in self.BUILT_IN_FUNCS:
                    self.translations[name] = self._generate_builtin_call(name, func)
            else:
                # Convert to method
                self.translations[name] = self._generate_function(name, func)

        # Add common PineScript functions
        self._add_common_translations()

    def _generate_builtin_call(self, name: str, func: Any) -> str:
        """Generate code for built-in function call."""
        if name not in self.BUILT_IN_FUNCS:
            raise ValueError(f"Unknown built-in function: {name}")

        template = self.BUILT_IN_FUNCS[name]
        indicator_name = template[0]
        input_args = template[1:]

        # Add to imports
        self.imported_modules.add(indicator_name)

        # Generate call
        args = ', '.join(input_args)
        if func.params:
            args += ', ' + ', '.join(f"{p}={self.translations.get(p, p)}"
                                   for p in func.params)

        return f"{indicator_name}({args})"

    def _generate_function(self, name: str, func: Any) -> str:
        """Generate code for user-defined function."""
        # Convert parameters
        params = []
        for param in func.params:
            if param in self.translations:
                params.append(self.translations[param])
            else:
                params.append(param)

        # Convert body
        body = func.body
        for old, new in self.translations.items():
            body = re.sub(r'\b' + old + r'\b', new, body)

        # Generate function
        return f"""
    def _{name}({', '.join(params)}):
        {body}
        """

    def _generate_strategy(self, parsed: Dict[str, Any]) -> str:
        """Generate complete strategy class code."""
        # Generate imports
        import_lines = [
            'from algame.strategy import StrategyBase',
            'from algame.indicators import *',
            'import numpy as np',
            ''
        ]

        # Add any additional imports
        for module in sorted(self.imported_modules):
            import_lines.append(f"from algame.indicators import {module}")

        # Generate class structure
        class_lines = [
            f"class {parsed['strategy'].get('title', 'PineStrategy')}(StrategyBase):",
            '    """',
            '    Converted PineScript Strategy.',
            '',
            f"    Original Version: {parsed['version'].name}",
            '    """',
            '',
            '    def __init__(self, parameters=None):',
            '        """Initialize strategy."""',
            '        super().__init__(parameters)',
            '',
            '        # Default parameters',
            f'        self.parameters = parameters or {self.strategy_vars!r}',
            '',
            '        # Initialize variables'
        ]

        # Add instance variables
        for name, var in parsed['variables'].items():
            if not var.is_input and not var.is_series:
                value = repr(var.value)
                class_lines.append(f'        self._{name} = {value}')

        # Add initialize method
        init_lines = [
            '',
            '    def initialize(self):',
            '        """Initialize strategy components."""'
        ]

        # Add indicators
        for name, indicator in self.indicators.items():
            init_lines.append(f"        self.{name} = {self.translations[name]}")

        # Add next method
        next_lines = [
            '',
            '    def next(self):',
            '        """Generate trading signals."""',
            ''
        ]

        # Convert entry conditions
        for entry in parsed['entries']:
            condition = self._translate_expression(entry['condition'])
            size = entry.get('size', 1.0)
            stop_loss = entry.get('stop_loss')
            take_profit = entry.get('take_profit')

            next_lines.extend([
                f'        if {condition}:',
                f'            self.buy('
            ])

            # Add optional parameters
            params = []
            if size != 1.0:
                params.append(f'size={size}')
            if stop_loss:
                params.append(f'sl={stop_loss}')
            if take_profit:
                params.append(f'tp={take_profit}')

            if params:
                next_lines.append(f'                {", ".join(params)}')
            next_lines.append('            )')

        # Convert exit conditions
        for exit in parsed['exits']:
            condition = self._translate_expression(exit['condition'])
            next_lines.extend([
                f'        if {condition}:',
                '            self.close()'
            ])

        # Combine all code
        code = '\n'.join(import_lines + [''] + class_lines + init_lines + next_lines)
        return code

    def _translate_expression(self, expr: str) -> str:
        """
        Translate PineScript expression to Python.

        Handles:
        - Variable references
        - Function calls
        - Operators
        - Series indexing
        - Common patterns
        """
        # Replace operators
        for pine_op, py_op in self.OPERATORS.items():
            expr = expr.replace(pine_op, py_op)

        # Replace variables
        for name, translation in self.translations.items():
            expr = re.sub(r'\b' + name + r'\b', translation, expr)

        # Handle array indexing
        expr = re.sub(r'\[(\d+)\]', lambda m: f'[-{int(m.group(1))+1}]', expr)

        # Handle common patterns
        expr = expr.replace('strategy.position_size', 'self.position.size')
        expr = expr.replace('close', 'self.data.Close[-1]')
        expr = expr.replace('open', 'self.data.Open[-1]')
        expr = expr.replace('high', 'self.data.High[-1]')
        expr = expr.replace('low', 'self.data.Low[-1]')
        expr = expr.replace('volume', 'self.data.Volume[-1]')

        return expr

    def _add_common_translations(self):
        """Add translations for common PineScript functions."""
        self.translations.update({
            'cross': lambda x, y: f"({x}[-1] > {y}[-1] and {x}[-2] <= {y}[-2])",
            'crossover': lambda x, y: f"({x}[-1] > {y}[-1] and {x}[-2] <= {y}[-2])",
            'crossunder': lambda x, y: f"({x}[-1] < {y}[-1] and {x}[-2] >= {y}[-2])",
            'highest': lambda x, p: f"max({x}[-{p}:])",
            'lowest': lambda x, p: f"min({x}[-{p}:])",
            'barssince': lambda cond: f"self._bars_since({cond})",
        })

    def _validate_code(self, code: str):
        """Validate generated Python code."""
        try:
            # Check syntax
            compile(code, '<string>', 'exec')
        except SyntaxError as e:
            logger.error(f"Generated invalid Python code: {str(e)}")
            raise
