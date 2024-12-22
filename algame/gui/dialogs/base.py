"""
Dialog implementations for Algame GUI.

This module provides modal dialogs for:
1. Parameter configuration
2. Data source settings
3. Application preferences
4. About information

All dialogs follow consistent patterns:
- Modal interaction
- Validation before closing
- State persistence
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

class BaseDialog(tk.Toplevel):
    """
    Base class for modal dialogs.

    Provides common functionality:
    1. Modal behavior
    2. Window positioning
    3. Basic layout
    4. Result handling
    """

    def __init__(self, parent, title="Dialog"):
        """Initialize dialog."""
        super().__init__(parent)
        self.title(title)

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Initialize result
        self.result = None

        # Create widgets
        self._create_widgets()

        # Position window
        self.center_window()

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Wait for window
        self.wait_window()

    def _create_widgets(self):
        """Create dialog widgets."""
        # Main frame
        main = ttk.Frame(self, padding="5 5 5 5")
        main.pack(fill='both', expand=True)

        # Create custom widgets
        self._create_dialog_widgets(main)

        # Button frame
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill='x', pady=10)

        ttk.Button(
            btn_frame,
            text="OK",
            command=self._on_ok
        ).pack(side='right', padx=5)

        ttk.Button(
            btn_frame,
            text="Cancel",
            command=self._on_close
        ).pack(side='right')

    def _create_dialog_widgets(self, frame):
        """Create dialog-specific widgets."""
        raise NotImplementedError("Subclasses must implement this")

    def center_window(self):
        """Center dialog on parent window."""
        self.update_idletasks()
        parent = self.master

        # Get geometries
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        width = self.winfo_width()
        height = self.winfo_height()

        # Calculate position
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2

        self.geometry(f'+{x}+{y}')

    def _validate(self) -> bool:
        """Validate dialog inputs."""
        return True

    def _on_ok(self):
        """Handle OK button."""
        if not self._validate():
            return
        self.destroy()

    def _on_close(self):
        """Handle dialog close."""
        self.result = None
        self.destroy()


class ParameterDialog(BaseDialog):
    """
    Parameter configuration dialog.

    Allows editing of:
    - Parameter name
    - Parameter type
    - Default value
    - Valid range
    - Description
    """

    def __init__(self, parent, parameter: Optional[Dict[str, Any]] = None):
        """Initialize dialog."""
        self.parameter = parameter
        super().__init__(parent, title="Edit Parameter")

    def _create_dialog_widgets(self, frame):
        """Create parameter editing widgets."""
        # Name
        name_frame = ttk.Frame(frame)
        name_frame.pack(fill='x', pady=5)

        ttk.Label(name_frame, text="Name:").pack(side='left')
        self.name_var = tk.StringVar()
        ttk.Entry(
            name_frame,
            textvariable=self.name_var
        ).pack(side='left', fill='x', expand=True, padx=5)

        # Type
        type_frame = ttk.Frame(frame)
        type_frame.pack(fill='x', pady=5)

        ttk.Label(type_frame, text="Type:").pack(side='left')
        self.type_var = tk.StringVar(value='float')
        ttk.Combobox(
            type_frame,
            textvariable=self.type_var,
            values=['int', 'float', 'bool', 'str'],
            state='readonly'
        ).pack(side='left', fill='x', expand=True, padx=5)

        # Default value
        default_frame = ttk.Frame(frame)
        default_frame.pack(fill='x', pady=5)

        ttk.Label(default_frame, text="Default:").pack(side='left')
        self.default_var = tk.StringVar()
        ttk.Entry(
            default_frame,
            textvariable=self.default_var
        ).pack(side='left', fill='x', expand=True, padx=5)

        # Range
        range_frame = ttk.LabelFrame(frame, text="Valid Range")
        range_frame.pack(fill='x', pady=5)

        min_frame = ttk.Frame(range_frame)
        min_frame.pack(fill='x', pady=2)
        ttk.Label(min_frame, text="Min:").pack(side='left')
        self.min_var = tk.StringVar()
        ttk.Entry(
            min_frame,
            textvariable=self.min_var
        ).pack(side='left', fill='x', expand=True, padx=5)

        max_frame = ttk.Frame(range_frame)
        max_frame.pack(fill='x', pady=2)
        ttk.Label(max_frame, text="Max:").pack(side='left')
        self.max_var = tk.StringVar()
        ttk.Entry(
            max_frame,
            textvariable=self.max_var
        ).pack(side='left', fill='x', expand=True, padx=5)

        # Description
        desc_frame = ttk.LabelFrame(frame, text="Description")
        desc_frame.pack(fill='x', pady=5)
        self.desc_text = tk.Text(desc_frame, height=3, width=40)
        self.desc_text.pack(fill='x', padx=5, pady=5)

        # Set initial values if editing
        if self.parameter:
            self._set_values(self.parameter)

    def _set_values(self, parameter: Dict[str, Any]):
        """Set dialog values from parameter."""
        self.name_var.set(parameter.get('name', ''))
        self.type_var.set(parameter.get('type', 'float'))
        self.default_var.set(str(parameter.get('default', '')))
        self.min_var.set(str(parameter.get('min', '')))
        self.max_var.set(str(parameter.get('max', '')))
        self.desc_text.insert('1.0', parameter.get('description', ''))

    def _validate(self) -> bool:
        """Validate parameter values."""
        # Check name
        name = self.name_var.get().strip()
        if not name:
            tk.messagebox.showerror("Error", "Name is required")
            return False

        # Check type specific values
        param_type = self.type_var.get()
        try:
            if param_type == 'int':
                int(self.default_var.get())
                int(self.min_var.get())
                int(self.max_var.get())
            elif param_type == 'float':
                float(self.default_var.get())
                float(self.min_var.get())
                float(self.max_var.get())
            elif param_type == 'bool':
                bool(self.default_var.get())

        except ValueError:
            tk.messagebox.showerror(
                "Error",
                "Invalid values for parameter type"
            )
            return False

        # Create result
        self.result = {
            'name': name,
            'type': param_type,
            'default': self.default_var.get(),
            'min': self.min_var.get(),
            'max': self.max_var.get(),
            'description': self.desc_text.get('1.0', 'end-1c')
        }

        return True


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
