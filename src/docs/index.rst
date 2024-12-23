Welcome to Algame's documentation!
================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   quickstart
   userguide/index
   api/index
   contributing
   changelog

Installation
-----------
.. code-block:: bash

   pip install algame-mrimadha

Quick Start
----------
.. code-block:: python

   from algame.core import core
   from algame.strategy import StrategyBase

   # Create and run a simple strategy
   class MyStrategy(StrategyBase):
       def initialize(self):
           self.sma = self.add_indicator('SMA', self.data.Close, period=20)

       def next(self):
           if self.data.Close[-1] > self.sma[-1]:
               self.buy()
           else:
               self.sell()

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
