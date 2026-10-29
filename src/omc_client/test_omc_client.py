import os
import pytest
from dotenv import load_dotenv
from omc_client import OMCClient


@pytest.fixture
def omc_client():
    """Create an OMC client for testing."""
    return OMCClient()


@pytest.fixture
def must_gather_path():
    """
    Get must-gather path from environment variable.

    Example:
        export OMC_MUST_GATHER=/path/to/must-gather
    """
    path = os.getenv("OMC_MUST_GATHER")

    if not path:
        pytest.skip(
            "OMC_MUST_GATHER environment variable is not set"
        )

    return path


def test_omc_version(omc_client):
    """Test that OMC version can be retrieved."""

    version = omc_client.version()

    assert version is not None
    assert str(version).strip() != ""


def test_omc_use(omc_client, must_gather_path):
    """Test loading a must-gather using OMC."""

    result = omc_client.use(must_gather_path)

    assert result is not None


