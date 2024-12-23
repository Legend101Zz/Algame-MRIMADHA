"""Quick start example for Algame package."""
import pandas as pd
from algame.core import core
from algame.strategy import StrategyBase
from algame.core.config import BacktestConfig, StrategyConfig

# Create a simple moving average strategy
class SMAStrategy(StrategyBase):
    def __init__(self, parameters=None):
        super().__init__(parameters)
        self.fast_period = self.parameters.get('fast_period', 10)
        self.slow_period = self.parameters.get('slow_period', 30)

    def initialize(self):
        """Setup indicators."""
        self.fast_ma = self.add_indicator('SMA', self.data.Close, period=self.fast_period)
        self.slow_ma = self.add_indicator('SMA', self.data.Close, period=self.slow_period)

    def next(self):
        """Generate trading signals."""
        if len(self.data) < self.slow_period:
            return

        if self.fast_ma[-1] > self.slow_ma[-1]:
            self.buy()
        elif self.fast_ma[-1] < self.slow_ma[-1]:
            self.sell()

def main():
    """Run example backtest."""
    # Create configuration
    config = BacktestConfig(
        name="SMA Strategy Test",
        description="Simple moving average crossover strategy test",
        symbols=['AAPL'],
        strategy=StrategyConfig(
            name="SMA Crossover",
            parameters={
                'fast_period': 10,
                'slow_period': 30
            }
        )
    )

    # Create and run backtest
    print("\nRunning backtest...")
    backtest = core.create_backtest(config)
    results = backtest.run(SMAStrategy)

    # Print results
    print("\nBacktest Results:")
    print("-----------------")
    print(f"Total Return: {results.metrics['total_return']:.2f}%")
    print(f"Sharpe Ratio: {results.metrics['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {results.metrics['max_drawdown']:.2f}%")
    print(f"Win Rate: {results.metrics['win_rate']:.1f}%")

if __name__ == "__main__":
    main()
