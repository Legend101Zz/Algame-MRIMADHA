"""
Main window implementation for Algame GUI.

This module provides the main application window that:
1. Manages overall layout and navigation
2. Coordinates between panels
3. Handles global events
4. Manages application state

The window uses a notebook layout with tabs for:
- Data Management
- Strategy Development
- Backtesting
- Results Analysis
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Optional
import logging
from pathlib import Path

from .panels.data import DataPanel
from .panels.strategy import StrategyPanel
from .panels.results import ResultsPanel
from .components.chart import Chart

logger = logging.getLogger(__name__)

class MainWindow:
    """
    Main application window.

    This class provides:
    1. Application layout management
    2. Panel coordination
    3. Global event handling
    4. State management

    The window uses a notebook (tabbed) interface with:
    - Each major function in its own tab
    - Shared components accessible globally
    - State synchronized between panels

    Attributes:
        root: Root tkinter window
        config: Window configuration
        panels: Dictionary of active panels
        current_panel: Currently active panel
    """

    def __init__(self, root: tk.Tk, config: Dict[str, Any]):
        """
        Initialize main window.

        Args:
            root: Root tkinter window
            config: Window configuration
        """
        self.root = root
        self.config = config

        # Initialize state
        self.panels = {}
        self.current_panel = None
        self.modified = False

        # Setup window
        self._setup_window()
        self._create_menu()
        self._create_toolbar()
        self._create_statusbar()
        self._create_panels()

        # Bind events
        self._bind_events()

        logger.info("Initialized main window")

    def _setup_window(self):
        """Setup main window properties."""
        # Configure grid
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Set window icon
        # TODO: Add window icon

        # Set window state handlers
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_menu(self):
        """Create main menu bar."""
        self.menu = tk.Menu(self.root)
        self.root.config(menu=self.menu)

        # File menu
        file_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Project", command=self._new_project)
        file_menu.add_command(label="Open Project...", command=self._open_project)
        file_menu.add_command(label="Save Project", command=self._save_project)
        file_menu.add_separator()
        file_menu.add_command(label="Export Results...", command=self._export_results)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_close)

        # Edit menu
        edit_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Preferences...", command=self._show_preferences)

        # View menu
        view_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Data Panel", command=lambda: self._show_panel('data'))
        view_menu.add_command(label="Strategy Panel", command=lambda: self._show_panel('strategy'))
        view_menu.add_command(label="Results Panel", command=lambda: self._show_panel('results'))

        # Tools menu
        tools_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Strategy Optimizer...", command=self._show_optimizer)
        tools_menu.add_command(label="Data Browser...", command=self._show_data_browser)

        # Help menu
        help_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self._show_docs)
        help_menu.add_command(label="About", command=self._show_about)

    def _create_toolbar(self):
        """Create main toolbar."""
        self.toolbar = ttk.Frame(self.root)
        self.toolbar.grid(row=0, column=0, sticky='ew', padx=5, pady=2)

        # Create toolbar buttons
        ttk.Button(
            self.toolbar,
            text="New",
            command=self._new_project
        ).pack(side='left', padx=2)

        ttk.Button(
            self.toolbar,
            text="Open",
            command=self._open_project
        ).pack(side='left', padx=2)

        ttk.Button(
            self.toolbar,
            text="Save",
            command=self._save_project
        ).pack(side='left', padx=2)

        ttk.Separator(self.toolbar, orient='vertical').pack(side='left', padx=5, fill='y')

        ttk.Button(
            self.toolbar,
            text="Run",
            command=self._run_backtest
        ).pack(side='left', padx=2)

        ttk.Button(
            self.toolbar,
            text="Stop",
            command=self._stop_backtest
        ).pack(side='left', padx=2)

        ttk.Separator(self.toolbar, orient='vertical').pack(side='left', padx=5, fill='y')

        ttk.Button(
            self.toolbar,
            text="Results",
            command=lambda: self._show_panel('results')
        ).pack(side='left', padx=2)

    def _create_statusbar(self):
        """Create status bar."""
        self.statusbar = ttk.Frame(self.root)
        self.statusbar.grid(row=2, column=0, sticky='ew')

        # Status message
        self.status_var = tk.StringVar()
        ttk.Label(
            self.statusbar,
            textvariable=self.status_var
        ).pack(side='left', padx=5)

        # Progress bar
        self.progress = ttk.Progressbar(
            self.statusbar,
            mode='determinate',
            length=200
        )
        self.progress.pack(side='right', padx=5)

    def _create_panels(self):
        """Create main panels."""
        # Create notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)

        # Create panels
        self.panels['data'] = DataPanel(self.notebook)
        self.notebook.add(self.panels['data'], text='Data')

        self.panels['strategy'] = StrategyPanel(self.notebook)
        self.notebook.add(self.panels['strategy'], text='Strategy')

        self.panels['results'] = ResultsPanel(self.notebook)
        self.notebook.add(self.panels['results'], text='Results')

    def _bind_events(self):
        """Bind event handlers."""
        # Panel change events
        self.notebook.bind('<<NotebookTabChanged>>', self._on_panel_change)

        # Window state events
        self.root.bind('<Control-s>', lambda e: self._save_project())
        self.root.bind('<Control-o>', lambda e: self._open_project())
        self.root.bind('<Control-n>', lambda e: self._new_project())

    def _on_panel_change(self, event):
        """Handle panel change events."""
        # Get new panel
        tab_id = self.notebook.select()
        panel_name = self.notebook.tab(tab_id, 'text').lower()

        # Update current panel
        self.current_panel = self.panels.get(panel_name)
        if self.current_panel:
            self.current_panel.on_activate()

        logger.debug(f"Switched to panel: {panel_name}")

    def _show_panel(self, name: str):
        """Show specified panel."""
        if name in self.panels:
            tab_id = self.notebook.tabs().index(str(self.panels[name]))
            self.notebook.select(tab_id)

    def set_status(self, message: str):
        """Set status bar message."""
        self.status_var.set(message)

    def _new_project(self):
        """Create new project."""
        if self.modified:
            if not messagebox.askyesno(
                "Unsaved Changes",
                "Discard current changes?"
            ):
                return

        # Reset panels
        for panel in self.panels.values():
            panel.reset()

        self.modified = False
        self.set_status("New project created")

    def _open_project(self):
        """Open existing project."""
        if self.modified:
            if not messagebox.askyesno(
                "Unsaved Changes",
                "Discard current changes?"
            ):
                return

        from tkinter import filedialog
        filename = filedialog.askopenfilename(
            filetypes=[("Algame projects", "*.alg")]
        )

        if filename:
            try:
                self._load_project(filename)
                self.set_status(f"Opened project: {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open project: {e}")

    def _save_project(self):
        """Save current project."""
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".alg",
            filetypes=[("Algame projects", "*.alg")]
        )

        if filename:
            try:
                self._save_project_file(filename)
                self.modified = False
                self.set_status(f"Saved project: {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save project: {e}")

    def _load_project(self, filename: str):
        """
        Load project from file.

        Args:
            filename: Project file path

        Raises:
            ValueError: If file format is invalid
        """
        import json

        try:
            with open(filename, 'r') as f:
                data = json.load(f)

            # Validate format
            if 'version' not in data:
                raise ValueError("Invalid project file")

            # Load into panels
            for panel in self.panels.values():
                panel.load_state(data.get(panel.name, {}))

            self.set_status(f"Loaded project: {filename}")

        except Exception as e:
            logger.error(f"Failed to load project: {str(e)}")
            raise

    def _save_project_file(self, filename: str):
        """
        Save project to file.

        Args:
            filename: Output file path
        """
        import json

        # Collect panel states
        data = {
            'version': '1.0.0',
            'created_at': str(dt.datetime.now()),
            'config': self.config
        }

        # Add panel states
        for name, panel in self.panels.items():
            data[name] = panel.save_state()

        # Save to file
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)

    def _run_backtest(self):
        """Run backtest with current configuration."""
        try:
            # Get strategy from strategy panel
            strategy = self.panels['strategy'].get_strategy()

            # Get data from data panel
            data = self.panels['data'].get_data()

            # Run backtest
            from algame.core import Backtester
            bt = Backtester()
            results = bt.run(strategy, data)

            # Update results panel
            self.panels['results'].show_results(results)

            # Switch to results panel
            self._show_panel('results')

        except Exception as e:
            messagebox.showerror("Error", f"Backtest failed: {str(e)}")

    def _stop_backtest(self):
        """Stop running backtest."""
        # TODO: Implement backtest stopping
        pass

    def _export_results(self):
        """Export backtest results."""
        if 'results' not in self.panels:
            messagebox.showwarning(
                "No Results",
                "No results available to export"
            )
            return

        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            filetypes=[
                ("Excel files", "*.xlsx"),
                ("CSV files", "*.csv"),
                ("HTML report", "*.html")
            ]
        )

        if filename:
            try:
                self.panels['results'].export_results(filename)
                self.set_status(f"Exported results to: {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export results: {e}")

    def _show_preferences(self):
        """Show preferences dialog."""
        from .dialogs.preferences import PreferencesDialog
        PreferencesDialog(self.root, self.config)

    def _show_optimizer(self):
        """Show strategy optimizer."""
        if 'strategy' not in self.panels:
            messagebox.showwarning(
                "No Strategy",
                "Create a strategy before optimization"
            )
            return

        from .dialogs.optimizer import OptimizerDialog
        OptimizerDialog(
            self.root,
            self.panels['strategy'].get_strategy()
        )

    def _show_data_browser(self):
        """Show data browser dialog."""
        from .dialogs.browser import DataBrowserDialog
        DataBrowserDialog(self.root)

    def _show_docs(self):
        """Show documentation."""
        import webbrowser
        webbrowser.open("https://algame.readthedocs.io")

    def _show_about(self):
        """Show about dialog."""
        from .dialogs.about import AboutDialog
        AboutDialog(self.root)

    def _on_close(self):
        """Handle window close."""
        if self.modified:
            if not messagebox.askyesno(
                "Unsaved Changes",
                "Exit without saving changes?"
            ):
                return

        self.root.quit()

    def update_status(self, message: str, progress: Optional[float] = None):
        """
        Update status bar.

        Args:
            message: Status message
            progress: Optional progress (0-100)
        """
        self.status_var.set(message)

        if progress is not None:
            self.progress['value'] = progress
