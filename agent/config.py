"""Configuration for the PLO agent."""

import json
import os
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CALENDAR_FILE = DATA_DIR / "calendar.json"
CASES_FILE = DATA_DIR / "cases.json"

# CCAP base URL (Wisconsin Circuit Court Access)
CCAP_BASE_URL = "https://wcca.wicourts.gov"
CCAP_SEARCH_URL = f"{CCAP_BASE_URL}/jsonPost/courtCaseSearch"

# Practice areas this agent supports
PRACTICE_AREAS = ["criminal_defense", "family_law"]


def ensure_data_dir():
    """Create data directory and seed files if they don't exist."""
    DATA_DIR.mkdir(exist_ok=True)
    for filepath, default in [(CALENDAR_FILE, []), (CASES_FILE, [])]:
        if not filepath.exists():
            filepath.write_text(json.dumps(default, indent=2))


def load_json(filepath):
    """Load a JSON file, return empty list if missing or corrupt."""
    try:
        return json.loads(filepath.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_json(filepath, data):
    """Save data to a JSON file."""
    ensure_data_dir()
    filepath.write_text(json.dumps(data, indent=2))
