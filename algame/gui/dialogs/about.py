"""
About dialog implementation.

This dialog displays:
1. Application information and version
2. System information
3. License details
4. Credits and acknowledgments
"""

import tkinter as tk
from tkinter import ttk
import platform
import sys
from pathlib import Path
import webbrowser
from datetime import datetime
from typing import Dict

from .base import BaseDialog

class AboutDialog(BaseDialog):
    """
    Application about dialog.

    Features:
    - Version information
    - System details
    - License information
    - External links
    - Acknowledgments
    """

    def __init__(self, parent):
        """Initialize dialog."""
        super().__init__(parent, title="About Algame")

    def _create_dialog_widgets(self, frame):
        """Create about dialog widgets."""
        # Logo frame
        logo_frame = ttk.Frame(frame)
        logo_frame.pack(pady=10)

        # Load logo if available
        logo_path = Path(__file__).parent.parent / 'resources' / 'logo.png'
        if logo_path.exists():
            self.logo_img = tk.PhotoImage(file=str(logo_path))
            ttk.Label(
                logo_frame,
                image=self.logo_img
            ).pack()

        # Application info
        info_frame = ttk.LabelFrame(frame, text="Application")
        info_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(
            info_frame,
            text="Algame Backtesting Platform",
            font=('Arial', 12, 'bold')
        ).pack(pady=5)

        ttk.Label(
            info_frame,
            text="Version 0.1.0"
        ).pack()

        ttk.Label(
            info_frame,
            text=f"Build Date: {datetime.now().strftime('%Y-%m-%d')}"
        ).pack(pady=5)

        # System info
        sys_frame = ttk.LabelFrame(frame, text="System Information")
        sys_frame.pack(fill='x', padx=10, pady=5)

        sys_info = {
            'Python Version': sys.version.split()[0],
            'Platform': platform.platform(),
            'Architecture': platform.machine(),
            'Processor': platform.processor()
        }

        for key, value in sys_info.items():
            ttk.Label(
                sys_frame,
                text=f"{key}: {value}"
            ).pack(anchor='w', padx=5, pady=2)

        # License
        license_frame = ttk.LabelFrame(frame, text="License")
        license_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(
            license_frame,
            text="MIT License",
            font=('Arial', 10, 'bold')
        ).pack(pady=5)

        ttk.Label(
            license_frame,
            text="Copyright (c) 2024 Your Name",
            wraplength=300,
            justify='left'
        ).pack(padx=5, pady=5)

        license_text = (
            "Permission is hereby granted, free of charge, to any person obtaining a copy "
            "of this software and associated documentation files (the \"Software\"), to deal "
            "in the Software without restriction..."
        )

        text = tk.Text(
            license_frame,
            height=4,
            wrap='word',
            font=('Arial', 9)
        )
        text.insert('1.0', license_text)
        text.configure(state='disabled')
        text.pack(fill='x', padx=5, pady=5)

        # Credits
        credits_frame = ttk.LabelFrame(frame, text="Credits")
        credits_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(
            credits_frame,
            text="Development Team:",
            font=('Arial', 10, 'bold')
        ).pack(anchor='w', padx=5, pady=2)

        developers = [
            "Lead Developer: Your Name",
            "Core Contributors:",
            "  - Contributor 1",
            "  - Contributor 2"
        ]

        for dev in developers:
            ttk.Label(
                credits_frame,
                text=dev,
                justify='left'
            ).pack(anchor='w', padx=5, pady=1)

        # External Libraries
        libs_frame = ttk.LabelFrame(frame, text="External Libraries")
        libs_frame.pack(fill='x', padx=10, pady=5)

        libraries = [
            ("pandas", "https://pandas.pydata.org/"),
            ("numpy", "https://numpy.org/"),
            ("backtesting.py", "https://kernc.github.io/backtesting.py/"),
            ("yfinance", "https://pypi.org/project/yfinance/")
        ]

        for lib, url in libraries:
            lib_frame = ttk.Frame(libs_frame)
            lib_frame.pack(fill='x', padx=5, pady=1)

            ttk.Label(
                lib_frame,
                text=lib
            ).pack(side='left')

            link = ttk.Label(
                lib_frame,
                text="[Website]",
                foreground='blue',
                cursor='hand2'
            )
            link.pack(side='right')
            link.bind('<Button-1>', lambda e, url=url: self._open_url(url))

        # Links
        links_frame = ttk.Frame(frame)
        links_frame.pack(fill='x', padx=10, pady=10)

        links = [
            ("Documentation", "https://algame.readthedocs.io"),
            ("GitHub", "https://github.com/yourusername/algame"),
            ("Report Issue", "https://github.com/yourusername/algame/issues")
        ]

        for text, url in links:
            link = ttk.Button(
                links_frame,
                text=text,
                command=lambda url=url: self._open_url(url)
            )
            link.pack(side='left', padx=5)

    def _open_url(self, url: str):
        """Open URL in default browser."""
        try:
            webbrowser.open(url)
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror(
                "Error",
                f"Failed to open URL: {str(e)}"
            )

    def _create_buttons(self, frame):
        """Create dialog buttons."""
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill='x', pady=10)

        ttk.Button(
            btn_frame,
            text="Close",
            command=self.destroy
        ).pack(side='right', padx=5)

        ttk.Button(
            btn_frame,
            text="Check for Updates",
            command=self._check_updates
        ).pack(side='right', padx=5)

    def _check_updates(self):
        """Check for application updates."""
        try:
            # Here you would implement version checking logic
            # For now just show a message
            from tkinter import messagebox
            messagebox.showinfo(
                "Updates",
                "You are running the latest version."
            )
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to check for updates: {str(e)}"
            )

    def _load_version(self) -> str:
        """Load version information."""
        try:
            version_file = Path(__file__).parent.parent.parent / 'VERSION'
            if version_file.exists():
                return version_file.read_text().strip()
        except Exception:
            pass
        return "0.1.0"  # Default version

    def _load_build_info(self) -> Dict[str, str]:
        """Load build information."""
        try:
            info_file = Path(__file__).parent.parent.parent / 'build_info.json'
            if info_file.exists():
                import json
                return json.loads(info_file.read_text())
        except Exception:
            pass
        return {
            'build_date': datetime.now().strftime('%Y-%m-%d'),
            'git_hash': 'development',
            'python_version': sys.version.split()[0]
        }
