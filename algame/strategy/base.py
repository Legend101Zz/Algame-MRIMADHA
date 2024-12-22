from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
import pandas as pd
import numpy as np
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

@dataclass
class Order:
    """Trading order details."""
    type: str  # 'buy' or 'sell'
    size: float
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    time: Optional[datetime] = None
    status: str = 'pending'  # pending, filled, cancelled
    id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Trade:
    """Completed trade details."""
    entry_time: datetime
    entry_price: float
    size: float
    type: str  # 'long' or 'short'
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    pnl: float = 0.0
    fees: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration(self) -> Optional[float]:
        """Get trade duration in days."""
        if self.exit_time and self.entry_time:
            return (self.exit_time - self.entry_time).total_seconds() / 86400
        return None

    @property
    def return_pct(self) -> Optional[float]:
        """Get trade return percentage."""
        if self.exit_price and self.entry_price:
            return ((self.exit_price - self.entry_price) / self.entry_price) * 100
        return None

class Position:
    """Position management."""

    def __init__(self):
        """Initialize position."""
        self.size: float = 0.0  # Current position size
        self.entry_price: Optional[float] = None  # Average entry price
        self.last_update: Optional[datetime] = None
        self.stop_loss: Optional[float] = None
        self.take_profit: Optional[float] = None
        self.orders: List[Order] = []  # Pending orders
        self.trades: List[Trade] = []  # Completed trades
        self.pnl: float = 0.0  # Realized P&L
        self.fees: float = 0.0  # Total fees

    @property
    def is_long(self) -> bool:
        """Check if position is long."""
        return self.size > 0

    @property
    def is_short(self) -> bool:
        """Check if position is short."""
        return self.size < 0

    @property
    def is_open(self) -> bool:
        """Check if position is open."""
        return self.size != 0

    def add_order(self, order: Order) -> None:
        """Add new order."""
        self.orders.append(order)

    def update(self, current_price: float, current_time: datetime) -> None:
        """Update position state."""
        # Update last price
        self._current_price = current_price
        self.last_update = current_time

        # Check stops
        if self.should_stop_out(current_price):
            self.close(current_price, current_time)

    def should_stop_out(self, price: float) -> bool:
        """Check if position should be stopped out."""
        if not self.is_open:
            return False

        if self.stop_loss:
            if self.is_long and price <= self.stop_loss:
                return True
            if self.is_short and price >= self.stop_loss:
                return True

        if self.take_profit:
            if self.is_long and price >= self.take_profit:
                return True
            if self.is_short and price <= self.take_profit:
                return True

        return False

    def close(self, price: float, time: datetime) -> None:
        """Close position."""
        if not self.is_open:
            return

        # Create trade record
        trade = Trade(
            entry_time=self.entry_time,
            entry_price=self.entry_price,
            exit_time=time,
            exit_price=price,
            size=abs(self.size),
            type='long' if self.is_long else 'short',
            pnl=self._calculate_pnl(price),
            fees=self.fees
        )
        self.trades.append(trade)

        # Update p&l
        self.pnl += trade.pnl

        # Reset position
        self.size = 0
        self.entry_price = None
        self.stop_loss = None
        self.take_profit = None
        self.fees = 0

    def _calculate_pnl(self, exit_price: float) -> float:
        """Calculate trade P&L."""
        if not self.entry_price:
            return 0.0
        price_diff = exit_price - self.entry_price
        return price_diff * self.size

class StrategyState:
    """Strategy state container."""

    def __init__(self):
        self.position = Position()
        self.equity = []  # Equity curve
        self.trades = []  # Completed trades
        self.indicators = {}  # Technical indicators
        self._data = None  # Market data reference
        self._last_update = None  # Last update time

    @property
    def data(self):
        """Get market data."""
        return self._data

    @data.setter
    def data(self, value):
        """Set market data."""
        self._data = value
        self._on_data_update()

    def _on_data_update(self):
        """Handle data updates."""
        if not self._data:
            return

        # Update indicators
        for ind in self.indicators.values():
            ind.update(self._data)

        # Update last time
        if len(self._data) > 0:
            self._last_update = self._data.index[-1]

class StrategyBase(ABC):
    """Base class for trading strategies."""

    def __init__(self, parameters: Optional[Dict[str, Any]] = None):
        """Initialize strategy."""
        # Initialize state
        self.state = StrategyState()

        # Store parameters
        self.parameters = parameters or {}

        # Initialize metadata
        self.name = self.__class__.__name__
        self.version = "1.0.0"
        self.author = ""
        self._initialized = False

    @abstractmethod
    def initialize(self) -> None:
        """Initialize strategy."""
        pass

    @abstractmethod
    def next(self) -> None:
        """Process next market update."""
        pass

    def set_data(self, data: pd.DataFrame) -> None:
        """Set market data."""
        self.state.data = data
        if not self._initialized:
            self.initialize()
            self._initialized = True

    def buy(self, size: float = 1.0, **kwargs) -> Order:
        """Place buy order."""
        order = Order(
            type='buy',
            size=size,
            stop_loss=kwargs.get('sl'),
            take_profit=kwargs.get('tp'),
            time=self.state._last_update
        )
        self.state.position.add_order(order)
        return order

    def sell(self, size: float = 1.0, **kwargs) -> Order:
        """Place sell order."""
        order = Order(
            type='sell',
            size=size,
            stop_loss=kwargs.get('sl'),
            take_profit=kwargs.get('tp'),
            time=self.state._last_update
        )
        self.state.position.add_order(order)
        return order

    def close(self) -> None:
        """Close current position."""
        if self.state.position.is_open:
            self.state.position.close(
                self.state.data['Close'][-1],
                self.state._last_update
            )

    # Indicator management
    def add_indicator(self, name: str, indicator: Any, *args, **kwargs) -> Any:
        """Add technical indicator."""
        # Create indicator instance if needed
        if isinstance(indicator, type):
            indicator = indicator(*args, **kwargs)

        # Calculate indicator
        values = indicator.calculate(self.state.data)

        # Store instance and values
        self.state.indicators[name] = {
            'instance': indicator,
            'values': values
        }

        return values

    def get_parameters(self) -> Dict[str, Any]:
        """Get strategy parameters."""
        return self.parameters

    def set_parameters(self, parameters: Dict[str, Any]) -> None:
        """Set strategy parameters."""
        self.parameters = parameters

    def validate_parameters(self) -> bool:
        """Validate strategy parameters."""
        # Override to add validation
        return True

    @classmethod
    def get_parameter_info(cls) -> Dict[str, Dict[str, Any]]:
        """Get parameter metadata."""
        return {}

# Example usage
# class SimpleStrategy(StrategyBase):
#     def initialize(self):
#         # Add 20-period SMA
#         self.sma = self.add_indicator('SMA', SMA, period=20)

#     def next(self):
#         if not self.state.position.is_open:
#             # Buy if price crosses above SMA
#             if self.state.data['Close'][-1] > self.sma[-1]:
#                 self.buy()
#         else:
#             # Sell if price crosses below SMA
#             if self.state.data['Close'][-1] < self.sma[-1]:
#                 self.sell()
