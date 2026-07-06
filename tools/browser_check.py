import os
import winreg
import subprocess


# =========================
# BROWSER PATHS
# =========================

def get_browser_paths(browser):
    username = os.getenv("USERNAME")

    paths = {
        "chrome": {
            "cache": rf"C:\Users\{username}\AppData\Local\Google\Chrome\User Data\Default\Cache",
            "extensions": rf"C:\Users\{username}\AppData\Local\Google\Chrome\User Data\Default\Extensions",
            "exe": r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        },

        "edge": {
            "cache": rf"C:\Users\{username}\AppData\Local\Microsoft\Edge\User Data\Default\Cache",
            "extensions": rf"C:\Users\{username}\AppData\Local\Microsoft\Edge\User Data\Default\Extensions",
            "exe": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        },

        "firefox": {
            "profile_root": rf"C:\Users\{username}\AppData\Roaming\Mozilla\Firefox\Profiles"
        }
    }

    return paths.get(browser.lower())


# =========================
# FIREFOX PROFILE
# =========================

def get_firefox_profile(profile_root):
    try:
        if not os.path.exists(profile_root):
            return None

        profiles = os.listdir(profile_root)

        for profile in profiles:
            full_path = os.path.join(profile_root, profile)

            if os.path.isdir(full_path):
                return full_path

    except Exception:
        return None

    return None


# =========================
# CACHE SIZE
# =========================

def get_cache_size(cache_path):
    total_size = 0

    try:
        if not os.path.exists(cache_path):
            return 0

        for root, dirs, files in os.walk(cache_path):
            for file in files:
                file_path = os.path.join(root, file)

                try:
                    total_size += os.path.getsize(file_path)

                except Exception:
                    continue

        size_mb = total_size / (1024 * 1024)
        return round(size_mb, 2)

    except Exception:
        return 0


# =========================
# CACHE STATUS
# =========================

def evaluate_cache_status(size_mb):
    if size_mb < 1024:
        return "Good"

    elif 1024 <= size_mb <= 3072:
        return "Warning"

    else:
        return "Critical"


# =========================
# EXTENSION COUNT
# =========================

def get_extension_count(extension_path):
    try:
        if not os.path.exists(extension_path):
            return 0

        count = 0

        for item in os.listdir(extension_path):
            item_path = os.path.join(extension_path, item)

            if os.path.isdir(item_path):
                count += 1

        return count

    except Exception:
        return 0


# =========================
# EXTENSION STATUS
# =========================

def evaluate_extension_status(count):
    if count <= 10:
        return "Good"

    elif 11 <= count <= 20:
        return "Warning"

    else:
        return "Critical"


# =========================
# BROWSER VERSION
# =========================

def get_browser_version(exe_path):
    try:
        if not os.path.exists(exe_path):
            return "Unknown"

        # Chrome and Edge can sometimes hang if we use --version
        # especially if another instance is running.
        # It's better to read the version from the file info on Windows.
        import win32api

        info = win32api.GetFileVersionInfo(exe_path, "\\")
        ms = info['FileVersionMS']
        ls = info['FileVersionLS']
        version = f"{win32api.HIWORD(ms)}.{win32api.LOWORD(ms)}.{win32api.HIWORD(ls)}.{win32api.LOWORD(ls)}"

        return version

    except Exception:
        # Fallback to subprocess if win32api is not available or fails
        try:
            result = subprocess.check_output(
                [exe_path, "--version"],
                text=True,
                timeout=5
            )
            return result.strip()
        except Exception:
            return "Unknown"


# =========================
# DEFAULT BROWSER
# =========================

def get_default_browser():
    try:
        registry_path = (
            r"Software\Microsoft\Windows\Shell\Associations"
            r"\UrlAssociations\http\UserChoice"
        )

        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            registry_path
        )

        prog_id, _ = winreg.QueryValueEx(key, "ProgId")

        prog_id = prog_id.lower()

        if "chrome" in prog_id:
            return "Chrome"

        elif "edge" in prog_id:
            return "Edge"

        elif "firefox" in prog_id:
            return "Firefox"

        else:
            return "Other"

    except Exception:
        return "Unknown"


# =========================
# MAIN FUNCTION
# =========================

def browser_check(browser):
    browser = browser.lower()

    result = {
        "browser": browser,
        "browser_found": False,
        "cache_size_mb": 0,
        "cache_status": "Unknown",
        "extension_count": 0,
        "extension_status": "Unknown",
        "browser_version": "Unknown",
        "default_browser": get_default_browser(),
        "error_messages": []
    }

    paths = get_browser_paths(browser)

    if not paths:
        result["error_messages"].append("Unsupported browser")
        return result

    # =====================
    # FIREFOX
    # =====================

    if browser == "firefox":

        profile_path = get_firefox_profile(paths["profile_root"])

        if not profile_path:
            result["error_messages"].append("Firefox profile not found")
            return result

        cache_path = os.path.join(profile_path, "cache2")
        extension_path = os.path.join(profile_path, "extensions")

        exe_path = r"C:\Program Files\Mozilla Firefox\firefox.exe"

        result["browser_found"] = True

    # =====================
    # CHROME / EDGE
    # =====================

    else:
        cache_path = paths["cache"]
        extension_path = paths["extensions"]
        exe_path = paths["exe"]

        if not os.path.exists(exe_path):
            result["error_messages"].append(
                f"{browser.capitalize()} not installed"
            )
            return result

        result["browser_found"] = True

    # =====================
    # CACHE
    # =====================

    cache_size = get_cache_size(cache_path)

    result["cache_size_mb"] = cache_size
    result["cache_status"] = evaluate_cache_status(cache_size)

    # =====================
    # EXTENSIONS
    # =====================

    extension_count = get_extension_count(extension_path)

    result["extension_count"] = extension_count
    result["extension_status"] = evaluate_extension_status(extension_count)

    # =====================
    # VERSION
    # =====================

    version = get_browser_version(exe_path)

    result["browser_version"] = version

    return result