Tutorials
========

Strategy Development
------------------

1. Creating a Basic Strategy
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from algame.strategy import StrategyBase

    class MyFirstStrategy(StrategyBase):
        def initialize(self):
            """Initialize strategy components."""
            self.sma = self.add_indicator('SMA', self.data.Close, period=20)
            self.rsi = self.add_indicator('RSI', self.data.Close, period=14)

        def next(self):
            """Generate trading signals."""
            if self.rsi[-1] < 30 and self.data.Close[-1] > self.sma[-1]:
                self.buy()
            elif self.rsi[-1] > 70:
                self.sell()

2. Risk Management
~~~~~~~~~~~~~~~~

Learn how to add risk management to your strategies:

.. code-block:: python

    def next(self):
        # Position sizing based on ATR
        atr = self.atr[-1]
        risk_amount = self.portfolio_value * 0.02  # 2% risk
        position_size = risk_amount / atr

        if self.entry_signal():
            self.buy(size=position_size,
                    sl=self.data.Close[-1] - 2*atr)

3. Multi-Asset Trading
~~~~~~~~~~~~~~~~~~~~

Example of trading multiple assets:

.. code-block:: python

    class MultiAssetStrategy(StrategyBase):
        def next(self):
            for symbol in self.data.keys():
                price = self.data[symbol].Close[-1]
                sma = self.indicators[symbol]['sma'][-1]

                if price > sma:
                    self.buy(symbol)
                else:
                    self.sell(symbol)
