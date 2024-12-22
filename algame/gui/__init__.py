"""
GUI module for Algame backtesting framework.

This module provides a complete graphical interface for:
1. Strategy development and testing
2. Data management and visualization
3. Backtesting and optimization
4. Results analysis

Architecture:
------------
The GUI is built using a modular, component-based architecture:

- Main Window: Central application container
- Components: Reusable UI elements
- Panels: Major functional sections
- Dialogs: Modal interactions

Component Hierarchy:
------------------
MainWindow
├── DataPanel
│   ├── DataSourceSelector
│   ├── TimeframeSelector
│   └── DataPreview
├── StrategyPanel
│   ├── StrategyBuilder
│   ├── ParameterEditor
│   └── IndicatorSelector
├── BacktestPanel
│   ├── EngineSelector
│   ├── ConfigEditor
│   └── ExecutionControl
└── ResultsPanel
    ├── PerformanceMetrics
    ├── TradeList
    └── Charts

Each component is designed to be:
- Self-contained
- Reusable
- Configurable
- Event-driven
"""

from typing import Dict, Optional, Any
import logging
import tkinter as tk
from pathlib import Path

logger = logging.getLogger(__name__)

# Version info
__version__ = "0.1.0"

# Import components
from .components.chart import Chart
from .components.builder import StrategyBuilder
from .components.optimizer import OptimizerPanel

# Import panels
from .panels.data import DataPanel
from .panels.strategy import StrategyPanel
from .panels.results import ResultsPanel

# Import main window
from .main import MainWindow

# GUI Configuration
DEFAULT_CONFIG = {
    'theme': 'default',
    'window_size': (1200, 800),
    'chart_style': 'light',
    'font_family': 'Arial',
    'font_size': 10
}

class GUI:
    """
    Main GUI controller.

    This class manages:
    1. Window creation and lifecycle
    2. Theme and styling
    3. Configuration
    4. Global state

    Usage:
        gui = GUI()
        gui.start()
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize GUI.

        Args:
            config: Optional configuration override
        """
        self.config = {**DEFAULT_CONFIG, **(config or {})}
        self._setup_logging()

    def _setup_logging(self):
        """Setup GUI logging."""
        log_dir = Path.home() / '.algame' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)

        handler = logging.FileHandler(log_dir / 'gui.log')
        handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )

        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

    def start(self):
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
            logger.error(f"Failed to start GUI: {str(e)}")
            raise

    def stop(self):
        """Stop GUI application."""
        try:
            self.window.quit()
        except Exception as e:
            logger.error(f"Failed to stop GUI: {str(e)}")

# Create default instance
app = GUI()

# Export public interface
__all__ = [
    'GUI',
    'MainWindow',
    'Chart',
    'StrategyBuilder',
    'OptimizerPanel',
    'DataPanel',
    'StrategyPanel',
    'ResultsPanel',
    'app',
    '__version__'
]
