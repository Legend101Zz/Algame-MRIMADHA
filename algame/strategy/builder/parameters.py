from .base import BuilderComponent

class ParameterComponent(BuilderComponent):
    """Strategy parameter component."""

    def validate(self) -> bool:
        required = ['type', 'default']
        if not all(k in self.parameters for k in required):
            return False

        # Validate type
        if self.parameters['type'] not in ['int', 'float', 'bool', 'str']:
            return False

        return True

    def generate_code(self) -> str:
        param_type = self.parameters['type']
        default = self.parameters['default']
        return f"{self.name}: {param_type} = {default}"
