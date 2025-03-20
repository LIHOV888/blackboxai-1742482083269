"""
Command-line interface for the Telegram UID Scraper
"""

import argparse
from datetime import datetime
from pathlib import Path
import re
from typing import Tuple

from .types import (
    AutoAddConfig,
    DashboardConfig,
    ExportConfig,
    FilterConfig,
    LogConfig,
    ScraperConfig,
    UIConfig,
)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Scrape Telegram user IDs from groups"
    )

    # Input/Output options
    parser.add_argument(
        "groups",
        nargs="+",
        help="Telegram group(s) to scrape UIDs from"
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory to store output files"
    )
    parser.add_argument(
        "--format",
        choices=["json", "csv"],
        default="json",
        help="Output format for scraped UIDs"
    )

    # Scraping options
    parser.add_argument(
        "--concurrent",
        type=int,
        default=10,
        help="Number of concurrent requests"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Delay between requests in seconds"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Request timeout in seconds"
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="Number of retries for failed requests"
    )
    parser.add_argument(
        "--stealth",
        action="store_true",
        help="Enable stealth mode to avoid detection"
    )

    # Auto-add options
    parser.add_argument(
        "--auto-add",
        action="store_true",
        help="Automatically add scraped users to target channel"
    )
    parser.add_argument(
        "--target-channel",
        help="Target channel for auto-adding users"
    )
    parser.add_argument(
        "--bot-token",
        help="Telegram bot token for auto-adding users"
    )
    parser.add_argument(
        "--invite-delay",
        type=float,
        default=1.0,
        help="Delay between invite attempts in seconds"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Number of users to add in each batch"
    )

    # Filter options
    parser.add_argument(
        "--min-activity",
        type=int,
        help="Minimum user activity level"
    )
    parser.add_argument(
        "--max-activity",
        type=int,
        help="Maximum user activity level"
    )
    parser.add_argument(
        "--join-after",
        help="Only include users who joined after this date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--join-before",
        help="Only include users who joined before this date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--username-pattern",
        help="Regular expression pattern for usernames"
    )
    parser.add_argument(
        "--exclude-banned",
        action="store_true",
        help="Exclude banned users"
    )
    parser.add_argument(
        "--only-active",
        action="store_true",
        help="Only include active users"
    )

    # UI options
    parser.add_argument(
        "--no-animation",
        action="store_true",
        help="Disable progress bar animation"
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Use compact display mode"
    )

    # Dashboard options
    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Enable web dashboard"
    )

    # Logging options
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level"
    )
    parser.add_argument(
        "--encrypt-logs",
        action="store_true",
        help="Encrypt log files"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    return parser.parse_args()


def create_configs(args: argparse.Namespace) -> Tuple[
    ScraperConfig,
    FilterConfig,
    LogConfig,
    UIConfig,
    ExportConfig,
    DashboardConfig
]:
    """Create configuration objects from parsed arguments"""
    
    # Create output directory if it doesn't exist
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create scraper config
    scraper_config = ScraperConfig(
        groups=args.groups,
        concurrent_requests=args.concurrent,
        request_delay=args.delay,
        timeout=args.timeout,
        max_retries=args.retries,
        stealth_mode=args.stealth
    )

    # Create filter config
    filter_config = FilterConfig(
        min_activity_level=args.min_activity,
        max_activity_level=args.max_activity,
        join_date_start=datetime.fromisoformat(args.join_after) if args.join_after else None,
        join_date_end=datetime.fromisoformat(args.join_before) if args.join_before else None,
        username_pattern=re.compile(args.username_pattern) if args.username_pattern else None,
        exclude_banned=args.exclude_banned,
        only_active=args.only_active
    )

    # Create log config
    log_config = LogConfig(
        level=args.log_level,
        output_dir=output_dir,
        encrypt=args.encrypt_logs,
        verbose=args.verbose
    )

    # Create UI config
    ui_config = UIConfig(
        animated=not args.no_animation,
        compact=args.compact
    )

    # Create export config
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_config = ExportConfig(
        format=args.format,
        output_path=output_dir / f"uids_{timestamp}.{args.format}"
    )

    # Create dashboard config
    dashboard_config = DashboardConfig(
        enabled=args.dashboard,
        host="0.0.0.0",  # Allow external access
        port=8000
    )

    return (
        scraper_config,
        filter_config,
        log_config,
        ui_config,
        export_config,
        dashboard_config
    )