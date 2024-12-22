"""
Data management panel implementation.

This panel provides:
1. Data source selection and configuration
2. Data loading and preprocessing
3. Data visualization and exploration
4. Data validation and quality checks

The panel uses a modular design where each major function is a separate
component that can be tested and maintained independently.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, Optional, Any, List
import pandas as pd
import logging
from pathlib import Path

from ...core.data import MarketData
from ..components.chart import Chart

logger = logging.getLogger(__name__)

class DataPanel(ttk.Frame):
    """
    Data management panel.

    This panel allows users to:
    1. Load data from various sources
    2. Configure data preprocessing
    3. Visualize and explore data
    4. Validate data quality

    The panel is designed to be modular and extensible, making it
    easy to add support for new data sources and preprocessing steps.

    Attributes:
        data: Currently loaded market data
        chart: Data visualization component
        current_source: Active data source name
    """

    def __init__(self, master):
        """Initialize panel."""
        super().__init__(master)

        # State
        self.data: Optional[MarketData] = None
        self.current_source: Optional[str] = None
        self.timeframe = tk.StringVar(value='1d')
        self.modified = False

        # Create components
        self._create_widgets()
        self._create_layout()
        self._bind_events()

        logger.debug("Initialized DataPanel")

    def _create_widgets(self):
        """Create panel widgets.

        The panel has three main sections:
        1. Data source selection
        2. Data configuration
        3. Data preview
        """
        # Source selection
        self.source_frame = ttk.LabelFrame(self, text="Data Source")

        # Data sources
        sources = [
            ("CSV Files", self._load_csv),
            ("Yahoo Finance", self._load_yahoo),
            ("Interactive Brokers", self._load_ibkr),
            ("Alpha Vantage", self._load_alpha_vantage)
        ]

        self.source_buttons = []
        for name, command in sources:
            btn = ttk.Button(
                self.source_frame,
                text=name,
                command=command
            )
            self.source_buttons.append(btn)

        # Configuration
        self.config_frame = ttk.LabelFrame(self, text="Configuration")

        # Timeframe selection
        tf_frame = ttk.Frame(self.config_frame)
        ttk.Label(tf_frame, text="Timeframe:").pack(side='left')
        self.tf_combo = ttk.Combobox(
            tf_frame,
            textvariable=self.timeframe,
            values=['1m', '5m', '15m', '1h', '4h', '1d'],
            state='readonly'
        )
        self.tf_combo.pack(side='left', padx=5)

        # Date range
        date_frame = ttk.Frame(self.config_frame)
        ttk.Label(date_frame, text="Date Range:").pack(side='left')
        self.start_date = ttk.Entry(date_frame, width=10)
        self.start_date.pack(side='left', padx=5)
        ttk.Label(date_frame, text="to").pack(side='left')
        self.end_date = ttk.Entry(date_frame, width=10)
        self.end_date.pack(side='left', padx=5)

        # Preview
        self.preview_frame = ttk.LabelFrame(self, text="Preview")
        self.chart = Chart(self.preview_frame)

        # Status
        self.status_frame = ttk.Frame(self)
        self.status_var = tk.StringVar()
        ttk.Label(
            self.status_frame,
            textvariable=self.status_var
        ).pack(side='left')

    def _create_layout(self):
        """Create panel layout.

        The layout uses grid geometry manager for flexibility:
        - Source selection at top
        - Configuration below source
        - Preview taking remaining space
        - Status bar at bottom
        """
        # Source frame
        self.source_frame.grid(
            row=0, column=0,
            sticky='ew',
            padx=5, pady=5
        )
        for i, btn in enumerate(self.source_buttons):
            btn.pack(side='left', padx=2)

        # Config frame
        self.config_frame.grid(
            row=1, column=0,
            sticky='ew',
            padx=5, pady=5
        )
        for widget in self.config_frame.winfo_children():
            widget.pack(fill='x', padx=5, pady=2)

        # Preview frame
        self.preview_frame.grid(
            row=2, column=0,
            sticky='nsew',
            padx=5, pady=5
        )
        self.chart.pack(fill='both', expand=True)

        # Status frame
        self.status_frame.grid(
            row=3, column=0,
            sticky='ew',
            padx=5, pady=5
        )

        # Configure grid
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def _bind_events(self):
        """Bind event handlers."""
        self.timeframe.trace('w', self._on_timeframe_change)

    def _load_csv(self):
        """Load data from CSV file."""
        try:
            # Get filename
            filename = filedialog.askopenfilename(
                filetypes=[("CSV files", "*.csv")]
            )
            if not filename:
                return

            # Load data
            df = pd.read_csv(filename)

            # Convert to MarketData
            self.data = MarketData(df, Path(filename).stem)
            self.current_source = 'csv'

            # Update display
            self._update_preview()
            self.set_status(f"Loaded {filename}")
            self.modified = True

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to load CSV: {str(e)}"
            )

    def _load_yahoo(self):
        """Load data from Yahoo Finance."""
        try:
            # Show symbol dialog
            from ..dialogs.yahoo import YahooDialog
            dialog = YahooDialog(self)

            if dialog.result:
                symbol = dialog.result['symbol']
                start = dialog.result['start_date']
                end = dialog.result['end_date']

                # Load data
                import yfinance as yf
                ticker = yf.Ticker(symbol)
                df = ticker.history(
                    start=start,
                    end=end,
                    interval=self.timeframe.get()
                )

                # Convert to MarketData
                self.data = MarketData(df, symbol)
                self.current_source = 'yahoo'

                # Update display
                self._update_preview()
                self.set_status(f"Loaded {symbol} from Yahoo Finance")
                self.modified = True

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to load from Yahoo: {str(e)}"
            )

    def _load_ibkr(self):
        """Load data from Interactive Brokers."""
        messagebox.showinfo(
            "Not Implemented",
            "Interactive Brokers support coming soon!"
        )

    def _load_alpha_vantage(self):
        """Load data from Alpha Vantage."""
        messagebox.showinfo(
            "Not Implemented",
            "Alpha Vantage support coming soon!"
        )

    def _update_preview(self):
        """Update data preview."""
        if self.data is None:
            return

        # Update chart
        self.chart.set_data(self.data.to_df())

    def _on_timeframe_change(self, *args):
        """Handle timeframe change."""
        if self.data is None:
            return

        try:
            # Resample data
            timeframe = self.timeframe.get()
            self.data = self.data.resample(timeframe)

            # Update display
            self._update_preview()
            self.set_status(f"Resampled data to {timeframe}")
            self.modified = True

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to resample data: {str(e)}"
            )

    def set_status(self, message: str):
        """Set status message."""
        self.status_var.set(message)

    def get_data(self) -> Optional[MarketData]:
        """Get current market data."""
        return self.data

    def save_state(self) -> Dict[str, Any]:
        """Save panel state."""
        return {
            'timeframe': self.timeframe.get(),
            'start_date': self.start_date.get(),
            'end_date': self.end_date.get(),
            'source': self.current_source
        }

    def load_state(self, state: Dict[str, Any]):
        """Load panel state."""
        self.timeframe.set(state.get('timeframe', '1d'))
        self.start_date.insert(0, state.get('start_date', ''))
        self.end_date.insert(0, state.get('end_date', ''))
        self.current_source = state.get('source')

    def reset(self):
        """Reset panel state."""
        self.data = None
        self.current_source = None
        self.timeframe.set('1d')
        self.start_date.delete(0, 'end')
        self.end_date.delete(0, 'end')
        self.status_var.set('')
        self.modified = False
        self._update_preview()
