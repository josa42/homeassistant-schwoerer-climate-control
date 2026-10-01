"""Rendering a decision change into the logbook.

This is where the history lives. A sensor's attributes answer what is true now,
and the question is almost always about the past: why was the auxiliary heater on
at three in the morning. An entry per change, carrying the finished sentence,
answers that for as long as the logbook is kept, and costs the recorder one row
rather than a trace four times an hour.
"""

from __future__ import annotations

from collections.abc import Callable

from homeassistant.components.logbook import (
    LOGBOOK_ENTRY_ENTITY_ID,
    LOGBOOK_ENTRY_MESSAGE,
    LOGBOOK_ENTRY_NAME,
)
from homeassistant.core import Event, HomeAssistant, callback

from .const import DOMAIN, EVENT_DECISION


@callback
def async_describe_events(
    hass: HomeAssistant,
    async_describe_event: Callable[[str, str, Callable[[Event], dict[str, str]]], None],
) -> None:
    """Register the describer for the decision event."""

    @callback
    def describe(event: Event) -> dict[str, str]:
        data = event.data
        return {
            LOGBOOK_ENTRY_NAME: data.get("name", "Climate control"),
            LOGBOOK_ENTRY_MESSAGE: data.get("message", ""),
            LOGBOOK_ENTRY_ENTITY_ID: data.get("entity_id"),
        }

    async_describe_event(DOMAIN, EVENT_DECISION, describe)
