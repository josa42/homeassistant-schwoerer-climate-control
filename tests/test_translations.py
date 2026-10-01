"""The translation files have to agree with each other and with the code.

A missing key does not fail anywhere at runtime: Home Assistant shows the key
itself, so a form quietly turns into a list of identifiers.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from custom_components.schwoerer_climate_control.const import (
    ActuatorKind,
    FanMode,
    Intent,
    Mode,
    RoomIntent,
)

BASE = Path("custom_components/schwoerer_climate_control")
LANGUAGES = ("en", "de")


def load(name: str) -> dict[str, Any]:
    return json.loads((BASE / name).read_text(encoding="utf-8"))


def keys(value: Any, prefix: str = "") -> set[str]:
    if not isinstance(value, dict):
        return {prefix}
    found: set[str] = set()
    for key, child in value.items():
        found |= keys(child, f"{prefix}.{key}" if prefix else key)
    return found


def test_strings_and_english_are_the_same() -> None:
    assert load("strings.json") == load("translations/en.json")


@pytest.mark.parametrize("language", LANGUAGES)
def test_every_language_has_every_key(language: str) -> None:
    assert keys(load(f"translations/{language}.json")) == keys(load("strings.json"))


@pytest.mark.parametrize("language", LANGUAGES)
def test_nothing_is_left_untranslated(language: str) -> None:
    def walk(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                walk(child, f"{path}.{key}")
        else:
            assert isinstance(value, str) and value.strip(), f"{path} is empty"

    walk(load(f"translations/{language}.json"), language)


@pytest.mark.parametrize("language", LANGUAGES)
def test_every_mode_and_intent_can_be_shown(language: str) -> None:
    data = load(f"translations/{language}.json")["entity"]
    assert set(data["select"]["mode"]["state"]) == {mode.value for mode in Mode}
    assert {mode.value for mode in FanMode} <= set(data["select"]["fan"]["state"])
    shown = set(data["sensor"]["decision"]["state"])
    assert {intent.value for intent in Intent} <= shown
    assert {intent.value for intent in RoomIntent} <= shown


@pytest.mark.parametrize("language", LANGUAGES)
def test_every_actuator_kind_can_be_chosen(language: str) -> None:
    options = load(f"translations/{language}.json")["selector"]["actuator"]["options"]
    assert set(options) == {kind.value for kind in ActuatorKind}
