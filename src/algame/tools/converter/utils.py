"""Utility functions for PineScript conversion."""

from pathlib import Path
from typing import Optional
from .converter import PineScriptConverter

def convert_strategy(pine_code: str) -> str:
    """Convert PineScript strategy to Python."""
    converter = PineScriptConverter()
    return converter.converter.convert(pine_code)

def convert_file(input_file: str, output_file: Optional[str] = None) -> Optional[str]:
    """Convert PineScript file."""
    converter = PineScriptConverter()
    return converter.convert_file(input_file, output_file)
