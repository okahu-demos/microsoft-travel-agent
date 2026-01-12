import asyncio
import os
from agent_framework import ChatAgent
from agent_framework.azure import AzureOpenAIAssistantsClient
from azure.identity.aio import AzureCliCredential
from typing import Annotated
import random

# Enable Monocle Tracing
from monocle_apptrace import setup_monocle_telemetry
setup_monocle_telemetry(workflow_name = 'mic_ag_assistants', monocle_exporters_list = 'file')

# Flight booking tool
def book_flight(
    from_airport: Annotated[str, "The departure airport code (e.g., JFK, LAX)"],
    to_airport: Annotated[str, "The destination airport code (e.g., SFO, ORD)"],
) -> str:
    """Book a flight from one airport to another"""
    confirmation = f"FL{random.randint(100000, 999999)}"
    cost = random.randint(300, 800)
    return f"FLIGHT BOOKING CONFIRMED #{confirmation}: {from_airport} to {to_airport} - ${cost}"


async def multi_turn_example():
    # Initialize Azure OpenAI Assistants client (server-managed threads)
    
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    if api_key:
        client = AzureOpenAIAssistantsClient(
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            deployment_name=os.getenv("AZURE_OPENAI_API_DEPLOYMENT"),  # Required at client level
            api_version="2024-05-01-preview",  # Assistants API version
            api_key=api_key,
        )
    else:
        # Use Azure CLI authentication (requires: az login)
        client = AzureOpenAIAssistantsClient(
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            deployment_name=os.getenv("AZURE_OPENAI_API_DEPLOYMENT"),  # Required at client level
            api_version="2024-05-01-preview",  # Assistants API version
            credential=AzureCliCredential(),
        )
    
    # Create flight booking agent
    flight_agent = client.create_agent(
        name="MS_Flight_Booking_Agent",
        instructions=(
            "You are a Flight Booking Assistant. "
            "Your goal is to help users book flights between any two cities or airports. "
            "Book the requested flight and provide confirmation details."
        ),
        tools=[book_flight],
    )

    # Step 1: Let Azure create the thread (don't pass service_thread_id on first call)
    print(f"\n🆕 Creating new Azure-managed thread...")
    thread = flight_agent.get_new_thread()

    # First interaction
    print("\n[User]: Book a flight from BOM to JFK for December 15th")
    response1 = await flight_agent.run("Book a flight from BOM to JFK for December 15th", thread=thread)
    print(f"[Agent]: {response1.text}")

    # Step 2: Azure has created the thread - get its ID (starts with 'thread_')
    azure_thread_id = thread.service_thread_id
    print(f"\n📋 Azure Thread ID: {azure_thread_id}")
    print(f"✅ Thread is stored on Azure server - use this ID to resume")

    # Second interaction - continue with same thread
    print("\n[User]: Book a return flight for December 20th")
    response2 = await flight_agent.run("Book a return flight for December 20th", thread=thread)
    print(f"[Agent]: {response2.text}")
    
    # --- Simulate resuming session later ---
    print("\n" + "="*60)
    print("🔄 Simulating session resume (like after app restart)")
    print("="*60)
    
    # Step 3: Resume by passing Azure's thread_id as service_thread_id
    # Azure retrieves the stored conversation automatically
    resumed_thread = flight_agent.get_new_thread(service_thread_id=azure_thread_id)
    print(f"✅ Thread resumed with ID: {azure_thread_id}")
    print(f"🔗 Azure retrieved full conversation history from server")
    
    # Continue conversation - agent has full context from Azure-stored thread
    print("\n[User]: What did we talk about?")
    response3 = await flight_agent.run("What did we talk about?", thread=resumed_thread)
    print(f"[Agent]: {response3.text}")
    
    print(f"\n✅ All conversation updates automatically saved to Azure")

if __name__ == "__main__":
    asyncio.run(multi_turn_example())
