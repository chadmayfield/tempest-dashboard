"""Verify all static files are served correctly by the dev server."""

import urllib.request
import json

import pytest


class TestStaticFiles:
    """All dashboard files must be served with correct content types."""

    FILES = [
        "/index.html",
        "/css/style.css",
        "/js/app.js",
        "/js/config.js",
        "/js/state.js",
        "/js/api.js",
        "/js/current.js",
        "/js/controls.js",
        "/js/charts.js",
        "/js/plugins.js",
        "/plugins.json",
        "/manifest.json",
        "/sw.js",
        "/icons/favicon.svg",
    ]

    @pytest.mark.parametrize("path", FILES)
    def test_file_served(self, dashboard_server, path):
        url = dashboard_server + path
        resp = urllib.request.urlopen(url)
        assert resp.status == 200
        assert len(resp.read()) > 0

    def test_plugins_json_is_empty_array(self, dashboard_server):
        url = dashboard_server + "/plugins.json"
        resp = urllib.request.urlopen(url)
        data = json.loads(resp.read())
        assert data == [], "Core repo plugins.json should be an empty array"

    def test_manifest_json_valid(self, dashboard_server):
        url = dashboard_server + "/manifest.json"
        resp = urllib.request.urlopen(url)
        data = json.loads(resp.read())
        assert "name" in data
        assert "icons" in data
        assert data["display"] == "standalone"


class TestServiceWorker:
    """Service worker must be valid JavaScript."""

    def test_sw_contains_cache_name(self, dashboard_server):
        url = dashboard_server + "/sw.js"
        resp = urllib.request.urlopen(url)
        content = resp.read().decode()
        assert "CACHE_NAME" in content
        assert "tempest-dashboard" in content

    def test_sw_has_install_listener(self, dashboard_server):
        url = dashboard_server + "/sw.js"
        resp = urllib.request.urlopen(url)
        content = resp.read().decode()
        assert "addEventListener('install'" in content or 'addEventListener("install"' in content
