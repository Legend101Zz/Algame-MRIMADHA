Quick Start Guide
===============

Basic Usage
---------

Here's a simple example to get you started:

.. code-block:: python

    from algame.strategy import StrategyBase
    from algame.core import EngineManager
    from algame.data import YahooData

    # Create a simple moving average strategy
    class SMAStrategy(StrategyBase):
        def initialize(self):
            # Add 20-day SMA indicator
            self.sma = self.add_indicator('SMA', self.data.Close, period=20)

        def next(self):
            # Buy when price crosses above SMA
            if self.data.Close[-1] > self.sma[-1] and \
               self.data.Close[-2] <= self.sma[-2]:
                self.buy()
            # Sell when price crosses below SMA
            elif self.data.Close[-1] < self.sma[-1] and \
                 self.data.Close[-2] >= self.sma[-2]:
                self.sell()

    # Load data
    data = YahooData.download('AAPL', '2020-01-01', '2023-12-31')

    # Run backtest
    engine = EngineManager()
    results = engine.run_backtest(SMAStrategy, data)

    # Print results
    print(f"Total Return: {results.metrics['total_return']:.2f}%")
    print(f"Sharpe Ratio: {results.metrics['sharpe_ratio']:.2f}")

Using the GUI
-----------

Launch the GUI:

.. code-block:: python

    from algame.gui import start_app
    start_app()
