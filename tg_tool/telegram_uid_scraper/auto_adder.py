"""
Auto-add functionality for Telegram UID Scraper
"""

import asyncio
import random
from typing import List, Optional

import aiohttp
from aiohttp import ClientTimeout

from .logger import Logger
from .types import AutoAddConfig, TelegramUID


class TelegramAutoAdder:
    """
    Handles automatic addition of scraped UIDs to target channels/groups
    """

    def __init__(self, config: AutoAddConfig, logger: Logger):
        self.config = config
        self.logger = logger
        self._session: Optional[aiohttp.ClientSession] = None
        self._running = False
        self._success_count = 0
        self._failure_count = 0

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop()

    async def start(self):
        """Initialize the auto-adder"""
        if self._session:
            return

        timeout = ClientTimeout(total=self.config.timeout)
        self._session = aiohttp.ClientSession(timeout=timeout)
        self._running = True
        self.logger.info("Auto-adder initialized successfully")

    async def stop(self):
        """Clean up resources"""
        self._running = False
        if self._session:
            await self._session.close()
            self._session = None
        self.logger.info("Auto-adder stopped and cleaned up")

    async def _make_request(
        self,
        uid: int,
        method: str = "POST",
        **kwargs
    ) -> Optional[dict]:
        """Make an HTTP request with retry logic"""
        if not self._session:
            raise RuntimeError("Auto-adder session not initialized")

        for attempt in range(self.config.retry_attempts):
            try:
                # Add random delay between attempts
                if attempt > 0:
                    delay = self.config.invite_delay * (1 + random.random())
                    await asyncio.sleep(delay)

                # Simulate API endpoint for demonstration
                # In production, this would be a real Telegram API endpoint
                url = f"https://api.telegram.org/bot{self.config.bot_token}/inviteToChannel"
                
                async with self._session.request(
                    method,
                    url,
                    json={
                        "chat_id": self.config.target_channel,
                        "user_id": uid
                    },
                    **kwargs
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    
                    self.logger.warning(
                        f"Add request failed with status {response.status}"
                    )
                    
            except asyncio.TimeoutError:
                self.logger.warning(
                    f"Add request timeout (attempt {attempt + 1}/{self.config.retry_attempts})"
                )
            except Exception as e:
                self.logger.error(f"Add request error: {str(e)}")

            # Exponential backoff
            await asyncio.sleep(2 ** attempt)

        return None

    async def add_user(self, uid: TelegramUID) -> bool:
        """
        Add a single user to the target channel
        Returns True if successful, False otherwise
        """
        try:
            # For demonstration, simulate success/failure
            # In production, this would make real API calls
            success = random.random() > 0.2  # 80% success rate
            
            if success:
                self._success_count += 1
                self.logger.info(
                    f"Successfully added UID {uid['uid']} to {self.config.target_channel}"
                )
                return True
            
            self._failure_count += 1
            self.logger.error(
                f"Failed to add UID {uid['uid']} to {self.config.target_channel}"
            )
            return False

        except Exception as e:
            self._failure_count += 1
            self.logger.error(
                f"Error adding UID {uid['uid']}: {str(e)}"
            )
            return False

    async def batch_add(self, uids: List[TelegramUID]) -> dict:
        """
        Add multiple users in batch
        Returns statistics about the operation
        """
        if not self._running:
            await self.start()

        total = len(uids)
        successful = 0
        failed = 0

        for uid in uids:
            if await self.add_user(uid):
                successful += 1
            else:
                failed += 1

            # Respect rate limiting
            await asyncio.sleep(self.config.invite_delay)

        return {
            "total": total,
            "successful": successful,
            "failed": failed
        }

    @property
    def stats(self) -> dict:
        """Get current auto-add statistics"""
        return {
            "success_count": self._success_count,
            "failure_count": self._failure_count,
            "total_attempts": self._success_count + self._failure_count
        }