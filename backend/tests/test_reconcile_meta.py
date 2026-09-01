from decimal import Decimal

from scripts.reconcile_meta import compare_totals


def test_reconciliation_reports_exact_differences() -> None:
    local = {
        "spend": "100.00", "impressions": 1000, "clicks": 50,
        "link_clicks": 40, "leads": 3, "conversations": 2,
        "landing_page_views": 30,
    }
    meta = {
        "spend": "101.25", "impressions": 1000, "clicks": 50,
        "link_clicks": 40, "leads": 3, "conversations": 3,
        "landing_page_views": 30,
    }

    result = compare_totals(local, meta)

    assert result["matches"] is False
    assert result["metrics"]["spend"] == {
        "local": Decimal("100.00"), "meta": Decimal("101.25"), "difference": Decimal("-1.25"), "matches": False,
    }
    assert result["metrics"]["conversations"]["difference"] == -1
