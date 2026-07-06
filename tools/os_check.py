import platform


def is_windows():
    """Checks whether the current operating system is Windows."""
    return platform.system() == "Windows"
