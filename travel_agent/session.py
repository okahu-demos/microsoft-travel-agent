"""Session normalization helpers for agent invocations."""

from __future__ import annotations

from agent_framework import Agent, AgentSession
from agent_framework.openai import OpenAIChatCompletionClient


def resolve_session(flight_agent: Agent, session: AgentSession | str | None) -> AgentSession:
    """Resolve caller-provided session input into an AgentSession instance."""
    if session is None:
        return flight_agent.create_session()

    if isinstance(session, AgentSession):
        return session

    service_session_id = session.strip()
    if not service_session_id:
        raise ValueError("Session ID cannot be empty.")

    # Chat Completions does not support ID-only server resume.
    if isinstance(flight_agent.client, OpenAIChatCompletionClient):
        raise ValueError(
            "String-based session resume is not supported with OpenAI Chat Completions. "
            "Persist and restore the full AgentSession (session.to_dict()/AgentSession.from_dict())."
        )

    return flight_agent.get_session(service_session_id=service_session_id)


def session_identifier(session: AgentSession) -> str:
    """Return the best resumable identifier for display/logging purposes."""
    return session.service_session_id or session.session_id
