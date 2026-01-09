import asyncio
import os
from agent_framework import ChatAgent
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity.aio import AzureCliCredential
from typing import Annotated
import random

# Enable Monocle Tracing
from monocle_apptrace import setup_monocle_telemetry
setup_monocle_telemetry(workflow_name = 'mic_ag_fm', monocle_exporters_list = 'file')

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
    # Initialize Azure OpenAI client
    client = AzureOpenAIChatClient(
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        deployment_name=os.getenv("AZURE_OPENAI_API_DEPLOYMENT"),
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

    # Create a thread for persistent conversation
    thread = flight_agent.get_new_thread()

    # First interaction
    response1 = await flight_agent.run("Book a flight from BOM to JFK for December 15th", thread=thread)
    print(f"Agent: {response1.text}")

    # Second interaction - agent remembers the name
    response2 = await flight_agent.run("Book a return flight for December 20th", thread=thread)
    print(f"Agent: {response2.text}")  # Should mention "Alice"

    # Serialize thread for storage
    serialized = await thread.serialize()
    print("\nThread serialized for storage...")

    # Later, deserialize and continue conversation
    new_thread = await flight_agent.deserialize_thread(serialized)
    response3 = await flight_agent.run("What did we talk about?", thread=new_thread)
    print(f"Agent: {response3.text}")  # Should remember previous context

if __name__ == "__main__":
    import asyncio
    asyncio.run(multi_turn_example())