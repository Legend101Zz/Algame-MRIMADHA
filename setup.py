from setuptools import setup, find_packages

setup(
    name="algame-MRIMADHA",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.21.0",
        "pandas>=1.3.0",
        "backtesting>=0.3.3",
        "matplotlib>=3.4.0",
        "PyYAML>=5.4.1",
        "tkinter",  # Usually comes with Python
        "yfinance>=0.1.63",
    ],
    extras_require={
        'dev': [
            'pytest>=6.0',
            'pytest-cov>=2.0',
            'flake8>=3.9.0',
            'black>=21.5b2',
            'mypy>=0.910',
        ],
    },
    author="Mrigesh Thakur, Dharuva Thakur, Maanas Sood",
    author_email="mrigeshthakur11@gmail.com",
    description="algame is a powerful, modular backtesting framework for algorithmic trading. Easily test multiple strategies across assets and timeframes, visualize results with a TradingView-like GUI, and integrate custom data or engines. Flexible, user-friendly, and future-ready.",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Legend101Zz/Algame-MRIMADHA",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
)
