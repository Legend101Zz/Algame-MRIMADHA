"""
PineScript converter panel implementation.

This panel provides:
1. PineScript code input/file loading
2. Conversion options
3. Preview of generated Python code
4. Validation feedback
5. Export options
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional
import logging
from pathlib import Path

from ...tools.converter import PineScriptConverter

logger = logging.getLogger(__name__)

class ConverterPanel(ttk.Frame):
    """
    PineScript converter panel.

    Features:
    - Code editor for PineScript input
    - File upload/download
    - Template selection
    - Live preview
    - Validation indicators
    """

    def __init__(self, master):
        super().__init__(master)

        # Initialize converter
        self.converter = PineScriptConverter()

        # State
        self.current_file: Optional[str] = None
        self.modified = False

        # Create UI
        self._create_widgets()
        self._create_layout()
        self._bind_events()

    def _create_widgets(self):
        """Create panel widgets."""
        # Toolbar
        self.toolbar = ttk.Frame(self)

        # File operations
        ttk.Button(
            self.toolbar,
            text="Open Pine",
            command=self._open_file
        ).pack(side='left', padx=2)

        ttk.Button(
            self.toolbar,
            text="Save Python",
            command=self._save_file
        ).pack(side='left', padx=2)

        # Template selection
        ttk.Label(
            self.toolbar,
            text="Template:"
        ).pack(side='left', padx=5)

        self.template_var = tk.StringVar()
        self.template_combo = ttk.Combobox(
            self.toolbar,
            textvariable=self.template_var,
            values=list(self.converter.templates.keys()),
            state='readonly',
            width=20
        )
        self.template_combo.pack(side='left', padx=2)

        # Convert button
        ttk.Button(
            self.toolbar,
            text="Convert",
            command=self._convert_code
        ).pack(side='right', padx=2)

        # Editor panes
        self.paned = ttk.PanedWindow(self, orient='horizontal')

        # Pine editor
        pine_frame = ttk.LabelFrame(self.paned, text="PineScript")
        self.pine_editor = tk.Text(
            pine_frame,
            wrap='none',
            font=('Courier', 10)
        )
        self.pine_editor.pack(fill='both', expand=True)

        # Python preview
        python_frame = ttk.LabelFrame(self.paned, text="Python")
        self.python_preview = tk.Text(
            python_frame,
            wrap='none',
            font=('Courier', 10),
            state='disabled'
        )
        self.python_preview.pack(fill='both', expand=True)

        # Add to paned window
        self.paned.add(pine_frame)
        self.paned.add(python_frame)

        # Status bar
        self.status = ttk.Label(self, text="Ready")

    def _create_layout(self):
        """Create panel layout."""
        # Toolbar at top
        self.toolbar.pack(fill='x', padx=5, pady=5)

        # Editor panes in middle
        self.paned.pack(fill='both', expand=True, padx=5, pady=5)

        # Status at bottom
        self.status.pack(fill='x', padx=5, pady=2)

    def _bind_events(self):
        """Bind event handlers."""
        # Text change events
        self.pine_editor.bind('<<Modified>>', self._on_text_change)

        # Template selection
        self.template_var.trace('w', self._on_template_change)

    def _open_file(self):
        """Open PineScript file."""
        if self.modified:
            if not messagebox.askyesno(
                "Unsaved Changes",
                "Discard current changes?"
            ):
                return

        filename = filedialog.askopenfilename(
            filetypes=[
                ("PineScript files", "*.pine"),
                ("All files", "*.*")
            ]
        )

        if filename:
            try:
                with open(filename, 'r') as f:
                    content = f.read()

                self.pine_editor.delete('1.0', 'end')
                self.pine_editor.insert('1.0', content)

                self.current_file = filename
                self.modified = False

                self.set_status(f"Opened {filename}")

            except Exception as e:
                messagebox.showerror(
                    "Error",
                    f"Failed to open file: {str(e)}"
                )

    def _save_file(self):
        """Save converted Python code."""
        if not self.python_preview.get('1.0', 'end').strip():
            messagebox.showwarning(
                "No Code",
                "No Python code to save."
            )
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".py",
            filetypes=[
                ("Python files", "*.py"),
                ("All files", "*.*")
            ]
        )

        if filename:
            try:
                code = self.python_preview.get('1.0', 'end')
                with open(filename, 'w') as f:
                    f.write(code)

                self.set_status(f"Saved to {filename}")

            except Exception as e:
                messagebox.showerror(
                    "Error",
                    f"Failed to save file: {str(e)}"
                )

    def _convert_code(self):
        """Convert current PineScript code."""
        pine_code = self.pine_editor.get('1.0', 'end')
        if not pine_code.strip():
            messagebox.showwarning(
                "No Code",
                "No PineScript code to convert."
            )
            return

        try:
            # Get template if selected
            template = None
            if self.template_var.get():
                template = self.template_var.get()

            # Convert code
            result = self.converter.convert(pine_code)

            if result.success:
                # Update preview
                self.python_preview['state'] = 'normal'
                self.python_preview.delete('1.0', 'end')
                self.python_preview.insert('1.0', result.python_code)
                self.python_preview['state'] = 'disabled'

                # Show warnings if any
                if result.warnings:
                    messagebox.showwarning(
                        "Conversion Warnings",
                        "\n".join(result.warnings)
                    )

                self.set_status("Conversion successful")

            else:
                messagebox.showerror(
                    "Conversion Failed",
                    "\n".join(result.warnings)
                )

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Conversion error: {str(e)}"
            )

    def _on_text_change(self, event):
        """Handle text changes."""
        self.modified = True

    def _on_template_change(self, *args):
        """Handle template selection."""
        template = self.template_var.get()
        if template:
            # Load template
            try:
                content = self.converter.get_template(template)

                # Show template in editor
                self.pine_editor.delete('1.0', 'end')
                self.pine_editor.insert('1.0', content)

                self.set_status(f"Loaded template: {template}")

            except Exception as e:
                messagebox.showerror(
                    "Error",
                    f"Failed to load template: {str(e)}"
                )

    def set_status(self, message: str):
        """Set status message."""
        self.status['text'] = message
