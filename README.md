# AI IT Support Agent (Windows)

An AI-powered Windows IT Support Agent built using the **Google Antigravity SDK (ADK 2.0)** Graph Workflow engine. This agent acts as a client that connects to an external Model Context Protocol (MCP) server running separately over SSE to run diagnostics and execute repairs according to deterministic IT Support Standard Operating Procedures (SOPs).

---

## Project Overview

The **AI IT Support Agent** is designed to triage and troubleshoot common Windows operating system issues including performance degradation, network connectivity failures, battery health degradation, and browser malfunctions. Instead of allowing the underlying LLM to reason freely or fabricate diagnostics, this agent uses a structured graph workflow and strict SOP instructions to ensure deterministic and safe operation on the user's machine.

---

## Architecture

The project follows a modular, client-server architecture:

- **Client Application (ADK 2.0)**: Coordinates task execution, processes the user query, classifies the problem, and delegates it to a specialized agent.
- **Diagnostics & Repair Server (MCP Server)**: Exposes local OS capabilities (utilities, hardware checks, settings flush) via tools. The client connects to this server over a Server-Sent Events (SSE) connection.
- **LLM Engine**: Powers the reasoning agents (`gemini-2.5-flash`) to interpret diagnostic outputs and recommend next steps.

```
                  ┌──────────────────────────────────────────────┐
                  │                 User Query                   │
                  └──────────────────────┬───────────────────────┘
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │       Save Query & Classify Issue            │
                  └──────────────────────┬───────────────────────┘
                                         ▼
                                ┌─────────────────┐
                                │  Issue Router   │
                                └────────┬────────┘
                                         │
        ┌──────────────────┬─────────────┴──────┬──────────────────┐
        ▼                  ▼                    ▼                  ▼
  ┌───────────┐      ┌───────────┐        ┌───────────┐      ┌───────────┐
  │Performance│      │  Network  │        │  Battery  │      │  Browser  │
  │   Agent   │      │   Agent   │        │   Agent   │      │   Agent   │
  └─────┬─────┘      └─────┬─────┘        └─────┬─────┘      └─────┬─────┘
        │                  │                    │                  │
        └──────────────────┼────────────────────┴──────────────────┘
                           │ (McpToolset Client)
                           ▼
              ┌───────────────────────────┐
              │  Existing MCP SSE Server   │
              └───────────────────────────┘
```

---

## ADK Graph Workflow

The workflow is designed as a directed execution graph using ADK `Workflow` and `Event` routing:

1. **START** $\rightarrow$ `save_user_query`:
   - A function node that intercepts the raw query and saves it to the session state variable `user_query` for downstream agent reference.
2. `save_user_query` $\rightarrow$ `classify_agent`:
   - An LLM agent that maps the query to one of four categories: `PERFORMANCE`, `NETWORK`, `BATTERY`, or `BROWSER`.
3. `classify_agent` $\rightarrow$ `issue_router`:
   - A routing function node that takes the classification output and returns an `Event(route=...)` to branch the execution.
4. **Specialized Agent Branches**:
   - Executes the selected specialized agent node. The agent utilizes its toolset to run diagnostics, perform checks, and output a diagnosis/recommendation.

---

## MCP Integration

This project operates strictly as an **MCP Client** using the `google-adk` toolset integration:
- Uses `McpToolset` coupled with `StreamableHTTPConnectionParams` to connect to an external server via an HTTP/SSE connection.
- Allows configuration of the connection URL using the `MCP_SERVER_URL` environment variable.
- Passes the toolset to the specialized agents, allowing them to invoke server-side tools dynamically while following strict security/confirmation rules.

---

## Project Structure

```
ai-it-support-agent/
├── .agents/
│   └── CONTEXT.md                 # Persistent project rules and agent SOP instructions
├── .venv/                         # Isolated Python virtual environment
├── .env                           # Environment variables configuration (API Keys & Server URL)
├── requirements.txt               # Python package dependencies
├── main.py                        # Execution runner script utilizing InMemoryRunner
└── it_support_agent/              # Core agent module
    ├── __init__.py                # Package initialization
    └── agent.py                   # Graph workflow, nodes, specialized agents, and MCP client config
```

---

## Features & Troubleshooting SOPs

### Global Safety Rules
- **No Fabrication**: Conclusions must be derived strictly from actual MCP tool outputs.
- **Diagnose Before Repair**: Diagnostic checks must always run before any repair utility is invoked.
- **Root Cause Analysis (RCA)**: A structured RCA explanation must be outputted prior to recommending repairs.

### Specialized Agent SOPs
*   **Performance Agent**:
    - Executes `performance_check` $\rightarrow$ `startup_check` $\rightarrow$ `disk_check`.
    - Safe execution rule: Only calls `clear_temp_files` or `kill_heavy_process` after explicit user confirmation.
*   **Network Agent**:
    - Runs `network_check` and `ping_test`.
    - Automatically flushes DNS (`flush_dns`) or renews IP (`release_ip` + `renew_ip`) if issues are identified.
    - Safe execution rule: Only restarts adapters (`restart_network_adapter`) after user confirmation.
*   **Battery Agent**:
    - Runs `battery_check` to inspect health and cycle count.
    - Never attempts software repairs; directly recommends battery replacement if degraded.
*   **Browser Agent**:
    - Runs `network_check` first to isolate connection issues.
    - Runs `browser_check`.
    - Safe execution rule: Only clears browser cache (`clear_browser_cache`) after user confirmation.

---

## Setup Instructions

1. **Prerequisites**:
   - Python 3.10+
   - Node.js (if your external MCP server has Node dependencies)

2. **Initialize Environment & Dependencies**:
   ```bash
   # Create a virtual environment
   python -m venv .venv
   
   # Activate virtual environment
   # Windows PowerShell:
   .venv\Scripts\Activate.ps1
   # Windows CMD:
   .venv\Scripts\activate.bat
   # Linux/macOS:
   source .venv/bin/activate

   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Open the [.env](file:///c:/Users/kamal/Desktop/ai_it_support_agent/.env) file and configure:
   - `GOOGLE_API_KEY`: Your Gemini API key from Google AI Studio.
   - `MCP_SERVER_URL`: The URL of your running SSE MCP server (e.g. `http://localhost:8080/sse`).

4. **Run the Agent**:
   ```bash
   python main.py "My computer is running very slowly and my apps are freezing."
   ```

---

## Future Enhancements

- **Interactive Human-In-The-Loop (HITL)**: Integrate the ADK `RequestInput` or `ResumeOrRequestInput` primitives to handle the repair confirmation pauses dynamically inside the graph execution instead of conversation history checks.
- **Multi-Server MCP Router**: Enable connection to multiple separate MCP servers (e.g. separate network and hardware diagnostic services) simultaneously.
- **Web UI Control Panel**: Build a web-based dashboard using FastAPI and standard HTML/JS to view live diagnostics and approve repair actions with single-click buttons.
