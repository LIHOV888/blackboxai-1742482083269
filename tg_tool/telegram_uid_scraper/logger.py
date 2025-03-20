"""
Logging functionality for the Telegram UID Scraper
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from .types import LogConfig


class Logger:
    """
    Handles logging for the application
    """

    def __init__(self, config: LogConfig):
        self.config = config
        self.logs: List[Dict[str, Any]] = []
        self._setup_logger()

    def _setup_logger(self):
        """Set up the logger"""
        # Create logger
        self.logger = logging.getLogger("telegram-uid-scraper")
        self.logger.setLevel(self.config.level)

        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.config.level)

        # Create formatter
        formatter = logging.Formatter(
            "%(levelname)-8s %(message)s"
        )
        console_handler.setFormatter(formatter)

        # Add handler to logger
        self.logger.addHandler(console_handler)

        # Create output directory if it doesn't exist
        self.config.output_dir.mkdir(parents=True, exist_ok=True)

    def debug(self, message: str):
        """Log a debug message"""
        self.logger.debug(message)
        self._add_log("DEBUG", message)

    def info(self, message: str):
        """Log an info message"""
        self.logger.info(message)
        self._add_log("INFO", message)

    def warning(self, message: str):
        """Log a warning message"""
        self.logger.warning(message)
        self._add_log("WARNING", message)

    def error(self, message: str):
        """Log an error message"""
        self.logger.error(message)
        self._add_log("ERROR", message)

    def _add_log(self, level: str, message: str):
        """Add a log entry to the internal list"""
        self.logs.append({
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message
        })

        # Keep only the most recent logs
        if len(self.logs) > 1000:
            self.logs.pop(0)

    async def get_recent_logs(
        self,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get recent log entries"""
        if limit:
            return self.logs[-limit:]
        return self.logs

    async def export_json(
        self,
        data: List[Any],
        output_path: Path
    ):
        """Export data to a JSON file"""
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
        self.info(f"Successfully exported {len(data)} UIDs to {output_path}")

    async def export_csv(
        self,
        data: List[Any],
        output_path: Path
    ):
        """Export data to a CSV file"""
        if not data:
            return

        # Get field names from first item
        fields = list(data[0].__dict__.keys())

        with open(output_path, "w") as f:
            # Write header
            f.write(",".join(fields) + "\n")

            # Write data
            for item in data:
                values = [str(getattr(item, field)) for field in fields]
                f.write(",".join(values) + "\n")

        self.info(f"Successfully exported {len(data)} UIDs to {output_path}")