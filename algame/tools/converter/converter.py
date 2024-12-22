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


"""
High-level interface for PineScript conversion.

Key differences between PineConverter and PineScriptConverter:

PineConverter:
- Core conversion engine
- Handles syntax translations
- Manages state and mappings
- Lower level API

PineScriptConverter:
- High-level interface
- File handling
- Error handling & reporting
- Code validation & formatting
- Template management
- Integration with IDE/GUI
"""

@dataclass
class ConversionResult:
    """Result of strategy conversion."""
    python_code: str
    meta_info: Dict[str, Any]
    warnings: List[str]
    success: bool
    timestamp: datetime = datetime.now()

class PineScriptConverter:
    """
    High-level interface for converting PineScript strategies.

    Features:
    - File handling
    - Error reporting
    - Code validation
    - Template management
    - Conversion history

    Example:
        converter = PineScriptConverter()
        result = converter.convert_file('strategy.pine')
        if result.success:
            print(result.python_code)
    """

    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialize converter.

        Args:
            template_dir: Optional custom template directory
        """
        # Core converter
        self.converter = PineConverter()

        # Template management
        self.template_dir = Path(template_dir) if template_dir else \
                          Path(__file__).parent / 'templates'

        # Load templates
        self.templates = self._load_templates()

        # Conversion history
        self._history: List[ConversionResult] = []

        # Settings
        self.settings = {
            'auto_format': True,
            'strict_validation': False,
            'save_history': True,
            'max_history': 100
        }

    def convert(self, pine_code: str) -> ConversionResult:
        """
        Convert PineScript code to Python.

        Args:
            pine_code: Raw PineScript code

        Returns:
            ConversionResult containing:
            - Generated Python code
            - Metadata about conversion
            - Any warnings
            - Success status
        """
        warnings = []
        try:
            # Pre-process code
            processed_code = self._preprocess_code(pine_code)

            # Basic validation
            self._validate_pine_code(processed_code)

            # Convert code
            python_code = self.converter.convert(processed_code)

            # Post-process code
            python_code = self._postprocess_code(python_code)

            # Format if enabled
            if self.settings['auto_format']:
                python_code = self._format_code(python_code)

            # Build metadata
            meta = {
                'pine_version': str(self.converter.parser.version),
                'strategy_name': self.converter.parsed['strategy'].get('title', 'PineStrategy'),
                'num_indicators': len(self.converter.indicators),
                'num_variables': len(self.converter.strategy_vars)
            }

            # Create result
            result = ConversionResult(
                python_code=python_code,
                meta_info=meta,
                warnings=warnings,
                success=True
            )

            # Add to history
            if self.settings['save_history']:
                self._add_to_history(result)

            return result

        except Exception as e:
            logger.error(f"Conversion failed: {str(e)}")
            return ConversionResult(
                python_code='',
                meta_info={},
                warnings=warnings + [str(e)],
                success=False
            )

    def convert_file(self,
                    input_file: Union[str, Path],
                    output_file: Optional[Union[str, Path]] = None,
                    use_template: Optional[str] = None) -> ConversionResult:
        """
        Convert PineScript file to Python.

        Args:
            input_file: PineScript file path
            output_file: Optional output file path
            use_template: Optional template name to use

        Returns:
            ConversionResult with conversion details

        Raises:
            FileNotFoundError: If input file not found
            ValueError: If template not found
        """
        try:
            # Read input file
            with open(input_file, 'r') as f:
                pine_code = f.read()

            # Apply template if specified
            if use_template:
                template = self.get_template(use_template)
                pine_code = self._apply_template(pine_code, template)

            # Convert code
            result = self.convert(pine_code)

            # Save if output specified
            if output_file and result.success:
                self.save_strategy(result.python_code, output_file)

            return result

        except FileNotFoundError:
            logger.error(f"Input file not found: {input_file}")
            raise
        except Exception as e:
            logger.error(f"File conversion failed: {str(e)}")
            raise

    def validate_conversion(self, pine_code: str, python_code: str) -> List[str]:
        """
        Validate conversion result.

        Performs:
        1. Syntax validation
        2. Strategy class validation
        3. Logic comparison

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        try:
            # Check Python syntax
            compile(python_code, '<string>', 'exec')

            # Import and instantiate strategy
            namespace = {}
            exec(python_code, namespace)

            strategy_class = None
            for obj in namespace.values():
                if isinstance(obj, type) and issubclass(obj, StrategyBase):
                    strategy_class = obj
                    break

            if not strategy_class:
                errors.append("No strategy class found in generated code")

            # Check required methods
            if strategy_class:
                if not hasattr(strategy_class, 'initialize'):
                    errors.append("Missing initialize method")
                if not hasattr(strategy_class, 'next'):
                    errors.append("Missing next method")

            # Validate logic (if strict)
            if self.settings['strict_validation']:
                errors.extend(self._validate_logic(pine_code, python_code))

        except Exception as e:
            errors.append(f"Validation error: {str(e)}")

        return errors

    def _preprocess_code(self, code: str) -> str:
        """Pre-process PineScript code."""
        # Remove comments
        code = re.sub(r'//.*$', '', code, flags=re.MULTILINE)
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)

        # Normalize whitespace
        code = code.strip()

        # Add version if missing
        if not re.search(r'//@version=\d+', code):
            code = "//@version=5\n" + code

        return code

    def _postprocess_code(self, code: str) -> str:
        """Post-process generated Python code."""
        # Add module docstring
        docstring = '"""\nGenerated Python strategy.\n\nConverted from PineScript.\n"""\n\n'
        code = docstring + code

        # Add imports
        imports = set()
        if 'StrategyBase' in code:
            imports.add('from algame.strategy import StrategyBase')
        if any(ind in code for ind in ['SMA', 'RSI', 'MACD']):
            imports.add('from algame.indicators import *')

        if imports:
            code = '\n'.join(sorted(imports)) + '\n\n' + code

        return code

    def _format_code(self, code: str) -> str:
        """Format Python code."""
        try:
            import black
            return black.format_str(code, mode=black.FileMode())
        except ImportError:
            logger.warning("black not installed, skipping formatting")
            return code

    def _load_templates(self) -> Dict[str, str]:
        """Load conversion templates."""
        templates = {}

        if not self.template_dir.exists():
            return templates

        for file in self.template_dir.glob('*.template'):
            try:
                templates[file.stem] = file.read_text()
            except Exception as e:
                logger.warning(f"Failed to load template {file}: {e}")

        return templates

    def get_template(self, name: str) -> str:
        """Get template by name."""
        if name not in self.templates:
            raise ValueError(f"Template not found: {name}")
        return self.templates[name]

    def _apply_template(self, code: str, template: str) -> str:
        """Apply template to code."""
        # Extract key components from code
        components = self._extract_components(code)

        # Fill template placeholders
        filled = template
        for key, value in components.items():
            filled = filled.replace(f"{{{key}}}", value)

        return filled

    def _extract_components(self, code: str) -> Dict[str, str]:
        """Extract key components from code."""
        components = {}

        # Extract strategy name/settings
        if match := re.search(r'strategy\((.*?)\)', code):
            components['strategy_settings'] = match.group(1)

        # Extract indicators
        indicators = []
        for line in code.split('\n'):
            if 'ta.' in line:
                indicators.append(line.strip())
        components['indicators'] = '\n'.join(indicators)

        return components

    def _add_to_history(self, result: ConversionResult):
        """Add conversion to history."""
        self._history.append(result)

        # Trim if needed
        if len(self._history) > self.settings['max_history']:
            self._history = self._history[-self.settings['max_history']:]

    def get_history(self) -> List[ConversionResult]:
        """Get conversion history."""
        return self._history.copy()

    def clear_history(self):
        """Clear conversion history."""
        self._history.clear()

    @property
    def num_conversions(self) -> int:
        """Get number of conversions performed."""
        return len(self._history)

    @property
    def success_rate(self) -> float:
        """Get conversion success rate."""
        if not self._history:
            return 0.0
        successes = sum(1 for r in self._history if r.success)
        return successes / len(self._history)
