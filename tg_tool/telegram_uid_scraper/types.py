"""
Type definitions for the Telegram UID Scraper
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re
from typing import List, Optional, Dict, Any, Pattern


@dataclass
class ScraperConfig:
    """Configuration for the scraper"""
    groups: List[str]
    concurrent_requests: int
    request_delay: float
    timeout: int
    max_retries: int
    stealth_mode: bool


@dataclass
class FilterConfig:
    """Configuration for filtering UIDs"""
    min_activity_level: Optional[int]
    max_activity_level: Optional[int]
    join_date_start: Optional[datetime]
    join_date_end: Optional[datetime]
    username_pattern: Optional[Pattern]
    exclude_banned: bool
    only_active: bool


@dataclass
class LogConfig:
    """Configuration for logging"""
    level: str
    output_dir: Path
    encrypt: bool
    verbose: bool


@dataclass
class UIConfig:
    """Configuration for the terminal UI"""
    animated: bool
    compact: bool


@dataclass
class ExportConfig:
    """Configuration for exporting results"""
    format: str
    output_path: Path


@dataclass
class DashboardConfig:
    """Configuration for the web dashboard"""
    enabled: bool
    host: str = "0.0.0.0"  # Allow external access
    port: int = 8000


@dataclass
class AutoAddConfig:
    """Configuration for auto-adding users"""
    enabled: bool
    target_channel: Optional[str]
    bot_token: Optional[str]
    invite_delay: float
    batch_size: int


@dataclass
class Stats:
    """Statistics for the scraping process"""
    total_processed: int = 0
    successful_scrapes: int = 0
    failed_scrapes: int = 0
    current_rate: float = 0.0
    bandwidth_used: int = 0
    estimated_time_remaining: float = 0.0
    auto_add_stats: Optional[Dict[str, Any]] = None
    start_time: Optional[datetime] = None


@dataclass
class TelegramUID:
    """Represents a Telegram user ID with metadata"""
    uid: int
    username: Optional[str]
    status: str
    activity_level: int
    join_date: datetime
    metadata: Dict[str, Any]