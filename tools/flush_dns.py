# tools/flush_dns.py

import subprocess

def flush_dns() -> dict:
    """
    Flushes the DNS cache on Windows.
    """
    result = subprocess.run(
        "ipconfig /flushdns",
        capture_output=True,
        text=True,
        shell=True
    )

    success = "successfully flushed" in result.stdout.lower()

    return {
        "success": success,
        "message": result.stdout.strip()
    }