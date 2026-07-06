import subprocess
from bs4 import BeautifulSoup

def generate_battery_report():
    """
    Generates Windows battery report.
    """

    report_path = "battery-report.html"

    command = [
        "powercfg",
        "/batteryreport",
        "/output",
        report_path
    ]

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode == 0:

        return {
            "success": True,
            "report_path": report_path
        }

    return {
        "success": False,
        "error": result.stderr
    }
def parse_battery_report(report_path):
    """
    Extracts battery information from battery report HTML.
    """
    with open(report_path, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "html.parser")

    battery_data = {
        "design_capacity": "N/A",
        "full_charge_capacity": "N/A",
        "cycle_count": "N/A"
    }

    # Find the "Installed batteries" header
    installed_batteries_header = None
    for h2 in soup.find_all("h2"):
        if "Installed batteries" in h2.get_text():
            installed_batteries_header = h2
            break
    
    if installed_batteries_header:
        # The table is the next sibling table after the header's parent or within the next sibling
        table = installed_batteries_header.find_next("table")
        if table:
            for tr in table.find_all("tr"):
                cells = tr.find_all("td")
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).upper()
                    value = cells[1].get_text(strip=True)
                    
                    if "DESIGN CAPACITY" in label:
                        battery_data["design_capacity"] = value
                    elif "FULL CHARGE CAPACITY" in label:
                        battery_data["full_charge_capacity"] = value
                    elif "CYCLE COUNT" in label:
                        battery_data["cycle_count"] = value

    return battery_data

def analyze_battery_health(battery_data):
    """
    Analyze battery health and generate diagnostics.
    """

    if battery_data["design_capacity"] == "N/A" or \
       battery_data["full_charge_capacity"] == "N/A":
        return {
            "health_percent": 0,
            "wear_percent"  : 0,
            "status"        : "Unknown",
            "recommendation": "Could not read battery data from report."
        }

    design_capacity = battery_data["design_capacity"]
    full_charge_capacity = battery_data["full_charge_capacity"]

    # Remove commas and mWh text
    design_capacity = (
        design_capacity
        .replace(",", "")
        .replace("mWh", "")
        .strip()
    )

    full_charge_capacity = (
        full_charge_capacity
        .replace(",", "")
        .replace("mWh", "")
        .strip()
    )

    # Convert strings to integers
    design_capacity = int(design_capacity)
    full_charge_capacity = int(full_charge_capacity)

    # Calculate health percentage
    health_percent = (
        full_charge_capacity / design_capacity
    ) * 100

    # Calculate wear percentage
    wear_percent = 100 - health_percent

    # Determine battery condition
    if health_percent >= 95:

        status = "Excellent"
        recommendation = "Battery health is excellent."

    elif health_percent >= 85:

        status = "Good"
        recommendation = "Battery is in good condition."

    elif health_percent >= 70:

        status = "Aging"
        recommendation = (
            "Battery is aging. "
            "Monitor performance closely."
        )

    else:

        status = "Replace Soon"
        recommendation = (
            "Consider replacing the battery."
        )

    return {
        "health_percent": round(health_percent, 2),
        "wear_percent": round(wear_percent, 2),
        "status": status,
        "recommendation": recommendation
    }