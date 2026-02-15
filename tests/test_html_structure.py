"""Verify the HTML structure has all required elements and attributes."""

import os
import re
from html.parser import HTMLParser

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_HTML = os.path.join(REPO_ROOT, "index.html")


@pytest.fixture(scope="module")
def html():
    with open(INDEX_HTML) as f:
        return f.read()


class IDCollector(HTMLParser):
    """Collect all element IDs and tag attributes from HTML."""

    def __init__(self):
        super().__init__()
        self.ids = set()
        self.scripts = []
        self.links = []
        self.metas = []
        self.canvases = []

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        if "id" in attr_dict:
            self.ids.add(attr_dict["id"])
        if tag == "script":
            self.scripts.append(attr_dict)
        if tag == "link":
            self.links.append(attr_dict)
        if tag == "meta":
            self.metas.append(attr_dict)
        if tag == "canvas":
            self.canvases.append(attr_dict)


@pytest.fixture(scope="module")
def parsed(html):
    collector = IDCollector()
    collector.feed(html)
    return collector


class TestRequiredElements:
    """All IDs referenced by JS modules must exist in the HTML."""

    REQUIRED_IDS = [
        # Config banner
        "config-banner",
        "config-url",
        "config-connect",
        "config-error",
        # Header
        "station-select",
        "unit-metric",
        "unit-imperial",
        "status-dot",
        "status-text",
        # Current conditions
        "current-conditions",
        "stats-grid",
        # Charts
        "chart-temperature",
        "chart-humidity",
        "chart-wind",
        "chart-pressure",
        "chart-rain",
        "chart-solar",
        # Plugin container
        "plugin-sections",
        # Footer
        "last-updated",
        "refresh-countdown",
        # Custom date range
        "custom-start",
        "custom-end",
        "custom-apply",
    ]

    @pytest.mark.parametrize("element_id", REQUIRED_IDS)
    def test_element_exists(self, parsed, element_id):
        assert element_id in parsed.ids, f"Missing element with id='{element_id}'"


class TestChartCanvases:
    """Each chart panel must have a canvas element."""

    EXPECTED_CANVASES = [
        "chart-temperature",
        "chart-humidity",
        "chart-wind",
        "chart-pressure",
        "chart-rain",
        "chart-solar",
    ]

    def test_all_canvases_present(self, parsed):
        canvas_ids = {c.get("id") for c in parsed.canvases}
        for cid in self.EXPECTED_CANVASES:
            assert cid in canvas_ids, f"Missing canvas id='{cid}'"

    def test_canvas_count(self, parsed):
        assert len(parsed.canvases) >= 6


class TestCDNScripts:
    """CDN scripts must have integrity and crossorigin attributes."""

    def test_cdn_scripts_have_sri(self, parsed):
        cdn_scripts = [s for s in parsed.scripts if s.get("src", "").startswith("https://")]
        assert len(cdn_scripts) == 4, f"Expected 4 CDN scripts, got {len(cdn_scripts)}"
        for script in cdn_scripts:
            assert "integrity" in script, f"Missing integrity on {script.get('src')}"
            assert script.get("crossorigin") == "anonymous", (
                f"Missing crossorigin=anonymous on {script.get('src')}"
            )

    def test_chart_js_included(self, parsed):
        srcs = [s.get("src", "") for s in parsed.scripts]
        assert any("chart.js" in s for s in srcs), "Chart.js CDN script not found"

    def test_date_adapter_included(self, parsed):
        srcs = [s.get("src", "") for s in parsed.scripts]
        assert any("chartjs-adapter-date-fns" in s for s in srcs)

    def test_hammer_included(self, parsed):
        srcs = [s.get("src", "") for s in parsed.scripts]
        assert any("hammerjs" in s or "hammer.min" in s for s in srcs)

    def test_zoom_plugin_included(self, parsed):
        srcs = [s.get("src", "") for s in parsed.scripts]
        assert any("chartjs-plugin-zoom" in s for s in srcs)


class TestCSP:
    """Content Security Policy meta tag must be present."""

    def test_csp_meta_exists(self, parsed):
        csp_metas = [
            m for m in parsed.metas
            if m.get("http-equiv", "").lower() == "content-security-policy"
        ]
        assert len(csp_metas) == 1, "Expected exactly one CSP meta tag"

    def test_csp_allows_self(self, html):
        assert "script-src 'self'" in html

    def test_csp_allows_jsdelivr(self, html):
        assert "https://cdn.jsdelivr.net" in html


class TestAppEntryPoint:
    """The app module must be loaded as type=module."""

    def test_app_module_script(self, parsed):
        module_scripts = [
            s for s in parsed.scripts
            if s.get("type") == "module" and "app.js" in s.get("src", "")
        ]
        assert len(module_scripts) == 1, "Expected one module script loading app.js"


class TestPWA:
    """PWA manifest and theme-color must be present."""

    def test_manifest_link(self, parsed):
        manifest_links = [l for l in parsed.links if l.get("rel") == "manifest"]
        assert len(manifest_links) == 1

    def test_theme_color(self, parsed):
        theme_metas = [m for m in parsed.metas if m.get("name") == "theme-color"]
        assert len(theme_metas) == 1


class TestTimeRangeButtons:
    """Time range preset buttons must exist with correct data attributes."""

    def test_preset_buttons(self, html):
        for preset in ["6h", "24h", "7d", "30d", "90d"]:
            assert f'data-range="{preset}"' in html, f"Missing time range button for {preset}"
