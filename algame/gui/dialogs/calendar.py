"""
Calendar widget for date selection.

This module provides a calendar popup for date selection with:
1. Month/year navigation
2. Day selection
3. Today shortcut
4. Date validation

The calendar follows system locale settings for:
- First day of week
- Date formatting
- Month/day names
"""

import tkinter as tk
from tkinter import ttk
import calendar
from datetime import datetime, date
import locale

class Calendar(tk.Toplevel):
    """
    Calendar popup widget.

    Features:
    - Month/year navigation
    - Day selection grid
    - Today highlighting
    - Locale support

    Example:
        cal = Calendar(parent)
        if cal.result:
            print(f"Selected date: {cal.result}")
    """

    def __init__(self, parent):
        """Initialize calendar."""
        super().__init__(parent)
        self.title("Select Date")

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Initialize state
        self.result = None
        self._selection = None
        self._today = date.today()

        # Set current display date
        self._display_date = self._today

        # Create widgets
        self._create_widgets()
        self._update_calendar()

        # Position window
        self.center_window()

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # Wait for window
        self.wait_window()

    def _create_widgets(self):
        """Create calendar widgets."""
        # Main frame
        main = ttk.Frame(self, padding="5 5 5 5")
        main.pack(fill='both', expand=True)

        # Navigation frame
        nav_frame = ttk.Frame(main)
        nav_frame.pack(fill='x')

        # Previous month
        ttk.Button(
            nav_frame,
            text="<",
            width=5,
            command=self._prev_month
        ).pack(side='left')

        # Month/Year selector
        month_year = ttk.Frame(nav_frame)
        month_year.pack(side='left', expand=True)

        # Month selector
        months = list(calendar.month_name)[1:]
        self.month_var = tk.StringVar()
        ttk.Combobox(
            month_year,
            textvariable=self.month_var,
            values=months,
            state='readonly',
            width=10
        ).pack(side='left', padx=5)

        # Year selector
        current_year = date.today().year
        years = list(range(current_year - 10, current_year + 11))
        self.year_var = tk.StringVar()
        ttk.Combobox(
            month_year,
            textvariable=self.year_var,
            values=years,
            state='readonly',
            width=6
        ).pack(side='left')

        # Next month
        ttk.Button(
            nav_frame,
            text=">",
            width=5,
            command=self._next_month
        ).pack(side='right')

        # Calendar frame
        self.cal_frame = ttk.Frame(main)
        self.cal_frame.pack(fill='both', expand=True, pady=5)

        # Weekday headers
        weekdays = list(calendar.day_abbr)
        for i, day in enumerate(weekdays):
            ttk.Label(
                self.cal_frame,
                text=day,
                anchor='center',
                width=4
            ).grid(row=0, column=i, padx=1, pady=1)

        # Day buttons
        style = ttk.Style()
        style.configure(
            'Calendar.TButton',
            width=4,
            padding=0
        )

        self._day_buttons = []
        for week in range(6):
            for day in range(7):
                btn = ttk.Button(
                    self.cal_frame,
                    style='Calendar.TButton',
                    command=lambda w=week, d=day: self._select_day(w, d)
                )
                btn.grid(
                    row=week + 1,
                    column=day,
                    padx=1,
                    pady=1,
                    sticky='nsew'
                )
                self._day_buttons.append(btn)

        # Today button
        ttk.Button(
            main,
            text="Today",
            command=self._select_today
        ).pack(pady=5)

        # Bind events
        self.month_var.trace('w', lambda *args: self._update_calendar())
        self.year_var.trace('w', lambda *args: self._update_calendar())

    def _prev_month(self):
        """Go to previous month."""
        year = self._display_date.year
        month = self._display_date.month - 1

        if month < 1:
            month = 12
            year -= 1

        self._display_date = self._display_date.replace(year=year, month=month)
        self._update_calendar()

    def _next_month(self):
        """Go to next month."""
        year = self._display_date.year
        month = self._display_date.month + 1

        if month > 12:
            month = 1
            year += 1

        self._display_date = self._display_date.replace(year=year, month=month)
        self._update_calendar()

    def _select_day(self, week: int, day: int):
        """Handle day selection."""
        # Get calendar data
        cal = calendar.monthcalendar(
            self._display_date.year,
            self._display_date.month
        )

        try:
            day_num = cal[week][day]
            if day_num != 0:
                self._selection = self._display_date.replace(day=day_num)
                self._update_calendar()

                # Set result and close
                self.result = self._selection
                self.destroy()

        except IndexError:
            pass

    def _select_today(self):
        """Select today's date."""
        self._display_date = self._today
        self._selection = self._today
        self._update_calendar()

        # Set result and close
        self.result = self._selection
        self.destroy()

    def _is_today(self, day: int) -> bool:
        """Check if date is today."""
        return (self._display_date.year == self._today.year and
                self._display_date.month == self._today.month and
                day == self._today.day)

    def _is_selected(self, day: int) -> bool:
        """Check if date is selected."""
        return (self._selection and
                self._display_date.year == self._selection.year and
                self._display_date.month == self._selection.month and
                day == self._selection.day)

    def center_window(self):
        """Center window on parent."""
        self.update_idletasks()
        parent = self.master

        # Get geometries
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        width = self.winfo_width()
        height = self.winfo_height()

        # Calculate position
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2

        self.geometry(f'+{x}+{y}')

    def _on_cancel(self):
        """Handle dialog cancel."""
        self.result = None
        self.destroy()

    def _update_calendar(self):
        """Update calendar display."""
        # Set month/year display
        self.month_var.set(calendar.month_name[self._display_date.month])
        self.year_var.set(str(self._display_date.year))

        # Get calendar data
        cal = calendar.monthcalendar(
            self._display_date.year,
            self._display_date.month
        )

        # Update day buttons
        for i, btn in enumerate(self._day_buttons):
            week = i // 7
            day = i % 7

            try:
                day_num = cal[week][day]
                if day_num == 0:
                    btn.configure(text='', state='disabled')
                else:
                    btn.configure(
                        text=str(day_num),
                        state='normal'
                    )

                    # Highlight today
                    if self._is_today(day_num):
                        btn.configure(style='Calendar.TButton.Today')
                    else:
                        btn.configure(style='Calendar.TButton')

                    # Highlight selection
                    if self._is_selected(day_num):
                        btn.configure(style='Calendar.TButton.Selected')

            except IndexError:
                btn
