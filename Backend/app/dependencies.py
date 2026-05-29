"""Dependency injection and shared dependencies."""
import json
import os
from typing import Annotated

from fastapi import Depends
import networkx as nx

from .config import Settings, get_settings
from .engines.social_graph import build_graph


class AppState:
    """Shared application state."""

    def __init__(self):
        self.merchants = []
        self.merchant_map = {}
        self.graph = None
        self.settings = get_settings()

    def load_merchants(self):
        """Load merchant data from JSON file."""
        data_file = os.path.join(
            os.path.dirname(__file__), "..", "data", "mock_merchants.json"
        )
        if os.path.exists(data_file):
            with open(data_file, "r", encoding="utf-8") as f:
                self.merchants = json.load(f)
            self.merchant_map = {m["merchant_id"]: m for m in self.merchants}
            self.graph = build_graph(self.merchants)
        else:
            print(f"Warning: Mock data file not found at {data_file}")
            print("Run: python Backend/data/generate_mock.py to generate mock data")


# Global app state
_app_state = None


def get_app_state() -> AppState:
    """Get application state (dependency for FastAPI)."""
    global _app_state
    if _app_state is None:
        _app_state = AppState()
        _app_state.load_merchants()
    return _app_state


# Type aliases for dependency injection
AppStateDep = Annotated[AppState, Depends(get_app_state)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
