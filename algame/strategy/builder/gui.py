# algame/strategy/builder/gui.py

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Optional, List
import logging
import json
from pathlib import Path

from ..base import StrategyBase
from ..indicators import list_indicators, get_indicator
from .base import BuilderComponent, ComponentRegistry
from .strategy import StrategyBuilder

logger = logging.getLogger(__name__)

class StrategyEditor(ttk.Frame):
    """
    GUI editor for building trading strategies.

    This class provides a complete GUI for:
    1. Strategy template selection
    2. Parameter configuration
    3. Indicator selection and setup
    4. Rule creation and editing
    5. Strategy testing and validation

    The editor uses a component-based approach where:
    - Each strategy part is a separate panel
    - Changes are validated in real-time
    - Live preview is available
    - Code is generated automatically
    """

    def __init__(self, master):
        """Initialize editor."""
        super().__init__(master)

        # Initialize builder
        self.builder = StrategyBuilder()

        # Strategy metadata
        self.strategy_name = tk.StringVar(value="MyStrategy")
        self.strategy_desc = tk.StringVar()

        # Component tracking
        self.current_component: Optional[str] = None
        self.modified = False

        # Create and layout widgets
        self._create_widgets()
        self._layout_widgets()

        # Bind events
        self._bind_events()

        logger.debug("Initialized Strategy Editor")

    def _create_widgets(self):
        """Create editor widgets."""
        # Create main notebook for tabs
        self.notebook = ttk.Notebook(self)

        # Create panels
        self._create_metadata_panel()
        self._create_template_panel()
        self._create_parameter_panel()
        self._create_indicator_panel()
        self._create_rule_panel()
        self._create_preview_panel()

        # Create toolbar
        self._create_toolbar()

    def _create_metadata_panel(self):
        """Create strategy metadata panel."""
        self.metadata_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.metadata_frame, text="Metadata")

        # Strategy name
        name_frame = ttk.LabelFrame(self.metadata_frame, text="Strategy Name")
        name_frame.pack(fill='x', padx=5, pady=5)

        ttk.Entry(
            name_frame,
            textvariable=self.strategy_name
        ).pack(fill='x', padx=5, pady=5)

        # Strategy description
        desc_frame = ttk.LabelFrame(self.metadata_frame, text="Description")
        desc_frame.pack(fill='x', padx=5, pady=5)

        ttk.Entry(
            desc_frame,
            textvariable=self.strategy_desc
        ).pack(fill='x', padx=5, pady=5)

    def _create_template_panel(self):
        """Create template selection panel."""
        self.template_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.template_frame, text="Template")

        # Template selection
        template_frame = ttk.LabelFrame(self.template_frame, text="Select Template")
        template_frame.pack(fill='x', padx=5, pady=5)

        self.template_var = tk.StringVar()
        templates = [
            "Empty Strategy",
            "Trend Following",
            "Mean Reversion",
            "Breakout",
            "Pattern Trading"
        ]

        for template in templates:
            ttk.Radiobutton(
                template_frame,
                text=template,
                value=template,
                variable=self.template_var
            ).pack(anchor='w', padx=5, pady=2)

        # Template description
        desc_frame = ttk.LabelFrame(self.template_frame, text="Description")
        desc_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.template_desc = tk.Text(desc_frame, height=10, wrap='word')
        self.template_desc.pack(fill='both', expand=True, padx=5, pady=5)

    def _create_parameter_panel(self):
        """Create parameter configuration panel."""
        self.param_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.param_frame, text="Parameters")

        # Parameter list
        list_frame = ttk.Frame(self.param_frame)
        list_frame.pack(side='left', fill='y', padx=5, pady=5)

        self.param_list = ttk.Treeview(
            list_frame,
            columns=('Value', 'Type'),
            show='headings',
            height=10
        )

        self.param_list.heading('Value', text='Value')
        self.param_list.heading('Type', text='Type')
        self.param_list.pack(fill='y')

        # Parameter editor
        editor_frame = ttk.LabelFrame(self.param_frame, text="Edit Parameter")
        editor_frame.pack(side='left', fill='both', expand=True, padx=5, pady=5)

        # Name
        name_frame = ttk.Frame(editor_frame)
        name_frame.pack(fill='x', padx=5, pady=5)

        ttk.Label(name_frame, text="Name:").pack(side='left')
        self.param_name = ttk.Entry(name_frame)
        self.param_name.pack(side='left', fill='x', expand=True, padx=5)

        # Type
        type_frame = ttk.Frame(editor_frame)
        type_frame.pack(fill='x', padx=5, pady=5)

        ttk.Label(type_frame, text="Type:").pack(side='left')
        self.param_type = ttk.Combobox(
            type_frame,
            values=['int', 'float', 'bool', 'str'],
            state='readonly'
        )
        self.param_type.pack(side='left', fill='x', expand=True, padx=5)

        # Default value
        default_frame = ttk.Frame(editor_frame)
        default_frame.pack(fill='x', padx=5, pady=5)

        ttk.Label(default_frame, text="Default:").pack(side='left')
        self.param_default = ttk.Entry(default_frame)
        self.param_default.pack(side='left', fill='x', expand=True, padx=5)

        # Range (for numeric types)
        range_frame = ttk.Frame(editor_frame)
        range_frame.pack(fill='x', padx=5, pady=5)

        ttk.Label(range_frame, text="Range:").pack(side='left')
        self.param_min = ttk.Entry(range_frame, width=10)
        self.param_min.pack(side='left', padx=5)
        ttk.Label(range_frame, text="to").pack(side='left')
        self.param_max = ttk.Entry(range_frame, width=10)
        self.param_max.pack(side='left', padx=5)

        # Buttons
        btn_frame = ttk.Frame(editor_frame)
        btn_frame.pack(fill='x', padx=5, pady=5)

        ttk.Button(
            btn_frame,
            text="Add/Update",
            command=self._update_parameter
        ).pack(side='left', padx=5)

        ttk.Button(
            btn_frame,
            text="Delete",
            command=self._delete_parameter
        ).pack(side='left', padx=5)

    def _create_indicator_panel(self):
        """Create indicator selection panel."""
        self.indicator_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.indicator_frame, text="Indicators")

        # Category selection
        cat_frame = ttk.LabelFrame(self.indicator_frame, text="Categories")
        cat_frame.pack(side='left', fill='y', padx=5, pady=5)

        indicators = list_indicators()
        categories = set(ind.category for ind in indicators.values())

        self.category_var = tk.StringVar()
        for category in sorted(categories):
            ttk.Radiobutton(
                cat_frame,
                text=category,
                value=category,
                variable=self.category_var,
                command=self._update_indicator_list
            ).pack(anchor='w', padx=5, pady=2)

        # Indicator list
        list_frame = ttk.LabelFrame(self.indicator_frame, text="Indicators")
        list_frame.pack(side='left', fill='both', expand=True, padx=5, pady=5)

        self.indicator_list = ttk.Treeview(
            list_frame,
            columns=('Name', 'Description'),
            show='headings',
            height=10
        )

        self.indicator_list.heading('Name', text='Name')
        self.indicator_list.heading('Description', text='Description')
        self.indicator_list.pack(fill='both', expand=True)

        # Configuration editor
        config_frame = ttk.LabelFrame(self.indicator_frame, text="Configuration")
        config_frame.pack(side='right', fill='y', padx=5, pady=5)

        self.indicator_config = {}
        self._create_indicator_config(config_frame)

    def _create_rule_panel(self):
        """Create trading rule panel."""
        self.rule_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.rule_frame, text="Rules")

        # Rule list
        list_frame = ttk.LabelFrame(self.rule_frame, text="Rules")
        list_frame.pack(fill='x', padx=5, pady=5)

        self.rule_list = ttk.Treeview(
            list_frame,
            columns=('Type', 'Condition'),
            show='headings',
            height=5
        )

        self.rule_list.heading('Type', text='Type')
        self.rule_list.heading('Condition', text='Condition')
        self.rule_list.pack(fill='x')

        # Rule editor
        editor_frame = ttk.LabelFrame(self.rule_frame, text="Edit Rule")
        editor_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Rule type
        type_frame = ttk.Frame(editor_frame)
        type_frame.pack(fill='x', padx=5, pady=5)

        ttk.Label(type_frame, text="Type:").pack(side='left')
        self.rule_type = ttk.Combobox(
            type_frame,
            values=['Entry', 'Exit'],
            state='readonly'
        )
        self.rule_type.pack(side='left', fill='x', expand=True, padx=5)

        # Rule condition
        cond_frame = ttk.Frame(editor_frame)
        cond_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.condition = tk.Text(cond_frame, height=5)
        self.condition.pack(fill='both', expand=True)

        # Buttons
        btn_frame = ttk.Frame(editor_frame)
        btn_frame.pack(fill='x', padx=5, pady=5)

        ttk.Button(
            btn_frame,
            text="Add Rule",
            command=self._add_rule
        ).pack(side='left', padx=5)

        ttk.Button(
            btn_frame,
            text="Delete Rule",
            command=self._delete_rule
        ).pack(side='left', padx=5)

    def _create_preview_panel(self):
        """Create code preview panel."""
        self.preview_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.preview_frame, text="Preview")

        # Code preview
        self.code_preview = tk.Text(
            self.preview_frame,
            wrap='none',
            height=20
        )
        self.code_preview.pack(fill='both', expand=True, padx=5, pady=5)

    def _create_toolbar(self):
        """Create toolbar with actions."""
        toolbar = ttk.Frame(self)
        toolbar.pack(fill='x', padx=5, pady=5)

        # File operations
        ttk.Button(
            toolbar,
            text="New",
            command=self._new_strategy
        ).pack(side='left', padx=2)

        ttk.Button(
            toolbar,
            text="Load",
            command=self._load_strategy
        ).pack(side='left', padx=2)

        ttk.Button(
            toolbar,
            text="Save",
            command=self._save_strategy
        ).pack(side='left', padx=2)

        # Build operations
        ttk.Button(
            toolbar,
            text="Generate",
            command=self._generate_strategy
        ).pack(side='right', padx=2)

        ttk.Button(
            toolbar,
            text="Test",
            command=self._test_strategy
        ).pack(side='right', padx=2)

    def _bind_events(self):
        """Bind event handlers."""
        # Template selection
        self.template_var.trace('w', self._on_template_change)

        # Parameter events
        self.param_list.bind('<<TreeviewSelect>>', self._on_param_select)
        self.param_type.bind('<<ComboboxSelected>>', self._on_param_type_change)

        # Indicator events
        self.indicator_list.bind('<<TreeviewSelect>>', self._on_indicator_select)

        # Rule events
        self.rule_list.bind('<<TreeviewSelect>>', self._on_rule_select)

        # Preview update
        self.notebook.bind('<<NotebookTabChanged>>', self._update_preview)

    def _update_parameter(self):
        """Add or update parameter."""
        name = self.param_name.get()
        if not name:
            messagebox.showerror("Error", "Parameter name required")
            return

        param_type = self.param_type.get()
        default = self.param_default.get()

        # Create parameter
        param = {
            'type': param_type,
            'default': default,
            'range': [
                self.param_min.get(),
                self.param_max.get()
            ] if param_type in ('int', 'float') else None
        }

        # Add to builder
        self.builder.add_component(
            'parameter',
            name,
            param
        )

        # Update list
        self._update_param_list()
        self.modified = True

    def _delete_parameter(self):
        """Delete selected parameter."""
        selected = self.param_list.selection()
        if not selected:
            return

        # Get parameter name
        param_name = self.param_list.item(selected[0])['values'][0]

        # Remove from builder
        self.builder.remove_component(param_name)

        # Update list
        self._update_param_list()
        self.modified = True

    def _update_param_list(self):
        """Update parameter list display."""
        # Clear list
        for item in self.param_list.get_children():
            self.param_list.delete(item)

        # Add parameters
        for name, component in self.builder.components.items():
            if component.__class__.__name__ == 'ParameterComponent':
                self.param_list.insert('', 'end', values=(
                    name,
                    component.parameters['type'],
                    component.parameters['default']
                ))

    def _on_param_select(self, event):
        """Handle parameter selection."""
        selected = self.param_list.selection()
        if not selected:
            return

        # Get parameter details
        param_name = self.param_list.item(selected[0])['values'][0]
        component = self.builder.components.get(param_name)
        if not component:
            return

        # Update editor fields
        self.param_name.delete(0, 'end')
        self.param_name.insert(0, param_name)

        self.param_type.set(component.parameters['type'])

        self.param_default.delete(0, 'end')
        self.param_default.insert(0, component.parameters['default'])

        if 'range' in component.parameters and component.parameters['range']:
            self.param_min.delete(0, 'end')
            self.param_min.insert(0, component.parameters['range'][0])
            self.param_max.delete(0, 'end')
            self.param_max.insert(0, component.parameters['range'][1])

    def _on_param_type_change(self, event):
        """Handle parameter type change."""
        param_type = self.param_type.get()

        # Enable/disable range fields for numeric types
        state = 'normal' if param_type in ('int', 'float') else 'disabled'
        self.param_min.configure(state=state)
        self.param_max.configure(state=state)

    def _update_indicator_list(self):
        """Update indicator list based on selected category."""
        # Clear list
        for item in self.indicator_list.get_children():
            self.indicator_list.delete(item)

        # Get indicators for category
        category = self.category_var.get()
        indicators = list_indicators()

        for name, metadata in indicators.items():
            if metadata.category == category:
                self.indicator_list.insert('', 'end', values=(
                    name,
                    metadata.description
                ))

    def _on_indicator_select(self, event):
        """Handle indicator selection."""
        selected = self.indicator_list.selection()
        if not selected:
            return

        # Get indicator details
        indicator_name = self.indicator_list.item(selected[0])['values'][0]
        indicator = get_indicator(indicator_name)

        # Update configuration panel
        self._update_indicator_config(indicator)

    def _create_indicator_config(self, parent):
        """Create indicator configuration widgets."""
        # Parameters frame
        self.ind_params = ttk.LabelFrame(parent, text="Parameters")
        self.ind_params.pack(fill='x', padx=5, pady=5)

        # Input selection
        input_frame = ttk.Frame(parent)
        input_frame.pack(fill='x', padx=5, pady=5)

        ttk.Label(input_frame, text="Input:").pack(side='left')
        self.ind_input = ttk.Combobox(
            input_frame,
            values=['Close', 'Open', 'High', 'Low', 'Volume'],
            state='readonly'
        )
        self.ind_input.pack(side='left', fill='x', expand=True, padx=5)

        # Add button
        ttk.Button(
            parent,
            text="Add Indicator",
            command=self._add_indicator
        ).pack(fill='x', padx=5, pady=5)

    def _update_indicator_config(self, indicator):
        """Update indicator configuration panel."""
        # Clear existing parameters
        for widget in self.ind_params.winfo_children():
            widget.destroy()

        # Add parameter fields
        self.ind_config = {}
        for name, meta in indicator.get_parameters().items():
            frame = ttk.Frame(self.ind_params)
            frame.pack(fill='x', padx=5, pady=2)

            ttk.Label(frame, text=f"{name}:").pack(side='left')

            if meta['type'] == 'bool':
                var = tk.BooleanVar(value=meta['default'])
                widget = ttk.Checkbutton(frame, variable=var)
            else:
                var = tk.StringVar(value=str(meta['default']))
                widget = ttk.Entry(frame, textvariable=var)

            widget.pack(side='left', fill='x', expand=True, padx=5)
            self.ind_config[name] = var

    def _add_indicator(self):
        """Add indicator to strategy."""
        selected = self.indicator_list.selection()
        if not selected:
            messagebox.showerror("Error", "Select an indicator first")
            return

        # Get indicator details
        indicator_name = self.indicator_list.item(selected[0])['values'][0]

        # Get configuration
        params = {
            name: var.get()
            for name, var in self.ind_config.items()
        }

        # Add to builder
        try:
            self.builder.add_component(
                'indicator',
                indicator_name.lower(),
                {
                    'type': indicator_name,
                    'input': self.ind_input.get(),
                    'parameters': params
                }
            )
            self.modified = True
            messagebox.showinfo("Success", "Indicator added")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _add_rule(self):
        """Add trading rule."""
        rule_type = self.rule_type.get()
        if not rule_type:
            messagebox.showerror("Error", "Select rule type")
            return

        condition = self.condition.get('1.0', 'end-1c')
        if not condition:
            messagebox.showerror("Error", "Enter rule condition")
            return

        # Add to builder
        try:
            self.builder.add_component(
                'rule',
                f"{rule_type.lower()}_rule_{len(self.rule_list.get_children())}",
                {
                    'type': rule_type.lower(),
                    'condition': condition
                }
            )

            # Update list
            self.rule_list.insert('', 'end', values=(
                rule_type,
                condition
            ))

            self.modified = True
            self.condition.delete('1.0', 'end')

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _delete_rule(self):
        """Delete selected rule."""
        selected = self.rule_list.selection()
        if not selected:
            return

        # Get rule details
        rule_type = self.rule_list.item(selected[0])['values'][0]
        condition = self.rule_list.item(selected[0])['values'][1]

        # Find matching component
        for name, component in self.builder.components.items():
            if (component.__class__.__name__ == 'RuleComponent' and
                component.parameters['type'] == rule_type.lower() and
                component.parameters['condition'] == condition):
                self.builder.remove_component(name)
                break

        # Update list
        self.rule_list.delete(selected[0])
        self.modified = True

    def _on_rule_select(self, event):
        """Handle rule selection."""
        selected = self.rule_list.selection()
        if not selected:
            return

        # Get rule details
        rule_type = self.rule_list.item(selected[0])['values'][0]
        condition = self.rule_list.item(selected[0])['values'][1]

        # Update editor
        self.rule_type.set(rule_type)
        self.condition.delete('1.0', 'end')
        self.condition.insert('1.0', condition)

    def _new_strategy(self):
        """Create new strategy."""
        if self.modified:
            if not messagebox.askyesno(
                "Unsaved Changes",
                "Discard current changes?"
            ):
                return

        # Reset builder
        self.builder = StrategyBuilder()

        # Reset UI
        self.strategy_name.set("MyStrategy")
        self.strategy_desc.set("")
        self.template_var.set("")

        self._update_param_list()
        self.rule_list.delete(*self.rule_list.get_children())

        self.modified = False

    def _load_strategy(self):
        """Load strategy configuration."""
        if self.modified:
            if not messagebox.askyesno(
                "Unsaved Changes",
                "Discard current changes?"
            ):
                return

        from tkinter import filedialog
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")]
        )

        if filename:
            try:
                self.builder.load(filename)
                self._update_ui_from_builder()
                self.modified = False

            except Exception as e:
                messagebox.showerror("Error", f"Failed to load strategy: {e}")

    def _save_strategy(self):
        """Save strategy configuration."""
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )

        if filename:
            try:
                self.builder.save(filename)
                self.modified = False
                messagebox.showinfo("Success", "Strategy saved")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to save strategy: {e}")

    def _generate_strategy(self):
        """Generate strategy code."""
        try:
            strategy_class = self.builder.generate_strategy(
                self.strategy_name.get()
            )

            # Show preview
            code = self._get_strategy_code(strategy_class)
            self.code_preview.delete('1.0', 'end')
            self.code_preview.insert('1.0', code)

            self.notebook.select(self.preview_frame)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate strategy: {e}")

    def _test_strategy(self):
        """Test generated strategy."""
        try:
            strategy_class = self.builder.generate_strategy(
                self.strategy_name.get()
            )

            # TODO: Implement strategy testing
            messagebox.showinfo("TODO", "Strategy testing not implemented")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to test strategy: {e}")

    def _get_strategy_code(self, strategy_class: type) -> str:
        """Get formatted strategy code."""
        import inspect
        code = inspect.getsource(strategy_class)

        # Add imports
        imports = [
            "from algame.strategy import StrategyBase",
            "from algame.strategy.indicators import *",
            "import pandas as pd",
            "import numpy as np"
        ]

        return "\n".join(imports + ["", code])

    def _update_ui_from_builder(self):
        """Update UI from builder state."""
        # Update parameters
        self._update_param_list()

        # Update rules
        self.rule_list.delete(*self.rule_list.get_children())
        for component in self.builder.components.values():
            if component.__class__.__name__ == 'RuleComponent':
                self.rule_list.insert('', 'end', values=(
                    component.parameters['type'].title(),
                    component.parameters['condition']
                ))

        # Update preview
        self._generate_strategy()

    def _layout_widgets(self):
        """Layout main widgets."""
        # Pack notebook
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
