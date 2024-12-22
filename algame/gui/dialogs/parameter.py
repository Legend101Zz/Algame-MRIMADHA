"""Parameter editing dialog for optimizer."""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Optional, Any

from base import BaseDialog

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
