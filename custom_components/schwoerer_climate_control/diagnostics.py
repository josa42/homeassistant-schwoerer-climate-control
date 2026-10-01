"""The full trace, for when the sensors and the logbook are not enough.

Everything the decision sensors keep out of the recorder is here in full, plus
the writes the controller would send right now and whether each one is needed.
That last part is the answer to "it decided that, so why has nothing happened".
"""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from .coordinator import ClimateControlConfigEntry


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ClimateControlConfigEntry
) -> dict[str, Any]:
    """Everything known about the current state of the controller."""
    coordinator = entry.runtime_data
    decision = coordinator.data

    writes = []
    if decision is not None:
        writes = [
            {
                "label": write.label,
                "entity_id": write.entity_id,
                "expect": write.expect,
                "needed": coordinator.needs_write(write),
            }
            for write in coordinator.plan(decision)
        ]

    return {
        "controls": {
            "enabled": coordinator.enabled,
            "dry_run": coordinator.dry_run,
            "mode": str(coordinator.mode),
            "holiday": coordinator.holiday,
            "fan_request": str(coordinator.fan_request),
        },
        "unit": {
            "operation_mode": coordinator.operation_mode,
            "stuck_writes": list(coordinator.stuck_writes),
        },
        "configuration": {
            "hub": coordinator.hub_config,
            "rooms": [
                {"title": room.title, "room_id": room.room_id, "config": room.config}
                for room in coordinator.rooms.values()
            ],
        },
        "decision": None if decision is None else decision.as_dict(),
        "writes": writes,
        "history": [entry.as_dict() for entry in coordinator.history],
    }
