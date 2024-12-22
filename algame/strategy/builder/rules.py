from .base import BuilderComponent

class RuleComponent(BuilderComponent):
    """Trading rule component."""

    def validate(self) -> bool:
        if 'condition' not in self.parameters:
            return False

        # Validate rule syntax
        try:
            condition = self.parameters['condition']
            compile(condition, '<string>', 'eval')
        except:
            return False

        return True

    def generate_code(self) -> str:
        condition = self.parameters['condition']

        if self.parameters.get('type') == 'entry':
            return f"if {condition}:\n    self.buy()"
        else:
            return f"if {condition}:\n    self.sell()"


class RuleParser:
    """Parser for trading rules."""

    def parse(self, condition: str) -> str:
        """
        Parse rule condition.

        Converts user-friendly syntax to Python code:
        "RSI < 30" -> "self.rsi[-1] < 30"
        "Cross(SMA1, SMA2)" -> "self.sma1[-1] > self.sma2[-1] and self.sma1[-2] <= self.sma2[-2]"
        """
        # TODO: Implement rule parsing
        return condition
