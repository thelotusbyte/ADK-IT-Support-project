import psutil
import subprocess
import platform


def _bytes_to_gb(bytes_value):
    return round(bytes_value / (1024 ** 3), 2)


def _detect_drive_type_windows(drive_letter):

    letter = drive_letter.rstrip("\\")

    ps_command = (
        f"$vol = Get-WmiObject Win32_LogicalDiskToPartition | "
        f"Where-Object {{$_.Dependent -like '*{letter}*'}}; "
        f"if ($vol) {{"
        f"  $part = [wmi]$vol.Antecedent; "
        f"  $disk = Get-WmiObject Win32_DiskDrive | "
        f"    Where-Object {{$_.Index -eq $part.DiskIndex}}; "
        f"  Write-Output ($disk.MediaType + '|' + $disk.SpindleSpeed)"
        f"}} else {{ Write-Output 'NOTFOUND' }}"
    )

    try:
        result = subprocess.run(
            ["powershell", "-NonInteractive", "-Command", ps_command],
            capture_output=True,
            text=True,
            timeout=10
        )

        raw = result.stdout.strip()

        if not raw or raw == "NOTFOUND":
            return "Unknown"

        parts = raw.split("|")

        media_type = parts[0].strip().upper() if parts else ""
        spindle_speed = parts[1].strip() if len(parts) > 1 else ""

        if "NVME" in media_type or "NVM" in media_type:
            return "NVMe"

        if "SSD" in media_type:
            return "SSD"

        if "HDD" in media_type or "FIXED" in media_type:
            if spindle_speed == "0":
                return "SSD"
            return "HDD"

        if spindle_speed == "0":
            return "SSD"

        return "Unknown"

    except Exception:
        return "Unknown"


def _detect_drive_type(drive_letter):

    if platform.system() == "Windows":
        return _detect_drive_type_windows(drive_letter)

    return "Unknown"


def disk_check():

    results = []

    partitions = psutil.disk_partitions(all=False)

    for partition in partitions:

        # Skip CD/DVD drives
        if 'cdrom' in partition.opts.lower():
            continue

        try:
            usage = psutil.disk_usage(partition.mountpoint)

            if usage.percent >= 90:
                status = "CRITICAL"
            elif usage.percent >= 80:
                status = "WARNING"
            else:
                status = "OK"

            results.append({
                "drive": partition.mountpoint,
                "total_gb": _bytes_to_gb(usage.total),
                "used_gb": _bytes_to_gb(usage.used),
                "free_gb": _bytes_to_gb(usage.free),
                "used_percent": usage.percent,
                "disk_type": _detect_drive_type(partition.mountpoint),
                "status": status
            })

        except PermissionError:
            continue

    return results


def display_disk_check(results):

    print("\n========== DISK CHECK ==========")

    for entry in results:

        print(f"\nDrive : {entry['drive']}")
        print(f"Type  : {entry['disk_type']}")
        print(f"Total : {entry['total_gb']} GB")
        print(f"Used  : {entry['used_gb']} GB")
        print(f"Free  : {entry['free_gb']} GB")
        print(f"Usage : {entry['used_percent']}%")
        print(f"Status: {entry['status']}")