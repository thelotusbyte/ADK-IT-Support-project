import platform
from pydantic import Field
from mcp.server.fastmcp import FastMCP
from tools.network_check import (
    check_internet_connection,
    check_dns_resolution,
    tcp_ping,
    get_network_stats
)
from tools.battery_check import (generate_battery_report, parse_battery_report, analyze_battery_health)

from tools.flush_dns import flush_dns

from tools.performance_check import (
    get_ram_usage,
    get_cpu_usage,
    get_top_cpu_processes,
    get_top_ram_processes
)

from tools.disk_check import disk_check
from tools.browser_check import browser_check
from tools.startup_check import get_startup_apps
from tools.clear_temp_files import clear_temp_files
from tools.release_ip import release_ip
from tools.renew_ip import renew_ip
from tools.ping_test import ping_test
from tools.restart_network_adapter import restart_network_adapter
from tools.kill_process import kill_process
from tools.clear_browser_cache import clear_browser_cache
mcp = FastMCP("IT Support Agent")

def is_windows() -> bool:
    return platform.system().lower() == "windows"

@mcp.tool()
def network_check() -> dict:
    """
    Checks internet connectivity, DNS, and ping latency.
    Use when user reports internet not working, slow connection,
    or cannot reach a website or portal.
    """
    internet = check_internet_connection()
    dns      = check_dns_resolution()
    ping     = tcp_ping()
    stats    = get_network_stats()

    return {
        "internet_available": internet,
        "dns"               : dns,
        "ping"              : ping,
        "network_stats"     : stats
    }

@mcp.tool()
def battery_check() -> dict:
    """
    Generates and analyzes a Windows battery report.
    Use when the user reports battery issues, fast draining, 
    or wants to know their battery health/wear.
    Only works on Windows systems.
    """
    if not is_windows():
        return {"error": "Battery report is only available on Windows."}

    report = generate_battery_report()
    if not report["success"]:
        return {"error": f"Failed to generate battery report: {report.get('error')}"}

    data = parse_battery_report(report["report_path"])
    analysis = analyze_battery_health(data)

    return {
        "design_capacity": data.get("design_capacity"),
        "full_charge_capacity": data.get("full_charge_capacity"),
        "cycle_count": data.get("cycle_count"),
        "health_percent": analysis.get("health_percent"),
        "wear_percent": analysis.get("wear_percent"),
        "status": analysis.get("status"),
        "recommendation": analysis.get("recommendation")
    }

@mcp.tool()
def flush_dns_tool() -> dict:
    """
    Flushes the DNS cache on Windows.
    Use when user can connect to internet but
    cannot reach specific websites or portals.
    """
    return flush_dns()

@mcp.tool()
def check_ram_metrics() -> dict:
    """
    Checks overall system RAM/Memory statistics (Total, Used, and Usage Percentage).
    Use this when the user mentions their computer is feeling sluggish, lagging during multitasking, 
    or applications are crashing with 'out of memory' warnings.
    """
    return get_ram_usage()


@mcp.tool()
def check_cpu_metrics() -> dict:
    """
    Checks the total system CPU load percentage.
    Use this when the user complains that their computer's fan is spinning loudly, 
    the system is suddenly freezing, or responsiveness drops abruptly.
    """
    return get_cpu_usage()


@mcp.tool()
def check_top_cpu_processes() -> list:
    """
    Identifies the top 5 running applications consuming the most CPU processing power.
    Use this right after confirming high CPU usage to trace exactly which background app 
    or rogue system process is causing the slowdown.
    """
    return get_top_cpu_processes()


@mcp.tool()
def check_top_ram_processes() -> list:
    """
    Identifies the top 5 applications hogging system RAM (grouped together neatly by application name).
    Use this when overall system memory is constrained to pinpoint which application 
    (like a browser with too many open tabs) is taking up the most space.
    """
    return get_top_ram_processes()

@mcp.tool()
def check_disk_storage() -> list:
    """
    Checks all mounted disk partitions for capacity, free space, and hardware type (SSD/HDD/NVMe).
    Use this when the user reports "low disk space" warnings, slow computer performance, 
    or wants to know what kind of storage drives they have installed.
    """
    return disk_check()
@mcp.tool()
def check_browser_health(browser_name: str) -> dict:
    """
    Diagnoses a specific web browser's health (cache size, extension count, and version).
    Valid inputs for browser_name are: 'chrome', 'edge', or 'firefox'.
    Use this when the user reports a slow browser, websites not loading correctly, 
    weird pop-ups (often caused by too many extensions), or needs to know their default browser.
    """
    return browser_check(browser_name)

@mcp.tool()
def check_startup_programs() -> dict:
    """
    Checks the list of applications configured to start automatically when Windows boots.
    Use this when the user reports very slow boot times, their computer is lagging heavily 
    immediately after logging in, or they want to clean up background processes.
    """
    return get_startup_apps()

@mcp.tool()
def release_dhcp_ip() -> dict:
    """
    Releases the current IP address from the DHCP server (ipconfig /release).
    Use this as step 1 when the user has an IP conflict or needs a fresh network configuration.
    You MUST usually follow this up by calling the renew_dhcp_ip tool.
    """
    return release_ip()


@mcp.tool()
def renew_dhcp_ip() -> dict:
    """
    Renews the IP address from the DHCP server (ipconfig /renew).
    Use this as step 2 after releasing the IP, or when the computer is connected 
    to a router but has no actual internet access.
    """
    return renew_ip()


@mcp.tool()
def run_ping_test(host: str) -> dict:
    """
    Executes a standard ICMP ping test to a specific hostname or IP address.
    Pass the target website (e.g., 'google.com') or IP address as the 'host' parameter.
    Use this to verify if a specific external server or internal network device is reachable.
    """
    return ping_test(host)


@mcp.tool()
def reset_network_adapter(adapter_name: str) -> dict:
    """
    Disables and then immediately re-enables a network adapter on Windows.
    Pass the exact name of the adapter (e.g., 'Wi-Fi' or 'Ethernet') as the 'adapter_name' parameter.
    Use this as a last-resort workflow step for severe local network connectivity issues.
    NOTE: This command often requires Administrator privileges to succeed.
    """
    return restart_network_adapter(adapter_name)

@mcp.tool()
def terminate_process(pid: int) -> dict:
    """
    Terminates a heavy or frozen background application using its Process ID (PID).
    CRITICAL RULE: You must NEVER guess a PID. If a user asks you to close an app (like Chrome), 
    you MUST run the check_top_ram_processes or check_top_cpu_processes tool first 
    to retrieve the correct PID, and then pass that integer into this tool.
    """
    return kill_process(pid)
@mcp.tool()
def optimize_browser(browser: str) -> dict:
    """
    Clears the cache and triggers an update check for a browser (chrome or edge).
    CRITICAL: Advise the user to close all browser windows before running this,
    otherwise, the cache files will be locked and the cleanup will partially fail.
    """
    return clear_browser_cache(browser)
if __name__ == "__main__":
    mcp.run(transport="sse")
