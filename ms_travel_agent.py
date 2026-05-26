"""Compatibility entrypoint for the Microsoft travel agent sample.

This module re-exports the most-used functions from the refactored
`travel_agent` package so existing imports continue to work.
"""

from __future__ import annotations

import asyncio
import logging

from travel_agent.agent_runtime import get_flight_agent, setup_agents
from travel_agent.client import create_assistants_client
from travel_agent.runner import multi_turn_example, run_agent
from travel_agent.session import resolve_session, session_identifier
from travel_agent.tools import book_flight

from monocle_apptrace import setup_monocle_telemetry

setup_monocle_telemetry(workflow_name="ms_travel_agent",
                        monocle_exporters_list='file,okahu')
__all__ = [
    "book_flight",
    "create_assistants_client",
    "setup_agents",
    "get_flight_agent",
    "resolve_session",
    "session_identifier",
    "run_agent",
    "multi_turn_example",
]

if __name__ == "__main__":
    """Run a multi-turn demo when invoked as a script."""
    logging.basicConfig(level=logging.INFO)
    asyncio.run(multi_turn_example())
