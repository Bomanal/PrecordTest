"""Optional Google ADK entrypoint. The FastAPI workbench does not need this."""

from . import agent

__all__ = ["agent"]
