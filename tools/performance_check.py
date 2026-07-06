"""
performance_check.py
=====================
IT Agent — Performance Check Module

Functions:
  get_ram_usage()          → total RAM stats
  get_cpu_usage()          → total CPU %
  get_top_cpu_processes()  → top 5 by CPU (fixed: two-pass measurement)
  get_top_ram_processes()  → top 5 by RAM (fixed: grouped by app name)

Fixes over previous version:
  1. CPU processes no longer show 0.0% — uses two-pass measurement
  2. RAM processes grouped by name — Firefox shows as one line, not 5
  3. System Idle Process filtered out — it's not a real consumer
"""

import psutil
import time


# ─────────────────────────────────────────
#  No changes needed here — these were fine
# ─────────────────────────────────────────

def get_ram_usage():
    ram = psutil.virtual_memory()
    return {
        "total_ram_gb": round(ram.total / (1024 ** 3), 2),
        "used_ram_gb" : round(ram.used  / (1024 ** 3), 2),
        "ram_percent" : ram.percent
    }


def get_cpu_usage():
    cpu_percent = psutil.cpu_percent(interval=1)
    return {
        "cpu_percent": cpu_percent
    }


# ─────────────────────────────────────────
#  FIX 1: get_top_cpu_processes
#
#  Problem in old version:
#    One pass → cpu_percent always 0.0%
#    psutil needs TWO calls with a time gap
#    to calculate actual CPU usage.
#
#  Fix:
#    Pass 1 → initialise each process counter
#    Wait 1 second
#    Pass 2 → read the actual CPU value
# ─────────────────────────────────────────

def get_top_cpu_processes(limit=5):
    """
    Returns top N processes by CPU usage.
    Each item: { pid, name, cpu_percent, memory_mb }

    Why two passes?
    cpu_percent() measures usage BETWEEN two calls.
    First call starts the clock. Second call reads it.
    Without this gap, everything returns 0.0%.
    """

    # Pass 1 — start the CPU counter for every process
    for process in psutil.process_iter(['pid', 'name', 'cpu_percent']):
        try:
            process.cpu_percent(interval=None)  # initialise, don't read yet
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    # Wait — let the measurement interval pass
    time.sleep(1)

    # Pass 2 — now read the actual CPU values
    processes = []
    for process in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
        try:
            name    = process.info['name'] or "Unknown"
            pid     = process.info['pid']
            cpu_pct = round(process.info['cpu_percent'] or 0.0, 1)
            ram_mb  = round(
                (process.info['memory_info'].rss if process.info['memory_info'] else 0)
                / (1024 ** 2), 2
            )

            # Filter: System Idle Process is not a real consumer
            if name.lower() in ('system idle process', 'idle'):
                continue

            processes.append({
                "pid"        : pid,
                "name"       : name,
                "cpu_percent": cpu_pct,
                "memory_mb"  : ram_mb,
            })

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    # Sort by CPU, return top N
    processes = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)
    return processes[:limit]


# ─────────────────────────────────────────
#  FIX 2: get_top_ram_processes
#
#  Problem in old version:
#    Firefox with 5 tabs → 5 separate entries
#    User sees the same app name repeated
#    which is confusing and wastes space.
#
#  Fix:
#    Group processes by name
#    Sum their RAM together
#    Show instance count
#
#  Example output:
#    firefox.exe | 3 instances | 3,420 MB
#    instead of:
#    firefox.exe | 1651 MB
#    firefox.exe |  699 MB
#    firefox.exe |  637 MB
# ─────────────────────────────────────────

def get_top_ram_processes(limit=5):
    """
    Returns top N apps by total RAM usage.
    Multiple instances of the same app are grouped.
    Each item: { name, total_memory_mb, instances, pids }
    """

    # Step 1 — collect all processes
    raw = []
    for process in psutil.process_iter(['pid', 'name', 'memory_info']):
        try:
            name   = process.info['name'] or "Unknown"
            pid    = process.info['pid']
            ram_mb = round(
                (process.info['memory_info'].rss if process.info['memory_info'] else 0)
                / (1024 ** 2), 2
            )
            raw.append({"name": name, "pid": pid, "ram_mb": ram_mb})

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    # Step 2 — group by name, sum RAM, collect PIDs
    grouped = {}
    for proc in raw:
        name = proc["name"]
        if name not in grouped:
            grouped[name] = {
                "name"            : name,
                "total_memory_mb" : 0.0,
                "instances"       : 0,
                "pids"            : [],
            }
        grouped[name]["total_memory_mb"] += proc["ram_mb"]
        grouped[name]["instances"]       += 1
        grouped[name]["pids"].append(proc["pid"])

    # Step 3 — round totals, sort, return top N
    for app in grouped.values():
        app["total_memory_mb"] = round(app["total_memory_mb"], 2)

    sorted_apps = sorted(
        grouped.values(),
        key=lambda x: x["total_memory_mb"],
        reverse=True
    )

    return sorted_apps[:limit]