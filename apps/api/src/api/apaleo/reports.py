"""Apaleo report calls used by the dashboard."""

from __future__ import annotations

from datetime import date

from api.apaleo import client


async def list_properties() -> list[dict]:
    properties: list[dict] = []
    page = 1
    while True:
        payload = await client.cached_call(
            "ListProperties", {"page_size": 100, "page_number": page}, ttl_seconds=600
        )
        if not payload or not payload.get("properties"):
            break
        properties.extend(payload["properties"])
        total = payload.get("count")
        if total is None or len(properties) >= total or len(payload["properties"]) < 100:
            break
        page += 1
    # `isTemplate` marks how a property was set up, not whether it earns: Wiesloch is flagged as
    # a template and books ~45k a month. Only archived properties stay out.
    return [p for p in properties if not p.get("isArchived")]


async def performance_report(property_id: str, from_day: date, to_day: date) -> dict:
    """KPIs for [from_day, to_day); the API takes an inclusive end date."""
    last_inclusive = date.fromordinal(to_day.toordinal() - 1)
    return await client.cached_call(
        "ListPropertyPerformanceReport",
        {
            "property_id": property_id,
            "from_": from_day.isoformat(),
            "to": last_inclusive.isoformat(),
        },
        ttl_seconds=300,
    )


async def revenues_report(property_id: str, from_day: date, to_day: date) -> dict:
    """Revenue by account tree; `to_day` is exclusive, the API allows at most one year."""
    return await client.cached_call(
        "ListRevenuesReport",
        {"property_id": property_id, "from_": from_day.isoformat(), "to": to_day.isoformat()},
        ttl_seconds=300,
    )


async def room_nights_report(property_id: str, year: int, month: int) -> dict:
    return await client.cached_call(
        "GetRoomNightsReport", {"property_id": property_id, "year": year, "month": month}, ttl_seconds=300
    )


async def arrivals_report(property_id: str, year: int, month: int) -> dict:
    return await client.cached_call(
        "ListArrivalsReport", {"property_id": property_id, "year": year, "month": month}, ttl_seconds=300
    )


async def current_account() -> dict:
    return await client.cached_call("GetCurrentAccount", {}, ttl_seconds=600)
