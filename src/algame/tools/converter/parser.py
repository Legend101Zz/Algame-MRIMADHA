"""
PineScript to Python Strategy Converter.

This module provides functionality to convert TradingView PineScript strategies
to AlGame Python strategies. It handles:

1. PineScript Parsing:
   - Lexical analysis of PineScript code
   - AST (Abstract Syntax Tree) generation
   - Script version detection

2. Code Translation:
   - Variable and function mapping
   - State tracking and conversion
   - Built-in function translation

3. Strategy Generation:
   - Python code generation
   - Indicator adaptation
   - Strategy class creation

Features:
- Support for PineScript v4 and v5
- Built-in function translation
- State management
- Indicator conversion
- Strategy validation
"""

import re
import ast
from typing import Dict, List, Set, Optional, Any, Union, Tuple
import logging
from dataclasses import dataclass
from enum import Enum
import pandas as pd

logger = logging.getLogger(__name__)

class PineVersion(Enum):
    """PineScript version enumeration."""
    V4 = 4
    V5 = 5

@dataclass
class PineFunction:
    """PineScript function information."""
    name: str
    params: List[str]
    return_type: str
    body: str
    is_builtin: bool = False

@dataclass
class PineVariable:
    """PineScript variable information."""
    name: str
    type: str
    value: Any
    is_series: bool = False
    is_input: bool = False

class PineParser:
    """
    PineScript code parser.

    This class handles:
    1. Script version detection
    2. Lexical analysis
    3. Function and variable extraction
    4. State tracking

    The parser maintains state about:
    - Declared functions
    - Variables and their types
    - Input parameters
    - Strategy settings
    """

    # Common PineScript patterns
    PATTERNS = {
        'function': r'//@function\s+([\w\d_]+)\s*\((.*?)\)',
        'variable': r'(var|input\.[^=]+)\s*([\w\d_]+)\s*=\s*([^;\n]+)',
        'strategy': r'strategy\((.*?)\)',
        'entry': r'strategy\.(entry|order)\((.*?)\)',
        'exit': r'strategy\.close\((.*?)\)',
        'indicator': r'(ta\.|math\.)([\w\d_]+)\((.*?)\)',
    }

    # Built-in function mappings
    BUILTIN_FUNCS = {
        'ta.sma': 'self.add_indicator("SMA", {0}, {1})',
        'ta.ema': 'self.add_indicator("EMA", {0}, {1})',
        'ta.rsi': 'self.add_indicator("RSI", {0}, {1})',
        'ta.macd': 'self.add_indicator("MACD", {0}, {1}, {2})',
        'ta.crossover': '{0}[-1] <= {1}[-1] and {0}[-2] > {1}[-2]',
        'ta.crossunder': '{0}[-1] >= {1}[-1] and {0}[-2] < {1}[-2]',
    }

    def __init__(self):
        """Initialize parser."""
        self.version = PineVersion.V5  # Default to latest
        self.functions: Dict[str, PineFunction] = {}
        self.variables: Dict[str, PineVariable] = {}
        self.strategy_settings: Dict[str, Any] = {}
        self.used_indicators: Set[str] = set()

        # Compilation state
        self._current_function: Optional[str] = None
        self._loops: List[str] = []
        self._conditionals: List[str] = []

    def parse(self, code: str) -> Dict[str, Any]:
        """
        Parse PineScript code.

        Args:
            code: Raw PineScript code

        Returns:
            Dict containing parsed components:
            - version: PineScript version
            - functions: Declared functions
            - variables: Declared variables
            - strategy: Strategy settings
            - indicators: Used indicators
        """
        # Detect version
        self.version = self._detect_version(code)
        logger.info(f"Detected PineScript version: {self.version}")

        # Clean code
        code = self._clean_code(code)

        # Extract components
        self._extract_functions(code)
        self._extract_variables(code)
        self._extract_strategy_settings(code)
        self._analyze_indicators(code)

        return {
            'version': self.version,
            'functions': self.functions,
            'variables': self.variables,
            'strategy': self.strategy_settings,
            'indicators': self.used_indicators
        }

    def _detect_version(self, code: str) -> PineVersion:
        """
        Detect PineScript version from code.

        Uses several heuristics:
        1. Explicit version indicator
        2. Syntax patterns
        3. Feature usage
        """
        # Check for explicit version
        if '//@version=5' in code:
            return PineVersion.V5
        elif '//@version=4' in code:
            return PineVersion.V4

        # Check syntax patterns
        v5_patterns = [
            'var.time_',  # v5 time variables
            'matrix.',    # v5 matrix operations
            'lines[]',    # v5 array syntax
        ]

        v5_count = sum(1 for p in v5_patterns if p in code)
        return PineVersion.V5 if v5_count > 0 else PineVersion.V4

    def _clean_code(self, code: str) -> str:
        """
        Clean and normalize PineScript code.

        Handles:
        1. Comment removal
        2. Whitespace normalization
        3. Line continuation
        """
        # Remove comments
        code = re.sub(r'//.*$', '', code, flags=re.MULTILINE)
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)

        # Handle line continuation
        code = re.sub(r'\\\n\s*', '', code)

        # Normalize whitespace
        code = re.sub(r'\s+', ' ', code)

        return code.strip()

    def _extract_functions(self, code: str):
        """Extract function declarations and implementations."""
        # Find all function declarations
        func_matches = re.finditer(self.PATTERNS['function'], code)

        for match in func_matches:
            name = match.group(1)
            params_str = match.group(2)

            # Parse parameters
            params = [p.strip() for p in params_str.split(',') if p.strip()]

            # Find function body
            body_start = match.end()
            body_end = self._find_function_end(code, body_start)
            body = code[body_start:body_end].strip()

            # Store function
            self.functions[name] = PineFunction(
                name=name,
                params=params,
                return_type='float',  # Default type
                body=body
            )

    def _find_function_end(self, code: str, start: int) -> int:
        """Find the end of a function body."""
        bracket_count = 1
        i = start

        while i < len(code):
            if code[i] == '{':
                bracket_count += 1
            elif code[i] == '}':
                bracket_count -= 1
                if bracket_count == 0:
                    return i
            i += 1

        return len(code)

    def _extract_variables(self, code: str):
        """Extract variable declarations and initializations."""
        var_matches = re.finditer(self.PATTERNS['variable'], code)

        for match in var_matches:
            type_spec = match.group(1)
            name = match.group(2)
            value = match.group(3)

            # Determine variable type
            is_input = type_spec.startswith('input.')
            is_series = 'array' in type_spec or '[' in value

            # Parse value
            try:
                parsed_value = self._parse_value(value)
            except:
                parsed_value = value

            # Store variable
            self.variables[name] = PineVariable(
                name=name,
                type=type_spec,
                value=parsed_value,
                is_series=is_series,
                is_input=is_input
            )

    def _parse_value(self, value: str) -> Any:
        """Parse variable value from string."""
        # Try numeric
        try:
            return float(value)
        except ValueError:
            pass

        # Try boolean
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'

        # Try array
        if value.startswith('['):
            try:
                return ast.literal_eval(value)
            except:
                pass

        # Return as string
        return value

    def _extract_strategy_settings(self, code: str):
        """Extract strategy configuration settings."""
        # Find strategy declaration
        match = re.search(self.PATTERNS['strategy'], code)
        if not match:
            return

        settings_str = match.group(1)

        # Parse settings
        settings = {}
        for setting in settings_str.split(','):
            if '=' not in setting:
                continue

            key, value = setting.split('=')
            key = key.strip()
            value = value.strip()

            try:
                value = self._parse_value(value)
            except:
                pass

            settings[key] = value

        self.strategy_settings.update(settings)

    def _analyze_indicators(self, code: str):
        """Find and analyze technical indicator usage."""
        # Find all indicator calls
        matches = re.finditer(self.PATTERNS['indicator'], code)

        for match in matches:
            namespace = match.group(1)  # ta. or math.
            func = match.group(2)       # indicator name
            args = match.group(3)       # arguments

            indicator = f"{namespace}{func}"
            self.used_indicators.add(indicator)

            # Parse arguments
            args = [a.strip() for a in args.split(',')]

            # Store as function
            self.functions[indicator] = PineFunction(
                name=indicator,
                params=args,
                return_type='float',
                body='',
                is_builtin=True
            )
