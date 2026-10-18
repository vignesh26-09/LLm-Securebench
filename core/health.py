"""Small framework-independent health check used by delivery adapters."""

from typing import Final

SERVICE_NAME: Final = "securellmbench"


def health_status() -> dict[str, str]:
    """Return the minimal liveness payload for the application."""
    return {"service": SERVICE_NAME, "status": "ok"}
