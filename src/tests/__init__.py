"""Test suite for algame package."""

import pytest
import os
import sys

# Add src directory to path so tests can import algame
src_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src')
sys.path.insert(0, src_path)

# Constants used by multiple tests
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
SAMPLE_CONFIG_PATH = os.path.join(TEST_DATA_DIR, 'sample_config.yaml')

# Pytest configuration
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers",
        "slow: mark test as slow running"
    )
