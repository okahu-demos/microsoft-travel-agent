import asyncio
import os
import logging
from agent_framework import ChatAgent
from agent_framework.azure import AzureOpenAIAssistantsClient
from azure.identity.aio import AzureCliCredential
from typing import Annotated
import random
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Enable Monocle Tracing
from monocle_apptrace import setup_monocle_telemetry
setup_monocle_telemetry(workflow_name = 'mic_ag_assistants', monocle_exporters_list = 'file')

logger = logging.getLogger(__name__)

# Flight booking tool
def book_flight(
    from_airport: Annotated[str, "The departure airport code (e.g., JFK, LAX)"],
    to_airport: Annotated[str, "The destination airport code (e.g., SFO, ORD)"],
) -> str:
    """Book a flight from one airport to another"""
    confirmation = f"FL{random.randint(100000, 999999)}"
    cost = random.randint(300, 800)
    return f"FLIGHT BOOKING CONFIRMED #{confirmation}: {from_airport} to {to_airport} - ${cost}"


def create_assistants_client() -> AzureOpenAIAssistantsClient:
    deployment_name = (
        os.getenv("AZURE_OPENAI_MODEL_DEPLOYMENT_NAME")
        or os.getenv("AZURE_OPENAI_API_DEPLOYMENT")
        or os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")
    )
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-05-01-preview")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")

    if not deployment_name:
        raise RuntimeError(
            "Azure OpenAI deployment name is missing. Set AZURE_OPENAI_MODEL_DEPLOYMENT_NAME "
            "(preferred), AZURE_OPENAI_API_DEPLOYMENT, or AZURE_OPENAI_CHAT_DEPLOYMENT_NAME."
        )
    if not endpoint:
        raise RuntimeError(
            "Azure OpenAI endpoint is missing. Set AZURE_OPENAI_ENDPOINT."
        )

    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    if api_key:
        return AzureOpenAIAssistantsClient(
            endpoint=endpoint,
            deployment_name=deployment_name,
            api_version=api_version,
            api_key=api_key,
        )

    return AzureOpenAIAssistantsClient(
        endpoint=endpoint,
        deployment_name=deployment_name,
        api_version=api_version,
        credential=AzureCliCredential(),
    )


async def setup_agents() -> ChatAgent:
    client = create_assistants_client()
    return client.as_agent(
        name="MS_Flight_Booking_Agent",
        instructions=(
            "You are a Flight Booking Assistant. "
            "Your goal is to help users book flights between any two cities or airports. "
            "Book the requested flight and provide confirmation details."
        ),
        tools=[book_flight],
    )


async def run_agent(request: str, service_thread_id: str | None = None):
    try:
        flight_agent = await setup_agents()
    except Exception as exc:
        logger.error("Failed to initialize agent. Check Azure OpenAI settings in .env", exc_info=True)
        raise RuntimeError("Failed to initialize Azure OpenAI assistant client.") from exc

    thread = flight_agent.get_new_thread(service_thread_id=service_thread_id)
    response = await flight_agent.run(request, thread=thread)
    return response.text, thread.service_thread_id


async def multi_turn_example():
    print("\n🆕 Creating new Azure-managed thread...")
    print("\n[User]: Book a flight from BOM to JFK for December 15th")
    response1, azure_thread_id = await run_agent("Book a flight from BOM to JFK for December 15th")
    print(f"[Agent]: {response1}")
    print(f"\n📋 Azure Thread ID: {azure_thread_id}")
    print(f"✅ Thread is stored on Azure server - use this ID to resume")

    print("\n[User]: Book a return flight for December 20th")
    response2, _ = await run_agent("Book a return flight for December 20th", service_thread_id=azure_thread_id)
    print(f"[Agent]: {response2}")
    
    # --- Simulate resuming session later ---
    print("\n" + "="*60)
    print("🔄 Simulating session resume (like after app restart)")
    print("="*60)
    
    print(f"✅ Thread resumed with ID: {azure_thread_id}")
    print(f"🔗 Azure retrieved full conversation history from server")
    
    print("\n[User]: What did we talk about?")
    response3, _ = await run_agent("What did we talk about?", service_thread_id=azure_thread_id)
    print(f"[Agent]: {response3}")
    
    print(f"\n✅ All conversation updates automatically saved to Azure")

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARN)
    asyncio.run(multi_turn_example())
