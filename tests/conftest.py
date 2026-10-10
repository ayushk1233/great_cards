import json
from pathlib import Path

import pytest

RAW = Path(__file__).resolve().parent.parent / "discovery" / "raw"
CATALOG = Path(__file__).resolve().parent.parent / "discovery" / "tools.json"


@pytest.fixture
def raw():
    """Load a recorded discovery response: raw('edge__details_bad_alias')['raw_result']."""
    return lambda name: json.loads((RAW / f"{name}.json").read_text())


@pytest.fixture
def live_catalog():
    return json.loads(CATALOG.read_text())["tools"]
