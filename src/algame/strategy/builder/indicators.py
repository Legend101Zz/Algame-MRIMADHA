from .base import BuilderComponent

class IndicatorComponent(BuilderComponent):
    """Technical indicator component."""

    def validate(self) -> bool:
        required = ['type', 'inputs', 'parameters']
        if not all(k in self.parameters for k in required):
            return False

        # Validate indicator exists
        try:
            from ..indicators import get_indicator
            get_indicator(self.parameters['type'])
        except:
            return False

        return True

    def generate_code(self) -> str:
        ind_type = self.parameters['type']
        inputs = self.parameters['inputs']
        params = self.parameters['parameters']

        # Format parameters
        param_str = ", ".join(f"{k}={v}" for k,v in params.items())

        return f"self.{self.name} = self.add_indicator('{ind_type}', {inputs}, {param_str})"
