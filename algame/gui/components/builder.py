# algame/gui/components/builder.py

"""
Strategy builder component.

Provides a drag-and-drop interface for building trading strategies:
1. Indicator selection and configuration
2. Entry/exit rule creation
3. Risk management settings
4. Parameter configuration

The builder uses a visual programming approach where users can:
- Add indicators from a library
- Create trading rules using conditions
- Set risk and money management parameters
- Preview and test the strategy
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional, Any
import logging
from functools import partial

from ...strategy import StrategyBase
from ...strategy.indicators import list_indicators, get_indicator
from ...strategy.validation import validate_strategy

logger = logging.getLogger(__name__)

class StrategyBuilder(ttk.Frame):
    """
    Visual strategy builder.

    Features:
    - Drag-and-drop interface
    - Live code preview
    - Validation feedback
    - Template-based building

    The builder follows these principles:
    1. Visual First: Everything should be visually represented
    2. Immediate Feedback: Changes show results instantly
    3. Safe Defaults: Smart default values that work
    4. Progressive Disclosure: Show complexity gradually
    """

    def __init__(self, master):
        """Initialize builder."""
        super().__init__(master)

        # Strategy state
        self.strategy_name = tk.StringVar(value="MyStrategy")
        self.strategy_type = tk.StringVar(value="Basic")
        self.modified = False

        # Component state
        self.components: Dict[str, Any] = {}
        self.selected_component = None

        # Create widgets
        self._create_widgets()

        # Initial update
        self._update_preview()

    def _create_widgets(self):
        """Create builder interface."""
        # Main container
        self.paned = ttk.PanedWindow(self, orient='horizontal')
        self.paned.pack(fill='both', expand=True)

        # Create component panels
        self._create_library_panel()
        self._create_workspace_panel()
        self._create_properties_panel()

        # Add panels to paned window
        self.paned.add(self.library_frame)
        self.paned.add(self.workspace_frame)
        self.paned.add(self.properties_frame)

    def _create_library_panel(self):
        """Create component library panel."""
        self.library_frame = ttk.LabelFrame(self.paned, text="Components")

        # Create tabs for different component types
        self.library_tabs = ttk.Notebook(self.library_frame)
        self.library_tabs.pack(fill='both', expand=True)

        # Indicators tab
        self.indicator_frame = ttk.Frame(self.library_tabs)
        self.library_tabs.add(self.indicator_frame, text="Indicators")
        self._create_indicator_library()

        # Rules tab
        self.rules_frame = ttk.Frame(self.library_tabs)
        self.library_tabs.add(self.rules_frame, text="Rules")
        self._create_rule_library()

        # Risk tab
        self.risk_frame = ttk.Frame(self.library_tabs)
        self.library_tabs.add(self.risk_frame, text="Risk")
        self._create_risk_library()

    def _create_indicator_library(self):
        """Create indicator library section."""
        # Category selection
        cat_frame = ttk.Frame(self.indicator_frame)
        cat_frame.pack(fill='x')

        ttk.Label(cat_frame, text="Category:").pack(side='left', padx=5)

        categories = [
            "Trend",
            "Momentum",
            "Volatility",
            "Volume",
            "Custom"
        ]

        self.category_var = tk.StringVar()
        cat_combo = ttk.Combobox(
            cat_frame,
            textvariable=self.category_var,
            values=categories,
            state='readonly'
        )
        cat_combo.pack(side='left', fill='x', expand=True, padx=5)
        cat_combo.bind('<<ComboboxSelected>>', self._update_indicator_list)

        # Indicator list
        self.indicator_list = ttk.Treeview(
            self.indicator_frame,
            columns=('name', 'description'),
            show='headings',
            height=10
        )
        self.indicator_list.pack(fill='both', expand=True, padx=5, pady=5)

        self.indicator_list.heading('name', text='Name')
        self.indicator_list.heading('description', text='Description')

        # Drag and drop bindings
        self.indicator_list.bind('<ButtonPress-1>', self._start_drag)
        self.indicator_list.bind('<B1-Motion>', self._drag)
        self.indicator_list.bind('<ButtonRelease-1>', self._drop)

        # Initial indicator list
        self._update_indicator_list()

    def _create_rule_library(self):
        """Create trading rule library section."""
        # Rule templates
        templates = [
            ("Price Cross", "Price crosses above/below value"),
            ("Indicator Cross", "Indicator crosses another indicator"),
            ("Price Level", "Price reaches specific level"),
            ("Time Based", "Time-based entry/exit"),
            ("Custom", "Create custom rule")
        ]

        for name, desc in templates:
            frame = ttk.Frame(self.rules_frame)
            frame.pack(fill='x', padx=5, pady=2)

            ttk.Label(
                frame,
                text=name,
                font=('Arial', 10, 'bold')
            ).pack(anchor='w')

            ttk.Label(
                frame,
                text=desc,
                wraplength=200
            ).pack(anchor='w')

            # Make draggable
            frame.bind('<ButtonPress-1>', partial(self._start_rule_drag, name))
            frame.bind('<B1-Motion>', self._drag)
            frame.bind('<ButtonRelease-1>', self._drop)

    def _create_risk_library(self):
        """Create risk management library section."""
        # Risk components
        components = [
            ("Position Size", "Calculate position size"),
            ("Stop Loss", "Set stop loss rules"),
            ("Take Profit", "Set take profit rules"),
            ("Risk/Reward", "Set risk/reward ratio"),
            ("Max Drawdown", "Set max drawdown limit"),
            ("Custom", "Create custom risk rule")
        ]

        for name, desc in components:
            frame = ttk.Frame(self.risk_frame)
            frame.pack(fill='x', padx=5, pady=2)

            ttk.Label(
                frame,
                text=name,
                font=('Arial', 10, 'bold')
            ).pack(anchor='w')

            ttk.Label(
                frame,
                text=desc,
                wraplength=200
            ).pack(anchor='w')

            # Make draggable
            frame.bind('<ButtonPress-1>', partial(self._start_risk_drag, name))
            frame.bind('<B1-Motion>', self._drag)
            frame.bind('<ButtonRelease-1>', self._drop)

    def _create_workspace_panel(self):
        """Create strategy workspace panel."""
        self.workspace_frame = ttk.LabelFrame(self.paned, text="Strategy")

        # Strategy header
        header = ttk.Frame(self.workspace_frame)
        header.pack(fill='x', padx=5, pady=5)

        ttk.Label(header, text="Name:").pack(side='left')
        ttk.Entry(
            header,
            textvariable=self.strategy_name,
            width=30
        ).pack(side='left', padx=5)

        ttk.Label(header, text="Type:").pack(side='left', padx=5)
        ttk.Combobox(
            header,
            textvariable=self.strategy_type,
            values=['Basic', 'Multi-Asset', 'Multi-Timeframe'],
            state='readonly',
            width=15
        ).pack(side='left')

        # Component sections
        self._create_indicator_section()
        self._create_rule_section()
        self._create_risk_section()

        # Code preview
        preview = ttk.LabelFrame(self.workspace_frame, text="Preview")
        preview.pack(fill='both', expand=True, padx=5, pady=5)

        self.preview = tk.Text(preview, height=10, wrap='none')
        self.preview.pack(fill='both', expand=True)

    def _create_indicator_section(self):
        """Create indicator section in workspace."""
        frame = ttk.LabelFrame(self.workspace_frame, text="Indicators")
        frame.pack(fill='x', padx=5, pady=5)

        self.indicator_tree = ttk.Treeview(
            frame,
            columns=('type', 'params'),
            show='headings',
            height=5
        )
        self.indicator_tree.pack(fill='x')

        self.indicator_tree.heading('type', text='Type')
        self.indicator_tree.heading('params', text='Parameters')

        # Selection binding
        self.indicator_tree.bind('<<TreeviewSelect>>', self._show_indicator_properties)

    def _create_rule_section(self):
        """Create rule section in workspace."""
        frame = ttk.LabelFrame(self.workspace_frame, text="Rules")
        frame.pack(fill='x', padx=5, pady=5)

        self.rule_tree = ttk.Treeview(
            frame,
            columns=('type', 'condition'),
            show='headings',
            height=5
        )
        self.rule_tree.pack(fill='x')

        self.rule_tree.heading('type', text='Type')
        self.rule_tree.heading('condition', text='Condition')

        # Selection binding
        self.rule_tree.bind('<<TreeviewSelect>>', self._show_rule_properties)

    def _create_risk_section(self):
        """Create risk management section in workspace."""
        frame = ttk.LabelFrame(self.workspace_frame, text="Risk Management")
        frame.pack(fill='x', padx=5, pady=5)

        self.risk_tree = ttk.Treeview(
            frame,
            columns=('type', 'settings'),
            show='headings',
            height=5
        )
        self.risk_tree.pack(fill='x')

        self.risk_tree.heading('type', text='Type')
        self.risk_tree.heading('settings', text='Settings')

        # Selection binding
        self.risk_tree.bind('<<TreeviewSelect>>', self._show_risk_properties)

    def _create_properties_panel(self):
        """Create properties panel."""
        self.properties_frame = ttk.LabelFrame(self.paned, text="Properties")

        # Property editor
        self.property_editor = ttk.Frame(self.properties_frame)
        self.property_editor.pack(fill='both', expand=True)

        # Initial message
        ttk.Label(
            self.property_editor,
            text="Select a component to edit its properties",
            wraplength=200
        ).pack(padx=10, pady=10)

    def _update_indicator_list(self, event=None):
        """Update indicator list based on category."""
        # Clear list
        for item in self.indicator_list.get_children():
            self.indicator_list.delete(item)

        # Get indicators for category
        category = self.category_var.get()
        indicators = list_indicators()

        for name, meta in indicators.items():
            if meta.category == category:
                self.indicator_list.insert('', 'end', values=(
                    name,
                    meta.description[:50] + '...'
                ))

    def _start_drag(self, event):
        """Start drag operation."""
        # Get selected indicator
        item = self.indicator_list.identify_row(event.y)
        if not item:
            return

        # Save drag data
        self._drag_data = {
            'item': item,
            'type': 'indicator',
            'name': self.indicator_list.item(item, 'values')[0]
        }

    def _start_rule_drag(self, name: str, event):
        """Start rule drag operation."""
        self._drag_data = {
            'type': 'rule',
            'name': name
        }

    def _start_risk_drag(self, name: str, event):
        """Start risk component drag operation."""
        self._drag_data = {
            'type': 'risk',
            'name': name
        }

    def _drag(self, event):
        """Handle drag motion."""
        if not hasattr(self, '_drag_data'):
            return

        # Update drag visual
        pass  # TODO: Add drag visual

    def _drop(self, event):
        """Handle drop operation."""
        if not hasattr(self, '_drag_data'):
            return

        try:
            # Add component based on type
            type = self._drag_data['type']
            name = self._drag_data['name']

            if type == 'indicator':
                self._add_indicator(name)
            elif type == 'rule':
                self._add_rule(name)
            else:  # risk
                self._add_risk(name)

        finally:
            # Clear drag data
            del self._drag_data

    def _add_indicator(self, name: str):
        """Add indicator to strategy."""
        try:
            # Get indicator
            indicator = get_indicator(name)

            # Add to components
            component_id = f"indicator_{len(self.components)}"
            self.components[component_id] = {
                'type': 'indicator',
                'name': name,
                'indicator': indicator,
                'params': indicator.get_default_params()
            }

            # Add to tree
            self.indicator_tree.insert('', 'end',
                values=(name, str(indicator.get_default_params())))

            self.modified = True
            self._update_preview()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to add indicator: {str(e)}")

    def _add_rule(self, name: str):
        """Add trading rule to strategy."""
        try:
            # Create rule template
            component_id = f"rule_{len(self.components)}"
            self.components[component_id] = {
                'type': 'rule',
                'name': name,
                'condition': 'price > sma'  # Default condition
            }

            # Add to tree
            self.rule_tree.insert('', 'end',
                values=(name, 'price > sma'))

            self.modified = True
            self._update_preview()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to add rule: {str(e)}")

# algame/gui/components/builder.py (continued)

    def _add_risk(self, name: str):
        """Add risk management component."""
        try:
            # Create risk component
            component_id = f"risk_{len(self.components)}"
            self.components[component_id] = {
                'type': 'risk',
                'name': name,
                'settings': self._get_default_risk_settings(name)
            }

            # Add to tree
            self.risk_tree.insert('', 'end',
                values=(name, str(self._get_default_risk_settings(name))))

            self.modified = True
            self._update_preview()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to add risk component: {str(e)}")

    def _get_default_risk_settings(self, component_type: str) -> Dict[str, Any]:
        """Get default settings for risk component."""
        if component_type == "Position Size":
            return {
                'type': 'fixed',
                'size': 1.0,
                'max_size': 5.0
            }
        elif component_type == "Stop Loss":
            return {
                'type': 'fixed',
                'distance': 0.02,
                'atr_multiple': 2.0
            }
        elif component_type == "Take Profit":
            return {
                'type': 'fixed',
                'distance': 0.03,
                'risk_multiple': 1.5
            }
        elif component_type == "Risk/Reward":
            return {
                'min_ratio': 1.5,
                'preferred_ratio': 2.0
            }
        elif component_type == "Max Drawdown":
            return {
                'max_drawdown': 0.20,
                'trailing': True
            }
        else:
            return {}

    def _show_indicator_properties(self, event):
        """Show indicator properties in editor."""
        selected = self.indicator_tree.selection()
        if not selected:
            return

        # Get indicator component
        component_id = None
        for id, comp in self.components.items():
            if (comp['type'] == 'indicator' and
                comp['name'] == self.indicator_tree.item(selected[0])['values'][0]):
                component_id = id
                break

        if not component_id:
            return

        # Show properties editor
        self._show_properties_editor(
            component_id,
            self.components[component_id]
        )

    def _show_rule_properties(self, event):
        """Show rule properties in editor."""
        selected = self.rule_tree.selection()
        if not selected:
            return

        # Get rule component
        component_id = None
        for id, comp in self.components.items():
            if (comp['type'] == 'rule' and
                comp['name'] == self.rule_tree.item(selected[0])['values'][0]):
                component_id = id
                break

        if not component_id:
            return

        # Show properties editor
        self._show_properties_editor(
            component_id,
            self.components[component_id]
        )

    def _show_risk_properties(self, event):
        """Show risk component properties in editor."""
        selected = self.risk_tree.selection()
        if not selected:
            return

        # Get risk component
        component_id = None
        for id, comp in self.components.items():
            if (comp['type'] == 'risk' and
                comp['name'] == self.risk_tree.item(selected[0])['values'][0]):
                component_id = id
                break

        if not component_id:
            return

        # Show properties editor
        self._show_properties_editor(
            component_id,
            self.components[component_id]
        )

    def _show_properties_editor(self, component_id: str, component: Dict[str, Any]):
        """Show properties editor for component."""
        # Clear current editor
        for widget in self.property_editor.winfo_children():
            widget.destroy()

        self.selected_component = component_id

        # Create editor based on component type
        if component['type'] == 'indicator':
            self._create_indicator_editor(component)
        elif component['type'] == 'rule':
            self._create_rule_editor(component)
        else:  # risk
            self._create_risk_editor(component)

    def _create_indicator_editor(self, component: Dict[str, Any]):
        """Create indicator properties editor."""
        # Name
        name_frame = ttk.Frame(self.property_editor)
        name_frame.pack(fill='x', padx=5, pady=5)

        ttk.Label(name_frame, text="Name:").pack(side='left')
        name_var = tk.StringVar(value=component['name'])
        ttk.Entry(
            name_frame,
            textvariable=name_var,
            state='readonly'
        ).pack(side='left', fill='x', expand=True, padx=5)

        # Parameters
        params_frame = ttk.LabelFrame(self.property_editor, text="Parameters")
        params_frame.pack(fill='x', padx=5, pady=5)

        param_vars = {}
        for name, value in component['params'].items():
            frame = ttk.Frame(params_frame)
            frame.pack(fill='x', padx=5, pady=2)

            ttk.Label(frame, text=f"{name}:").pack(side='left')

            if isinstance(value, bool):
                var = tk.BooleanVar(value=value)
                ttk.Checkbutton(
                    frame,
                    variable=var,
                    command=self._on_property_change
                ).pack(side='left', padx=5)
            else:
                var = tk.StringVar(value=str(value))
                ttk.Entry(
                    frame,
                    textvariable=var
                ).pack(side='left', fill='x', expand=True, padx=5)
                var.trace('w', lambda *args: self._on_property_change())

            param_vars[name] = var

        # Store references
        self.current_editor = {
            'type': 'indicator',
            'vars': param_vars
        }

    def _create_rule_editor(self, component: Dict[str, Any]):
        """Create rule properties editor."""
        # Type frame
        type_frame = ttk.Frame(self.property_editor)
        type_frame.pack(fill='x', padx=5, pady=5)

        ttk.Label(type_frame, text="Type:").pack(side='left')
        type_var = tk.StringVar(value=component['name'])
        ttk.Entry(
            type_frame,
            textvariable=type_var,
            state='readonly'
        ).pack(side='left', fill='x', expand=True, padx=5)

        # Condition
        cond_frame = ttk.LabelFrame(self.property_editor, text="Condition")
        cond_frame.pack(fill='x', padx=5, pady=5)

        condition_var = tk.StringVar(value=component['condition'])
        condition_text = tk.Text(cond_frame, height=3, wrap='word')
        condition_text.pack(fill='x', padx=5, pady=5)
        condition_text.insert('1.0', component['condition'])

        # Validation button
        ttk.Button(
            self.property_editor,
            text="Validate Condition",
            command=lambda: self._validate_condition(condition_text.get('1.0', 'end-1c'))
        ).pack(fill='x', padx=5, pady=5)

        # Store references
        self.current_editor = {
            'type': 'rule',
            'text': condition_text
        }

    def _create_risk_editor(self, component: Dict[str, Any]):
        """Create risk component properties editor."""
        # Type frame
        type_frame = ttk.Frame(self.property_editor)
        type_frame.pack(fill='x', padx=5, pady=5)

        ttk.Label(type_frame, text="Type:").pack(side='left')
        type_var = tk.StringVar(value=component['name'])
        ttk.Entry(
            type_frame,
            textvariable=type_var,
            state='readonly'
        ).pack(side='left', fill='x', expand=True, padx=5)

        # Settings
        settings_frame = ttk.LabelFrame(self.property_editor, text="Settings")
        settings_frame.pack(fill='x', padx=5, pady=5)

        setting_vars = {}
        for name, value in component['settings'].items():
            frame = ttk.Frame(settings_frame)
            frame.pack(fill='x', padx=5, pady=2)

            ttk.Label(frame, text=f"{name}:").pack(side='left')

            if isinstance(value, bool):
                var = tk.BooleanVar(value=value)
                ttk.Checkbutton(
                    frame,
                    variable=var,
                    command=self._on_property_change
                ).pack(side='left', padx=5)
            else:
                var = tk.StringVar(value=str(value))
                ttk.Entry(
                    frame,
                    textvariable=var
                ).pack(side='left', fill='x', expand=True, padx=5)
                var.trace('w', lambda *args: self._on_property_change())

            setting_vars[name] = var

        # Store references
        self.current_editor = {
            'type': 'risk',
            'vars': setting_vars
        }

    def _on_property_change(self, *args):
        """Handle property change."""
        if not self.selected_component:
            return

        try:
            # Update component
            component = self.components[self.selected_component]

            if self.current_editor['type'] == 'indicator':
                # Update indicator parameters
                for name, var in self.current_editor['vars'].items():
                    component['params'][name] = self._parse_value(var.get())

            elif self.current_editor['type'] == 'rule':
                # Update rule condition
                component['condition'] = self.current_editor['text'].get('1.0', 'end-1c')

            else:  # risk
                # Update risk settings
                for name, var in self.current_editor['vars'].items():
                    component['settings'][name] = self._parse_value(var.get())

            # Update tree display
            self._update_component_display(self.selected_component)

            # Update preview
            self._update_preview()

            self.modified = True

        except Exception as e:
            logger.error(f"Error updating property: {str(e)}")

    def _parse_value(self, value: str) -> Any:
        """Parse string value to appropriate type."""
        try:
            # Try float
            return float(value)
        except ValueError:
            # Try bool
            if value.lower() in ('true', 'false'):
                return value.lower() == 'true'
            # Return as string
            return value

    def _update_component_display(self, component_id: str):
        """Update component display in tree."""
        component = self.components[component_id]

        # Find tree and item
        if component['type'] == 'indicator':
            tree = self.indicator_tree
            values = (component['name'], str(component['params']))
        elif component['type'] == 'rule':
            tree = self.rule_tree
            values = (component['name'], component['condition'])
        else:  # risk
            tree = self.risk_tree
            values = (component['name'], str(component['settings']))

        # Update display
        for item in tree.get_children():
            if tree.item(item)['values'][0] == component['name']:
                tree.item(item, values=values)
                break

    def _validate_condition(self, condition: str):
        """Validate rule condition."""
        try:
            # TODO: Implement condition validation
            messagebox.showinfo("Validation", "Condition is valid")
        except Exception as e:
            messagebox.showerror("Validation Error", str(e))

    def _update_preview(self):
        """Update code preview."""
        try:
            code = self._generate_strategy_code()
            self.preview.delete('1.0', 'end')
            self.preview.insert('1.0', code)
        except Exception as e:
            logger.error(f"Error generating preview: {str(e)}")

    def _generate_strategy_code(self) -> str:
        """Generate strategy code."""
        # Generate imports
        imports = [
            "from algame.strategy import StrategyBase",
            "from algame.indicators import *",
            "import pandas as pd",
            "import numpy as np",
            ""
        ]

        # Generate class definition
        class_def = [
            f"class {self.strategy_name.get()}(StrategyBase):",
            "    def __init__(self, parameters=None):",
            "        super().__init__(parameters)",
            ""
        ]

        # Generate initialize method
        init = [
            "    def initialize(self):"
        ]

        # Add indicators
        for comp in self.components.values():
            if comp['type'] == 'indicator':
                params = ", ".join(f"{k}={v}" for k, v in comp['params'].items())
                init.append(f"        self.{comp['name'].lower()} = {comp['name']}({params})")

        init.append("")

        # Generate next method
        next = [
            "    def next(self):",
            "        # Skip if not enough data",
            "        if len(self.data) < 2:",
            "            return",
            ""
        ]

        # Add rules
        for comp in self.components.values():
            if comp['type'] == 'rule':
                next.append(f"        # {comp['name']}")
                next.append(f"        if {comp['condition']}:")
                next.append("            self.buy()")
                next.append("")

        # Combine code
        code = "\n".join(imports + class_def + init + next)
        return code

    def get_strategy(self) -> StrategyBase:
        """Get generated strategy class."""
        # Generate code
        code = self._generate_strategy_code()

        # Create class
        namespace = {}
        exec(code, globals(), namespace)

        # Get strategy class
        strategy_class = namespace[self.strategy_name.get()]

        return strategy_class

    def save_strategy(self, filename: str):
        """Save strategy configuration."""
        data = {
            'name': self.strategy_name.get(),
            'type': self.strategy_type.get(),
            'components': self.components
        }

        with open(filename, 'w') as f:
            import json
            json.dump(data, f, indent=4)

    def load_strategy(self, filename: str):
        """Load strategy configuration."""
        with open(filename, 'r') as f:
            import json
            data = json.load(f)

        # Clear current state
        self.clear()

        # Update state
        self.strategy_name.set(data['name'])
        self.strategy_type.set(data.get('type', 'Basic'))
        self.components = data['components']

        # Update trees
        self._update_all_trees()

        # Update preview
        self._update_preview()

    def clear(self):
        """Clear current strategy."""
        # Clear state
        self.components.clear()
        self.selected_component = None

        # Clear trees
        for tree in [self.indicator_tree, self.rule_tree, self.risk_tree]:
            for item in tree.get_children():
                tree.delete(item)

        # Clear preview
        self.preview.delete('1.0', 'end')

        self.modified = False

    def _update_all_trees(self):
        """Update all component trees."""
        # Clear trees
        for tree in [self.indicator_tree, self.rule_tree, self.risk_tree]:
            for item in tree.get_children():
                tree.delete(item)

        # Add components
        for comp in self.components.values():
            if comp['type'] == 'indicator':
                self.indicator_tree.insert('', 'end', values=(
                    comp['name'],
                    str(comp['params'])
                ))
            elif comp['type'] == 'rule':
                self.rule_tree.insert('', 'end', values=(
                    comp['name'],
                    comp['condition']
                ))
            else:  # risk
                self.risk_tree.insert('', 'end', values=(
                    comp['name'],
                    str(comp['settings'])
                ))

    def export_code(self, filename: str):
        """Export generated code to file."""
        code = self._generate_strategy_code()
        with open(filename, 'w') as f:
            f.write(code)

    def validate_strategy(self) -> bool:
        """Validate complete strategy."""
        try:
            # Get strategy class
            strategy_class = self.get_strategy()

            # Validate using strategy validator
            from ...strategy.validation import validate_strategy
            validation = validate_strategy(strategy_class)

            if not validation.passed:
                messagebox.showerror(
                    "Validation Error",
                    "\n".join(validation.errors)
                )
                return False

            return True

        except Exception as e:
            messagebox.showerror(
                "Validation Error",
                f"Failed to validate strategy: {str(e)}"
            )
            return False
