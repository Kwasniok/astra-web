from shortuuid import uuid
from datetime import datetime


def get_uuid() -> str:
    """Generate a new UUID based on the current date and time."""
    return f"{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}-{uuid()[:8]}"
