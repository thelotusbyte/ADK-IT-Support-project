import subprocess
import ctypes

def is_admin():
    """Checks if the Python process has Windows Administrator privileges."""
    try:
        # Calls the native Windows API
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

def restart_network_adapter(adapter_name="Wi-Fi"):
    # 1. Immediate Privilege Check
    if not is_admin():
        return {
            "status": "failed",
            "step": "pre_check",
            "error": "I tried to reset your Wi-Fi adapter, but I don't have the necessary permissions. Please contact the administrator."
        }

    # 2. Proceed with restart if privileges exist
    try:
        # Disable adapter
        disable_result = subprocess.run(
            ["netsh", "interface", "set", "interface", adapter_name, "disable"],
            capture_output=True,
            text=True,
            shell=True
        )

        # Check disable status
        if disable_result.returncode != 0:
            return {
                "status": "failed",
                "step": "disable_adapter",
                "error": disable_result.stderr.strip() or disable_result.stdout.strip()
            }

        # Enable adapter
        enable_result = subprocess.run(
            ["netsh", "interface", "set", "interface", adapter_name, "enable"],
            capture_output=True,
            text=True,
            shell=True
        )

        # Check enable status
        if enable_result.returncode != 0:
            return {
                "status": "failed",
                "step": "enable_adapter",
                "error": enable_result.stderr.strip() or enable_result.stdout.strip()
            }

        return {
            "status": "success",
            "adapter": adapter_name,
            "message": "Network adapter restarted successfully"
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }