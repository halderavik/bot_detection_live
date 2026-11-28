"""The OpenAI limiter waits for a free slot instead of failing at once."""

import asyncio
import time

import pytest

from app.services.openai_service import RateLimiter


@pytest.mark.asyncio
async def test_waits_for_a_slot_then_gives_up_after_the_wait():
    limiter = RateLimiter(max_requests=2, window_minutes=1)
    limiter.window_seconds = 0.3
    assert await limiter.acquire() and await limiter.acquire()
    assert not await limiter.acquire()  # no wait: refused at once
    started = time.monotonic()
    assert await limiter.acquire(wait=2)  # a slot frees after 0.3 s
    assert 0.2 < time.monotonic() - started < 1.5
    limiter.window_seconds = 60
    await limiter.acquire()  # window full again (2 recent requests)
    assert not await limiter.acquire(wait=0.2)


@pytest.mark.asyncio
async def test_many_waiters_all_get_slots_in_turn():
    limiter = RateLimiter(max_requests=3, window_minutes=1)
    limiter.window_seconds = 0.2
    results = await asyncio.gather(*(limiter.acquire(wait=3) for _ in range(9)))
    assert all(results)
