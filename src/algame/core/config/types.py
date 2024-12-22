from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union, Any
from pathlib import Path
import datetime as dt

@dataclass
class EngineConfig:
    """
    Configuration for backtesting engine.

    This class defines all settings related to the backtesting engine behavior:
    - Trading parameters (commission, slippage)
    - Risk management rules
    - Position sizing
    - Data handling preferences

    Having all settings in one place makes it easy to:
    1. Save/load different configurations
    2. Share settings between components
    3. Validate settings as a group
    4. Track setting changes
    """
    # Basic settings
    initial_capital: float = 100000.0
    commission: float = 0.001  # 0.1%
    slippage: float = 0.0001  # 0.01%

    # Trading rules
    max_position_size: float = 1.0  # Max size as % of capital
    max_leverage: float = 1.0  # No leverage by default
    allow_shorting: bool = False

    # Risk management
    max_drawdown: float = 0.25  # 25% max drawdown
    risk_per_trade: float = 0.02  # 2% risk per trade
    stop_loss_atr: float = 2.0  # Stop loss in ATR units

    # Data settings
    default_timeframe: str = "1d"
    price_type: str = "close"  # close, ohlc4, etc.
    adjust_prices: bool = True  # Adjust for splits/dividends

    # Performance
    use_cache: bool = True
    parallel_assets: bool = True
    max_workers: Optional[int] = None

@dataclass
class StrategyConfig:
    """
    Configuration for trading strategy.

    Contains all settings related to strategy behavior:
    - Strategy parameters
    - Indicator settings
    - Entry/exit rules
    - Position management
    """
    name: str
    version: str = "1.0.0"
    parameters: Dict[str, Any] = field(default_factory=dict)

    # Time settings
    trading_hours: Dict[str, str] = field(default_factory=lambda: {
        "start": "09:30",
        "end": "16:00"
    })
    trading_days: List[int] = field(default_factory=lambda: [0,1,2,3,4])  # Mon-Fri

    # Trade management
    entry_rules: List[Dict] = field(default_factory=list)
    exit_rules: List[Dict] = field(default_factory=list)
    position_sizing: Dict = field(default_factory=dict)
    risk_management: Dict = field(default_factory=dict)

    # Indicators
    indicators: Dict[str, Dict] = field(default_factory=dict)

    def validate(self) -> bool:
        """Validate strategy configuration."""
        # Check required fields
        if not self.name:
            raise ValueError("Strategy name required")

        # Validate parameters
        if not isinstance(self.parameters, dict):
            raise ValueError("Parameters must be a dictionary")

        # Validate trading hours
        try:
            dt.datetime.strptime(self.trading_hours["start"], "%H:%M")
            dt.datetime.strptime(self.trading_hours["end"], "%H:%M")
        except (ValueError, KeyError):
            raise ValueError("Invalid trading hours format")

        return True

@dataclass
class BacktestConfig:
    """
    Complete backtest configuration.

    This class combines all settings needed for a backtest:
    - Engine configuration
    - Strategy settings
    - Data sources
    - Analysis preferences

    Having a single configuration object makes it easy to:
    1. Save/load complete backtest setups
    2. Share configurations between users
    3. Version control configurations
    4. Compare different setups
    """
    # Metadata
    name: str
    description: str = ""
    author: str = ""
    created_at: dt.datetime = field(default_factory=dt.datetime.now)
    version: str = "1.0.0"

    # Components
    engine: EngineConfig = field(default_factory=EngineConfig)
    strategy: StrategyConfig = field(default_factory=StrategyConfig)

    # Data settings
    symbols: List[str] = field(default_factory=list)
    start_date: dt.datetime = field(default_factory=lambda: dt.datetime(2010,1,1))
    end_date: dt.datetime = field(default_factory=dt.datetime.now)
    timeframe: str = "1d"
    data_source: str = "yahoo"

    # Analysis settings
    metrics: List[str] = field(default_factory=lambda: [
        "total_return",
        "sharpe_ratio",
        "max_drawdown",
        "win_rate"
    ])
    plots: List[str] = field(default_factory=lambda: [
        "equity_curve",
        "drawdown",
        "monthly_returns"
    ])

    def validate(self) -> bool:
        """Validate complete configuration."""
        try:
            # Validate components
            self.engine = EngineConfig(**self.engine) if isinstance(self.engine, dict) else self.engine
            self.strategy = StrategyConfig(**self.strategy) if isinstance(self.strategy, dict) else self.strategy

            # Validate strategy
            self.strategy.validate()

            # Validate dates
            if self.start_date >= self.end_date:
                raise ValueError("Start date must be before end date")

            # Validate symbols
            if not self.symbols:
                raise ValueError("At least one symbol required")

            return True

        except Exception as e:
            raise ValueError(f"Invalid configuration: {str(e)}")

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        from dataclasses import asdict
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'BacktestConfig':
        """Create from dictionary."""
        return cls(**data)
