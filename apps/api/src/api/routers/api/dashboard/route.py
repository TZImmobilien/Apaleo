"""Dashboard endpoints: monthly KPIs, history, on-the-books future, and a year overview."""

from __future__ import annotations

import asyncio
from datetime import date, timedelta
from typing import Annotated

from api.apaleo import client, metrics, reports
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter()

DEFAULT_TZ = "Europe/Berlin"
PAST_MONTHS_DEFAULT = 12
FUTURE_MONTHS_DEFAULT = 6


class AccountInfo(BaseModel):
    name: str | None = None
    code: str | None = None
    type: str | None = None


class PropertyInfo(BaseModel):
    id: str
    name: str | None = None
    city: str | None = None
    currency: str | None = None


class BootstrapResponse(BaseModel):
    account: AccountInfo
    today: str
    properties: list[PropertyInfo]


class MonthEntry(BaseModel):
    month: str
    is_future: bool
    is_current: bool
    days_in_month: int
    revenue_gross: float
    revenue_net: float
    accommodation_revenue_gross: float
    fnb_revenue_gross: float
    other_revenue_gross: float
    adr_gross: float | None = None
    adr_net: float | None = None
    revpar: float | None = None
    occupancy: float | None = None
    room_nights: int | None = None
    available_room_nights: int
    arrivals: int | None = None
    departures: int | None = None
    cancellations: int | None = None
    no_shows: int | None = None
    currency: str | None = None
    los: float | None = None
    delta_revenue: float | None = None
    delta_adr: float | None = None
    delta_revpar: float | None = None
    delta_occupancy: float | None = None


class RevenueRow(BaseModel):
    account: str | None = None
    number: int | str | None = None
    net: float
    gross: float
    level: int


class TravelPurpose(BaseModel):
    purpose: str | None = None
    count: int | None = None
    percent: float | None = None


class YearOverview(BaseModel):
    year: int
    ytd_revenue_gross: float
    ytd_room_nights: float
    ytd_arrivals: float
    ytd_cancellations: float
    ytd_revpar: float | None = None
    ytd_adr: float | None = None
    ytd_occupancy: float | None = None
    ytd_los: float | None = None
    otb_revenue_gross: float
    otb_room_nights: float
    otb_occupancy: float | None = None
    otb_adr: float | None = None
    forecast_revenue_gross: float
    months: list[MonthEntry]


class DashboardResponse(BaseModel):
    today: str
    currency: str
    selected_property: str
    current_month: MonthEntry
    previous_month: MonthEntry | None = None
    timeline: list[MonthEntry]
    revenue_breakdown: list[RevenueRow]
    travel_purpose: list[TravelPurpose]
    year_overview: YearOverview


def _resolve_properties(requested: str, properties: list[dict]) -> list[dict]:
    if requested in ("", "all"):
        return properties
    matches = [p for p in properties if p.get("id") == requested or p.get("code") == requested]
    if not matches:
        raise HTTPException(status_code=404, detail=f"Unknown property '{requested}'")
    return matches


async def _month_entry(
    property_ids: list[str], month_first: date, *, full_month: bool, today: date
) -> dict:
    month_end = metrics.add_months(month_first, 1)
    to_day = month_end if full_month else min(today + timedelta(days=1), month_end)

    entries = await asyncio.gather(
        *(reports.performance_report(property_id, month_first, to_day) for property_id in property_ids)
    )
    entry = entries[0] if len(entries) == 1 else metrics.combine_performance(list(entries))
    return {
        "month": metrics.month_key(month_first),
        "is_future": month_first > today,
        "is_current": month_first == metrics.month_start(today),
        "days_in_month": metrics.days_in_month(month_first),
        "revenue_gross": metrics.total_revenue(entry),
        "revenue_net": metrics.net_total_revenue(entry),
        "accommodation_revenue_gross": metrics.amount(entry.get("grossAccommodationRevenue")) or 0.0,
        "fnb_revenue_gross": metrics.amount(entry.get("grossFoodAndBeveragesRevenue")) or 0.0,
        "other_revenue_gross": metrics.amount(entry.get("grossOtherRevenue")) or 0.0,
        "adr_gross": metrics.amount(entry.get("grossAdr")),
        "adr_net": metrics.amount(entry.get("netAdr")),
        "revpar": metrics.amount(entry.get("revPar")),
        "occupancy": entry.get("occupancyPercentage"),
        "room_nights": entry.get("soldCount"),
        "available_room_nights": metrics.available_room_nights(entry),
        "arrivals": entry.get("arrivalsCount"),
        "departures": entry.get("departuresCount"),
        "cancellations": entry.get("cancellationsCount"),
        "no_shows": entry.get("noShowsCount"),
        "currency": metrics.currency_of(entry.get("grossAccommodationRevenue")),
    }


def _stay_metrics(room_nights_payload: dict | None) -> tuple[float | None, int]:
    """Average length of stay and the underlying room-night total."""
    if not room_nights_payload:
        return None, 0
    total = int(room_nights_payload.get("total") or 0)
    purposes = room_nights_payload.get("travelPurposeBreakdown") or []
    reservations = sum(len(p.get("reservationIds") or []) for p in purposes)
    return metrics.length_of_stay(total, reservations), total


async def _los_for_months(property_requested: str, months: list[dict]) -> dict[str, float | None]:
    """Average length of stay per month key, from the room-nights report."""
    if property_requested in ("", "all"):
        return {}

    async def one(entry: dict) -> tuple[str, float | None]:
        year, month = (int(part) for part in entry["month"].split("-"))
        try:
            payload = await reports.room_nights_report(property_requested, year, month)
        except client.ApaleoError:
            return entry["month"], None
        los, _ = _stay_metrics(payload)
        return entry["month"], los

    results = await asyncio.gather(*(one(entry) for entry in months))
    return {key: los for key, los in results if los is not None}


def _revenue_rows(tree: dict | None, level: int) -> list[dict]:
    if not tree:
        return []
    account = tree.get("account") or {}
    rows = [
        {
            "account": account.get("name"),
            "number": account.get("number"),
            "net": metrics.amount(tree.get("netAmount")) or 0.0,
            "gross": metrics.amount(tree.get("grossAmount")) or 0.0,
            "level": level,
        }
    ]
    for child in tree.get("children") or []:
        rows.extend(_revenue_rows(child, level + 1))
    return rows


async def _revenue_breakdown(property_ids: list[str], from_day: date, to_day: date) -> list[dict]:
    """Merged revenue account tree (top two levels) across the selected properties."""
    trees = await asyncio.gather(
        *(reports.revenues_report(property_id, from_day, to_day) for property_id in property_ids)
    )
    merged: dict[str, dict] = {}
    for tree in trees:
        for row in _revenue_rows(tree, 0):
            if row["level"] > 1:
                continue
            key = f"{row['level']}:{row['number']}"
            if key in merged:
                merged[key]["net"] = round(merged[key]["net"] + row["net"], 2)
                merged[key]["gross"] = round(merged[key]["gross"] + row["gross"], 2)
            else:
                merged[key] = row
    return sorted(merged.values(), key=lambda row: (row["level"], -row["gross"]))


def _add_deltas(entries: list[dict]) -> list[dict]:
    result: list[dict] = []
    previous: dict | None = None
    for entry in entries:
        enriched = {**entry}
        if previous is not None and not entry["is_future"] and not previous["is_future"]:
            enriched["delta_revenue"] = metrics.percent_delta(entry["revenue_gross"], previous["revenue_gross"])
            enriched["delta_adr"] = metrics.percent_delta(entry["adr_gross"], previous["adr_gross"])
            enriched["delta_revpar"] = metrics.percent_delta(entry["revpar"], previous["revpar"])
            enriched["delta_occupancy"] = metrics.percent_delta(entry["occupancy"], previous["occupancy"])
        result.append(enriched)
        previous = entry
    return result


def _weighted_average(entries: list[dict], value_field: str, weight_field: str) -> float | None:
    weight = sum(entry.get(weight_field) or 0.0 for entry in entries)
    if weight == 0:
        return None
    return round(
        sum((entry.get(value_field) or 0.0) * (entry.get(weight_field) or 0.0) for entry in entries) / weight, 2
    )


def _summed(entries: list[dict], field: str) -> float:
    return round(sum(entry.get(field) or 0.0 for entry in entries), 2)


def _year_summary(entries: list[dict], year: int) -> dict:
    year_entries = [entry for entry in entries if entry["month"].startswith(str(year))]
    past = [entry for entry in year_entries if not entry["is_future"]]
    future = [entry for entry in year_entries if entry["is_future"]]
    ytd_revenue = _summed(past, "revenue_gross")
    otb_revenue = _summed(future, "revenue_gross")
    return {
        "year": year,
        "ytd_revenue_gross": ytd_revenue,
        "ytd_room_nights": _summed(past, "room_nights"),
        "ytd_arrivals": _summed(past, "arrivals"),
        "ytd_cancellations": _summed(past, "cancellations"),
        "ytd_revpar": _weighted_average(past, "revpar", "available_room_nights"),
        "ytd_adr": _weighted_average(past, "adr_gross", "room_nights"),
        "ytd_occupancy": _weighted_average(past, "occupancy", "available_room_nights"),
        "ytd_los": _weighted_average(past, "los", "room_nights"),
        "otb_revenue_gross": otb_revenue,
        "otb_room_nights": _summed(future, "room_nights"),
        "otb_occupancy": _weighted_average(future, "occupancy", "available_room_nights"),
        "otb_adr": _weighted_average(future, "adr_gross", "room_nights"),
        "forecast_revenue_gross": round(ytd_revenue + otb_revenue, 2),
        "months": year_entries,
    }


async def _travel_purpose(property_requested: str, month_key: str) -> list[dict]:
    if property_requested in ("", "all"):
        return []
    year, month = (int(part) for part in month_key.split("-"))
    try:
        payload = await reports.arrivals_report(property_requested, year, month)
    except client.ApaleoError:
        return []
    purposes = payload.get("travelPurposeBreakdown") or []
    return [
        {"purpose": p.get("purpose"), "count": p.get("number"), "percent": p.get("percent")} for p in purposes
    ]


async def _bootstrap_payload() -> dict:
    try:
        account, properties = await asyncio.gather(reports.current_account(), reports.list_properties())
    except client.ApaleoError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    return {
        "account": {
            "name": account.get("name"),
            "code": account.get("code"),
            "type": account.get("type"),
        },
        "today": metrics.today_in(DEFAULT_TZ).isoformat(),
        "properties": [
            {
                "id": p["id"],
                "name": p.get("name"),
                "city": (p.get("location") or {}).get("city"),
                "currency": p.get("currencyCode"),
            }
            for p in properties
        ],
    }


@router.get("/bootstrap", operation_id="dashboard_bootstrap")
async def bootstrap() -> BootstrapResponse:
    """Account, properties, and today's date in the account timezone."""
    return BootstrapResponse.model_validate(await _bootstrap_payload())


@router.get("", operation_id="dashboard_overview")
async def overview(
    property: Annotated[str, Query(description="Property ID, or 'all' for every property")] = "all",
    past_months: Annotated[int, Query(ge=1, le=24)] = PAST_MONTHS_DEFAULT,
    future_months: Annotated[int, Query(ge=0, le=24)] = FUTURE_MONTHS_DEFAULT,
) -> DashboardResponse:
    """Everything the dashboard shows: current month, history, future, and the year overview."""
    try:
        bootstrap_data = await _bootstrap_payload()
        selected = _resolve_properties(property, bootstrap_data["properties"])
        property_ids = [p["id"] for p in selected]

        today = metrics.today_in(DEFAULT_TZ)
        current_month = metrics.month_start(today)

        history_first = metrics.add_months(current_month, -past_months)
        timeline_months = metrics.month_span(history_first, past_months + 1 + future_months)

        timeline = list(
            await asyncio.gather(
                *(
                    _month_entry(property_ids, month, full_month=month != current_month, today=today)
                    for month in timeline_months
                )
            )
        )
        los_map = await _los_for_months(property, timeline)
        timeline = _add_deltas([{**entry, "los": los_map.get(entry["month"])} for entry in timeline])

        current_entry = next(entry for entry in timeline if entry["is_current"])
        previous_key = metrics.month_key(metrics.add_months(current_month, -1))
        previous_entry = next((entry for entry in timeline if entry["month"] == previous_key), None)

        breakdown_from = current_month
        breakdown_to = min(today + timedelta(days=1), metrics.add_months(current_month, 1))
        breakdown, purposes = await asyncio.gather(
            _revenue_breakdown(property_ids, breakdown_from, breakdown_to),
            _travel_purpose(property, metrics.month_key(current_month)),
        )

        return DashboardResponse.model_validate(
            {
                "today": today.isoformat(),
                "currency": current_entry.get("currency") or "EUR",
                "selected_property": property,
                "current_month": current_entry,
                "previous_month": previous_entry,
                "timeline": timeline,
                "revenue_breakdown": breakdown,
                "travel_purpose": purposes,
                "year_overview": _year_summary(timeline, today.year),
            }
        )
    except client.ApaleoError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
