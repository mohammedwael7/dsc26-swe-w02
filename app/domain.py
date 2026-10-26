"""Pure parcel lifecycle rules; this module has no web-framework dependencies."""

from dataclasses import dataclass, replace
from enum import StrEnum

MAX_ATTEMPTS = 3


class ParcelState(StrEnum):
    CREATED = "created"
    OUT_FOR_DELIVERY = "out_for_delivery"
    FAILED_ATTEMPT = "failed_attempt"
    DELIVERED = "delivered"
    RETURNED = "returned"


class EventType(StrEnum):
    DISPATCH = "dispatch"
    DELIVER = "deliver"
    FAIL = "fail"
    RETURN = "return"


class InvalidTransition(Exception):
    """Raised when an event is not allowed for a parcel's current state."""


@dataclass(frozen=True)
class Parcel:
    id: str
    merchant_ref: str
    cod_amount_piastres: int
    address_text: str
    state: ParcelState = ParcelState.CREATED
    attempts: int = 0


def apply_event(parcel: Parcel, event: EventType) -> Parcel:
    """Return the next immutable parcel value, or reject an invalid event."""
    if parcel.state is ParcelState.CREATED and event is EventType.DISPATCH:
        return replace(parcel, state=ParcelState.OUT_FOR_DELIVERY, attempts=parcel.attempts + 1)
    if parcel.state is ParcelState.OUT_FOR_DELIVERY:
        if event is EventType.DELIVER:
            return replace(parcel, state=ParcelState.DELIVERED)
        if event is EventType.FAIL:
            return replace(parcel, state=ParcelState.FAILED_ATTEMPT)
    if parcel.state is ParcelState.FAILED_ATTEMPT:
        if event is EventType.DISPATCH and parcel.attempts < MAX_ATTEMPTS:
            return replace(parcel, state=ParcelState.OUT_FOR_DELIVERY, attempts=parcel.attempts + 1)
        if event is EventType.RETURN:
            return replace(parcel, state=ParcelState.RETURNED)
    raise InvalidTransition(f"Cannot apply {event} while parcel is {parcel.state}.")
