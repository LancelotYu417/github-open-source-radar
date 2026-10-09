"""Star-history aggregation and ranking, free of network/database dependencies."""
from datetime import datetime, timezone, timedelta
from typing import Any

WINDOWS = {"7d": 7, "30d": 30, "90d": 90, "6m": 182, "1y": 365}


def daily_stars(weeks: list[dict[str, Any]]) -> dict[str, int]:
    """GitHub weeks start Sunday; preserve each daily value and collapse duplicates."""
    result: dict[str, int] = {}
    for week in weeks:
        values = week.get("days")
        if not isinstance(values, list) or len(values) != 7:
            raise ValueError("GitHub history entry must have exactly seven days")
        if any(not isinstance(n, int) or n < 0 for n in values):
            raise ValueError("Daily stars must be nonnegative integers")
        start = datetime.fromtimestamp(week["week"], tz=timezone.utc).date()
        for offset, value in enumerate(values):
            day = (start + timedelta(days=offset)).isoformat()
            if day in result and result[day] != value:
                raise ValueError(f"Conflicting history for {day}")
            result[day] = value
    return result


def growth(days: dict[str, int], window: int, as_of: datetime | None = None) -> int:
    """Rolling N calendar dates inclusive of the as_of date (UTC approximation)."""
    as_of = as_of or datetime.now(timezone.utc)
    today = as_of.date()
    start = today - timedelta(days=window - 1)
    return sum(value for day, value in days.items() if start <= datetime.fromisoformat(day).date() <= today)


def metrics(weeks: list[dict[str, Any]], current_stars: int, as_of: datetime | None = None) -> dict:
    days = daily_stars(weeks)
    result = {}
    for key, window in WINDOWS.items():
        delta = growth(days, window, as_of)
        baseline = current_stars - delta
        result[key] = {"added": delta, "rate": round(delta / baseline * 100, 2) if baseline > 0 else None}
    return result
