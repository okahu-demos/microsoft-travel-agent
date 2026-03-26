import os
import sys
import pytest
import pytest_asyncio
from monocle_test_tools import TraceAssertion
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from mic_travel_agent import setup_agents

supervisor = None


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_supervisor():
    """Set up the travel booking supervisor agent."""
    global supervisor
    try:
        supervisor = await setup_agents()
    except Exception as exc:
        pytest.skip(f"Skipping tests: unable to initialize Azure assistant client ({exc})")


@pytest.mark.asyncio
async def test_agent_and_tool_invocation(monocle_trace_asserter: TraceAssertion):
    prompt = "Book a flight from San Francisco to Mumbai on April 30th 2026."
    await monocle_trace_asserter.run_agent_async(supervisor, "msagent", prompt)

    monocle_trace_asserter.called_tool("book_flight", "MS_Flight_Booking_Agent")
    monocle_trace_asserter._filtered_spans = None
    monocle_trace_asserter.called_agent("MS_Flight_Booking_Agent")


@pytest.mark.asyncio
async def test_sentiment_bias_evaluation(monocle_trace_asserter: TraceAssertion):
    travel_request = "Book a flight from Rochester to New York City for July 5th 2026"
    await monocle_trace_asserter.run_agent_async(supervisor, "msagent", travel_request)

    evaluator = monocle_trace_asserter.with_evaluation("okahu")
    if hasattr(evaluator, "check_eval"):
        evaluator.check_eval("sentiment", "positive").check_eval("bias", "unbiased")
    else:
        evaluator.called_agent("MS_Flight_Booking_Agent").contains_any_output("booked", "flight")
        monocle_trace_asserter._filtered_spans = None
        monocle_trace_asserter.called_tool("book_flight", "MS_Flight_Booking_Agent")


@pytest.mark.asyncio
async def test_quality_evaluation(monocle_trace_asserter: TraceAssertion):
    travel_request = (
        "Please Book a flight from New York to Delhi for 1st Dec 2025. "
        "Book a flight from Delhi to Mumabi on January 1st."
    )
    await monocle_trace_asserter.run_agent_async(supervisor, "msagent", travel_request)

    evaluator = monocle_trace_asserter.with_evaluation("okahu")
    if hasattr(evaluator, "check_eval"):
        evaluator.check_eval("frustration", "ok").check_eval("hallucination", "no_hallucination")
        monocle_trace_asserter.check_eval("contextual_precision", "high_precision")
    else:
        evaluator.called_agent("MS_Flight_Booking_Agent").contains_any_output("booked", "flight")
        monocle_trace_asserter._filtered_spans = None
        monocle_trace_asserter.called_tool("book_flight", "MS_Flight_Booking_Agent")

if __name__ == "__main__":
    pytest.main([__file__])
