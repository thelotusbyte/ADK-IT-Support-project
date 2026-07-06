import subprocess

def ping_test(host="8.8.8.8"):
    try:
        result = subprocess.run(
            ["ping", host],
            capture_output=True,
            text=True,
            shell=True
        )

        # Success
        if result.returncode == 0:
            return {
                "status": "success",
                "host": host,
                "output": result.stdout.strip()
            }

        # Ping failed
        else:
            return {
                "status": "failed",
                "host": host,
                "error": result.stderr.strip() or result.stdout.strip()
            }

    except Exception as e:
        return {
            "status": "error",
            "host": host,
            "error": str(e)
        }