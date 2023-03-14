"""Request a URL until response is received, or a given number of failures."""

import argparse
import socket
from sys import exit
from time import sleep
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import urlopen

parser = argparse.ArgumentParser()
parser.add_argument("url")
parser.add_argument("-t", "--timeout", type=float, default=2.0)
parser.add_argument("-r", "--retries", type=int, default=3)
parser.add_argument("-i", "--interval", type=float, default=0)


def wait_for_url(
    url: str = "",
    timeout: float = 2.0,
    retries: int = 3,
    interval: float = 0,
) -> None:
    """Request a URL until we get a response or retries all fail."""
    if not url:
        print("skipping empty URL")
        exit(1)
    try:
        urlparse(url)
        print(f"waiting for {url}...")
        urlopen(url, timeout=timeout)
        exit(0)
    except ValueError as bad_url:
        print(f"cannot parse {url}: {bad_url}")
    except URLError as err:
        if isinstance(err.reason, socket.timeout):
            print(f"{url} timed out")
            if retries:
                sleep(interval)
                print("retrying...")
                return wait_for_url(url, timeout, retries - 1, interval)
    exit(1)


if __name__ == "__main__":
    args = parser.parse_args()
    wait_for_url(args.url, args.timeout, args.retries, args.interval)
