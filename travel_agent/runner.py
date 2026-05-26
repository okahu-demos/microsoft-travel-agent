"""Execution helpers for running the travel assistant in single and multi-turn modes."""

from __future__ import annotations

import logging

from agent_framework import AgentSession

from .agent_runtime import get_flight_agent
from .session import resolve_session, session_identifier

logger = logging.getLogger(__name__)


async def run_agent(request: str, session: AgentSession | str | None = None) -> tuple[str, AgentSession]:
    """Run one user request through the flight agent and return response text and session."""
    try:
        flight_agent = await get_flight_agent()
    except Exception as exc:
        logger.error("Failed to initialize agent. Check Azure OpenAI settings in .env", exc_info=True)
        raise RuntimeError("Failed to initialize Azure OpenAI assistant client.") from exc

    resolved_session = resolve_session(flight_agent, session)
    response = await flight_agent.run(request, session=resolved_session)
    return response.text, resolved_session


async def multi_turn_example() -> None:
    """Demonstrate multi-turn usage and simulated app-restart resume behavior."""
    print("\nCreating new session...")
    print("\n[User]: Book a flight from BOM to JFK for December 15th")
    response1, session = await run_agent("Book a flight from BOM to JFK for December 15th")
    print(f"[Agent]: {response1}")
    print(f"\nSession: {session_identifier(session)}")
    print("Session created. Persist the full session payload to resume later.")

    print("\n[User]: Book a return flight for December 20th")
    response2, session = await run_agent("Book a return flight for December 20th", session=session)
    print(f"[Agent]: {response2}")

    print("\n" + "=" * 60)
    print("Simulating session resume (like after app restart)")
    print("=" * 60)

    persisted_session_payload = session.to_dict()
    restored_session = AgentSession.from_dict(persisted_session_payload)

    print(f"Session resumed with ID: {session_identifier(restored_session)}")
    print("Conversation history restored from persisted session payload")

    print("\n[User]: What did we talk about?")
    response3, _ = await run_agent("What did we talk about?", session=restored_session)
    print(f"[Agent]: {response3}")

    print("\nAll conversation updates saved in the current session payload.")
