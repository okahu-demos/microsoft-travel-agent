import os
import sys
import pytest
import pytest_asyncio
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from mic_travel_agent import setup_agents

supervisor = None


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_supervior():
    """Set up the travel booking supervisor agent."""
    global supervisor
    try:
        supervisor = await setup_agents()
    except Exception as exc:
        pytest.skip(f"Skipping fluent tests: unable to initialize Azure assistant client ({exc})")


async def _run_prompt_or_skip(prompt: str):
    thread = supervisor.get_new_thread()
    try:
        await supervisor.run(prompt, thread=thread)
    except Exception as exc:
        message = str(exc)
        if "Resource not found" in message or "Error code: 404" in message:
            pytest.skip(
                "Skipping fluent tests: Azure OpenAI endpoint/deployment is not reachable or invalid (404)."
            )
        raise


@pytest.mark.asyncio
async def test_agent_and_tool_invocation(monocle_trace_asserter):
    prompt = "Book a flight from San Francisco to Mumbai on April 30th 2026."
    await _run_prompt_or_skip(prompt)

    monocle_trace_asserter.called_tool("book_flight", "MS_Flight_Booking_Agent") \
        .contains_input("from_airport").contains_input("SFO") \
        .contains_input("to_airport").contains_input("BOM") \
        .contains_output("FLIGHT BOOKING CONFIRMED") \
        .contains_output("SFO to BOM")

    monocle_trace_asserter.called_agent("MS_Flight_Booking_Agent") \
        .contains_input(prompt) \
        .contains_output("flight") \
        .contains_output("San Francisco") \
        .contains_output("Mumbai")


@pytest.mark.asyncio
async def test_tool_invocation(monocle_trace_asserter):
    prompt = "Book a flight from Chennai to Mumbai on April 30th 2026."
    await _run_prompt_or_skip(prompt)

    monocle_trace_asserter.called_tool("book_flight", "MS_Flight_Booking_Agent") \
        .contains_input("from_airport").contains_input("MAA") \
        .contains_input("to_airport").contains_input("BOM") \
        .contains_output("FLIGHT BOOKING CONFIRMED") \
        .contains_output("MAA to BOM")


@pytest.mark.asyncio
async def test_agent_invocation(monocle_trace_asserter):
    prompt = "Book a flight from Chennai to Bengaluru for 28th April 2026."
    await _run_prompt_or_skip(prompt)

    monocle_trace_asserter.called_agent("MS_Flight_Booking_Agent") \
        .contains_input(prompt) \
        .contains_output("flight") \
        .contains_output("Chennai") \
        .contains_output("Bengaluru")


if __name__ == "__main__":
    pytest.main([__file__])
