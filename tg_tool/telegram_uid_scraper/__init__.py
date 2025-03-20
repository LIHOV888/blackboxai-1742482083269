"""
Telegram UID Scraper package
"""

from .types import (
    ScraperConfig,
    FilterConfig,
    LogConfig,
    UIConfig,
    ExportConfig,
    DashboardConfig,
    AutoAddConfig,
    Stats,
    TelegramUID
)

from .cli import parse_args, create_configs
from .__main__ import run

__version__ = "1.0.0"