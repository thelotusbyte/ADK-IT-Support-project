import subprocess

def release_ip():
    try:
        result = subprocess.run(
            ["ipconfig", "/release"],
            capture_output=True,
            text=True,
            shell=True
        )

        # Success
        if result.returncode == 0:
            return {
                "status": "success",
                "message": result.stdout.strip()
            }

        # Command failed
        else:
            return {
                "status": "failed",
                "error": result.stderr.strip()
            }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }