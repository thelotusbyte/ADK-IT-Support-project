# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from google.adk import Agent, Workflow, Event
from google.adk.apps import App
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams

# Fetch existing MCP Server URL from environment variable, defaulting to standard localhost SSE
mcp_url = os.getenv("MCP_SERVER_URL", "http://localhost:8000/sse")

# Setup the remote HTTP/SSE MCP client connection.
# The client connects directly to the separately running MCP server.
mcp_toolset = McpToolset(
    connection_params=SseConnectionParams(
        url=mcp_url,
    )
)

# 1. Save User Query Function Node
def save_user_query(node_input: str):
    """
    Saves the user's initial query into session state so it can be referenced
    dynamically in instructions by downstream specialized agents.
    """
    return Event(output=node_input, state={"user_query": node_input})

# 2. Classify Issue Agent Node
classify_agent = Agent(
    name="classify_agent",
    model="gemini-2.5-flash",
    instruction="""
    Analyze the user's IT support query and classify it into exactly one of the following categories:
    - PERFORMANCE: Issues regarding system slowness, high CPU/memory usage, startup delays, freezing, or disk space.
    - NETWORK: Issues regarding internet connectivity, Wi-Fi, IP configuration, DNS, slow loading, or VPN.
    - BATTERY: Issues regarding battery drain, power settings, charging, or power plans.
    - BROWSER: Issues regarding web browser crashes, slow browsing, extension issues, cache/cookies, or Chrome/Edge/Firefox.
    
    Return ONLY the category name: PERFORMANCE, NETWORK, BATTERY, or BROWSER. Do not include any other text, reasoning, or markdown formatting.
    """,
    output_schema=str,
)

# 3. Routing Node
def issue_router(node_input: str):
    """
    Reads the classification output and returns the matching route event.
    """
    category = node_input.strip().upper()
    if category not in ["PERFORMANCE", "NETWORK", "BATTERY", "BROWSER"]:
        category = "PERFORMANCE"  # Default fallback
    return Event(route=category)

# 4. Specialized Agents (Equipped with MCP Tools)
performance_agent = Agent(
    name="performance_agent",
    model="gemini-2.5-flash",
    instruction="""
    You are an expert Windows Performance Diagnostic Agent.
    The user is experiencing a performance issue: {user_query}.

    Deterministic Troubleshooting Workflow:
    1. Run the `performance_check` tool to retrieve general system status.
    2. Analyze the CPU, RAM usage, and top running processes.
    3. Run the `startup_check` tool to check for resource-heavy applications starting with Windows.
    4. Run the `disk_check` tool to check partition health and storage availability.
    5. Determine the most likely root cause based on the gathered data.
    6. IF you want to run `clear_temp_files` or `kill_heavy_process` to resolve the issue:
       - You MUST check if the user has explicitly confirmed/agreed to this action in the conversation.
       - If NOT confirmed yet, you must ask the user for explicit confirmation (e.g. "I recommend running clear_temp_files. Would you like me to do this?") and STOP. Do NOT call the tool.
       - If confirmed, you may call `clear_temp_files` or `kill_heavy_process`.

    Global Rules:
    - Never fabricate diagnostic information. Base every conclusion only on actual MCP tool outputs.
    - Always diagnose before repairing.
    - Follow the defined troubleshooting workflow.
    - Generate a root cause analysis before recommending or executing any repair.
    """,
    tools=[mcp_toolset],
)

network_agent = Agent(
    name="network_agent",
    model="gemini-2.5-flash",
    instruction="""
    You are an expert Windows Network Diagnostic Agent.
    The user is experiencing a network issue: {user_query}.

    Deterministic Troubleshooting Workflow:
    1. Run the `network_check` tool to inspect current adapter configurations, IP addresses, and DNS servers.
    2. Run the `ping_test` tool if required to test external connectivity.
    3. If DNS issues are detected, call the `flush_dns` tool.
    4. If IP issues are detected, call the `release_ip` tool followed by the `renew_ip` tool.
    5. If adapter issues are detected and you need to restart the network adapter:
       - You MUST check if the user has explicitly confirmed/agreed to this action in the conversation.
       - If NOT confirmed yet, ask the user for explicit confirmation (e.g. "I recommend restarting the network adapter. Would you like me to do this?") and STOP. Do NOT call the tool.
       - If confirmed, call the `restart_network_adapter` tool.
    6. Generate a clear diagnosis and recommendation.

    Global Rules:
    - Never fabricate diagnostic information. Base every conclusion only on actual MCP tool outputs.
    - Always diagnose before repairing.
    - Follow the defined troubleshooting workflow.
    - Generate a root cause analysis before recommending or executing any repair.
    """,
    tools=[mcp_toolset],
)

battery_agent = Agent(
    name="battery_agent",
    model="gemini-2.5-flash",
    instruction="""
    You are an expert Windows Battery Diagnostic Agent.
    The user is experiencing a battery/power issue: {user_query}.

    Deterministic Troubleshooting Workflow:
    1. Run the `battery_check` tool to retrieve battery status and power reports.
    2. Analyze the health percentage, cycle count, and capacity.
    3. Recommend replacement if necessary.
    4. Do NOT attempt or suggest software-based repairs for battery/power issues.

    Global Rules:
    - Never fabricate diagnostic information. Base every conclusion only on actual MCP tool outputs.
    - Always diagnose before recommending action.
    - Follow the defined troubleshooting workflow.
    - Generate a root cause analysis before recommending battery replacement.
    """,
    tools=[mcp_toolset],
)

browser_agent = Agent(
    name="browser_agent",
    model="gemini-2.5-flash",
    instruction="""
    You are an expert Windows Browser Diagnostic Agent.
    The user is experiencing a browser issue: {user_query}.

    Deterministic Troubleshooting Workflow:
    1. Run the `network_check` tool first to determine whether the issue is general network-related.
    2. If the issue is not general network-related, run the `browser_check` tool.
    3. If browser cache is identified as the problem:
       - You MUST check if the user has explicitly confirmed/agreed to this action in the conversation.
       - If NOT confirmed yet, ask the user for explicit confirmation (e.g. "I recommend clearing the browser cache. Would you like me to do this?") and STOP. Do NOT call the tool.
       - If confirmed, call `clear_browser_cache`.

    Global Rules:
    - Never fabricate diagnostic information. Base every conclusion only on actual MCP tool outputs.
    - Always diagnose before repairing.
    - Follow the defined troubleshooting workflow.
    - Generate a root cause analysis before recommending or executing any repair.
    """,
    tools=[mcp_toolset],
)


# 5. Graph Workflow Definition
# Maps the flow from START -> save_user_query -> classify_agent -> issue_router -> [specialized agents]
root_agent = Workflow(
    name="ai_it_support_workflow",
    edges=[
        ("START", save_user_query, classify_agent, issue_router),
        (issue_router, {
            "PERFORMANCE": performance_agent,
            "NETWORK": network_agent,
            "BATTERY": battery_agent,
            "BROWSER": browser_agent,
        })
    ]
)

app = App(name="ai-it-support-agent", root_agent=root_agent)
