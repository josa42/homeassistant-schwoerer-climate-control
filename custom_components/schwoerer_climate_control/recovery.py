"""Measuring whether the bypass actually moves any air.

The damper cannot be commanded, only steered through the conditions the unit
evaluates, so the controller's part is to report. On the unit this was written
for, register 123 moves and the flap is audible, and yet the supply air shows
full heat recovery whether it reports open or closed: across two weeks there is
no hour in which the air departed from the core. That is a fault in the bypass
path rather than in the actuator or the register.

Publishing the measurement is what keeps the two apart. A bypass that starts
working shows up at once, and one that never does cannot be mistaken for a
controller that is not trying.

Pure, with no Home Assistant import, like the engine.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Below this difference between outdoor and extract air the measurement has no
#: power: with little to recover, a working bypass and a closed one look alike.
MIN_GRADIENT = 5.0

#: Recovery below this, while the damper reports open, is a bypass doing
#: something. A heuristic rather than a specification: the measurements have
#: 0.88 to 0.96 while it reports open and 0.89 while it reports closed, so
#: anything near those figures is the air going through the core either way.
EFFECTIVE_BELOW = 0.70


@dataclass(frozen=True, slots=True)
class Recovery:
    """What the temperatures say about the exchanger and the damper."""

    #: Heat recovered by the exchanger, 0 to 1, or None when it cannot be told.
    ratio: float | None
    #: How much there was to recover, in kelvin.
    gradient: float | None
    #: Whether the gradient was large enough for the ratio to mean anything.
    meaningful: bool
    #: What register 123 reports, if it was read.
    bypass_open: bool | None
    #: Whether the damper is reported open and the air agrees. None when the
    #: question does not arise: no reading, nothing to recover, or a damper that
    #: reports closed, which recovering fully is the right answer for.
    effective: bool | None


def measure(
    supply: float | None,
    extract: float | None,
    outdoor: float | None,
    bypass_open: bool | None,
) -> Recovery:
    """Recovery from the three temperatures, as the research computed it.

    ``(T3 - T10) / (T5 - T10)``, where T3 is the supply air downstream of the
    exchanger, T5 the extract air and T10 outdoor. If the damper opened, T3 would
    fall towards outdoor and the ratio with it.
    """
    if supply is None or extract is None or outdoor is None:
        return Recovery(None, None, False, bypass_open, None)

    gradient = extract - outdoor
    if abs(gradient) < MIN_GRADIENT:
        return Recovery(None, round(gradient, 2), False, bypass_open, None)

    ratio = (supply - outdoor) / gradient
    # Only a damper that reports open can be judged. A closed one recovering
    # fully is the exchanger doing its job, and calling that ineffective would
    # raise a fault for most of the year.
    effective = None if not bypass_open else ratio < EFFECTIVE_BELOW
    return Recovery(round(ratio, 3), round(gradient, 2), True, bypass_open, effective)
