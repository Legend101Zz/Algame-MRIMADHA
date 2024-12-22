"""
GUI module for Algame backtesting framework.

This module provides a complete graphical interface for:
1. Strategy development and testing
2. Data management and visualization
3. Backtesting and optimization
4. Results analysis

Architecture:
------------
The GUI follows a modular, component-based architecture:

1. Main Window:
   - Central container for the application
   - Manages global state and navigation
   - Coordinates between panels

2. Panels:
   - DataPanel: Data management and visualization
   - StrategyPanel: Strategy development and configuration
   - ResultsPanel: Backtest results analysis
   Each panel is independent but can communicate via events

3. Components:
   - Chart: Interactive financial charting
   - Builder: Visual strategy building
   - Optimizer: Parameter optimization
   All components are reusable and self-contained

4. Dialogs:
   - Parameter: Parameter configuration
   - Preferences: Application settings
   - About: Application information

Design Principles:
-----------------
1. Separation of Concerns
   - Each component has a single responsibility
   - Business logic separated from presentation
   - Data flow is unidirectional

2. Reusability
   - Components are self-contained
   - Dependencies are explicit
   - Configuration via properties

3. User Experience
   - Consistent interface patterns
   - Progressive disclosure
   - Clear feedback
"""

from typing import Optional, Dict, Any
import logging
import tkinter as tk
from pathlib import Path
import json

# Import components
from .components.chart import Chart
from .components.optimizer import OptimizerPanel
from .panels.data import DataPanel
from .panels.strategy import StrategyPanel
from .panels.results import ResultsPanel
from .main import MainWindow

logger = logging.getLogger(__name__)

class GUI:
    """
    Main GUI application controller.

    This class manages:
    1. Window creation and lifecycle
    2. Configuration and settings
    3. Global state management
    4. Error handling

    Examples:
        # Create and start GUI
        app = GUI()
        app.start()

        # Create with custom config
        app = GUI(config={'theme': 'dark'})
        app.start()
    """

    # Default configuration
    DEFAULT_CONFIG = {
        'theme': 'default',
        'window_size': (1200, 800),
        'chart_style': 'light',
        'font_family': 'Arial',
        'font_size': 10
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize GUI application.

        Args:
            config: Optional configuration override
        """
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}
        self._setup_logging()
        self._load_user_settings()

        # Main window reference
        self.window: Optional[MainWindow] = None

    def _setup_logging(self) -> None:
        """Configure GUI logging."""
        log_dir = Path.home() / '.algame' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)

        handler = logging.FileHandler(log_dir / 'gui.log')
        handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )

        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

    def _load_user_settings(self) -> None:
        """Load user settings from config file."""
        config_file = Path.home() / '.algame' / 'gui_config.json'
        if config_file.exists():
            try:
                with config_file.open('r') as f:
                    user_config = json.load(f)
                self.config.update(user_config)
            except Exception as e:
                logger.error(f"Failed to load user config: {e}")

    def save_settings(self) -> None:
        """Save current settings to config file."""
        config_file = Path.home() / '.algame' / 'gui_config.json'
        try:
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with config_file.open('w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def start(self) -> None:
        """Start GUI application."""
        try:
            # Create root window
            root = tk.Tk()
            root.title("Algame - Backtesting Platform")

            # Set window size
            width, height = self.config['window_size']
            root.geometry(f"{width}x{height}")

            # Create main window
            self.window = MainWindow(root, self.config)

            # Start event loop
            root.mainloop()

        except Exception as e:
            logger.error(f"Failed to start GUI: {e}")
            raise

    def stop(self) -> None:
        """Stop GUI application."""
        try:
            # Save settings
            self.save_settings()

            # Close window
            if self.window:
                self.window.quit()

        except Exception as e:
            logger.error(f"Failed to stop GUI: {e}")

# Create default instance
app = GUI()

__all__ = [
    'GUI',
    'MainWindow',
    'Chart',
    'OptimizerPanel',
    'DataPanel',
    'StrategyPanel',
    'ResultsPanel',
    'app'
]
