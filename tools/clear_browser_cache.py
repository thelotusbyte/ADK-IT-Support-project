import os
import shutil
import subprocess
import psutil
from pathlib import Path

def is_browser_running(browser_name):
    """Checks if the browser process is currently active."""
    # Maps user-friendly names to actual process names
    process_map = {
        "chrome": "chrome.exe",
        "edge": "msedge.exe"
    }
    target_process = process_map.get(browser_name.lower())
    
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == target_process:
            return True
    return False

def clear_browser_cache(browser: str) -> dict:
    """
    Clears browser cache and triggers an update check for a browser.
    """
    browser = browser.lower()

    # 1. Safety Check: Is the browser running?
    if is_browser_running(browser):
        return {
            "status": "failed",
            "message": f"The {browser} browser is currently open. Please close it completely before running this cleanup."
        }

    browsers = {
        "chrome": {
            "cache_path": Path.home() / "AppData/Local/Google/Chrome/User Data/Default/Cache",
            "update_cmd": [r"C:\Program Files\Google\Update\GoogleUpdate.exe"]
        },
        "edge": {
            "cache_path": Path.home() / "AppData/Local/Microsoft/Edge/User Data/Default/Cache",
            "update_cmd": [r"C:\Program Files (x86)\Microsoft\EdgeUpdate\MicrosoftEdgeUpdate.exe"]
        }
    }

    if browser not in browsers:
        return {
            "status": "error",
            "message": f"Unsupported browser: {browser}"
        }

    cache_path = browsers[browser]["cache_path"]
    update_cmd = browsers[browser]["update_cmd"]

    result = {
        "browser": browser,
        "cache_cleared": False,
        "browser_updated": False,
        "errors": []
    }

    # 2. Clear Cache
    try:
        if cache_path.exists():
            for item in cache_path.iterdir():
                try:
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                except Exception as e:
                    result["errors"].append(f"Could not delete {item.name}: {str(e)}")
            
            result["cache_cleared"] = True
        else:
            result["errors"].append("Cache path not found")
    except Exception as e:
        result["errors"].append(f"Cache clear failed: {str(e)}")

    # 3. Update Browser
    try:
        if os.path.exists(update_cmd[0]):
            subprocess.run(
                update_cmd,
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            result["browser_updated"] = True
        else:
            result["errors"].append("Browser updater not found")
    except Exception as e:
        result["errors"].append(f"Browser update failed: {str(e)}")

    # 4. Final Status
    if result["cache_cleared"] and result["browser_updated"]:
        result["status"] = "success"
    else:
        result["status"] = "partial_success"

    return result