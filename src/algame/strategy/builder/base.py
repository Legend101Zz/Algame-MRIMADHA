from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class BuilderComponent(ABC):
    """Base class for strategy builder components."""

    def __init__(self, name: str):
        self.name = name
        self.parameters: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}

    @abstractmethod
    def validate(self) -> bool:
        """Validate component configuration."""
        pass

    @abstractmethod
    def generate_code(self) -> str:
        """Generate Python code for component."""
        pass

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'type': self.__class__.__name__,
            'parameters': self.parameters,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'BuilderComponent':
        """Create from dictionary."""
        component = cls(data['name'])
        component.parameters = data.get('parameters', {})
        component.metadata = data.get('metadata', {})
        return component


class ComponentRegistry:
    """Registry for builder components."""

    def __init__(self):
        """Initialize registry."""
        self._components: Dict[str, type] = {}

    def register(self, name: str, component_class: type) -> None:
        """Register component type."""
        if not issubclass(component_class, BuilderComponent):
            raise TypeError("Component must inherit from BuilderComponent")
        self._components[name] = component_class

    def get(self, name: str) -> type:
        """Get component class by name."""
        if name not in self._components:
            raise ValueError(f"Component not found: {name}")
        return self._components[name]

    def list_components(self) -> List[str]:
        """Get list of registered components."""
        return list(self._components.keys())
