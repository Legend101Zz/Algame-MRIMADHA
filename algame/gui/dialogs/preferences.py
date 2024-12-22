import tkinter as tk
from tkinter import ttk
from typing import Dict, Optional, Any
import logging

from base import BaseDialog

logger = logging.getLogger(__name__)




class PreferencesDialog(BaseDialog):
    """
    Application preferences dialog.

    Configures:
    - Theme settings
    - Chart preferences
    - Data defaults
    - Directory locations
    """

    def __init__(self, parent):
        super().__init__(parent, title="Preferences")

    def _create_dialog_widgets(self, frame):
        """Create preferences widgets."""
        notebook = ttk.Notebook(frame)
        notebook.pack(fill='both', expand=True)

        # Appearance
        appearance = ttk.Frame(notebook)
        notebook.add(appearance, text="Appearance")
        self._create_appearance_tab(appearance)

        # Charts
        charts = ttk.Frame(notebook)
        notebook.add(charts, text="Charts")
        self._create_charts_tab(charts)

        # Data
        data = ttk.Frame(notebook)
        notebook.add(data, text="Data")
        self._create_data_tab(data)

    def _create_appearance_tab(self, frame):
        """Create appearance settings."""
        # Theme
        theme_frame = ttk.LabelFrame(frame, text="Theme")
        theme_frame.pack(fill='x', padx=5, pady=5)

        ttk.Label(theme_frame, text="Color Theme:").pack(side='left')
        self.theme_var = tk.StringVar(value='default')
        ttk.Combobox(
            theme_frame,
            textvariable=self.theme_var,
            values=['default', 'dark', 'light'],
            state='readonly'
        ).pack(side='left', padx=5)

        # Font
        font_frame = ttk.LabelFrame(frame, text="Font")
        font_frame.pack(fill='x', padx=5, pady=5)

        ttk.Label(font_frame, text="Family:").pack(side='left')
        self.font_var = tk.StringVar(value='Arial')
        ttk.Combobox(
            font_frame,
            textvariable=self.font_var,
            values=['Arial', 'Helvetica', 'Times'],
            state='readonly'
        ).pack(side='left', padx=5)

        ttk.Label(font_frame, text="Size:").pack(side='left', padx=5)
        self.font_size = tk.StringVar(value='10')
        ttk.Spinbox(
            font_frame,
            textvariable=self.font_size,
            from_=8,
            to=16,
            width=5
        ).pack(side='left')

    def _create_charts_tab(self, frame):
        """Create chart settings."""
        # Style
        style_frame = ttk.LabelFrame(frame, text="Chart Style")
        style_frame.pack(fill='x', padx=5, pady=5)

        ttk.Label(style_frame, text="Style:").pack(side='left')
        self.chart_style = tk.StringVar(value='candles')
        ttk.Combobox(
            style_frame,
            textvariable=self.chart_style,
            values=['candles', 'ohlc', 'line'],
            state='readonly'
        ).pack(side='left', padx=5)

        # Colors
        colors_frame = ttk.LabelFrame(frame, text="Colors")
        colors_frame.pack(fill='x', padx=5, pady=5)

        ttk.Label(colors_frame, text="Up:").pack(side='left')
        self.up_color = tk.StringVar(value='green')
        ttk.Entry(
            colors_frame,
            textvariable=self.up_color,
            width=10
        ).pack(side='left', padx=5)

        ttk.Label(colors_frame, text="Down:").pack(side='left', padx=5)
        self.down_color = tk.StringVar(value='red')
        ttk.Entry(
            colors_frame,
            textvariable=self.down_color,
            width=10
        ).pack(side='left')

    def _create_data_tab(self, frame):
        """Create data settings."""
        # Defaults
        defaults_frame = ttk
