from dataclasses import FrozenInstanceError

import pytest

from app.domain import EventType, InvalidTransition, Parcel, ParcelState, apply_event


def parcel():
    return Parcel("pcl_test", "merchant-1", 0, "Cairo")


def test_delivery_lifecycle_and_input_immutability():
    original = parcel()
    dispatched = apply_event(original, EventType.DISPATCH)
    failed = apply_event(dispatched, EventType.FAIL)
    retried = apply_event(failed, EventType.DISPATCH)
    delivered = apply_event(retried, EventType.DELIVER)
    assert original.state is ParcelState.CREATED and original.attempts == 0
    assert dispatched.attempts == 1 and retried.attempts == 2
    assert delivered.state is ParcelState.DELIVERED and delivered.attempts == 2
    with pytest.raises(FrozenInstanceError):
        original.attempts = 1


def test_third_failed_attempt_can_only_be_returned():
    current = parcel()
    for _ in range(3):
        current = apply_event(current, EventType.DISPATCH)
        current = apply_event(current, EventType.FAIL)
    with pytest.raises(InvalidTransition):
        apply_event(current, EventType.DISPATCH)
    assert apply_event(current, EventType.RETURN).state is ParcelState.RETURNED


@pytest.mark.parametrize("event", list(EventType))
def test_created_only_accepts_dispatch(event):
    if event is EventType.DISPATCH:
        assert apply_event(parcel(), event).state is ParcelState.OUT_FOR_DELIVERY
    else:
        with pytest.raises(InvalidTransition):
            apply_event(parcel(), event)
