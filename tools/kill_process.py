import psutil

def kill_process(pid: int) -> dict:
    """
    Attempts to terminate a process by its PID.
    """
    try:
        # Check if the PID actually exists right now
        if not psutil.pid_exists(pid):
            return {
                "status": "failed",
                "error": f"No active process found with PID {pid}."
            }

        process = psutil.Process(pid)
        process_name = process.name()

        # Attempt a graceful termination first
        process.terminate()
        
        # Wait up to 3 seconds for it to close properly
        process.wait(timeout=3)

        return {
            "status": "success",
            "pid": pid,
            "process_name": process_name,
            "message": f"Successfully closed {process_name}."
        }

    except psutil.NoSuchProcess:
        return {
            "status": "failed",
            "error": f"The process (PID {pid}) already closed on its own."
        }
    except psutil.AccessDenied:
        return {
            "status": "failed",
            "error": "Access Denied. You need Administrator privileges to kill this system process."
        }
    except psutil.TimeoutExpired:
        # If it freezes and refuses to close gracefully, force kill it
        try:
            process.kill()
            return {
                "status": "success",
                "pid": pid,
                "process_name": getattr(process, 'name', lambda: 'Unknown')(),
                "message": f"Forcefully killed the frozen process (PID {pid})."
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to force kill: {str(e)}"
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }