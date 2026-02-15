"""Shared fixtures for tempest-dashboard tests."""

import os
import subprocess
import time
import urllib.request
import urllib.error

import pytest

from tests.mock_tempestd import start_mock_server

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVE_SCRIPT = os.path.join(REPO_ROOT, "scripts", "serve.py")

# Override with TEMPESTD_URL env var to test against a real server
DEFAULT_BACKEND = os.environ.get("TEMPESTD_URL", "")


def wait_for_server(url, timeout=10):
    """Poll until the server responds or timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=2)
            return True
        except (urllib.error.URLError, ConnectionError, OSError):
            time.sleep(0.2)
    return False


@pytest.fixture(scope="session")
def backend_url():
    """The tempestd backend URL — real or mock."""
    if DEFAULT_BACKEND:
        return DEFAULT_BACKEND

    # Start mock tempestd
    server, port = start_mock_server()
    url = f"http://127.0.0.1:{port}"
    assert wait_for_server(f"{url}/api/v1/health", timeout=5), "Mock server failed to start"
    return url


@pytest.fixture(scope="session")
def dashboard_server(backend_url):
    """Start the dev server for the test session and yield its base URL."""
    port = 18742  # unlikely to conflict
    base_url = f"http://localhost:{port}"

    proc = subprocess.Popen(
        ["python3", SERVE_SCRIPT, "--port", str(port), "--backend", backend_url],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    if not wait_for_server(f"{base_url}/index.html"):
        proc.terminate()
        proc.wait()
        pytest.fail(f"Dev server failed to start on port {port}")

    yield base_url

    proc.terminate()
    proc.wait()
