from __future__ import annotations

from pathlib import Path


TASK_YAML = Path(__file__).with_name("wiki_pageviews.yaml")


def test_prompt_pins_wikimedia_daily_route_and_debug_check() -> None:
    text = TASK_YAML.read_text()

    assert "/daily/{date1}/{date2}" in text
    assert "Do not omit the literal `/daily/` path segment" in text
    assert "Run a debug check with article=UiPath, date1=20240101, date2=20240115" in text
