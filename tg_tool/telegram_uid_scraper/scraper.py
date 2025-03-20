"""
Core scraping functionality for the Telegram UID Scraper
"""

import asyncio
import random
import time
from datetime import datetime
from typing import AsyncGenerator, Optional, List

import aiohttp
from aiohttp import ClientTimeout

from .logger import Logger
from .auto_adder import TelegramAutoAdder
from .types import (
    ScraperConfig,
    FilterConfig,
    Stats,
    TelegramUID,
    AutoAddConfig
)


class TelegramScraper:
    """
    Main scraper class that handles the extraction of UIDs from Telegram groups
    """

    def __init__(
        self,
        config: ScraperConfig,
        logger: Logger,
        filter_config: Optional[FilterConfig] = None
    ):
        self.config = config
        self.logger = logger
        self.filter_config = filter_config
        self.stats = Stats()
        self._session: Optional[aiohttp.ClientSession] = None
        self._auto_adder: Optional[TelegramAutoAdder] = None
        self._running = False
        self._user_agents = self._load_user_agents()

    def _load_user_agents(self) -> List[str]:
        """Load a list of user agents for rotation"""
        return [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15",
            "Mozilla/5.0 (iPad; CPU OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15"
        ]

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop()

    async def start(self):
        """Initialize the scraper"""
        if self._session:
            return

        timeout = ClientTimeout(total=self.config.timeout)
        self._session = aiohttp.ClientSession(timeout=timeout)
        self._running = True

        # Initialize auto-adder if configured
        if self.config.auto_add and self.config.auto_add.enabled:
            self._auto_adder = TelegramAutoAdder(self.config.auto_add, self.logger)
            await self._auto_adder.start()

        self.logger.info("Scraper initialized successfully")

    async def stop(self):
        """Clean up resources"""
        self._running = False
        if self._session:
            await self._session.close()
            self._session = None

        if self._auto_adder:
            await self._auto_adder.stop()
            # Update final auto-add stats
            self.stats.auto_add_stats = self._auto_adder.stats

        self.logger.info("Scraper stopped and cleaned up")

    def _get_random_user_agent(self) -> str:
        """Get a random user agent from the list"""
        return random.choice(self._user_agents)

    async def _make_request(
        self,
        url: str,
        method: str = "GET",
        **kwargs
    ) -> Optional[dict]:
        """Make an HTTP request with retry logic and stealth measures"""
        if not self._session:
            raise RuntimeError("Scraper session not initialized")

        headers = kwargs.pop('headers', {})
        if self.config.user_agent_rotation:
            headers['User-Agent'] = self._get_random_user_agent()

        for attempt in range(self.config.retry_attempts):
            try:
                if self.config.stealth_mode:
                    # Add random delay
                    delay = self.config.request_delay * (1 + random.random())
                    await asyncio.sleep(delay)

                async with self._session.request(
                    method,
                    url,
                    headers=headers,
                    **kwargs
                ) as response:
                    self.stats.bandwidth_used += len(
                        await response.read()
                    )
                    
                    if response.status == 200:
                        return await response.json()
                    
                    self.logger.warning(
                        f"Request failed with status {response.status}"
                    )
                    
            except asyncio.TimeoutError:
                self.logger.warning(
                    f"Request timeout (attempt {attempt + 1}/{self.config.retry_attempts})"
                )
            except Exception as e:
                self.logger.error(f"Request error: {str(e)}")

            # Exponential backoff
            await asyncio.sleep(2 ** attempt)

        return None

    def _update_stats(self, success: bool = True) -> None:
        """Update scraping statistics"""
        current_time = time.time()
        elapsed_time = current_time - self.stats.start_time

        self.stats.total_processed += 1
        if success:
            self.stats.successful_scrapes += 1
        else:
            self.stats.failed_scrapes += 1

        # Calculate current rate
        if elapsed_time > 0:
            self.stats.current_rate = self.stats.total_processed / elapsed_time

        # Estimate remaining time
        if self.stats.current_rate > 0:
            remaining_groups = len(self.config.target_groups) - self.stats.total_processed
            self.stats.estimated_time_remaining = remaining_groups / self.stats.current_rate

    def _apply_filters(self, uid: TelegramUID) -> bool:
        """Apply configured filters to a UID"""
        if not self.filter_config:
            return True

        # Apply activity level filter
        if self.filter_config.min_activity_level is not None:
            if uid['activity_level'] < self.filter_config.min_activity_level:
                return False

        if self.filter_config.max_activity_level is not None:
            if uid['activity_level'] > self.filter_config.max_activity_level:
                return False

        # Apply join date filter
        if self.filter_config.join_date_start:
            if datetime.fromisoformat(uid['join_date']) < self.filter_config.join_date_start:
                return False

        if self.filter_config.join_date_end:
            if datetime.fromisoformat(uid['join_date']) > self.filter_config.join_date_end:
                return False

        # Apply username pattern filter
        if (self.filter_config.username_pattern and
            uid['username'] and
            not self.filter_config.username_pattern.match(uid['username'])):
            return False

        # Apply status filters
        if self.filter_config.exclude_banned and uid['status'] == 'banned':
            return False

        if self.filter_config.only_active and uid['status'] != 'active':
            return False

        return True

    async def _extract_uids(self, group: str) -> AsyncGenerator[TelegramUID, None]:
        """Extract UIDs from a single group"""
        if not self._running:
            return

        try:
            # Simulate UID extraction for demonstration
            # In a real implementation, this would interact with Telegram's API
            for i in range(10):  # Simulate finding 10 users
                if not self._running:
                    break

                uid = {
                    'uid': random.randint(100000000, 999999999),
                    'username': f"user_{i}" if random.random() > 0.3 else None,
                    'join_date': datetime.now().isoformat(),
                    'activity_level': random.randint(0, 10),
                    'last_seen': datetime.now().isoformat(),
                    'message_count': random.randint(0, 1000),
                    'is_admin': random.random() > 0.9,
                    'status': random.choice(['active', 'inactive', 'banned'])
                }

                if self._apply_filters(uid):
                    self._update_stats(success=True)
                    
                    # If auto-add is enabled, try to add the user
                    if self._auto_adder:
                        await self._auto_adder.add_user(uid)
                        # Update stats with auto-adder stats
                        self.stats.auto_add_stats = self._auto_adder.stats
                    
                    yield uid
                else:
                    self._update_stats(success=False)

                # Simulate processing time
                await asyncio.sleep(0.5)

        except Exception as e:
            self.logger.error(f"Error extracting UIDs from {group}: {str(e)}")
            self._update_stats(success=False)

    async def scrape_all(self) -> AsyncGenerator[TelegramUID, None]:
        """Scrape UIDs from all target groups"""
        if not self._running:
            await self.start()

        try:
            for group in self.config.target_groups:
                self.logger.info(f"Starting scrape of group: {group}")
                async for uid in self._extract_uids(group):
                    yield uid
                self.logger.info(f"Completed scrape of group: {group}")

        except Exception as e:
            self.logger.error(f"Error during scraping: {str(e)}")
            raise

    def get_stats(self) -> Stats:
        """Get current scraping statistics"""
        return self.stats