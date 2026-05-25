"""Agent construction and lifecycle helpers."""

from __future__ import annotations

import asyncio

from agent_framework import Agent

from .client import create_assistants_client
from .tools import book_flight

_flight_agent: Agent | None = None
_flight_agent_lock = asyncio.Lock()


async def setup_agents() -> Agent:
    """Construct a flight booking agent with configured tools and instructions."""
    client = create_assistants_client()
    return Agent(
        client=client,
        instructions=(
            "You are a Flight Booking Assistant. "
            "Your goal is to help users book flights between any two cities or airports. "
            "Book the requested flight and provide confirmation details."
        ),
        name="MS_Flight_Booking_Agent",
        tools=[book_flight],
    )


async def get_flight_agent() -> Agent:
    """Return a singleton flight agent instance, creating it once per process."""
    global _flight_agent
    if _flight_agent is not None:
        return _flight_agent

    async with _flight_agent_lock:
        if _flight_agent is None:
            _flight_agent = await setup_agents()
    return _flight_agent
