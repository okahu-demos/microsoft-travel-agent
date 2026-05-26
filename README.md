# Okahu agent demo with Microsoft Agent Framework (Azure OpenAI)

This repo includes a demo agent application built using Microsoft Agent Framework and pre-instrumented for observation with Okahu AI Observability Cloud. You can fork this repo and run it in GitHub Codespaces or locally to get started quickly.

## Prerequisites

- Azure OpenAI credentials (API key or Azure CLI access)
- Install the Okahu Extension for VS Code

![Okahu VS Code Extension](images/okahu_extension.png)

- An Okahu tenant and API key for the Okahu AI Observability Cloud
  - Sign up for an Okahu AI account with your LinkedIn or GitHub ID
  - After login, navigate to 'Settings' (left nav) and click 'Generate Okahu API Key'
  - Copy and store the key safely. You cannot retrieve it again once you leave the page

## Project layout

The sample has been split into a small package so the pieces can be reused and tested independently:

```
microsoft-travel-agent/
├── ms_travel_agent.py            # Thin entrypoint — wires telemetry and runs the demo
├── travel_agent/
│   ├── client.py                 # Builds the Azure OpenAI chat completion client
│   ├── tools.py                  # `book_flight` function tool
│   ├── agent_runtime.py          # `setup_agents` + cached `get_flight_agent`
│   ├── session.py                # `resolve_session` / `session_identifier` helpers
│   └── runner.py                 # `run_agent` (single turn) + `multi_turn_example`
├── tests/                        # Pytest suite using monocle-test-tools
├── Dockerfile                    # Container build for the demo
└── requirements.txt
```

`ms_travel_agent.py` re-exports the most common symbols from the package, so existing imports such as `from ms_travel_agent import setup_agents` keep working.

## Get started

### Create python virtual environment
```bash
python -m venv .venv
```

### Activate virtual environment

**Mac/Linux**
```bash
source .venv/bin/activate
```

**Windows**
```bash
.venv\Scripts\activate
```

### Install python dependencies
```bash
pip install -r requirements.txt
```

### Configure the demo environment

You can either export the variables in your shell or put them in a local `.env` file (the package loads it automatically via `python-dotenv`).

**Option 1: Using Azure OpenAI API Key**
```bash
export AZURE_OPENAI_API_KEY=<your-azure-openai-api-key>
export AZURE_OPENAI_ENDPOINT=<your-azure-openai-endpoint>
export AZURE_OPENAI_MODEL_DEPLOYMENT_NAME=<your-deployment-name>
export AZURE_OPENAI_API_VERSION=2024-05-01-preview
```

**Option 2: Using Azure CLI Authentication**
```bash
# Install Azure CLI (if not already installed)
brew install azure-cli  # Mac
# or download from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli

# Login to Azure
az login

# Set environment variables
export AZURE_OPENAI_ENDPOINT=<your-azure-openai-endpoint>
export AZURE_OPENAI_MODEL_DEPLOYMENT_NAME=<your-deployment-name>
export AZURE_OPENAI_API_VERSION=2024-05-01-preview
```

- Replace `<your-azure-openai-api-key>` with your Azure OpenAI API key (if using Option 1)
- Replace `<your-azure-openai-endpoint>` with your Azure OpenAI endpoint (e.g., `https://your-resource.openai.azure.com/`)
- Replace `<your-deployment-name>` with your chat completion deployment name (e.g., `gpt-4o`)
- `AZURE_OPENAI_MODEL_DEPLOYMENT_NAME` is preferred. `AZURE_OPENAI_API_DEPLOYMENT` and `AZURE_OPENAI_CHAT_DEPLOYMENT_NAME` are accepted as fallbacks.

### Run the pre-instrumented travel agent app
```bash
python ms_travel_agent.py
```

The entrypoint installs Monocle telemetry with workflow name `ms_travel_agent` and then calls [`multi_turn_example`](travel_agent/runner.py) to walk through a booking conversation, persist the session, and resume it.

### Run with Docker

A `Dockerfile` is provided for containerized runs:

```bash
docker build -t ms-travel-agent .
docker run --rm --env-file .env ms-travel-agent
```

## How the sample is wired

- [`travel_agent/client.py`](travel_agent/client.py) builds an `OpenAIChatCompletionClient` against your Azure OpenAI deployment, choosing between API-key auth and `AzureCliCredential` based on whether `AZURE_OPENAI_API_KEY` is set.
- [`travel_agent/tools.py`](travel_agent/tools.py) defines the `book_flight(from_airport, to_airport)` function tool that returns a simulated confirmation string.
- [`travel_agent/agent_runtime.py`](travel_agent/agent_runtime.py) constructs the `MS_Flight_Booking_Agent` with that client and tool. `get_flight_agent` lazily caches a single agent instance per process.
- [`travel_agent/session.py`](travel_agent/session.py) normalizes session input into an `AgentSession`. You can pass an existing `AgentSession`, `None` (a fresh one is created), or — for clients that support server-side resume — a session ID string.
- [`travel_agent/runner.py`](travel_agent/runner.py) exposes `run_agent(request, session=None)` for a single turn and `multi_turn_example()` for the end-to-end demo.

### Session persistence

This sample uses Azure OpenAI **Chat Completions** through `OpenAIChatCompletionClient`. Conversation history is held in an `AgentSession` object and persisted by serializing it locally:

```python
from agent_framework import AgentSession
from travel_agent.runner import run_agent

# Turn 1 — start a new session
reply, session = await run_agent("Book a flight from BOM to JFK for December 15th")

# Turn 2 — pass the same session back to keep context
reply, session = await run_agent("Book a return flight for December 20th", session=session)

# Persist before shutdown (write to disk, DB, cache, etc.)
payload = session.to_dict()

# Later — restore and continue the conversation
restored = AgentSession.from_dict(payload)
reply, session = await run_agent("What did we talk about?", session=restored)
```

Notes:
- `session_identifier(session)` returns the best display ID — `service_session_id` if the client supports server-managed threads, otherwise the local `session_id`.
- String-based resume (passing a session ID instead of an `AgentSession`) is rejected for Chat Completions, because the API does not store threads server-side. Persist the full payload from `session.to_dict()` and rehydrate with `AgentSession.from_dict()`.

Example interaction from `multi_turn_example`:
```
Creating new session...

[User]: Book a flight from BOM to JFK for December 15th
[Agent]: FLIGHT BOOKING CONFIRMED #FL482931: BOM to JFK - $612 ...

Session: <session-id>
Session created. Persist the full session payload to resume later.

[User]: Book a return flight for December 20th
[Agent]: FLIGHT BOOKING CONFIRMED #FL771204: JFK to BOM - $548 ...

============================================================
Simulating session resume (like after app restart)
============================================================
Session resumed with ID: <session-id>
Conversation history restored from persisted session payload

[User]: What did we talk about?
[Agent]: We booked two flights: BOM → JFK on December 15th and the return JFK → BOM on December 20th ...
```

## Test scenarios

### a. Basic flight booking:
```
Book a flight from BOM to JFK for December 15th
```

### b. Multi-turn conversation with context:
```
First: Book a flight from BOM to JFK for December 15th
Then: Book a return flight for December 20th
Finally: What flights did we book?
```
Expected: Agent remembers both bookings and provides confirmation details.

### c. Session resume:
```
# Run the app, book some flights, persist `session.to_dict()`,
# then restart and rebuild the session with `AgentSession.from_dict(payload)`.
What was the confirmation number for the first flight?
```
Expected: Agent recalls details from the restored session payload.

### d. Airport code handling:
```
Book a flight from Mumbai to New York next week
```
Expected: Agent interprets city names and books appropriately.

### e. Date handling:
```
Book a flight from SFO to LAX tomorrow
Book a flight from LAX to SFO next Monday
```
Expected: Agent handles relative date references.

## Running the test suite

The repository ships with a `pytest` suite under [`tests/`](tests/) that drives the agent through `monocle-test-tools`. Install both the application requirements and the test requirements before running the suite:

```bash
pip install -r requirements.txt
pip install -r tests/requirements.txt
pytest tests/
```

`tests/conftest.py` will load `.env.test` if present so you can keep test credentials separate from the demo `.env`.

## View traces

### Option 1: View traces in VS Code

1. Open the Okahu AI Observability extension

![Okahu VS Code Extension](images/okahu_vs_extension.png)

2. Select a trace file
3. Review trace and prompts generated by the application

![Sample trace](images/traces.png)
![New trace](images/new_trace.png)

### Option 2: View traces in Okahu Portal

1. Login to Okahu portal
2. Select 'Component' tab
3. Type the workflow name `ms_travel_agent` in the search box
4. Click the workflow tile
5. Review traces and prompts generated by the application

## Architecture

The application uses:
- **Microsoft Agent Framework** for agent orchestration
- **OpenAIChatCompletionClient** (Azure OpenAI Chat Completions) configured from environment variables
- **AgentSession** with local serialization (`to_dict` / `from_dict`) for conversation persistence
- **Monocle tracing** for observability (configured with workflow name `ms_travel_agent`, exporters `file,okahu`)
- **Function tools** (`book_flight`) for flight booking capabilities
- **Azure CLI or API Key** authentication, selected automatically by [`create_assistants_client`](travel_agent/client.py)

## Multi-Agent Orchestration

The Microsoft Agent Framework supports multiple orchestration patterns for coordinating agent workflows:

| Orchestrator | Description |
|--------------|-------------|
| **Sequential** | Agents execute tasks in a pipeline, one after another |
| **Concurrent** | Multiple agents work on the same task in parallel |
| **Handoff** | Agents transfer control based on context or expertise |
| **GroupChat** | Collaborative conversation with manager coordination |
| **Magnetic** | Dynamic collaboration for complex, open-ended tasks |

Monocle currently supports Sequential and Handoff workflows.

**Monocle Observability Features:**
- Track agent interactions and execution order
- Visualize message flow between agents
- Monitor performance metrics and token usage per agent
- Maintain session context across multi-turn conversations

All traces are automatically captured with `setup_monocle_telemetry()` at the top of [`ms_travel_agent.py`](ms_travel_agent.py).

### Trace Files

Monocle traces are written to files for observability:
- Check for trace files in your working directory (the `file` exporter)
- View traces in VS Code using the Okahu extension
- Upload to Okahu portal for team collaboration (the `okahu` exporter)
