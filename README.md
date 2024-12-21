# algame-MRIMADHA

**Backtesting made simple, scalable, and seamless.**

`algame-MRIMADHA` or `algame` (for short) is a powerful, modular, and user-friendly backtesting framework designed for algorithmic trading. With its built-in flexibility, it empowers both technical and non-technical users to easily test multiple strategies across assets and timeframes. The framework offers a TradingView-like GUI for visualization and supports custom data sources and engines for maximum adaptability.

---

## Key Features

- **Multi-Asset and Multi-Strategy Backtesting**: Seamlessly backtest multiple strategies across multiple assets and timeframes simultaneously.
- **Customizable GUI**: Drag and drop indicators, analyze asset charts, and configure backtests with ease.
- **Flexible Architecture**: Integrate custom data sources and engines or use the default engine. Switch between `algame`'s engine and `backtesting.py` effortlessly.
- **Pine Script Converter**: Convert TradingView strategies into `algame`-compatible or `backtesting.py` formats.
- **Future-Ready Design**: Built to expand without fundamental changes, enabling new features to integrate seamlessly.
- **Optimized for Non-Technical Users**: Export configurations for consistent testing across assets, strategies, and data.

---

## Installation

```bash
pip install algame
```

For development:

```bash
pip install algame[dev]
```

---

## Getting Started

### Basic Backtesting Example

```python
from algame import BacktestEngine

# Initialize the engine
engine = BacktestEngine()

# Load your strategy and data
engine.load_strategy("my_strategy.py")
engine.load_data("BTC-USD", timeframe="1h")

# Run the backtest
results = engine.run()

# Visualize results
engine.visualize()
```

### GUI Usage
Launch the GUI to configure and visualize backtests:

```bash
algame-gui
```

---

## Documentation
Comprehensive documentation is available at [Documentation](https://github.com/yourusername/algame/wiki).

---

## Contributing

We welcome contributions! To get started:

1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Submit a pull request with a detailed description of your changes.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Authors

`algame` is developed and maintained by:

- Mrigesh Thakur ([mrigeshthakur11@gmail.com])
- Dharuva Thakur ([21bma016@nith.ac.in])
- Maanas Sood ([21bma013@nith.ac.in])

---

## Acknowledgments

Special thanks to the open-source community and tools like `backtesting.py`, `yfinance`, and `matplotlib` for making this project possible.
