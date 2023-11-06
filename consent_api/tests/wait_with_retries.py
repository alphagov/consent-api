import time
from contextlib import contextmanager

MAX_RETRIES = 5
RETRY_WAIT = 1  # seconds


@contextmanager
def wait_with_retries(max_retries=MAX_RETRIES, retry_wait=RETRY_WAIT):
    retries = 0
    while True:
        try:
            yield
        except Exception as e:
            retries += 1
            if retries >= max_retries:
                raise
            print(f"Attempt {retries} failed with Exception: {e}")
            time.sleep(retry_wait)
        else:
            break
