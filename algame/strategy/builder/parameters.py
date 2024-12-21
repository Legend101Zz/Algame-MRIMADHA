from .base import BuilderComponent


class ParameterComponent(BuilderComponent):
    """Component for strategy parameters."""

    def validate(self) -> bool:
        """Validate parameter configuration."""
        required = ['type', 'default', 'range']
        if not all(k in self.parameters for k in required):
            return False

        # Check type
        if self.parameters['type'] not in ['int', 'float', 'bool', 'str']:
            return False

        # Check range
        if not isinstance(self.parameters['range'], (list, tuple)):
            return False

        return True
