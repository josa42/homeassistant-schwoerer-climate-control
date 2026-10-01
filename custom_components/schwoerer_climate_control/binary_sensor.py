"""One indicator: something the controller was told to read is not readable."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import ClimateControlConfigEntry, ClimateControlCoordinator
from .entity import HubEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ClimateControlConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([MissingInputsBinarySensor(entry.runtime_data)])


class MissingInputsBinarySensor(HubEntity, BinarySensorEntity):
    """On while a configured input cannot be read.

    v1 skipped a missing sensor silently, which turned a dead CO₂ sensor into
    good air and a dead contact into a closed window. This is the opposite of
    that: a failure is visible before it has to be inferred from behaviour.

    Named after what switches it on rather than after the consequence. "Degraded"
    was the first name and it did not say what was degraded, which is a question
    somebody then has to ask.
    """

    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, coordinator: ClimateControlCoordinator) -> None:
        super().__init__(coordinator, "missing_inputs")

    @property
    def is_on(self) -> bool:
        decision = self.coordinator.data
        return bool(decision and decision.degraded)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        decision = self.coordinator.data
        return {
            "failed_inputs": list(decision.degraded) if decision else [],
            "stuck_writes": list(self.coordinator.stuck_writes),
        }
