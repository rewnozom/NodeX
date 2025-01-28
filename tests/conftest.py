import os
import shutil
import pytest
import tempfile
import numpy as np
from unittest.mock import MagicMock

from ai_agent.config.ai_config import Config

# -----------------------------------------------------------
# 1) Global fixture: temporary directory for file tests
# -----------------------------------------------------------
@pytest.fixture
def temp_dir():
    """Creates and yields a temporary directory for tests, then cleans it up."""
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)

# -----------------------------------------------------------
# 2) Fixture: returns a fresh, default config object
# -----------------------------------------------------------
@pytest.fixture
def agent_config():
    """Returns a new Config object."""
    return Config()

# -----------------------------------------------------------
# 3) Fixture: mock model
# -----------------------------------------------------------
@pytest.fixture
def mock_model():
    """Returns a MagicMock for a typical LLM or Chat model."""
    model = MagicMock()
    model.__class__.__name__ = 'MockModel'
    return model

# -----------------------------------------------------------
# 4) Utility fixture: skip if PySide6 not available
# -----------------------------------------------------------
def _check_pyside6():
    try:
        import PySide6  # Just a quick import to see if installed
        return True
    except ImportError:
        return False

@pytest.fixture(scope="session")
def has_pyside6():
    """Check if PySide6 is installed in the current environment."""
    return _check_pyside6()

# -----------------------------------------------------------
# 5) Utility fixture: skip if crewai not available
# -----------------------------------------------------------
def _check_crewai():
    try:
        import crewai
        return True
    except ImportError:
        return False

@pytest.fixture(scope="session")
def has_crewai():
    """Check if crewai is installed in the current environment."""
    return _check_crewai()
