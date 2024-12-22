"""
Interactive charting component.

This module provides an interactive financial chart with:
1. Multiple chart types (candlestick, line, etc.)
2. Technical indicators
3. Drawing tools
4. Trade visualization
5. Real-time updates

The chart is built using HTML5 canvas for performance and
supports multiple time frames and data sources.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Chart(ttk.Frame):
    """
    Interactive financial chart.

    Features:
    - Multiple chart types
    - Technical indicators
    - Drawing tools
    - Trade markers
    - Real-time updates

    The chart uses a layered canvas approach:
    1. Base layer for price data
    2. Indicator layer
    3. Drawing layer
    4. Overlay layer for trades/markers

    Attributes:
        data: Chart data (OHLCV)
        indicators: Active indicators
        drawings: User drawings
        trades: Trade markers
    """

    def __init__(self,
                master,
                data: Optional[pd.DataFrame] = None,
                **kwargs):
        """
        Initialize chart.

        Args:
            master: Parent widget
            data: Initial OHLCV data
            **kwargs: Additional config
        """
        super().__init__(master)

        # Store data
        self.data = data
        self.indicators: Dict[str, Any] = {}
        self.drawings: List[Dict] = []
        self.trades: List[Dict] = []

        # Chart state
        self.selected_tool = None
        self.zoom_level = 1.0
        self.scroll_pos = 0

        # Create widgets
        self._create_widgets()
        self._create_toolbar()

        # Initial draw
        if data is not None:
            self.draw()

    def _create_widgets(self):
        """Create chart widgets."""
        # Main frame
        self.frame = ttk.Frame(self)
        self.frame.pack(fill='both', expand=True)

        # Create canvas layers
        self.price_canvas = tk.Canvas(
            self.frame,
            bg='white',
            highlightthickness=0
        )
        self.price_canvas.pack(fill='both', expand=True)

        self.indicator_canvas = tk.Canvas(
            self.frame,
            bg='transparent',
            highlightthickness=0
        )
        self.indicator_canvas.pack(fill='both', expand=True)

        self.drawing_canvas = tk.Canvas(
            self.frame,
            bg='transparent',
            highlightthickness=0
        )
        self.drawing_canvas.pack(fill='both', expand=True)

        self.overlay_canvas = tk.Canvas(
            self.frame,
            bg='transparent',
            highlightthickness=0
        )
        self.overlay_canvas.pack(fill='both', expand=True)

        # Scrollbar
        self.scrollbar = ttk.Scrollbar(
            self.frame,
            orient='horizontal',
            command=self._on_scroll
        )
        self.scrollbar.pack(fill='x')

        # Bind events
        self._bind_events()

    def _create_toolbar(self):
        """Create chart toolbar."""
        self.toolbar = ttk.Frame(self)
        self.toolbar.pack(fill='x')

        # Chart type selection
        self.chart_type = ttk.Combobox(
            self.toolbar,
            values=['Candlestick', 'OHLC', 'Line'],
            state='readonly',
            width=15
        )
        self.chart_type.set('Candlestick')
        self.chart_type.pack(side='left', padx=5)

        # Timeframe selection
        self.timeframe = ttk.Combobox(
            self.toolbar,
            values=['1m', '5m', '15m', '1h', '4h', '1d'],
            state='readonly',
            width=10
        )
        self.timeframe.set('1d')
        self.timeframe.pack(side='left', padx=5)

        # Drawing tools
        tools = ['Crosshair', 'Line', 'Rectangle', 'Text']
        self.tool_var = tk.StringVar(value='Crosshair')

        for tool in tools:
            ttk.Radiobutton(
                self.toolbar,
                text=tool,
                value=tool,
                variable=self.tool_var,
                command=self._on_tool_change
            ).pack(side='left', padx=2)

        # View controls
        ttk.Button(
            self.toolbar,
            text="Zoom In",
            command=self.zoom_in
        ).pack(side='right', padx=2)

        ttk.Button(
            self.toolbar,
            text="Zoom Out",
            command=self.zoom_out
        ).pack(side='right', padx=2)

        ttk.Button(
            self.toolbar,
            text="Reset",
            command=self.reset_view
        ).pack(side='right', padx=2)

    def _bind_events(self):
        """Bind canvas events."""
        # Mouse events
        self.drawing_canvas.bind('<Button-1>', self._on_click)
        self.drawing_canvas.bind('<B1-Motion>', self._on_drag)
        self.drawing_canvas.bind('<ButtonRelease-1>', self._on_release)

        # Mouse wheel for zooming
        self.drawing_canvas.bind('<MouseWheel>', self._on_mousewheel)

        # Keyboard shortcuts
        self.drawing_canvas.bind('<Delete>', self._delete_selected)

        # Window resize
        self.frame.bind('<Configure>', self._on_resize)

    def set_data(self,
                data: pd.DataFrame,
                redraw: bool = True):
        """
        Set chart data.

        Args:
            data: OHLCV data
            redraw: Whether to redraw chart
        """
        self.data = data
        if redraw:
            self.draw()

    def add_indicator(self,
                     name: str,
                     indicator: Any,
                     params: Dict[str, Any] = None):
        """
        Add technical indicator.

        Args:
            name: Indicator name
            indicator: Indicator instance
            params: Indicator parameters
        """
        self.indicators[name] = {
            'indicator': indicator,
            'params': params or {}
        }
        self.draw()

    def remove_indicator(self, name: str):
        """Remove indicator by name."""
        if name in self.indicators:
            del self.indicators[name]
            self.draw()

    def add_trade(self,
                 time: datetime,
                 price: float,
                 type: str,
                 size: float):
        """
        Add trade marker.

        Args:
            time: Trade time
            price: Trade price
            type: Trade type ('buy' or 'sell')
            size: Trade size
        """
        self.trades.append({
            'time': time,
            'price': price,
            'type': type,
            'size': size
        })
        self._draw_trades()

    def clear_trades(self):
        """Clear all trade markers."""
        self.trades.clear()
        self.overlay_canvas.delete('trade')

    def add_drawing(self, drawing: Dict[str, Any]):
        """
        Add drawing object.

        Args:
            drawing: Drawing specifications
        """
        self.drawings.append(drawing)
        self._draw_drawings()

    def clear_drawings(self):
        """Clear all drawings."""
        self.drawings.clear()
        self.drawing_canvas.delete('drawing')

    def zoom_in(self):
        """Zoom in chart."""
        self.zoom_level *= 1.2
        self.draw()

    def zoom_out(self):
        """Zoom out chart."""
        self.zoom_level /= 1.2
        self.draw()

    def reset_view(self):
        """Reset chart view."""
        self.zoom_level = 1.0
        self.scroll_pos = 0
        self.draw()

    def draw(self):
        """Draw complete chart."""
        if self.data is None:
            return

        self._draw_price()
        self._draw_indicators()
        self._draw_drawings()
        self._draw_trades()

    def _draw_price(self):
        """Draw price data layer."""
        # Clear canvas
        self.price_canvas.delete('all')

        # Get visible data range
        start = int(self.scroll_pos)
        end = min(
            len(self.data),
            start + int(self.price_canvas.winfo_width() / (10 * self.zoom_level))
        )

        data = self.data.iloc[start:end]

        # Calculate scaling
        price_range = data['High'].max() - data['Low'].min()
        height = self.price_canvas.winfo_height()
        scale = height / price_range

        # Draw based on chart type
        chart_type = self.chart_type.get()

        if chart_type == 'Candlestick':
            self._draw_candlesticks(data, scale)
        elif chart_type == 'OHLC':
            self._draw_ohlc(data, scale)
        else:  # Line chart
            self._draw_line(data, scale)

    def _draw_candlesticks(self,
                          data: pd.DataFrame,
                          scale: float):
        """
        Draw candlestick chart.

        Args:
            data: Price data to draw
            scale: Price scaling factor
        """
        width = 8 * self.zoom_level

        for i, (idx, row) in enumerate(data.iterrows()):
            x = i * (width + 2)

            # Calculate y-coordinates
            open_y = self._price_to_y(row['Open'], scale)
            close_y = self._price_to_y(row['Close'], scale)
            high_y = self._price_to_y(row['High'], scale)
            low_y = self._price_to_y(row['Low'], scale)

            # Draw candlestick
            color = 'green' if row['Close'] >= row['Open'] else 'red'

            # Draw wick
            self.price_canvas.create_line(
                x + width/2, high_y,
                x + width/2, low_y,
                fill=color,
                tags='candle'
            )

            # Draw body
            self.price_canvas.create_rectangle(
                x, open_y,
                x + width, close_y,
                fill=color,
                outline=color,
                tags='candle'
            )

    def _draw_ohlc(self,
                   data: pd.DataFrame,
                   scale: float):
        """
        Draw OHLC bars.

        Args:
            data: Price data to draw
            scale: Price scaling factor
        """
        width = 8 * self.zoom_level

        for i, (idx, row) in enumerate(data.iterrows()):
            x = i * (width + 2)

            # Calculate y-coordinates
            open_y = self._price_to_y(row['Open'], scale)
            close_y = self._price_to_y(row['Close'], scale)
            high_y = self._price_to_y(row['High'], scale)
            low_y = self._price_to_y(row['Low'], scale)

            # Draw OHLC bar
            color = 'green' if row['Close'] >= row['Open'] else 'red'

            # Vertical line
            self.price_canvas.create_line(
                x + width/2, high_y,
                x + width/2, low_y,
                fill=color,
                tags='ohlc'
            )

            # Open tick
            self.price_canvas.create_line(
                x, open_y,
                x + width/2, open_y,
                fill=color,
                tags='ohlc'
            )

            # Close tick
            self.price_canvas.create_line(
                x + width/2, close_y,
                x + width, close_y,
                fill=color,
                tags='ohlc'
            )

    def _draw_line(self,
                   data: pd.DataFrame,
                   scale: float):
        """
        Draw line chart.

        Args:
            data: Price data to draw
            scale: Price scaling factor
        """
        points = []
        width = 8 * self.zoom_level

        for i, (idx, row) in enumerate(data.iterrows()):
            x = i * (width + 2)
            y = self._price_to_y(row['Close'], scale)
            points.extend([x + width/2, y])

        if len(points) > 2:
            self.price_canvas.create_line(
                points,
                fill='blue',
                smooth=True,
                tags='line'
            )

    def _draw_indicators(self):
        """Draw technical indicators."""
        if not self.indicators:
            return

        # Clear canvas
        self.indicator_canvas.delete('all')

        # Get visible data
        start = int(self.scroll_pos)
        end = min(
            len(self.data),
            start + int(self.indicator_canvas.winfo_width() / (10 * self.zoom_level))
        )
        data = self.data.iloc[start:end]

        # Draw each indicator
        for name, ind in self.indicators.items():
            try:
                values = ind['indicator'].calculate(data)
                self._draw_indicator_values(values, ind['params'])
            except Exception as e:
                logger.error(f"Failed to draw indicator {name}: {str(e)}")

    def _draw_indicator_values(self,
                             values: np.ndarray,
                             params: Dict[str, Any]):
        """
        Draw indicator values.

        Args:
            values: Indicator values
            params: Drawing parameters
        """
        if len(values) < 2:
            return

        # Scale values to canvas
        y_scale = self.indicator_canvas.winfo_height() / (values.max() - values.min())
        points = []
        width = 8 * self.zoom_level

        for i, value in enumerate(values):
            if np.isnan(value):
                continue

            x = i * (width + 2)
            y = self._value_to_y(value, y_scale)
            points.extend([x + width/2, y])

        if len(points) > 2:
            self.indicator_canvas.create_line(
                points,
                fill=params.get('color', 'blue'),
                width=params.get('width', 1),
                smooth=params.get('smooth', True),
                tags='indicator'
            )

    def _draw_drawings(self):
        """Draw user drawings."""
        # Clear canvas
        self.drawing_canvas.delete('all')

        # Draw each object
        for drawing in self.drawings:
            self._draw_object(drawing)

    def _draw_object(self, drawing: Dict[str, Any]):
        """
        Draw single drawing object.

        Args:
            drawing: Drawing specifications
        """
        type = drawing['type']
        color = drawing.get('color', 'black')
        width = drawing.get('width', 1)

        if type == 'line':
            self.drawing_canvas.create_line(
                drawing['x1'], drawing['y1'],
                drawing['x2'], drawing['y2'],
                fill=color,
                width=width,
                tags='drawing'
            )

        elif type == 'rectangle':
            self.drawing_canvas.create_rectangle(
                drawing['x1'], drawing['y1'],
                drawing['x2'], drawing['y2'],
                outline=color,
                width=width,
                tags='drawing'
            )

        elif type == 'text':
            self.drawing_canvas.create_text(
                drawing['x'], drawing['y'],
                text=drawing['text'],
                fill=color,
                font=drawing.get('font', 'Arial 10'),
                tags='drawing'
            )

    def _draw_trades(self):
        """Draw trade markers."""
        # Clear canvas
        self.overlay_canvas.delete('trade')

        # Draw each trade
        width = 8 * self.zoom_level
        for trade in self.trades:
            x = self._time_to_x(trade['time'])
            y = self._price_to_y(trade['price'])

            # Draw marker
            if trade['type'] == 'buy':
                self._draw_buy_marker(x, y)
            else:
                self._draw_sell_marker(x, y)

    def _draw_buy_marker(self, x: float, y: float):
        """Draw buy trade marker (triangle)."""
        size = 6 * self.zoom_level
        points = [
            x, y - size,
            x - size, y + size,
            x + size, y + size
        ]

        self.overlay_canvas.create_polygon(
            points,
            fill='green',
            outline='darkgreen',
            tags='trade'
        )

    def _draw_sell_marker(self, x: float, y: float):
        """Draw sell trade marker (inverted triangle)."""
        size = 6 * self.zoom_level
        points = [
            x, y + size,
            x - size, y - size,
            x + size, y - size
        ]

        self.overlay_canvas.create_polygon(
            points,
            fill='red',
            outline='darkred',
            tags='trade'
        )

    def _price_to_y(self, price: float, scale: Optional[float] = None) -> float:
        """Convert price to y-coordinate."""
        if scale is None:
            price_range = self.data['High'].max() - self.data['Low'].min()
            scale = self.price_canvas.winfo_height() / price_range

        return self.price_canvas.winfo_height() - (price - self.data['Low'].min()) * scale

    def _value_to_y(self, value: float, scale: float) -> float:
        """Convert indicator value to y-coordinate."""
        return self.indicator_canvas.winfo_height() - value * scale

    def _time_to_x(self, time: datetime) -> float:
        """Convert time to x-coordinate."""
        index = self.data.index.get_loc(time)
        width = 8 * self.zoom_level
        return (index - self.scroll_pos) * (width + 2) + width/2

    def _x_to_time(self, x: float) -> datetime:
        """Convert x-coordinate to time."""
        width = 8 * self.zoom_level
        index = int(self.scroll_pos + x / (width + 2))
        return self.data.index[index]

    def _on_click(self, event):
        """Handle mouse click."""
        self.start_x = event.x
        self.start_y = event.y

        # Start drawing if tool selected
        if self.selected_tool:
            self.current_drawing = {
                'type': self.selected_tool,
                'x1': event.x,
                'y1': event.y
            }

    def _on_drag(self, event):
        """Handle mouse drag."""
        if not hasattr(self, 'start_x'):
            return

        # Update crosshair
        self._update_crosshair(event)

        # Update current drawing
        if self.current_drawing:
            self.current_drawing.update({
                'x2': event.x,
                'y2': event.y
            })
            self._draw_object(self.current_drawing)

    def _on_release(self, event):
        """Handle mouse release."""
        if self.current_drawing:
            # Finish drawing
            self.drawings.append(self.current_drawing)
            self.current_drawing = None

        delattr(self, 'start_x')
        delattr(self, 'start_y')

    def _on_mousewheel(self, event):
        """Handle mouse wheel."""
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def _on_scroll(self, *args):
        """Handle scrollbar."""
        self.scroll_pos = float(args[1])
        self.draw()

    def _on_resize(self, event):
        """Handle window resize."""
        self.draw()

    def _on_tool_change(self):
        """Handle drawing tool change."""
        self.selected_tool = self.tool_var.get()

    def _update_crosshair(self, event):
        """Update crosshair position."""
        self.overlay_canvas.delete('crosshair')

        self.overlay_canvas.create_line(
            0, event.y,
            self.overlay_canvas.winfo_width(), event.y,
            dash=(2,2),
            tags='crosshair'
        )

        self.overlay_canvas.create_line(
            event.x, 0,
            event.x, self.overlay_canvas.winfo_height(),
            dash=(2,2),
            tags='crosshair'
        )

    def _delete_selected(self, event):
        """Delete selected drawing."""
        # TODO: Implement selection and deletion
