import random
import time


def random_delay(min_seconds, max_seconds):
    """
    Introduces a randomized delay between `min_seconds` and `max_seconds`.

    :param min_seconds: Minimum number of seconds for the delay.
    :param max_seconds: Maximum number of seconds for the delay.
    """
    # Generate a random delay in seconds between min_seconds and max_seconds
    delay_seconds = random.uniform(min_seconds, max_seconds)

    # Pause the program's execution for the random delay duration
    time.sleep(delay_seconds)
