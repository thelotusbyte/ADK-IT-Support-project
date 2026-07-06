import socket
import time
import psutil


def check_internet_connection(
    host="8.8.8.8",
    port=53,
    timeout=3
):
    """
    Checks if internet is reachable.
    Attempts TCP connection to Google DNS.
    """

    try:
        socket.setdefaulttimeout(timeout)

        with socket.create_connection((host, port)):
            return True

    except OSError:
        return False


def check_dns_resolution(domain="google.com"):
    """
    Checks whether DNS resolution works.
    """

    try:
        ip_address = socket.gethostbyname(domain)

        return {
            "dns_working": True,
            "resolved_ip": ip_address
        }

    except socket.gaierror:
        return {
            "dns_working": False,
            "resolved_ip": None
        }


def tcp_ping(
    host="google.com",
    port=443,
    timeout=3
):
    """
    Measures TCP connection latency.
    """

    try:
        start_time = time.time()

        with socket.create_connection(
            (host, port),
            timeout=timeout
        ):
            end_time = time.time()

        latency_ms = round(
            (end_time - start_time) * 1000,
            2
        )

        return {
            "reachable": True,
            "latency_ms": latency_ms
        }

    except OSError:
        return {
            "reachable": False,
            "latency_ms": None
        }


def get_network_stats():
    """
    Returns basic network statistics.
    """

    stats = psutil.net_io_counters()

    return {
        "bytes_sent": stats.bytes_sent,
        "bytes_received": stats.bytes_recv,
        "packets_sent": stats.packets_sent,
        "packets_received": stats.packets_recv
    }