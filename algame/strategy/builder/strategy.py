from typing import Dict, List, Optional, Any
import logging
from pathlib import Path
import json

from .base import BuilderComponent, ComponentRegistry
from ..base import StrategyBase

logger = logging.getLogger(__name__)

class StrategyBuilder:
    """
    Strategy builder main class.

    This class coordinates the strategy building process:
    1. Component management
    2. Code generation
    3. Strategy validation
    4. Configuration management
    """

    def __init__(self):
        """Initialize builder."""
        self.components: Dict[str, BuilderComponent] = {}
        self.registry = ComponentRegistry()
        self._register_components()

    def _register_components(self) -> None:
        """Register built-in components."""
        from .indicators import IndicatorComponent
        from .rules import RuleComponent
        from .parameters import ParameterComponent

        self.registry.register('indicator', IndicatorComponent)
        self.registry.register('rule', RuleComponent)
        self.registry.register('parameter', ParameterComponent)

    def add_component(self,
                     type_name: str,
                     name: str,
                     parameters: Dict[str, Any]) -> None:
        """
        Add component to strategy.

        Args:
            type_name: Component type
            name: Component name
            parameters: Component parameters
        """
        # Get component class
        component_class = self.registry.get(type_name)

        # Create component
        component = component_class(name)
        component.parameters = parameters

        # Validate
        if not component.validate():
            raise ValueError(f"Invalid component configuration: {name}")

        # Add to strategy
        self.components[name] = component

    def remove_component(self, name: str) -> None:
        """Remove component from strategy."""
        if name in self.components:
            del self.components[name]

    def generate_strategy(self, name: str) -> type:
        """
        Generate strategy class.

        Args:
            name: Strategy name

        Returns:
            type: Generated strategy class
        """
        # Generate code sections
        sections = {
            'imports': self._generate_imports(),
            'class_def': self._generate_class_def(name),
            'init': self._generate_init(),
            'initialize': self._generate_initialize(),
            'next': self._generate_next()
        }

        # Combine code
        code = "\n\n".join(sections.values())

        # Create class
        namespace = {}
        exec(code, globals(), namespace)

        # Get class from namespace
        strategy_class = namespace[name]

        return strategy_class

    def _generate_imports(self) -> str:
        """Generate import statements."""
        imports = [
            "from algame.strategy import StrategyBase",
            "from algame.strategy.indicators import *",
            "import pandas as pd",
            "import numpy as np"
        ]
        return "\n".join(imports)

    def _generate_class_def(self, name: str) -> str:
        """Generate class definition."""
        return f"class {name}(StrategyBase):"

    def _generate_init(self) -> str:
        """Generate __init__ method."""
        # Get parameters
        params = [c for c in self.components.values()
                 if c.__class__.__name__ == 'ParameterComponent']

        # Generate parameter code
        param_code = []
        for p in params:
            param_code.append(f"self.{p.name} = {p.parameters['default']}")

        # Format code
        init_code = [
            "    def __init__(self, config=None):",
            "        super().__init__(config)",
            "        # Initialize parameters",
            *[f"        {line}" for line in param_code]
        ]

        return "\n".join(init_code)

    def _generate_initialize(self) -> str:
        """Generate initialize method."""
        # Get indicators
        indicators = [c for c in self.components.values()
                     if c.__class__.__name__ == 'IndicatorComponent']

        # Generate indicator code
        ind_code = []
        for ind in indicators:
            ind_code.append(ind.generate_code())

        # Format code
        init_code = [
            "    def initialize(self):",
            "        # Calculate indicators",
            *[f"        {line}" for line in ind_code]
        ]

        return "\n".join(init_code)

    def _generate_next(self) -> str:
        """Generate next method."""
        # Get rules
        entry_rules = [c for c in self.components.values()
                      if c.__class__.__name__ == 'RuleComponent'
                      and c.parameters['type'] == 'entry']

        exit_rules = [c for c in self.components.values()
                     if c.__class__.__name__ == 'RuleComponent'
                     and c.parameters['type'] == 'exit']

        # Generate rule code
        rule_code = []

        # Entry rules
        rule_code.append("        # Check entry conditions")
        rule_code.append("        if not self.position.is_open:")
        for rule in entry_rules:
            rule_code.append(f"            if {rule.generate_code()}:")
            rule_code.append("                self.buy()")

        # Exit rules
        rule_code.append("        # Check exit conditions")
        rule_code.append("        else:")
        for rule in exit_rules:
            rule_code.append(f"            if {rule.generate_code()}:")
            rule_code.append("                self.close()")

        # Format code
        next_code = [
            "    def next(self):",
            *rule_code
        ]

        return "\n".join(next_code)

    def save(self, file_path: str) -> None:
        """
        Save strategy configuration.

        Args:
            file_path: Path to save configuration
        """
        config = {
            'components': {
                name: component.to_dict()
                for name, component in self.components.items()
            }
        }

        with open(file_path, 'w') as f:
            json.dump(config, f, indent=4)

    def load(self, file_path: str) -> None:
        """
        Load strategy configuration.

        Args:
            file_path: Path to configuration file
        """
        with open(file_path, 'r') as f:
            config = json.load(f)

        # Clear current components
        self.components.clear()

        # Load components
        for name, data in config['components'].items():
            component_class = self.registry.get(data['type'])
            component = component_class.from_dict(data)
            self.components[name] = component
