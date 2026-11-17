"""Pure calendar and KPI helpers for the Apaleo dashboard."""

from __future__ import annotations

import calendar
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo


def today_in(tz_name: str) -> date:
    """Today's date in the given IANA timezone."""
    return datetime.now(ZoneInfo(tz_name)).date()


def month_start(day: date) -> date:
    return day.replace(day=1)


def add_months(day: date, months: int) -> date:
    index = day.year * 12 + (day.month - 1) + months
    year, month = divmod(index, 12)
    return date(year, month + 1, 1)


def days_in_month(day: date) -> int:
    return calendar.monthrange(day.year, day.month)[1]


def month_key(day: date) -> str:
    return f"{day.year:04d}-{day.month:02d}"


def month_span(start: date, months: int) -> list[date]:
    """The first day of `months` consecutive months starting at `start`'s month."""
    first = month_start(start)
    return [add_months(first, offset) for offset in range(months)]


def safe_div(numerator: float, denominator: float) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def percent_delta(current: float | None, previous: float | None) -> float | None:
    if current is None or previous is None or previous == 0:
        return None
    return (current - previous) / abs(previous) * 100


def length_of_stay(room_nights: int, reservations: int) -> float | None:
    return safe_div(room_nights, reservations)


def amount(value: dict | None) -> float | None:
    """The numeric amount of an Apaleo `{amount, currency}` object."""
    if value is None:
        return None
    return value.get("amount")


def currency_of(value: dict | None) -> str | None:
    if value is None:
        return None
    return value.get("currency")


def sum_amounts(values: list[dict | None]) -> dict | None:
    """Sum `{amount, currency}` objects; None when nothing contributes."""
    total = 0.0
    currency: str | None = None
    seen = False
    for value in values:
        if value is None:
            continue
        seen = True
        total += value.get("amount") or 0.0
        code = value.get("currency")
        if code:
            currency = code
    return {"amount": round(total, 2), "currency": currency} if seen else None


# Fields that add up when several properties are combined into one KPI set.
_COUNT_FIELDS = (
    "houseCount",
    "houseItemsCount",
    "soldCount",
    "soldItemsCount",
    "unsoldCount",
    "unsoldItemsCount",
    "outOfOrderCount",
    "outOfOrderItemsCount",
    "tentativelyBlockedCount",
    "tentativelyBlockedItemsCount",
    "definitelyBlockedCount",
    "optionallyBlockedCount",
    "arrivalsCount",
    "departuresCount",
    "noShowsCount",
    "cancellationsCount",
)
_REVENUE_FIELDS = (
    "grossUnitRevenue",
    "netUnitRevenue",
    "grossAccommodationRevenue",
    "netAccommodationRevenue",
    "grossFoodAndBeveragesRevenue",
    "netFoodAndBeveragesRevenue",
    "grossOtherRevenue",
    "netOtherRevenue",
)


def combine_performance(entries: list[dict]) -> dict:
    """Merge several per-property performance reports into one KPI set.

    Derived figures (occupancy, ADR, RevPAR) are recomputed from the summed
    counts and revenue; mixing currencies averages them into one field, which
    only matters for accounts running properties in different currencies.
    """
    combined: dict = {}
    for field in _COUNT_FIELDS:
        combined[field] = sum(int(entry.get(field) or 0) for entry in entries)
    for field in _REVENUE_FIELDS:
        merged = sum_amounts([entry.get(field) for entry in entries])
        combined[field] = merged
        if merged is None:
            combined[field] = {"amount": 0.0, "currency": None}

    sellable = combined["houseCount"] - combined["outOfOrderCount"]
    accommodation = combined["grossAccommodationRevenue"]
    revenue = amount(accommodation) or 0.0
    currency = currency_of(accommodation)

    combined["occupancyPercentage"] = round(
        100 * (combined["soldCount"] / sellable) if sellable else 0.0, 2
    )
    combined["grossAdr"] = {
        "amount": round(safe_div(revenue, combined["soldCount"]) or 0.0, 2),
        "currency": currency,
    }
    combined["revPar"] = {
        "amount": round(safe_div(revenue, sellable) or 0.0, 2) if sellable else 0.0,
        "currency": currency,
    }
    combined["netAdr"] = {
        "amount": round(
            safe_div(amount(combined["netAccommodationRevenue"]) or 0.0, combined["soldCount"]) or 0.0, 2
        ),
        "currency": currency,
    }
    return combined


def total_revenue(entry: dict) -> float:
    """Gross total revenue (accommodation + F&B + other) of a performance report."""
    return round(
        (amount(entry.get("grossAccommodationRevenue")) or 0.0)
        + (amount(entry.get("grossFoodAndBeveragesRevenue")) or 0.0)
        + (amount(entry.get("grossOtherRevenue")) or 0.0),
        2,
    )


def net_total_revenue(entry: dict) -> float:
    return round(
        (amount(entry.get("netAccommodationRevenue")) or 0.0)
        + (amount(entry.get("netFoodAndBeveragesRevenue")) or 0.0)
        + (amount(entry.get("netOtherRevenue")) or 0.0),
        2,
    )


def available_room_nights(entry: dict) -> int:
    return max(int(entry.get("houseCount") or 0) - int(entry.get("outOfOrderCount") or 0), 0)


def month_interval(day: date, *, full_month: bool, tz_name: str) -> tuple[date, date]:
    """Inclusive from / exclusive to for a month, either the whole month or up to today."""
    first = month_start(day)
    if full_month:
        return first, add_months(first, 1)
    # Inclusive of today: the report's `to` is exclusive.
    return first, min(day + timedelta(days=1), add_months(first, 1))


def current_tz_default() -> str:
    return "Europe/Berlin"
