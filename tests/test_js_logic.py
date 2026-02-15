"""Test JavaScript module logic by parsing the source files.

These tests verify the correctness of pure JS logic (resolution mapping,
time range definitions, etc.) by reading and evaluating the source code
rather than running a browser. This catches regressions in configuration
values and ensures consistency with the tempestd API contract.
"""

import os
import re

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JS_DIR = os.path.join(REPO_ROOT, "js")


def read_js(filename):
    with open(os.path.join(JS_DIR, filename)) as f:
        return f.read()


class TestConfigResolution:
    """Resolution auto-selection must match the documented mapping."""

    def _extract_resolution_thresholds(self):
        """Parse getResolution() from config.js to extract hour->resolution mapping."""
        source = read_js("config.js")
        # Match patterns like: if (hours <= 6) return '1m';
        pattern = r"if \(hours <= (\d+)\) return '(\w+)'"
        matches = re.findall(pattern, source)
        # Also get the final return (the default — no if condition)
        final = re.search(r"return '(\w+)';\s*//\s*90", source)
        return matches, final

    def test_resolution_thresholds_exist(self):
        matches, final = self._extract_resolution_thresholds()
        assert len(matches) >= 4, "Expected at least 4 resolution thresholds"

    def test_6h_uses_1m(self):
        matches, _ = self._extract_resolution_thresholds()
        thresholds = {int(h): r for h, r in matches}
        assert thresholds[6] == "1m"

    def test_24h_uses_5m(self):
        matches, _ = self._extract_resolution_thresholds()
        thresholds = {int(h): r for h, r in matches}
        assert thresholds[24] == "5m"

    def test_7d_uses_30m(self):
        matches, _ = self._extract_resolution_thresholds()
        thresholds = {int(h): r for h, r in matches}
        assert thresholds[168] == "30m"

    def test_30d_uses_1h(self):
        matches, _ = self._extract_resolution_thresholds()
        thresholds = {int(h): r for h, r in matches}
        assert thresholds[720] == "1h"

    def test_90d_uses_3h(self):
        matches, final = self._extract_resolution_thresholds()
        assert final is not None
        assert final.group(1) == "3h"


class TestTimeRangePresets:
    """TIME_RANGES must define all expected presets with correct hours."""

    EXPECTED = {
        "6h": 6,
        "24h": 24,
        "7d": 168,
        "30d": 720,
        "90d": 2160,
    }

    def test_all_presets_defined(self):
        source = read_js("config.js")
        for key in self.EXPECTED:
            assert f"'{key}'" in source, f"Missing time range preset: {key}"

    @pytest.mark.parametrize("key,hours", EXPECTED.items())
    def test_preset_hours(self, key, hours):
        source = read_js("config.js")
        # Match: '7d':  { hours: 168,
        pattern = rf"'{re.escape(key)}':\s*\{{\s*hours:\s*(\d+)"
        match = re.search(pattern, source)
        assert match is not None, f"Could not find hours for preset {key}"
        assert int(match.group(1)) == hours


class TestAPIEndpoints:
    """api.js must call the correct tempestd endpoints."""

    EXPECTED_PATHS = [
        "/api/v1/health",
        "/api/v1/stations",
    ]

    EXPECTED_PATTERNS = [
        r"/api/v1/stations/\$\{stationId\}/current",
        r"/api/v1/stations/\$\{stationId\}/observations",
        r"/api/v1/stations/\$\{stationId\}/summary",
        r"/api/v1/stations/\$\{stationId\}/range",
    ]

    def test_endpoint_paths(self):
        source = read_js("api.js")
        for path in self.EXPECTED_PATHS:
            assert path in source, f"Missing endpoint: {path}"

    @pytest.mark.parametrize("pattern", EXPECTED_PATTERNS)
    def test_parameterized_endpoints(self, pattern):
        source = read_js("api.js")
        assert re.search(pattern, source), f"Missing endpoint pattern: {pattern}"


class TestStateModule:
    """state.js must export a usable event emitter."""

    def test_exports_state(self):
        source = read_js("state.js")
        assert "export const state" in source or "export { state" in source

    def test_has_get_method(self):
        source = read_js("state.js")
        assert "get(key)" in source

    def test_has_set_method(self):
        source = read_js("state.js")
        assert "set(key, value)" in source or "set(key," in source

    def test_has_on_method(self):
        source = read_js("state.js")
        assert "on(key, callback)" in source or "on(key," in source


class TestChartsModule:
    """charts.js must define all 6 chart panels."""

    EXPECTED_CHARTS = [
        "chart-temperature",
        "chart-humidity",
        "chart-wind",
        "chart-pressure",
        "chart-rain",
        "chart-solar",
    ]

    @pytest.mark.parametrize("chart_id", EXPECTED_CHARTS)
    def test_chart_referenced(self, chart_id):
        source = read_js("charts.js")
        assert chart_id in source, f"Missing chart reference: {chart_id}"

    def test_zoom_requires_modifier_key(self):
        source = read_js("charts.js")
        assert "modifierKey" in source, "Zoom should require a modifier key"

    def test_no_point_dots(self):
        source = read_js("charts.js")
        assert "radius: 0" in source, "Charts should have point radius: 0"


class TestCurrentModule:
    """current.js must render all stat boxes from the plan."""

    EXPECTED_STATS = [
        "Temperature",
        "Humidity",
        "Wind",
        "Pressure",
        "UV Index",
        "Rain",
        "Solar Radiation",
    ]

    @pytest.mark.parametrize("stat", EXPECTED_STATS)
    def test_stat_rendered(self, stat):
        source = read_js("current.js")
        assert stat in source, f"Missing stat box: {stat}"

    def test_uv_severity_levels(self):
        source = read_js("current.js")
        for level in ["Low", "Moderate", "High", "Very High", "Extreme"]:
            assert level in source, f"Missing UV severity level: {level}"


class TestPluginsModule:
    """plugins.js must implement the plugin lifecycle."""

    LIFECYCLE_METHODS = ["init", "render", "createCharts", "refresh", "destroy"]

    @pytest.mark.parametrize("method", LIFECYCLE_METHODS)
    def test_lifecycle_method_called(self, method):
        source = read_js("plugins.js")
        assert f"plugin.{method}" in source, f"Missing lifecycle call: plugin.{method}"

    def test_loads_plugins_json(self):
        source = read_js("plugins.js")
        assert "plugins.json" in source

    def test_uses_dynamic_import(self):
        source = read_js("plugins.js")
        assert "import(" in source, "Should use dynamic import() for plugins"


class TestSecurityPatterns:
    """Verify security patterns are followed."""

    def test_no_innerhtml_in_current(self):
        source = read_js("current.js")
        assert "innerHTML" not in source, "current.js must not use innerHTML (XSS risk)"

    def test_no_innerhtml_in_controls(self):
        source = read_js("controls.js")
        assert "innerHTML" not in source, "controls.js must not use innerHTML (XSS risk)"

    def test_url_validation_in_config(self):
        source = read_js("config.js")
        assert "new URL(" in source, "Server URLs must be validated with URL constructor"

    def test_textcontent_used_in_current(self):
        source = read_js("current.js")
        assert "textContent" in source, "Should use textContent for safe rendering"
