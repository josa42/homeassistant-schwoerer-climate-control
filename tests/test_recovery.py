"""Tests for the bypass measurement, which is the one thing it can do about it."""

from __future__ import annotations

import pytest

from custom_components.schwoerer_climate_control.recovery import (
    EFFECTIVE_BELOW,
    MIN_GRADIENT,
    measure,
)


def test_full_recovery_is_what_a_closed_exchanger_looks_like() -> None:
    # Supply air arrives almost at extract temperature: everything recovered.
    recovery = measure(supply=21.0, extract=22.0, outdoor=7.0, bypass_open=False)
    assert recovery.ratio == pytest.approx(0.933, abs=0.001)
    assert recovery.meaningful is True
    assert recovery.effective is None, "it is not open, so there is nothing to judge"


def test_a_damper_that_reports_open_while_the_air_goes_through_the_core() -> None:
    # The finding this sensor exists for: 123 says open, the air says otherwise.
    recovery = measure(supply=21.0, extract=22.0, outdoor=7.0, bypass_open=True)
    assert recovery.ratio > EFFECTIVE_BELOW
    assert recovery.effective is False


def test_a_bypass_that_works_shows_up_at_once() -> None:
    # Supply air near outdoor: the air took the parallel channel.
    recovery = measure(supply=9.0, extract=22.0, outdoor=7.0, bypass_open=True)
    assert recovery.ratio < EFFECTIVE_BELOW
    assert recovery.effective is True


def test_too_little_to_recover_means_no_verdict() -> None:
    # With outdoor near the extract air, a working bypass and a closed one look
    # the same, so the measurement says nothing rather than guessing.
    recovery = measure(supply=21.5, extract=22.0, outdoor=20.0, bypass_open=True)
    assert recovery.ratio is None
    assert recovery.meaningful is False
    assert recovery.effective is None
    assert recovery.gradient == 2.0


def test_the_gradient_threshold_is_the_documented_one() -> None:
    just_under = measure(22.0, 22.0, 22.0 - MIN_GRADIENT + 0.1, True)
    just_over = measure(22.0, 22.0, 22.0 - MIN_GRADIENT - 0.1, True)
    assert just_under.meaningful is False
    assert just_over.meaningful is True


@pytest.mark.parametrize(
    ("supply", "extract", "outdoor"),
    [(None, 22.0, 7.0), (21.0, None, 7.0), (21.0, 22.0, None)],
)
def test_a_missing_temperature_answers_nothing(supply, extract, outdoor) -> None:
    recovery = measure(supply, extract, outdoor, True)
    assert recovery.ratio is None
    assert recovery.effective is None


def test_an_unread_bypass_leaves_the_verdict_open() -> None:
    recovery = measure(supply=9.0, extract=22.0, outdoor=7.0, bypass_open=None)
    assert recovery.ratio is not None
    assert recovery.effective is None
