"""
Multi-Agent Travel System using Microsoft Agent Framework with Azure OpenAI
Sequential workflow: flight -> hotel -> summarizer
"""

# Enable Monocle Tracing
from monocle_apptrace import setup_monocle_telemetry
setup_monocle_telemetry(workflow_name = 'mic_ag_fm', monocle_exporters_list = 'file')

import asyncio
import os
from typing import Annotated

from agent_framework import SequentialBuilder
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity.aio import AzureCliCredential


# Flight booking tool
def book_flight(
    from_airport: Annotated[str, "The departure airport code (e.g., JFK, LAX)"],
    to_airport: Annotated[str, "The destination airport code (e.g., SFO, ORD)"],
) -> str:
    """Book a flight from one airport to another"""
    import random
    
    # Simple booking simulation
    confirmation = f"FL{random.randint(100000, 999999)}"
    cost = random.randint(300, 800)
    
    return f"FLIGHT BOOKING CONFIRMED #{confirmation}: {from_airport} to {to_airport} - ${cost}"


# Hotel booking tool
def book_hotel(
    hotel_name: Annotated[str, "The name of the hotel to book"],
    city: Annotated[str, "The city where the hotel is located"],
    nights: Annotated[int, "Number of nights to stay"] = 1,
) -> str:
    """Book a hotel reservation"""
    import random
    
    # Simple booking simulation
    confirmation = f"HT{random.randint(100000, 999999)}"
    cost = nights * 150
    
    return f"HOTEL BOOKING CONFIRMED #{confirmation}: {hotel_name} in {city} for {nights} nights - ${cost}"


async def main():
    """Main function to run the multi-agent travel system."""
    
    print("🧠 Microsoft Agent Framework - Sequential Multi-Agent Travel System\n")
    
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
    
    # Create hotel booking agent
    hotel_agent = client.create_agent(
        name="MS_Hotel_Booking_Agent",
        instructions=(
            "You are a Hotel Booking Assistant. "
            "Your goal is to help users book hotel accommodations. "
            "Book the requested hotel and provide confirmation details."
        ),
        tools=[book_hotel],
    )
    
    # Create summarizer agent that reviews both bookings
    summarizer_agent = client.create_agent(
        name="MS_Travel_Summarizer",
        instructions=(
            "You are a Travel Booking Summarizer. "
            "Review all the booking confirmations provided and create a consolidated summary "
            "with all confirmation numbers and total costs. "
            "Provide a friendly final message to the user with all booking details."
        ),
        tools=[],
    )

    # Create sequential workflow: flight -> hotel -> summarizer
    workflow = (
        SequentialBuilder()
        .register_participants([
            lambda: flight_agent, 
            lambda: hotel_agent, 
            lambda: summarizer_agent
        ])
        .build()
    )
    
    print(f"🔍 Flight Agent: {type(flight_agent).__name__}")
    print(f"🔍 Hotel Agent: {type(hotel_agent).__name__}")
    print(f"� Summarizer Agent: {type(summarizer_agent).__name__}\n")
    
    # Define travel task
    task_description = "Book a flight from BOM to JFK for December 15th and also book a stay at the Marriott for 3 days."
    
    print(f"📋 Task: {task_description}\n")
    print("--- Travel Booking Process ---\n")
    
    # Execute sequential workflow
    workflow_response = await workflow.run(task_description)
    
    # Display the result
    print("\n🤖 Workflow Response:\n")
    print(workflow_response)
    
    print("\n✅ Travel booking completed!")


# Run the multi-agent system
if __name__ == "__main__":
    asyncio.run(main())
