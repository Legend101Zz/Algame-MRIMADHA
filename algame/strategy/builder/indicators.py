from .base import BuilderComponent

class IndicatorComponent(BuilderComponent):
    """Component for technical indicators."""

    def validate(self) -> bool:
        """Validate indicator configuration."""
        required = ['type', 'inputs', 'parameters']
        if not all(k in self.parameters for k in required):
            return False

        # Check indicator type exists
        from ..indicators import get_indicator
        try:
            get_indicator(self.parameters['type'])
        except ValueError:
            return False

        return True

    def generate_code(self) -> str:
        """Generate indicator code."""
        ind_type = self.parameters['type']
        inputs = self.parameters['inputs']
        params = self.parameters['parameters']

        # Format parameters
        param_str = ", ".join(f"{k}={v}" for k,v in params.items())

        # Generate code
        return f"self.{self.name} = self.add_indicator('{ind_type}', {inputs}, {param_str})"
