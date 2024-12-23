Installation Guide
================

Basic Installation
----------------

You can install Algame using pip:

.. code-block:: bash

    pip install algame-mrimadha

Development Installation
----------------------

For development setup:

.. code-block:: bash

    git clone https://github.com/Legend101Zz/Algame-MRIMADHA.git
    cd Algame-MRIMADHA
    pip install -e ".[dev]"

Dependencies
-----------

Core Dependencies:
    - Python >= 3.8
    - numpy
    - pandas
    - matplotlib
    - backtesting
    - yfinance

Optional Dependencies:
    For machine learning features:
        .. code-block:: bash

            pip install algame-mrimadha[ml]

    For development:
        .. code-block:: bash

            pip install algame-mrimadha[dev]
