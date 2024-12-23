import pytest
from pathlib import Path

from algame.tools.converter import (
    PineScriptConverter,
    PineParser,
    PineConverter,
    ConversionResult
)

@pytest.fixture
def converter():
    """Create PineScript converter instance."""
    return PineScriptConverter()

@pytest.fixture
def sample_pine_script():
    """Simple PineScript strategy."""
    return """
//@version=5
strategy("Simple MA Crossover", overlay=true)

// Input parameters
fastLength = input(10, "Fast Length")
slowLength = input(20, "Slow Length")

// Calculate MAs
fastMA = ta.sma(close, fastLength)
slowMA = ta.sma(close, slowLength)

// Entry conditions
if ta.crossover(fastMA, slowMA)
    strategy.entry("Long", strategy.long)

if ta.crossunder(fastMA, slowMA)
    strategy.close("Long")
"""

def test_pine_parser(sample_pine_script):
    """Test PineScript parsing."""
    parser = PineParser()
    result = parser.parse(sample_pine_script)

    assert result['version'].value == 5
    assert 'fastLength' in result['variables']
    assert 'slowLength' in result['variables']
    assert 'strategy' in result

def test_basic_conversion(converter, sample_pine_script):
    """Test basic PineScript conversion."""
    result = converter.convert(sample_pine_script)

    assert result.success
    assert len(result.warnings) == 0
    assert 'StrategyBase' in result.python_code
    assert 'def initialize' in result.python_code
    assert 'def next' in result.python_code

def test_conversion_with_template(converter):
    """Test conversion using template."""
    pine_code = """
//@version=5
strategy("RSI Strategy")

rsiLength = input(14, "RSI Length")
rsiOverbought = input(70)
rsiOversold = input(30)

rsi = ta.rsi(close, rsiLength)

if rsi < rsiOversold
    strategy.entry("Long", strategy.long)

if rsi > rsiOverbought
    strategy.close("Long")
"""

    result = converter.convert_file(
        pine_code,
        use_template='momentum'
    )

    assert result.success
    assert 'MomentumStrategy' in result.python_code

def test_indicator_conversion(converter):
    """Test technical indicator conversion."""
    pine_code = """
//@version=5
strategy("Indicator Test")

sma = ta.sma(close, 20)
rsi = ta.rsi(close, 14)
macd = ta.macd(close, 12, 26, 9)
"""

    result = converter.convert(pine_code)

    assert 'SMA' in result.python_code
    assert 'RSI' in result.python_code
    assert 'MACD' in result.python_code

def test_error_handling(converter):
    """Test conversion error handling."""
    # Invalid syntax
    invalid_code = """
//@version=5
strategy("Invalid")

if (invalid syntax here)
    strategy.entry("Long")
"""

    result = converter.convert(invalid_code)
    assert not result.success
    assert len(result.warnings) > 0

def test_pine_version_detection(converter):
    """Test PineScript version detection."""
    # Version 4
    v4_code = """
//@version=4
strategy("V4 Strategy")
"""
    result = converter.convert(v4_code)
    assert result.meta_info['pine_version'] == '4'

    # Version 5
    v5_code = """
//@version=5
strategy("V5 Strategy")
"""
    result = converter.convert(v5_code)
    assert result.meta_info['pine_version'] == '5'

def test_complex_strategy_conversion(converter):
    """Test converting complex strategy."""
    pine_code = """
//@version=5
strategy("Complex Strategy", overlay=true)

// Inputs
rsiLength = input(14, "RSI Length")
rsiOverbought = input(70)
rsiOversold = input(30)
atrPeriod = input(14, "ATR Period")
atrMultiplier = input(2, "ATR Multiplier")

// Indicators
rsi = ta.rsi(close, rsiLength)
atr = ta.atr(atrPeriod)

// Entry conditions
longCondition = rsi < rsiOversold and ta.crossover(close, ta.sma(close, 20))
shortCondition = rsi > rsiOverbought and ta.crossunder(close, ta.sma(close, 20))

// Position management
if longCondition
    stopLoss = close - (atr * atrMultiplier)
    takeProfit = close + (atr * atrMultiplier * 1.5)
    strategy.entry("Long", strategy.long, stop=stopLoss, limit=takeProfit)

if shortCondition
    strategy.close("Long")
"""

    result = converter.convert(pine_code)

    assert result.success
    assert 'RSI' in result.python_code
    assert 'ATR' in result.python_code
    assert 'stop_loss' in result.python_code
    assert 'take_profit' in result.python_code

def test_format_validation(converter):
    """Test output format validation."""
    result = converter.convert("""
//@version=5
strategy("Format Test")

sma = ta.sma(close, 20)
if ta.crossover(close, sma)
    strategy.entry("Long", strategy.long)
""")

    # Try to compile generated code
    import py_compile
    from tempfile import NamedTemporaryFile

    with NamedTemporaryFile(suffix='.py') as tmp:
        tmp.write(result.python_code.encode())
        tmp.flush()
        assert py_compile.compile(tmp.name) is not None

def test_conversion_history(converter):
    """Test conversion history tracking."""
    pine_code = """
//@version=5
strategy("History Test")
"""

    # Convert multiple times
    for _ in range(3):
        converter.convert(pine_code)

    history = converter.get_history()
    assert len(history) == 3
    assert all(isinstance(r, ConversionResult) for r in history)

def test_template_management(converter):
    """Test template management."""
    templates = converter.templates
    assert len(templates) > 0

    template = converter.get_template('basic')
    assert '{strategy_name}' in template
    assert '{indicators}' in template

def test_custom_template(converter):
    """Test using custom template."""
    template = """
from algame.strategy import StrategyBase

class {strategy_name}(StrategyBase):
    def initialize(self):
        {indicators}

    def next(self):
        {trading_logic}
"""

    result = converter.convert("""
//@version=5
strategy("Custom Template Test")
""", template=template)

    assert result.success
    assert 'initialize' in result.python_code
    assert 'next' in result.python_code

if __name__ == '__main__':
    pytest.main([__file__])
