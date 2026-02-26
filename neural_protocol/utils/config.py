import os
from typing import Any, Dict

def load_config() -> Dict[str, Any]:
    """Load configuration from environment variables (future use)."""
    return {
        "transport": os.getenv("NEURAL_TRANSPORT", "local"),
        "hub_url": os.getenv("NEURAL_HUB_URL", "ws://localhost:8765"),
    }