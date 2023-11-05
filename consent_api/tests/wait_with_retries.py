import time
from contextlib import contextmanager

from selenium.common.exceptions import WebDriverException

MAX_RETRIES = 5
RETRY_WAIT = 1  # seconds


@contextmanager
def wait_with_retries(max_retries=MAX_RETRIES, retry_wait=RETRY_WAIT):
    retries = 0
    while retries < max_retries:
        try:
            yield
            break
        except WebDriverException as e:
            print(f"Attempt {retries + 1} failed with WebDriverException: {e}")
            time.sleep(retry_wait)
            retries += 1
            if retries >= max_retries:
                raise
        except Exception as e:
            print(f"Attempt {retries + 1} failed with Exception: {e}")
            break
