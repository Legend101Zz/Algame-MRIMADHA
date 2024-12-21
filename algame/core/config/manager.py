import json
import yaml
from pathlib import Path
import logging
from typing import Optional, Union, Dict

from .types import BacktestConfig

logger = logging.getLogger(__name__)

class ConfigManager:
    """
    Configuration management system.

    This class handles:
    1. Loading/saving configurations
    2. Configuration validation
    3. Version management
    4. Default configurations
    5. Configuration migration

    Features:
    - Multiple file formats (JSON, YAML)
    - Validation on load/save
    - Version compatibility checking
    - Configuration templates
    """

    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize config manager.

        Args:
            config_dir: Directory for config files
        """
        self.config_dir = Path(config_dir) if config_dir else Path.home() / '.algame' / 'configs'
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def save_config(self,
                   config: BacktestConfig,
                   filename: Optional[str] = None,
                   format: str = 'yaml') -> Path:
        """
        Save configuration to file.

        Args:
            config: Configuration to save
            filename: Output filename
            format: File format ('json' or 'yaml')

        Returns:
            Path: Path to saved file
        """
        # Validate config
        config.validate()

        # Generate filename if not provided
        if filename is None:
            filename = f"{config.name.lower().replace(' ', '_')}_{config.version}"
            filename = f"{filename}.{format}"

        # Create full path
        file_path = self.config_dir / filename

        try:
            # Convert to dictionary
            data = config.to_dict()

            # Save file
            with file_path.open('w') as f:
                if format == 'json':
                    json.dump(data, f, indent=2, default=str)
                else:
                    yaml.dump(data, f, default_flow_style=False)

            logger.info(f"Saved configuration to {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"Error saving config: {str(e)}")
            raise

    def load_config(self, filename: Union[str, Path]) -> BacktestConfig:
        """
        Load configuration from file.

        Args:
            filename: Config file to load

        Returns:
            BacktestConfig: Loaded configuration
        """
        file_path = Path(filename)
        if not file_path.is_absolute():
            file_path = self.config_dir / file_path

        try:
            # Load file
            with file_path.open('r') as f:
                if file_path.suffix == '.json':
                    data = json.load(f)
                else:
                    data = yaml.safe_load(f)

            # Create config
            config = BacktestConfig.from_dict(data)

            # Validate
            config.validate()

            logger.info(f"Loaded configuration from {file_path}")
            return config

        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
            raise

    def list_configs(self) -> List[Dict]:
        """
        List available configurations.

        Returns:
            List[Dict]: List of config information
        """
        configs = []
        for file in self.config_dir.glob('*.*'):
            try:
                config = self.load_config(file)
                configs.append({
                    'name': config.name,
                    'version': config.version,
                    'author': config.author,
                    'created_at': config.created_at,
                    'path': str(file)
                })
            except Exception as e:
                logger.warning(f"Error loading {file}: {str(e)}")

        return configs

    def get_default_config(self) -> BacktestConfig:
        """
        Get default configuration.

        Returns:
            BacktestConfig: Default configuration
        """
        return BacktestConfig(
            name="Default Backtest",
            description="Default backtest configuration",
            engine=EngineConfig(),
            strategy=StrategyConfig(name="Default Strategy")
        )

    def create_template(self,
                       name: str,
                       template_type: str = 'basic') -> BacktestConfig:
        """
        Create configuration from template.

        Args:
            name: Configuration name
            template_type: Template type

        Returns:
            BacktestConfig: Created configuration
        """
        if template_type == 'basic':
            return BacktestConfig(
                name=name,
                description="Basic configuration template",
                engine=EngineConfig(
                    initial_capital=100000,
                    commission=0.001
                ),
                strategy=StrategyConfig(
                    name="Basic Strategy",
                    parameters={
                        'sma_period': 20,
                        'stop_loss': 0.02
                    }
                ),
                symbols=['AAPL', 'GOOGL']
            )

        elif template_type == 'optimization':
            return BacktestConfig(
                name=name,
                description="Optimization template",
                engine=EngineConfig(
                    parallel_assets=True,
                    max_workers=4
                ),
                strategy=StrategyConfig(
                    name="Optimization Strategy",
                    parameters={
                        'sma_fast': {'min': 10, 'max': 50, 'step': 5},
                        'sma_slow': {'min': 20, 'max': 100, 'step': 10}
                    }
                )
            )

        else:
            raise ValueError(f"Unknown template type: {template_type}")

    def validate_format(self, config: dict) -> bool:
        """
        Validate configuration format.

        Args:
            config: Configuration dictionary

        Returns:
            bool: True if valid

        Raises:
            ValueError: If format is invalid
        """
        required_fields = ['name', 'version', 'engine', 'strategy']
        missing = [f for f in required_fields if f not in config]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")

        # Check version format
        try:
            major, minor, patch = config['version'].split('.')
            int(major); int(minor); int(patch)
        except:
            raise ValueError("Invalid version format")

        return True
