import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from finops import report


def test_build_report_has_savings():
    md = report.build_report(100000, 25000, {"batching": 40000, "caching": 35000})
    assert "75%" in md and "Projected savings" in md and "batching" in md


def test_build_report_includes_your_turn_extensions():
    md = report.build_report(
        100000,
        25000,
        {"batching": 40000},
        extensions={
            "cache_economics": {"candidates": 10, "enabled": 9, "break_even_reads": 0.28},
            "reasoning_budget": {"requests": 3, "daily_cost": 1.5, "daily_wh": 200},
        },
    )
    assert "Your Turn Extensions" in md
    assert "Cache economics" in md
    assert "Reasoning budget" in md
