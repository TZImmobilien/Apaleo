"""Tests for the pure dashboard metric helpers."""

from datetime import date

from api.apaleo import metrics


def test_add_months_crosses_year_boundaries() -> None:
    assert metrics.add_months(date(2026, 11, 17), 2) == date(2027, 1, 1)
    assert metrics.add_months(date(2026, 1, 1), -1) == date(2025, 12, 1)
    assert metrics.add_months(date(2026, 11, 17), -12) == date(2025, 11, 1)


def test_month_span_covers_history_current_and_future() -> None:
    months = metrics.month_span(date(2025, 11, 1), 20)
    assert len(months) == 20
    assert months[0] == date(2025, 11, 1)
    assert months[-1] == date(2027, 6, 1)


def test_percent_delta() -> None:
    assert metrics.percent_delta(110.0, 100.0) == 10.0
    assert metrics.percent_delta(50.0, 100.0) == -50.0
    assert metrics.percent_delta(10.0, 0.0) is None
    assert metrics.percent_delta(None, 10.0) is None


def test_length_of_stay() -> None:
    assert metrics.length_of_stay(221, 100) == 2.21
    assert metrics.length_of_stay(0, 0) is None


def test_total_revenue_sums_all_segments() -> None:
    entry = {
        "grossAccommodationRevenue": {"amount": 3834.52, "currency": "EUR"},
        "grossFoodAndBeveragesRevenue": {"amount": 100.0, "currency": "EUR"},
        "grossOtherRevenue": {"amount": 240.0, "currency": "EUR"},
    }
    assert metrics.total_revenue(entry) == 4174.52
    assert metrics.net_total_revenue(entry) == 0.0


def test_combine_performance_recomputes_derived_kpis() -> None:
    entries = [
        {
            "houseCount": 100,
            "outOfOrderCount": 0,
            "soldCount": 60,
            "arrivalsCount": 30,
            "grossAccommodationRevenue": {"amount": 6000.0, "currency": "EUR"},
            "netAccommodationRevenue": {"amount": 5500.0, "currency": "EUR"},
        },
        {
            "houseCount": 100,
            "outOfOrderCount": 10,
            "soldCount": 40,
            "arrivalsCount": 20,
            "grossAccommodationRevenue": {"amount": 4000.0, "currency": "EUR"},
            "netAccommodationRevenue": {"amount": 3700.0, "currency": "EUR"},
        },
    ]
    combined = metrics.combine_performance(entries)
    assert combined["houseCount"] == 200
    assert combined["soldCount"] == 100
    assert combined["grossAccommodationRevenue"]["amount"] == 10000.0
    # 100 sold of 190 sellable unit nights
    assert combined["occupancyPercentage"] == 52.63
    assert combined["grossAdr"]["amount"] == 100.0
    assert combined["revPar"]["amount"] == 52.63


def test_month_interval_partial_month_is_inclusive_of_today() -> None:
    today = date(2026, 11, 17)
    from_day, to_day = metrics.month_interval(today, full_month=False, tz_name="Europe/Berlin")
    assert from_day == date(2026, 11, 1)
    assert to_day == date(2026, 11, 18)
    full_from, full_to = metrics.month_interval(today, full_month=True, tz_name="Europe/Berlin")
    assert full_from == date(2026, 11, 1)
    assert full_to == date(2026, 12, 1)
