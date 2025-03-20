"""
Filtering functionality for Telegram UIDs
"""

from datetime import datetime
import re
from typing import Optional, Pattern, List, Dict, Any

from .types import FilterConfig, TelegramUID


class UIDFilter:
    """
    Filter Telegram UIDs based on various criteria
    """

    def __init__(self, config: FilterConfig):
        self.config = config

    def _check_activity_level(self, uid: TelegramUID) -> bool:
        """Check if UID meets activity level requirements"""
        if self.config.min_activity_level is not None:
            if uid['activity_level'] < self.config.min_activity_level:
                return False

        if self.config.max_activity_level is not None:
            if uid['activity_level'] > self.config.max_activity_level:
                return False

        return True

    def _check_join_date(self, uid: TelegramUID) -> bool:
        """Check if UID meets join date requirements"""
        join_date = datetime.fromisoformat(uid['join_date'])

        if self.config.join_date_start:
            if join_date < self.config.join_date_start:
                return False

        if self.config.join_date_end:
            if join_date > self.config.join_date_end:
                return False

        return True

    def _check_username(self, uid: TelegramUID) -> bool:
        """Check if username matches pattern requirements"""
        if not self.config.username_pattern:
            return True

        if not uid['username']:
            return False

        return bool(self.config.username_pattern.match(uid['username']))

    def _check_status(self, uid: TelegramUID) -> bool:
        """Check if UID meets status requirements"""
        if self.config.exclude_banned and uid['status'] == 'banned':
            return False

        if self.config.only_active and uid['status'] != 'active':
            return False

        return True

    def matches(self, uid: TelegramUID) -> bool:
        """
        Check if a UID matches all filter criteria
        Returns True if the UID should be included, False otherwise
        """
        return all([
            self._check_activity_level(uid),
            self._check_join_date(uid),
            self._check_username(uid),
            self._check_status(uid)
        ])


class FilterBuilder:
    """
    Builder class for creating filter configurations
    """

    def __init__(self):
        self.min_activity: Optional[int] = None
        self.max_activity: Optional[int] = None
        self.join_after: Optional[datetime] = None
        self.join_before: Optional[datetime] = None
        self.username_pattern: Optional[Pattern] = None
        self.exclude_banned: bool = False
        self.only_active: bool = False

    def set_activity_range(
        self,
        min_activity: Optional[int] = None,
        max_activity: Optional[int] = None
    ) -> 'FilterBuilder':
        """Set activity level range"""
        self.min_activity = min_activity
        self.max_activity = max_activity
        return self

    def set_join_date_range(
        self,
        after: Optional[datetime] = None,
        before: Optional[datetime] = None
    ) -> 'FilterBuilder':
        """Set join date range"""
        self.join_after = after
        self.join_before = before
        return self

    def set_username_pattern(
        self,
        pattern: str
    ) -> 'FilterBuilder':
        """Set username pattern"""
        self.username_pattern = re.compile(pattern)
        return self

    def set_status_filters(
        self,
        exclude_banned: bool = False,
        only_active: bool = False
    ) -> 'FilterBuilder':
        """Set status-related filters"""
        self.exclude_banned = exclude_banned
        self.only_active = only_active
        return self

    def build(self) -> FilterConfig:
        """Build and return a FilterConfig object"""
        return FilterConfig(
            min_activity_level=self.min_activity,
            max_activity_level=self.max_activity,
            join_date_start=self.join_after,
            join_date_end=self.join_before,
            username_pattern=self.username_pattern,
            exclude_banned=self.exclude_banned,
            only_active=self.only_active
        )


def create_filter(
    min_activity: Optional[int] = None,
    max_activity: Optional[int] = None,
    join_after: Optional[str] = None,
    join_before: Optional[str] = None,
    username_pattern: Optional[str] = None,
    exclude_banned: bool = False,
    only_active: bool = False
) -> UIDFilter:
    """
    Convenience function to create a UIDFilter with common parameters
    """
    builder = FilterBuilder()

    if min_activity is not None or max_activity is not None:
        builder.set_activity_range(min_activity, max_activity)

    if join_after or join_before:
        after = datetime.fromisoformat(join_after) if join_after else None
        before = datetime.fromisoformat(join_before) if join_before else None
        builder.set_join_date_range(after, before)

    if username_pattern:
        builder.set_username_pattern(username_pattern)

    builder.set_status_filters(exclude_banned, only_active)

    return UIDFilter(builder.build())


def apply_filters(
    uids: List[TelegramUID],
    filters: List[UIDFilter]
) -> List[TelegramUID]:
    """
    Apply multiple filters to a list of UIDs
    Returns only UIDs that match all filters
    """
    if not filters:
        return uids

    return [
        uid for uid in uids
        if all(f.matches(uid) for f in filters)
    ]


def create_composite_filter(
    configs: List[FilterConfig]
) -> UIDFilter:
    """
    Create a composite filter from multiple configurations
    """
    if not configs:
        return UIDFilter(FilterConfig())

    # Combine all configurations
    composite_config = FilterConfig(
        min_activity_level=max(
            (c.min_activity_level for c in configs if c.min_activity_level is not None),
            default=None
        ),
        max_activity_level=min(
            (c.max_activity_level for c in configs if c.max_activity_level is not None),
            default=None
        ),
        join_date_start=max(
            (c.join_date_start for c in configs if c.join_date_start is not None),
            default=None
        ),
        join_date_end=min(
            (c.join_date_end for c in configs if c.join_date_end is not None),
            default=None
        ),
        username_pattern=configs[0].username_pattern,  # Take first non-None pattern
        exclude_banned=any(c.exclude_banned for c in configs),
        only_active=any(c.only_active for c in configs)
    )

    return UIDFilter(composite_config)