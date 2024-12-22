"""
Strategy optimizer component.

This component provides:
1. Parameter optimization interface
2. Multiple optimization methods
3. Results visualization
4. Parameter analysis

Optimization methods:
- Grid Search
- Random Search
- Bayesian Optimization
- Genetic Algorithm
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import logging

from ...core.optimization import Optimizer, OptimizationResult
from ...strategy import StrategyBase
from .chart import Chart

logger = logging.getLogger(__name__)

class OptimizerPanel(ttk.Frame):
    """
    Parameter optimization panel.

    Features:
    - Visual parameter configuration
    - Multiple optimization methods
    - Progress tracking
    - Results visualization
    """

    def __init__(self, master):
        """Initialize optimizer panel."""
        super().__init__(master)

        # State
        self.strategy: Optional[StrategyBase] = None
        self.parameters: Dict[str, Dict] = {}
        self.running = False

        # Create widgets
        self._create_widgets()

    def _create_widgets(self):
        """Create optimizer interface."""
        # Main container
        paned = ttk.PanedWindow(self, orient='horizontal')
        paned.pack(fill='both', expand=True)

        # Left panel (configuration)
        left_frame = ttk.Frame(paned)
        paned.add(left_frame)

        self._create_config_section(left_frame)

        # Right panel (results)
        right_frame = ttk.Frame(paned)
        paned.add(right_frame)

        self._create_results_section(right_frame)

    def _create_config_section(self, parent):
        """Create optimization configuration section."""
        # Parameters frame
        param_frame = ttk.LabelFrame(parent, text="Parameters")
        param_frame.pack(fill='x', padx=5, pady=5)

        self.param_tree = ttk.Treeview(
            param_frame,
            columns=('name', 'range', 'steps'),
            show='headings',
            height=5
        )
        self.param_tree.pack(fill='x')

        self.param_tree.heading('name', text='Parameter')
        self.param_tree.heading('range', text='Range')
        self.param_tree.heading('steps', text='Steps')

        # Parameter controls
        ctrl_frame = ttk.Frame(param_frame)
        ctrl_frame.pack(fill='x', padx=5, pady=5)

        ttk.Button(
            ctrl_frame,
            text="Add",
            command=self._add_parameter
        ).pack(side='left', padx=2)

        ttk.Button(
            ctrl_frame,
            text="Edit",
            command=self._edit_parameter
        ).pack(side='left', padx=2)

        ttk.Button(
            ctrl_frame,
            text="Remove",
            command=self._remove_parameter
        ).pack(side='left', padx=2)

        # Optimization settings
        settings_frame = ttk.LabelFrame(parent, text="Settings")
        settings_frame.pack(fill='x', padx=5, pady=5)

        # Method selection
        method_frame = ttk.Frame(settings_frame)
        method_frame.pack(fill='x', padx=5, pady=2)

        ttk.Label(method_frame, text="Method:").pack(side='left')
        self.method_var = tk.StringVar(value='grid')
        method_combo = ttk.Combobox(
            method_frame,
            textvariable=self.method_var,
            values=['grid', 'random', 'bayesian', 'genetic'],
            state='readonly'
        )
        method_combo.pack(side='left', fill='x', expand=True, padx=5)

        # Metric selection
        metric_frame = ttk.Frame(settings_frame)
        metric_frame.pack(fill='x', padx=5, pady=2)

        ttk.Label(metric_frame, text="Metric:").pack(side='left')
        self.metric_var = tk.StringVar(value='sharpe_ratio')
        metric_combo = ttk.Combobox(
            metric_frame,
            textvariable=self.metric_var,
            values=['sharpe_ratio', 'returns', 'drawdown', 'win_rate'],
            state='readonly'
        )
        metric_combo.pack(side='left', fill='x', expand=True, padx=5)

        # Max evaluations
        eval_frame = ttk.Frame(settings_frame)
        eval_frame.pack(fill='x', padx=5, pady=2)

        ttk.Label(eval_frame, text="Max Evaluations:").pack(side='left')
        self.max_evals = tk.StringVar(value='100')
        ttk.Entry(
            eval_frame,
            textvariable=self.max_evals,
            width=10
        ).pack(side='left', padx=5)

        # Control buttons
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill='x', padx=5, pady=5)

        self.start_btn = ttk.Button(
            btn_frame,
            text="Start Optimization",
            command=self.start_optimization
        )
        self.start_btn.pack(side='left', padx=2)

        self.stop_btn = ttk.Button(
            btn_frame,
            text="Stop",
            command=self.stop_optimization,
            state='disabled'
        )
        self.stop_btn.pack(side='left', padx=2)

        # Progress bar
        self.progress = ttk.Progressbar(
            parent,
            mode='determinate',
            length=200
        )
        self.progress.pack(fill='x', padx=5, pady=5)

    def _create_results_section(self, parent):
        """Create results visualization section."""
        # Results notebook
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill='both', expand=True)

        # Summary tab
        summary_frame = ttk.Frame(self.notebook)
        self.notebook.add(summary_frame, text="Summary")

        self.summary_text = tk.Text(
            summary_frame,
            height=10,
            wrap='none'
        )
        self.summary_text.pack(fill='both', expand=True)

        # Parameter analysis tab
        param_frame = ttk.Frame(self.notebook)
        self.notebook.add(param_frame, text="Parameters")

        self.param_chart = Chart(param_frame)
        self.param_chart.pack(fill='both', expand=True)

        # Surface plot tab
        surface_frame = ttk.Frame(self.notebook)
        self.notebook.add(surface_frame, text="Surface")

        self.surface_chart = Chart(surface_frame)
        self.surface_chart.pack(fill='both', expand=True)

    def _add_parameter(self):
        """Add optimization parameter."""
        from ..dialogs.parameter import ParameterDialog
        dialog = ParameterDialog(self)

        if dialog.result:
            # Add to parameters
            name = dialog.result['name']
            self.parameters[name] = dialog.result

            # Update tree
            self.param_tree.insert('', 'end', values=(
                name,
                f"{dialog.result['min']} - {dialog.result['max']}",
                dialog.result['steps']
            ))

    def _edit_parameter(self):
        """Edit selected parameter."""
        selected = self.param_tree.selection()
        if not selected:
            return

        # Get parameter
        name = self.param_tree.item(selected[0])['values'][0]
        param = self.parameters[name]

        # Show dialog
        from ..dialogs.parameter import ParameterDialog
        dialog = ParameterDialog(self, param)

        if dialog.result:
            # Update parameter
            self.parameters[name] = dialog.result

            # Update tree
            self.param_tree.item(selected[0], values=(
                name,
                f"{dialog.result['min']} - {dialog.result['max']}",
                dialog.result['steps']
            ))

    def _remove_parameter(self):
        """Remove selected parameter."""
        selected = self.param_tree.selection()
        if not selected:
            return

        # Get parameter
        name = self.param_tree.item(selected[0])['values'][0]

        # Remove from parameters
        del self.parameters[name]

        # Remove from tree
        self.param_tree.delete(selected[0])

    def set_strategy(self, strategy: StrategyBase):
        """Set strategy for optimization."""
        self.strategy = strategy

        # Get strategy parameters
        params = strategy.get_parameters()

        # Clear current parameters
        self.parameters.clear()
        for item in self.param_tree.get_children():
            self.param_tree.delete(item)

        # Add strategy parameters
        for name, meta in params.items():
            if meta['type'] in ('int', 'float'):
                self.parameters[name] = {
                    'name': name,
                    'type': meta['type'],
                    'min': meta['range'][0],
                    'max': meta['range'][1],
                    'steps': 10
                }

                self.param_tree.insert('', 'end', values=(
                    name,
                    f"{meta['range'][0]} - {meta['range'][1]}",
                    10
                ))

    def start_optimization(self):
        """Start optimization process."""
        if not self.strategy:
            messagebox.showerror("Error", "No strategy selected")
            return

        if not self.parameters:
            messagebox.showerror("Error", "No parameters selected")
            return

        try:
            # Create parameter space
            param_space = self._create_param_space()

            # Create optimizer
            self.optimizer = Optimizer()

            # Start optimization
            self.running = True
            self.start_btn.config(state='disabled')
            self.stop_btn.config(state='normal')

            # Run in thread
            self.thread = ThreadPoolExecutor(max_workers=1)
            self.future = self.thread.submit(
                self.optimizer.optimize,
                self.strategy,
                param_space,
                self.metric_var.get(),
                method=self.method_var.get(),
                max_evals=int(self.max_evals.get())
            )

            # Monitor progress
            self.after(100, self._check_progress)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to start optimization: {str(e)}")

    def stop_optimization(self):
        """Stop optimization process."""
        self.running = False
        self.optimizer.stop()

    def _check_progress(self):
        """Check optimization progress."""
        if not self.running:
            return

        try:
            # Update progress
            progress = self.optimizer.get_progress()
            self.progress['value'] = progress * 100

            # Check if complete
            if self.future.done():
                self.running = False
                self.start_btn.config(state='normal')
                self.stop_btn.config(state='disabled')

                # Get results
                results = self.future.result()
                self._show_results(results)

            else:
                # Check again later
                self.after(100, self._check_progress)

        except Exception as e:
            logger.error(f"Error checking progress: {str(e)}")


    def _create_param_space(self) -> Dict[str, np.ndarray]:
        """
        Create parameter space for optimization.

        Returns:
            Dict mapping parameter names to arrays of values to test
        """
        param_space = {}

        for name, param in self.parameters.items():
            if param['type'] == 'int':
                values = np.linspace(
                    int(param['min']),
                    int(param['max']),
                    int(param['steps']),
                    dtype=int
                )
            else:  # float
                values = np.linspace(
                    float(param['min']),
                    float(param['max']),
                    int(param['steps'])
                )
            param_space[name] = values

        return param_space

    def _show_results(self, results: OptimizationResult):
        """
        Display optimization results.

        Args:
            results: Optimization results
        """
        # Show summary
        self._show_summary(results)

        # Show parameter analysis
        self._show_parameter_analysis(results)

        # Show surface plot if applicable
        if len(self.parameters) == 2:
            self._show_surface_plot(results)

        # Switch to summary tab
        self.notebook.select(0)

    def _show_summary(self, results: OptimizationResult):
        """Show optimization summary."""
        # Clear current text
        self.summary_text.delete('1.0', 'end')

        # Add summary
        summary = [
            "Optimization Results",
            "===================",
            "",
            f"Method: {self.method_var.get()}",
            f"Metric: {self.metric_var.get()}",
            f"Total Evaluations: {len(results.all_results)}",
            "",
            "Best Parameters:",
            "---------------"
        ]

        for name, value in results.best_params.items():
            summary.append(f"{name}: {value}")

        summary.extend([
            "",
            "Best Metrics:",
            "------------"
        ])

        for name, value in results.best_metrics.items():
            summary.append(f"{name}: {value:.4f}")

        summary.extend([
            "",
            "Parameter Importance:",
            "-------------------"
        ])

        for name, importance in results.param_importance.items():
            summary.append(f"{name}: {importance:.1f}%")

        self.summary_text.insert('1.0', "\n".join(summary))

    def _show_parameter_analysis(self, results: OptimizationResult):
        """Show parameter impact analysis."""
        # Create parameter analysis plots
        df = results.all_results

        # Clear current chart
        self.param_chart.clear()

        # Add subplot for each parameter
        for i, (name, param) in enumerate(self.parameters.items()):
            values = df[name]
            scores = df[self.metric_var.get()]

            # Create scatter plot
            self.param_chart.add_subplot(
                len(self.parameters),
                1,
                i+1,
                title=f"Impact of {name}"
            )

            self.param_chart.scatter(values, scores)
            self.param_chart.add_trend_line(values, scores)

        self.param_chart.tight_layout()

    def _show_surface_plot(self, results: OptimizationResult):
        """Show parameter surface plot."""
        # Can only show surface for two parameters
        if len(self.parameters) != 2:
            return

        # Get parameter names
        param1, param2 = self.parameters.keys()

        # Create grid
        df = results.all_results
        X = df[param1].values
        Y = df[param2].values
        Z = df[self.metric_var.get()].values

        # Clear current chart
        self.surface_chart.clear()

        # Create surface plot
        self.surface_chart.plot_surface(
            X, Y, Z,
            title=f"{self.metric_var.get()} Surface",
            xlabel=param1,
            ylabel=param2
        )

    def export_results(self, filename: str):
        """
        Export optimization results.

        Args:
            filename: Output file path
        """
        import json

        # Create export data
        data = {
            'parameters': self.parameters,
            'settings': {
                'method': self.method_var.get(),
                'metric': self.metric_var.get(),
                'max_evals': int(self.max_evals.get())
            },
            'results': {
                'best_params': self.optimizer.best_params,
                'best_metrics': self.optimizer.best_metrics,
                'param_importance': self.optimizer.param_importance
            }
        }

        # Save to file
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)

    def load_results(self, filename: str):
        """
        Load optimization results.

        Args:
            filename: Results file path
        """
        import json

        with open(filename, 'r') as f:
            data = json.load(f)

        # Update parameters
        self.parameters = data['parameters']
        self._update_parameter_tree()

        # Update settings
        self.method_var.set(data['settings']['method'])
        self.metric_var.set(data['settings']['metric'])
        self.max_evals.set(str(data['settings']['max_evals']))

        # Show results
        results = OptimizationResult(
            best_params=data['results']['best_params'],
            best_metrics=data['results']['best_metrics'],
            param_importance=data['results']['param_importance']
        )
        self._show_results(results)

    def _update_parameter_tree(self):
        """Update parameter tree from current parameters."""
        # Clear tree
        for item in self.param_tree.get_children():
            self.param_tree.delete(item)

        # Add parameters
        for name, param in self.parameters.items():
            self.param_tree.insert('', 'end', values=(
                name,
                f"{param['min']} - {param['max']}",
                param['steps']
            ))

    def reset(self):
        """Reset optimizer state."""
        # Clear parameters
        self.parameters.clear()
        self._update_parameter_tree()

        # Reset settings
        self.method_var.set('grid')
        self.metric_var.set('sharpe_ratio')
        self.max_evals.set('100')

        # Clear results
        self.summary_text.delete('1.0', 'end')
        self.param_chart.clear()
        self.surface_chart.clear()

        # Reset progress
        self.progress['value'] = 0

        # Reset buttons
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')

# Import for type hints
from ...core.optimization import Optimizer, OptimizationResult
from ...strategy import StrategyBase
