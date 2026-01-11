import asyncio
import os
import uuid
import json
from pathlib import Path
from agent_framework import ChatAgent
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity.aio import AzureCliCredential
from typing import Annotated
import random

# Enable Monocle Tracing
from monocle_apptrace import setup_monocle_telemetry
setup_monocle_telemetry(workflow_name = 'mic_ag_fm', monocle_exporters_list = 'file')

# Session storage (in real app, use DB/Redis instead of file)
SESSIONS_DIR = Path("./sessions")
SESSIONS_DIR.mkdir(exist_ok=True)

def save_session(session_id: str, serialized_thread: dict) -> None:
    """Save session_id → serialized_thread mapping"""
    session_file = SESSIONS_DIR / f"{session_id}.json"
    with open(session_file, 'w') as f:
        json.dump(serialized_thread, f)
    print(f"💾 Session saved: {session_id}")

def load_session(session_id: str) -> dict | None:
    """Load serialized_thread by session_id"""
    session_file = SESSIONS_DIR / f"{session_id}.json"
    if not session_file.exists():
        return None
    with open(session_file, 'r') as f:
        return json.load(f)

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
    # Initialize Azure OpenAI client (uses Chat Completions API with local session management)
    
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    if api_key:
        client = AzureOpenAIChatClient(
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            deployment_name=os.getenv("AZURE_OPENAI_API_DEPLOYMENT"),
            api_key=api_key,
        )
    else:
        # Use Azure CLI authentication (requires: az login)
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

    # Generate YOUR session ID for tracking (not passed to thread)
    session_id = uuid.uuid4().hex
    
    # Create thread WITHOUT passing session_id (Chat Completions API doesn't support it)
    thread = flight_agent.get_new_thread()
    print(f"\n📋 Session ID (your tracking): {session_id}")
    print(f"🔗 Thread object created (local memory only)")

    # First interaction
    print("\n[User]: Book a flight from BOM to JFK for December 15th")
    response1 = await flight_agent.run("Book a flight from BOM to JFK for December 15th", thread=thread)
    print(f"[Agent]: {response1.text}")

    # Second interaction - thread maintains context in memory
    print("\n[User]: Book a return flight for December 20th")
    response2 = await flight_agent.run("Book a return flight for December 20th", thread=thread)
    print(f"[Agent]: {response2.text}")

    # Serialize thread and save with YOUR session_id as the key
    serialized_thread = await thread.serialize()
    save_session(session_id, serialized_thread)
    
    # --- Simulate resuming session later ---
    print("\n" + "="*60)
    print("🔄 Simulating session resume (like after app restart)")
    print("="*60)
    
    # Load serialized thread using YOUR session_id
    loaded_thread_data = load_session(session_id)
    if loaded_thread_data:
        print(f"✅ Session loaded: {session_id}")
        
        # Deserialize to restore conversation
        resumed_thread = await flight_agent.deserialize_thread(loaded_thread_data)
        print(f"🔗 Thread restored with full conversation history")
        
        # Continue conversation with full context
        print("\n[User]: What did we talk about?")
        response3 = await flight_agent.run("What did we talk about?", thread=resumed_thread)
        print(f"[Agent]: {response3.text}")
        
        # Update session with new conversation turn
        updated_serialized = await resumed_thread.serialize()
        save_session(session_id, updated_serialized)

if __name__ == "__main__":
    asyncio.run(multi_turn_example())