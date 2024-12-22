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
