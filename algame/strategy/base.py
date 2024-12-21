from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union, Any
import pandas as pd
import numpy as np
from datetime import datetime
import logging

from ..core.data import MarketData
from ..core.config import StrategyConfig

logger = logging.getLogger(__name__)

class StrategyBase(ABC):
    """
    Base class for all trading strategies.

    This abstract class defines the interface and core functionality that
    all strategies must implement. It provides:

    1. Strategy Lifecycle:
        - Initialization
        - Data updates
        - Signal generation
        - Position management

    2. Data Management:
        - Historical data access
        - Indicator calculation
        - Data validation

    3. Trading Interface:
        - Order management
        - Position tracking
        - Risk management

    4. Analysis:
        - Performance metrics
        - Trade statistics
        - Risk analytics

    The strategy framework follows several design principles:

    1. Separation of Concerns:
        - Trading logic separate from execution
        - Data management separate from analysis
        - Configuration separate from implementation

    2. Flexibility:
        - Support multiple assets
        - Support multiple timeframes
        - Support multiple order types

    3. Safety:
        - Type checking
        - Data validation
        - Position validation

    Usage:
        class MyStrategy(StrategyBase):
            def initialize(self):
                # Setup indicators
                self.sma = self.add_indicator('SMA', self.data.Close, 20)

            def next(self):
                # Generate signals
                if self.data.Close[-1] > self.sma[-1]:
                    self.buy()
    """

    def __init__(self, config: Optional[Union[Dict, StrategyConfig]] = None):
        """
        Initialize strategy.

        Args:
            config: Strategy configuration or parameters
        """
        # Convert dict config to StrategyConfig
        self.config = (StrategyConfig(**config) if isinstance(config, dict)
                      else config or StrategyConfig(name="Default"))

        # Initialize components
        self.data: Optional[MarketData] = None
        self.position = Position()
        self.indicators: Dict[str, Any] = {}
        self.trades: List[Trade] = []

        # State tracking
        self._initialized = False
        self._current_time: Optional[datetime] = None

        logger.debug(f"Initialized strategy: {self.config.name}")

    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize strategy.

        This method is called once before backtesting starts.
        Use it to:
        - Set up indicators
        - Initialize strategy variables
        - Validate data and parameters
        """
        pass

    @abstractmethod
    def next(self) -> None:
        """
        Process next market update.

        This method is called for each new market update.
        Use it to:
        - Generate trading signals
        - Manage positions
        - Update indicators
        """
        pass

    def set_data(self, data: MarketData) -> None:
        """
        Set market data.

        Args:
            data: Market data container
        """
        self.data = data
        if not self._initialized:
            self.initialize()
            self._initialized = True

    def add_indicator(self,
                     name: str,
                     func: callable,
                     *args,
                     **kwargs) -> np.ndarray:
        """
        Add technical indicator.

        Args:
            name: Indicator name
            func: Indicator calculation function
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            np.ndarray: Indicator values
        """
        # Calculate indicator
        values = func(*args, **kwargs)

        # Store indicator
        self.indicators[name] = values

        return values

    def buy(self,
           size: Optional[float] = None,
           limit: Optional[float] = None,
           stop: Optional[float] = None,
           sl: Optional[float] = None,
           tp: Optional[float] = None) -> Order:
        """
        Place buy order.

        Args:
            size: Position size (or None for full size)
            limit: Limit price
            stop: Stop price
            sl: Stop loss price
            tp: Take profit price

        Returns:
            Order: Created order
        """
        # Validate inputs
        if size is not None and size <= 0:
            raise ValueError("Size must be positive")

        # Use default size
        if size is None:
            size = 1.0  # Full position size

        # Create order
        order = Order(
            type='buy',
            size=size,
            limit=limit,
            stop=stop,
            sl=sl,
            tp=tp
        )

        # Add to position
        self.position.add_order(order)

        logger.debug(f"Created buy order: {order}")
        return order

    def sell(self,
            size: Optional[float] = None,
            limit: Optional[float] = None,
            stop: Optional[float] = None,
            sl: Optional[float] = None,
            tp: Optional[float] = None) -> Order:
        """
        Place sell order.

        Args:
            size: Position size (or None for full size)
            limit: Limit price
            stop: Stop price
            sl: Stop loss price
            tp: Take profit price

        Returns:
            Order: Created order
        """
        # Validate inputs
        if size is not None and size <= 0:
            raise ValueError("Size must be positive")

        # Use default size
        if size is None:
            size = 1.0  # Full position size

        # Create order
        order = Order(
            type='sell',
            size=size,
            limit=limit,
            stop=stop,
            sl=sl,
            tp=tp
        )

        # Add to position
        self.position.add_order(order)

        logger.debug(f"Created sell order: {order}")
        return order

    def close(self,
             size: Optional[float] = None,
             limit: Optional[float] = None,
             stop: Optional[float] = None) -> Order:
        """
        Close position.

        Args:
            size: Position size to close (None for full)
            limit: Limit price
            stop: Stop price

        Returns:
            Order: Created order
        """
        # Check position
        if not self.position.is_open:
            return None

        # Use remaining size
        if size is None:
            size = abs(self.position.size)

        # Create opposite order
        if self.position.is_long:
            return self.sell(size, limit, stop)
        else:
            return self.buy(size, limit, stop)

    def cancel_orders(self) -> None:
        """Cancel all pending orders."""
        self.position.cancel_orders()

    @property
    def is_initialized(self) -> bool:
        """Check if strategy is initialized."""
        return self._initialized

    def get_parameters(self) -> Dict[str, Any]:
        """Get strategy parameters."""
        return self.config.parameters

    def set_parameters(self, parameters: Dict[str, Any]) -> None:
        """Set strategy parameters."""
        self.config.parameters.update(parameters)

    def validate_parameters(self) -> bool:
        """
        Validate strategy parameters.

        Returns:
            bool: True if parameters are valid

        Raises:
            ValueError: If parameters are invalid
        """
        return True

class Position:
    """
    Position management.

    Handles:
    - Position tracking
    - Order management
    - Risk calculation
    """

    def __init__(self):
        """Initialize position."""
        self.size = 0.0
        self.orders: List[Order] = []
        self.trades: List[Trade] = []

    @property
    def is_open(self) -> bool:
        """Check if position is open."""
        return self.size != 0

    @property
    def is_long(self) -> bool:
        """Check if position is long."""
        return self.size > 0

    @property
    def is_short(self) -> bool:
        """Check if position is short."""
        return self.size < 0

    def add_order(self, order: Order) -> None:
        """Add order to position."""
        self.orders.append(order)

    def cancel_orders(self) -> None:
        """Cancel all pending orders."""
        self.orders = []

    def update(self, price: float) -> None:
        """
        Update position with new price.

        Args:
            price: Current price
        """
        # Process orders
        for order in self.orders[:]:
            if order.is_triggered(price):
                self._process_order(order, price)
                self.orders.remove(order)

    def _process_order(self, order: Order, price: float) -> None:
        """
        Process executed order.

        Args:
            order: Executed order
            price: Execution price
        """
        # Update size
        if order.type == 'buy':
            self.size += order.size
        else:
            self.size -= order.size

        # Create trade
        trade = Trade(
            type=order.type,
            size=order.size,
            entry_price=price,
            entry_time=datetime.now()
        )
        self.trades.append(trade)

class Order:
    """
    Trading order.

    Represents:
    - Order type (market, limit, stop)
    - Order parameters (size, price)
    - Order status (pending, filled, cancelled)
    """

    def __init__(self,
                type: str,
                size: float,
                limit: Optional[float] = None,
                stop: Optional[float] = None,
                sl: Optional[float] = None,
                tp: Optional[float] = None):
        """
        Initialize order.

        Args:
            type: Order type ('buy' or 'sell')
            size: Order size
            limit: Limit price
            stop: Stop price
            sl: Stop loss price
            tp: Take profit price
        """
        self.type = type
        self.size = size
        self.limit = limit
        self.stop = stop
        self.sl = sl
        self.tp = tp

        self.status = 'pending'
        self.filled_price = None
        self.filled_time = None

    def is_triggered(self, price: float) -> bool:
        """
        Check if order is triggered.

        Args:
            price: Current price

        Returns:
            bool: True if order should execute
        """
        if self.status != 'pending':
            return False

        if self.type == 'buy':
            # Buy stop
            if self.stop and price >= self.stop:
                return True
            # Buy limit
            if self.limit and price <= self.limit:
                return True

        else:  # sell
            # Sell stop
            if self.stop and price <= self.stop:
                return True
            # Sell limit
            if self.limit and price >= self.limit:
                return True

        return False

class Trade:
    """
    Completed trade.

    Contains:
    - Trade details (type, size, prices)
    - Trade times (entry, exit)
    - Trade metrics (pnl, return)
    """

    def __init__(self,
                type: str,
                size: float,
                entry_price: float,
                entry_time: datetime):
        """
        Initialize trade.

        Args:
            type: Trade type ('buy' or 'sell')
            size: Trade size
            entry_price: Entry price
            entry_time: Entry time
        """
        self.type = type
        self.size = size
        self.entry_price = entry_price
        self.entry_time = entry_time

        self.exit_price = None
        self.exit_time = None

    @property
    def is_closed(self) -> bool:
        """Check if trade is closed."""
        return self.exit_price is not None

    @property
    def pnl(self) -> Optional[float]:
        """Get trade profit/loss."""
        if not self.is_closed:
            return None

        if self.type == 'buy':
            return (self.exit_price - self.entry_price) * self.size
        else:
            return (self.entry_price - self.exit_price) * self.size

    @property
    def return_pct(self) -> Optional[float]:
        """Get trade return percentage."""
        if not self.is_closed:
            return None

        return self.pnl / (self.entry_price * self.size)

# Export classes
__all__ = ['StrategyBase', 'Position', 'Order', 'Trade']
