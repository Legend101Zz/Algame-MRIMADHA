"""Parameter editing dialog for optimizer."""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Optional, Any

class ParameterDialog(tk.Toplevel):
    """
    Dialog for editing optimization parameters.

    Features:
    - Parameter range selection
    - Type validation
    - Step size configuration
    - Value validation
    """

    def __init__(self, parent, parameter: Optional[Dict[str, Any]] = None):
        """
        Initialize dialog.

        Args:
            parent: Parent window
            parameter: Optional existing parameter to edit
        """
        super().__init__(parent)
        self.title("Edit Parameter")

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Store parameter
        self.parameter = parameter
        self.result = None

        # Create widgets
        self._create_widgets()

        # Center dialog
        self.geometry('300x250')
        self.resizable(False, False)
        self.center_window()

        # Initialize values
        if parameter:
            self._set_values(parameter)

        # Wait for window
        self.wait_window()

    def _create_widgets(self):
        """Create dialog widgets."""
        # Main frame
        main = ttk.Frame(self, padding="5 5 5 5")
        main.pack(fill='both', expand=True)

        # Name
        name_frame = ttk.Frame(main)
        name_frame.pack(fill='x', pady=5)

        ttk.Label(name_frame, text="Name:").pack(side='left')
        self.name_var = tk.StringVar()
        ttk.Entry(
            name_frame,
            textvariable=self.name_var
        ).pack(side='left', fill='x', expand=True, padx=5)

        # Type
        type_frame = ttk.Frame(main)
        type_frame.pack(fill='x', pady=5)

        ttk.Label(type_frame, text="Type:").pack(side='left')
        self.type_var = tk.StringVar(value='float')
        type_combo = ttk.Combobox(
            type_frame,
            textvariable=self.type_var,
            values=['int', 'float'],
            state='readonly'
        )
        type_combo.pack(side='left', fill='x', expand=True, padx=5)

        # Range
        range_frame = ttk.LabelFrame(main, text="Range")
        range_frame.pack(fill='x', pady=5)

        # Minimum
        min_frame = ttk.Frame(range_frame)
        min_frame.pack(fill='x', pady=2)

        ttk.Label(min_frame, text="Min:").pack(side='left')
        self.min_var = tk.StringVar()
        ttk.Entry(
            min_frame,
            textvariable=self.min_var
        ).pack(side='left', fill='x', expand=True, padx=5)

        # Maximum
        max_frame = ttk.Frame(range_frame)
        max_frame.pack(fill='x', pady=2)

        ttk.Label(max_frame, text="Max:").pack(side='left')
        self.max_var = tk.StringVar()
        ttk.Entry(
            max_frame,
            textvariable=self.max_var
        ).pack(side='left', fill='x', expand=True, padx=5)

        # Steps
        steps_frame = ttk.Frame(main)
        steps_frame.pack(fill='x', pady=5)

        ttk.Label(steps_frame, text="Steps:").pack(side='left')
        self.steps_var = tk.StringVar(value='10')
        ttk.Entry(
            steps_frame,
            textvariable=self.steps_var
        ).pack(side='left', fill='x', expand=True, padx=5)

        # Buttons
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
            command=self.destroy
        ).pack(side='right')

    def _set_values(self, parameter: Dict[str, Any]):
        """Set dialog values from parameter."""
        self.name_var.set(parameter['name'])
        self.type_var.set(parameter['type'])
        self.min_var.set(str(parameter['min']))
        self.max_var.set(str(parameter['max']))
        self.steps_var.set(str(parameter['steps']))

    def _validate(self) -> bool:
        """Validate parameter values."""
        # Check name
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Error", "Name is required")
            return False

        # Validate range
        try:
            if self.type_var.get() == 'int':
                min_val = int(self.min_var.get())
                max_val = int(self.max_var.get())
            else:
                min_val = float(self.min_var.get())
                max_val = float(self.max_var.get())

            if max_val <= min_val:
                messagebox.showerror("Error", "Maximum must be greater than minimum")
                return False

        except ValueError:
            messagebox.showerror("Error", "Invalid range values")
            return False

        # Validate steps
        try:
            steps = int(self.steps_var.get())
            if steps < 2:
                messagebox.showerror("Error", "Steps must be at least 2")
                return False

        except ValueError:
            messagebox.showerror("Error", "Invalid steps value")
            return False

        return True

    def _on_ok(self):
        """Handle OK button."""
        if not self._validate():
            return

        # Create result
        self.result = {
            'name': self.name_var.get().strip(),
            'type': self.type_var.get(),
            'min': self.min_var.get(),
            'max': self.max_var.get(),
            'steps': int(self.steps_var.get())
        }

        self.destroy()

    def center_window(self):
        """Center dialog on parent window."""
        parent = self.master

        # Get geometry
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        width = self.winfo_width()
        height = self.winfo_height()

        # Calculate position
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2

        # Set position
        self.geometry(f'+{x}+{y}')
