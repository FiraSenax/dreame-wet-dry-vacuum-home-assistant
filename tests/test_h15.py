"""H15 Mix command confirmation without Home Assistant or a live device."""
import asyncio
from types import SimpleNamespace

import pytest

from custom_components.dreame_wet_dry_vacuum.h15 import async_start_self_clean


async def no_sleep(_seconds):
    pass


def coordinator(*, online=True, status=4, status_after_refresh=26):
    sent = []
    snapshot = {"online": online, "status": status}

    async def set_property(*args):
        sent.append(args)
        return False  # observed live: code 1 can still start the cycle

    async def refresh():
        if status_after_refresh is not None:
            snapshot["status"] = status_after_refresh

    return SimpleNamespace(
        snapshot=snapshot,
        props={(2, 1): status},
        api=SimpleNamespace(set_property=set_property),
        device_id="test-device",
        async_request_refresh=refresh,
        sent=sent,
    )


def test_code_one_is_accepted_after_observed_state_change():
    device = coordinator()
    asyncio.run(async_start_self_clean(device, no_sleep))
    assert device.sent == [("test-device", 1, 1, 1)]


@pytest.mark.parametrize("online,status", [(False, 4), (True, 23), (True, 26)])
def test_command_blocked_unless_online_and_charging(online, status):
    device = coordinator(online=online, status=status)
    with pytest.raises(RuntimeError, match="charging on its station"):
        asyncio.run(async_start_self_clean(device, no_sleep))
    assert device.sent == []


def test_no_state_change_is_reported_as_failure():
    device = coordinator(status_after_refresh=None)
    with pytest.raises(RuntimeError, match="did not confirm"):
        asyncio.run(async_start_self_clean(device, no_sleep))
    assert len(device.sent) == 1
