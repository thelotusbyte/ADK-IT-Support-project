import subprocess


def get_startup_apps():
    try:
        command = [
            "powershell",
            "-Command",
            "Get-CimInstance Win32_StartupCommand | Select-Object Name"
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )

        output_lines = result.stdout.strip().split("\n")

        startup_apps = []

        for line in output_lines[3:]:
            app_name = line.strip()

            if app_name:
                startup_apps.append(app_name)

        return {
            "startup_app_count": len(startup_apps),
            "startup_apps": startup_apps
        }

    except Exception as e:
        return {
            "error": str(e)
        }