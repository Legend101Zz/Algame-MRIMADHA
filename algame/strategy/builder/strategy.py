from typing import Dict, List, Optional, Any ,Type
import logging
from pathlib import Path
import json

from .parameters import ParameterComponent
from .indicators import IndicatorComponent
from .rules import RuleComponent
from .base import BuilderComponent
from ..base import StrategyBase

logger = logging.getLogger(__name__)

class StrategyBuilder:
    """Main strategy builder class."""

    def __init__(self):
        self.components: Dict[str, BuilderComponent] = {}
        self._template_code = """
from typing import Dict, Any, Optional
from algame.strategy import StrategyBase
from algame.indicators import *

class {strategy_name}(StrategyBase):
    \"""
    {strategy_desc}
    \"""

    def __init__(self, parameters: Optional[Dict[str, Any]] = None):
        super().__init__(parameters)
        {init_code}

    def initialize(self) -> None:
        {initialize_code}

    def next(self) -> None:
        {next_code}
"""

    def add_component(self, component: BuilderComponent) -> None:
        """Add component to strategy."""
        if not component.validate():
            raise ValueError(f"Invalid component: {component.name}")
        self.components[component.name] = component

    def remove_component(self, name: str) -> None:
        """Remove component."""
        if name in self.components:
            del self.components[name]

    def generate_strategy(self, name: str, description: str = "") -> Type[StrategyBase]:
        """Generate strategy class."""
        # Collect components by type
        parameters = [c for c in self.components.values() if isinstance(c, ParameterComponent)]
        indicators = [c for c in self.components.values() if isinstance(c, IndicatorComponent)]
        rules = [c for c in self.components.values() if isinstance(c, RuleComponent)]

        # Generate initialization code
        init_code = "\n        ".join(p.generate_code() for p in parameters)

        # Generate indicators code
        initialize_code = "\n        ".join(i.generate_code() for i in indicators)

        # Generate trading rules code
        next_code = "\n        ".join(r.generate_code() for r in rules)

        # Fill template
        code = self._template_code.format(
            strategy_name=name,
            strategy_desc=description,
            init_code=init_code,
            initialize_code=initialize_code,
            next_code=next_code
        )

        # Create class
        namespace = {}
        exec(code, globals(), namespace)
        strategy_class = namespace[name]

        return strategy_class

    def save(self, file_path: str) -> None:
        """Save strategy configuration."""
        import json
        config = {
            'components': {
                name: component.to_dict()
                for name, component in self.components.items()
            }
        }
        with open(file_path, 'w') as f:
            json.dump(config, f, indent=4)

    def load(self, file_path: str) -> None:
        """Load strategy configuration."""
        import json
        with open(file_path, 'r') as f:
            config = json.load(f)

        # Clear current components
        self.components.clear()

        # Load components
        for name, data in config['components'].items():
            component_type = globals()[data['type']]
            component = component_type.from_dict(data)
            self.components[name] = component

    def validate(self) -> bool:
        """Validate complete strategy configuration."""
        # Validate all components
        for component in self.components.values():
            if not component.validate():
                return False

        # Validate component relationships
        indicators = [c for c in self.components.values() if isinstance(c, IndicatorComponent)]
        rules = [c for c in self.components.values() if isinstance(c, RuleComponent)]

        # Ensure rules only reference existing indicators
        for rule in rules:
            condition = rule.parameters.get('condition', '')
            for indicator in indicators:
                if indicator.name in condition and indicator.name not in condition:
                    return False

        return True
