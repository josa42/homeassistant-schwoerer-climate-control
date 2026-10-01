"""Tests for the dashboard strategy's wiring.

What the strategy renders is the frontend's business, but three things on this
side can break silently: the asset going missing, the tag names the frontend
looks a strategy up by, and the version that busts the browser's cache drifting
away from the release.
"""

from __future__ import annotations

import json
from pathlib import Path

from custom_components.schwoerer_climate_control import (
    STRATEGY_FILENAME,
    STRATEGY_URL_PATH,
    STRATEGY_VERSION,
)
from custom_components.schwoerer_climate_control.const import DOMAIN

PACKAGE = Path("custom_components/schwoerer_climate_control")
STRATEGY = PACKAGE / "www" / STRATEGY_FILENAME


def test_the_asset_is_there() -> None:
    assert STRATEGY.is_file()


def test_the_url_serves_the_file_that_exists() -> None:
    assert STRATEGY_URL_PATH == f"/{DOMAIN}/{STRATEGY_FILENAME}"


def test_the_version_matches_the_manifest() -> None:
    # The release script bumps both. If they drift, browsers keep running the
    # strategy they cached before the upgrade, which reads as the new code not
    # working at all.
    manifest = json.loads((PACKAGE / "manifest.json").read_text(encoding="utf-8"))
    assert STRATEGY_VERSION == manifest["version"]


def test_it_registers_the_tags_the_frontend_looks_for() -> None:
    source = STRATEGY.read_text(encoding="utf-8")
    for tag in (
        "ll-strategy-dashboard-schwoerer-climate-control",
        "ll-strategy-view-schwoerer-climate-control",
    ):
        assert tag in source, tag


def test_it_asks_for_our_own_entities_only() -> None:
    source = STRATEGY.read_text(encoding="utf-8")
    assert f'const DOMAIN = "{DOMAIN}"' in source
    assert "entry.platform === DOMAIN" in source
