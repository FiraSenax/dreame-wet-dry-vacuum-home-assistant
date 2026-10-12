"""Model-specific H15 Mix command confirmation."""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any


async def async_start_self_clean(
    coordinator: Any,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> None:
    """Start self-cleaning and confirm the observed device state.

    The H15 Mix has returned per-property code 1 even when it started the
    cycle. Only a subsequent status change counts as success.
    """
    snapshot = coordinator.snapshot
    status = coordinator.props.get((2, 1), snapshot.get("status"))
    if not snapshot.get("online") or status not in (4, 15):
        raise RuntimeError("H15 Mix must be charging on its station")

    await coordinator.api.set_property(coordinator.device_id, 1, 1, 1)
    for _ in range(5):
        await sleep(2)
        await coordinator.async_request_refresh()
        if coordinator.snapshot.get("status") in (5, 26, 27, 28):
            return
    raise RuntimeError("H15 Mix did not confirm self-cleaning")
