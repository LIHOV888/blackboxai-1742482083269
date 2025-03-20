"""
Terminal UI for the Telegram UID Scraper
"""

import asyncio
from datetime import datetime
from typing import Dict, Any

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.table import Table
from rich.text import Text

from .types import UIConfig, Stats, TelegramUID


class TelegramScraperUI:
    """
    Terminal-based UI with Matrix-style theme and real-time updates
    """

    def __init__(self, config: UIConfig):
        self.config = config
        self.console = Console()
        self._layout = self._create_layout()
        self._live: Live = None
        self._recent_uids = []
        self._stats = Stats()
        self._progress = Progress(
            SpinnerColumn(),
            BarColumn(),
            TextColumn("[progress.description]{task.description}"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        )
        self._task_id = self._progress.add_task(
            "Scraping UIDs...",
            total=None
        )

    def _create_layout(self) -> Layout:
        """Create the terminal UI layout"""
        layout = Layout(name="root")
        
        # Split into header and body
        layout.split(
            Layout(name="header", size=3),
            Layout(name="body")
        )
        
        # Split body into main and sidebar
        layout["body"].split_row(
            Layout(name="main", ratio=2),
            Layout(name="sidebar", ratio=1)
        )
        
        return layout

    def _render_header(self) -> Panel:
        """Render the header section"""
        title = Text("Telegram UID Scraper", style="bold green")
        subtitle = Text("Real-time Monitoring", style="cyan")
        return Panel(
            Layout(name="header_content").split(
                title,
                subtitle
            ),
            style=self.config.color_scheme["header"]
        )

    def _render_stats(self) -> Panel:
        """Render the statistics panel"""
        stats_table = Table.grid(padding=1)
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="green")
        
        # Add statistics rows
        stats_table.add_row(
            "Total Processed",
            str(self._stats.total_processed)
        )
        stats_table.add_row(
            "Successful",
            str(self._stats.successful_scrapes)
        )
        stats_table.add_row(
            "Failed",
            str(self._stats.failed_scrapes)
        )
        stats_table.add_row(
            "Rate",
            f"{self._stats.current_rate:.2f} UIDs/sec"
        )
        
        # Add auto-add stats if available
        if self._stats.auto_add_stats:
            stats_table.add_row(
                "Auto-Add Success",
                str(self._stats.auto_add_stats["success_count"])
            )
            stats_table.add_row(
                "Auto-Add Failed",
                str(self._stats.auto_add_stats["failure_count"])
            )
        
        return Panel(
            stats_table,
            title="Statistics",
            border_style=self.config.color_scheme["stats"]
        )

    def _render_recent_uids(self) -> Panel:
        """Render the recent UIDs panel"""
        if not self._recent_uids:
            return Panel(
                "No UIDs scraped yet",
                title="Recent UIDs",
                border_style=self.config.color_scheme["stats"]
            )

        table = Table(
            show_header=True,
            header_style="bold cyan",
            border_style=self.config.color_scheme["stats"]
        )
        table.add_column("UID")
        table.add_column("Username")
        table.add_column("Status")

        # Add most recent UIDs first
        for uid in reversed(self._recent_uids[-5:]):
            status_style = (
                "green" if uid["status"] == "active"
                else "yellow" if uid["status"] == "inactive"
                else "red"
            )
            table.add_row(
                str(uid["uid"]),
                uid["username"] or "N/A",
                Text(uid["status"], style=status_style)
            )

        return Panel(
            table,
            title="Recent UIDs",
            border_style=self.config.color_scheme["stats"]
        )

    def _render_progress(self) -> Panel:
        """Render the progress panel"""
        return Panel(
            self._progress,
            title="Progress",
            border_style=self.config.color_scheme["stats"]
        )

    def _update_layout(self):
        """Update the layout with current data"""
        # Update header
        self._layout["header"].update(self._render_header())
        
        # Update main section
        main_layout = Layout()
        main_layout.split(
            self._render_stats(),
            self._render_progress()
        )
        self._layout["main"].update(main_layout)
        
        # Update sidebar
        self._layout["sidebar"].update(self._render_recent_uids())

    async def start(self):
        """Start the UI"""
        self._live = Live(
            self._layout,
            console=self.console,
            refresh_per_second=4,
            screen=True
        )
        self._live.start()

    async def stop(self):
        """Stop the UI"""
        if self._live:
            self._live.stop()

    async def update(self, uid: TelegramUID, stats: Stats):
        """Update the UI with new data"""
        self._stats = stats
        self._recent_uids.append(uid)
        
        # Keep only last 100 UIDs
        if len(self._recent_uids) > 100:
            self._recent_uids = self._recent_uids[-100:]
        
        # Update progress
        if stats.total_processed > 0:
            self._progress.update(
                self._task_id,
                completed=stats.successful_scrapes,
                description=f"Processing: {stats.current_rate:.2f} UIDs/sec"
            )
        
        # Update layout
        self._update_layout()

    async def clear(self):
        """Clear the UI"""
        self._recent_uids = []
        self._stats = Stats()
        self._update_layout()