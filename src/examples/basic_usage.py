from algame.core import core, Strategy, BacktestConfig
from algame.core.config import StrategyConfig
import pandas as pd

# Create a simple moving average strategy
class SMAStrategy(Strategy):
    def __init__(self, parameters=None):
        super().__init__(parameters)
        self.fast_period = self.parameters.get('fast_period', 10)
        self.slow_period = self.parameters.get('slow_period', 30)

    def initialize(self):
        """Setup indicators."""
        # Calculate moving averages
        self.fast_ma = self.data['Close'].rolling(self.fast_period).mean()
        self.slow_ma = self.data['Close'].rolling(self.slow_period).mean()

    def next(self):
        """Generate trading signals."""
        if len(self.data) < self.slow_period:
            return

        # Check for cross over/under
        fast_above = self.fast_ma[-1] > self.slow_ma[-1]
        fast_above_prev = self.fast_ma[-2] > self.slow_ma[-2]

        if fast_above and not fast_above_prev:
            # Fast MA crossed above slow MA - BUY
            self.buy()
        elif not fast_above and fast_above_prev:
            # Fast MA crossed below slow MA - SELL
            self.sell()

def main():
    # Create configuration
    config = BacktestConfig(
        name="SMA Crossover Example",
        description="Simple moving average crossover strategy example",
        symbols=['AAPL', 'GOOGL'],
        start_date='2020-01-01',
        end_date='2023-12-31',
        strategy=StrategyConfig(
            name="SMA Crossover",
            parameters={
                'fast_period': 10,
                'slow_period': 30
            }
        )
    )

    # Create and run backtest
    backtest = core.create_backtest(config)
    results = backtest.run(SMAStrategy)

    # Print results
    print("\nBacktest Results:")
    print("-----------------")
    print(f"Total Return: {results.metrics['total_return']:.2%}")
    print(f"Sharpe Ratio: {results.metrics['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {results.metrics['max_drawdown']:.2%}")
    print(f"Win Rate: {results.metrics['win_rate']:.2%}")

    # Save configuration
    config_file = core.config_manager.save_config(config)
    print(f"\nSaved configuration to: {config_file}")

    # Optimize strategy
    param_grid = {
        'fast_period': range(5, 30, 5),
        'slow_period': range(20, 100, 10)
    }

    print("\nOptimizing strategy...")
    opt_results = core.optimize_strategy(
        strategy=SMAStrategy,
        param_grid=param_grid,
        metric='sharpe_ratio'
    )

    print("\nOptimization Results:")
    print("--------------------")
    print(f"Best Parameters: {opt_results['best_params']}")
    print(f"Best Sharpe Ratio: {opt_results['best_metrics']['sharpe_ratio']:.2f}")

    # Validate strategy
    print("\nValidating strategy...")
    validation = core.validate_strategy(SMAStrategy)

    print("\nValidation Results:")
    print("------------------")
    for check, result in validation.items():
        print(f"{check}: {'✓' if result['passed'] else '✗'}")
        if not result['passed']:
            print(f"  - {result['message']}")

if __name__ == "__main__":
    main()
