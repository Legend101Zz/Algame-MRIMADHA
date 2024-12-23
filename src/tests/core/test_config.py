import pytest
import json
from pathlib import Path
from datetime import datetime

from algame.core.config import (
    ConfigManager,
    BacktestConfig,
    StrategyConfig,
    EngineConfig
)

def test_config_manager_init(temp_data_dir):
    """Test ConfigManager initialization."""
    manager = ConfigManager(config_dir=temp_data_dir)
    assert manager.config_dir == temp_data_dir

def test_save_load_config(temp_data_dir):
    """Test saving and loading configurations."""
    manager = ConfigManager(config_dir=temp_data_dir)

    # Create test config
    config = BacktestConfig(
        name="Test Config",
        description="Test configuration",
        symbols=['AAPL', 'GOOGL'],
        start_date=datetime(2020, 1, 1),
        end_date=datetime(2020, 12, 31),
        strategy=StrategyConfig(
            name="Test Strategy",
            parameters={'period': 20}
        ),
        engine=EngineConfig(
            initial_capital=100000,
            commission=0.001
        )
    )

    # Save config
    saved_path = manager.save_config(config)
    assert saved_path.exists()

    # Load config
    loaded_config = manager.load_config(saved_path)

    # Compare configurations
    assert loaded_config.name == config.name
    assert loaded_config.symbols == config.symbols
    assert loaded_config.strategy.parameters == config.strategy.parameters

def test_config_validation():
    """Test configuration validation."""
    # Test valid config
    valid_config = BacktestConfig(
        name="Test Config",
        symbols=['AAPL'],
        start_date=datetime(2020, 1, 1),
        end_date=datetime(2020, 12, 31),
        strategy=StrategyConfig(name="Test Strategy")
    )
    assert valid_config.validate()

    # Test invalid config (no symbols)
    invalid_config = BacktestConfig(
        name="Test Config",
        symbols=[],  # Empty symbols list
        start_date=datetime(2020, 1, 1),
        end_date=datetime(2020, 12, 31),
        strategy=StrategyConfig(name="Test Strategy")
    )
    with pytest.raises(ValueError):
        invalid_config.validate()

def test_config_templates(temp_data_dir):
    """Test configuration templates."""
    manager = ConfigManager(config_dir=temp_data_dir)

    # Create from basic template
    basic_config = manager.create_template(
        "Basic Strategy",
        template_type='basic'
    )
    assert basic_config.validate()

    # Create from optimization template
    opt_config = manager.create_template(
        "Optimization Strategy",
        template_type='optimization'
    )
    assert opt_config.validate()
    assert isinstance(opt_config.strategy.parameters['sma_fast'], dict)

def test_config_versioning(temp_data_dir):
    """Test configuration versioning."""
    manager = ConfigManager(config_dir=temp_data_dir)

    # Create multiple versions
    config = BacktestConfig(
        name="Test Config",
        symbols=['AAPL'],
        version="1.0.0",
        strategy=StrategyConfig(name="Test Strategy")
    )

    path1 = manager.save_config(config)

    config.version = "1.1.0"
    path2 = manager.save_config(config)

    # List configs
    configs = manager.list_configs()
    assert len(configs) == 2
    assert any(c['version'] == "1.0.0" for c in configs)
    assert any(c['version'] == "1.1.0" for c in configs)

def test_default_config():
    """Test default configuration."""
    manager = ConfigManager()
    default = manager.get_default_config()

    assert default.validate()
    assert default.engine.initial_capital == 100000
    assert default.engine.commission == 0.001

def test_config_migration(temp_data_dir):
    """Test configuration migration."""
    manager = ConfigManager(config_dir=temp_data_dir)

    # Create old format config
    old_config = {
        'name': 'Old Config',
        'version': '0.9.0',
        'parameters': {'period': 20}
    }

    old_path = temp_data_dir / 'old_config.json'
    with old_path.open('w') as f:
        json.dump(old_config, f)

    # Should migrate to new format
    with pytest.raises(ValueError):
        manager.load_config(old_path)

def test_strategy_config():
    """Test strategy configuration."""
    config = StrategyConfig(
        name="Test Strategy",
        parameters={
            'sma_period': 20,
            'rsi_period': 14
        },
        trading_hours={
            'start': '09:30',
            'end': '16:00'
        }
    )

    assert config.validate()
    assert config.name == "Test Strategy"
    assert config.parameters['sma_period'] == 20

def test_engine_config():
    """Test engine configuration."""
    config = EngineConfig(
        initial_capital=100000,
        commission=0.001,
        slippage=0.0001,
        position_limit=1.0
    )

    assert config.initial_capital == 100000
    assert config.commission == 0.001
    assert config.position_limit == 1.0

if __name__ == '__main__':
    pytest.main([__file__])
