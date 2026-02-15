"""Browser tests: verify runtime behavior via Playwright."""

import re

import pytest
from playwright.sync_api import expect


def _stat_box(page, label):
    """Locate a stat box by its label text."""
    return page.locator(".stat-box", has=page.locator(".stat-label", has_text=label))


# --- Bootstrap Flow ---


class TestBootstrapFlow:
    """Dashboard loads, connects, and renders initial state."""

    def test_config_banner_hidden(self, bootstrapped_page):
        expect(bootstrapped_page.locator("#config-banner")).not_to_have_class(
            re.compile(r"\bvisible\b")
        )

    def test_station_dropdown_populated(self, bootstrapped_page):
        option = bootstrapped_page.locator("#station-select option")
        expect(option).to_have_count(1)
        expect(option.first).to_contain_text("Mock Station")

    def test_seven_stat_boxes(self, bootstrapped_page):
        expect(bootstrapped_page.locator(".stat-box")).to_have_count(7)

    def test_six_chart_canvases_visible(self, bootstrapped_page):
        canvases = bootstrapped_page.locator(".chart-grid canvas")
        expect(canvases).to_have_count(6)
        for i in range(6):
            expect(canvases.nth(i)).to_be_visible()

    def test_status_connected(self, bootstrapped_page):
        expect(bootstrapped_page.locator("#status-text")).to_have_text("Connected")


# --- Status Indicator ---


class TestStatusIndicator:
    """Status dot reflects connection state."""

    def test_status_dot_has_online_class(self, bootstrapped_page):
        expect(bootstrapped_page.locator("#status-dot")).to_have_class(
            re.compile(r"\bonline\b")
        )

    def test_status_dot_not_stale(self, bootstrapped_page):
        expect(bootstrapped_page.locator("#status-dot")).not_to_have_class(
            re.compile(r"\bstale\b")
        )


# --- Current Conditions ---


class TestCurrentConditions:
    """Stat boxes display correct values from mock API data."""

    def test_temperature_value(self, bootstrapped_page):
        box = _stat_box(bootstrapped_page, "Temperature")
        expect(box.locator(".stat-value")).to_contain_text("22.5")

    def test_temperature_feels_like(self, bootstrapped_page):
        box = _stat_box(bootstrapped_page, "Temperature")
        expect(box.locator(".stat-secondary")).to_contain_text("Feels like 22.1")

    def test_humidity_value(self, bootstrapped_page):
        box = _stat_box(bootstrapped_page, "Humidity")
        expect(box.locator(".stat-value")).to_contain_text("65")

    def test_humidity_dew_point(self, bootstrapped_page):
        box = _stat_box(bootstrapped_page, "Humidity")
        expect(box.locator(".stat-secondary")).to_contain_text("Dew point 15.3")

    def test_wind_value(self, bootstrapped_page):
        box = _stat_box(bootstrapped_page, "Wind")
        expect(box.locator(".stat-value")).to_contain_text("2.5")

    def test_wind_gust_and_direction(self, bootstrapped_page):
        box = _stat_box(bootstrapped_page, "Wind")
        expect(box.locator(".stat-secondary")).to_contain_text("Gust 4.1")
        expect(box.locator(".stat-secondary")).to_contain_text("SW")

    def test_pressure_value(self, bootstrapped_page):
        box = _stat_box(bootstrapped_page, "Pressure")
        expect(box.locator(".stat-value")).to_contain_text("1013")

    def test_uv_index_value(self, bootstrapped_page):
        box = _stat_box(bootstrapped_page, "UV Index")
        expect(box.locator(".stat-value")).to_contain_text("5")

    def test_uv_label_moderate(self, bootstrapped_page):
        box = _stat_box(bootstrapped_page, "UV Index")
        expect(box.locator(".stat-secondary")).to_have_text("Moderate")

    def test_solar_radiation_value(self, bootstrapped_page):
        box = _stat_box(bootstrapped_page, "Solar Radiation")
        expect(box.locator(".stat-value")).to_contain_text("800")


# --- Unit Toggle ---


class TestUnitToggle:
    """Switching units re-fetches data and updates display."""

    def test_metric_active_by_default(self, bootstrapped_page):
        expect(bootstrapped_page.locator("#unit-metric")).to_have_class(
            re.compile(r"\bactive\b")
        )
        expect(bootstrapped_page.locator("#unit-imperial")).not_to_have_class(
            re.compile(r"\bactive\b")
        )

    def test_click_imperial_shows_fahrenheit(self, bootstrapped_page):
        page = bootstrapped_page
        with page.expect_request(
            lambda r: "/current" in r.url and "units=imperial" in r.url
        ):
            page.click("#unit-imperial")
        box = _stat_box(page, "Temperature")
        expect(box.locator(".stat-value")).to_contain_text("72.5")

    def test_imperial_button_active(self, bootstrapped_page):
        expect(bootstrapped_page.locator("#unit-imperial")).to_have_class(
            re.compile(r"\bactive\b")
        )

    def test_click_metric_restores(self, bootstrapped_page):
        page = bootstrapped_page
        page.click("#unit-metric")
        box = _stat_box(page, "Temperature")
        expect(box.locator(".stat-value")).to_contain_text("22.5")


# --- Time Range Presets ---


class TestTimeRangePresets:
    """Time range buttons control active state."""

    def test_24h_active_by_default(self, bootstrapped_page):
        active = bootstrapped_page.locator(".time-presets button.active")
        expect(active).to_have_count(1)
        expect(active).to_have_attribute("data-range", "24h")

    def test_five_preset_buttons(self, bootstrapped_page):
        buttons = bootstrapped_page.locator(".time-presets button[data-range]")
        expect(buttons).to_have_count(5)
        for i, expected in enumerate(["6h", "24h", "7d", "30d", "90d"]):
            expect(buttons.nth(i)).to_have_attribute("data-range", expected)

    def test_click_7d_activates(self, bootstrapped_page):
        page = bootstrapped_page
        page.click(".time-presets button[data-range='7d']")
        expect(page.locator(".time-presets button[data-range='7d']")).to_have_class(
            re.compile(r"\bactive\b")
        )
        expect(
            page.locator(".time-presets button[data-range='24h']")
        ).not_to_have_class(re.compile(r"\bactive\b"))

    def test_restore_24h(self, bootstrapped_page):
        page = bootstrapped_page
        page.click(".time-presets button[data-range='24h']")
        expect(page.locator(".time-presets button[data-range='24h']")).to_have_class(
            re.compile(r"\bactive\b")
        )


# --- Custom Date Range ---


class TestCustomDateRange:
    """Custom date range inputs."""

    def test_valid_range_deactivates_presets(self, bootstrapped_page):
        page = bootstrapped_page
        page.fill("#custom-start", "2024-06-01T00:00")
        page.fill("#custom-end", "2024-06-02T00:00")
        page.click("#custom-apply")
        expect(page.locator(".time-presets button.active")).to_have_count(0)
        # Restore preset
        page.click(".time-presets button[data-range='24h']")

    def test_invalid_range_rejected(self, bootstrapped_page):
        page = bootstrapped_page
        page.fill("#custom-start", "2024-06-02T00:00")
        page.fill("#custom-end", "2024-06-01T00:00")
        page.click("#custom-apply")
        # 24h should still be active (restored in previous test)
        expect(page.locator(".time-presets button[data-range='24h']")).to_have_class(
            re.compile(r"\bactive\b")
        )


# --- Chart Rendering ---


class TestChartRendering:
    """Chart.js instances are created and populated."""

    def test_all_canvases_have_chart_instance(self, bootstrapped_page):
        page = bootstrapped_page
        canvas_ids = [
            "chart-temperature",
            "chart-humidity",
            "chart-wind",
            "chart-pressure",
            "chart-rain",
            "chart-solar",
        ]
        for cid in canvas_ids:
            has_chart = page.evaluate(
                f"Chart.getChart(document.getElementById('{cid}')) !== undefined"
            )
            assert has_chart, f"No Chart instance on #{cid}"

    def test_temperature_chart_has_data(self, bootstrapped_page):
        has_data = bootstrapped_page.evaluate(
            """() => {
            const chart = Chart.getChart(document.getElementById('chart-temperature'));
            return chart && chart.data.datasets[0].data.length > 0;
        }"""
        )
        assert has_data


# --- Footer ---


class TestFooter:
    """Footer displays update time and countdown."""

    def test_last_updated_has_timestamp(self, bootstrapped_page):
        text = bootstrapped_page.locator("#last-updated").text_content()
        assert "Last updated:" in text
        assert text != "Last updated: --"

    def test_refresh_countdown_shows_number(self, bootstrapped_page):
        text = bootstrapped_page.locator("#refresh-countdown").text_content()
        assert re.search(r"\d+", text)


# --- Plugin Sections ---


class TestPluginSections:
    """Plugin container is empty with no plugins configured."""

    def test_plugin_sections_empty(self, bootstrapped_page):
        inner = bootstrapped_page.locator("#plugin-sections").inner_html()
        assert inner.strip() == ""


# --- Config Banner Flow ---


class TestConfigBannerFlow:
    """Config banner shows when disconnected, hides on successful connect."""

    @pytest.fixture()
    def disconnected_page(self, browser, dashboard_server):
        """A page where the initial health check is blocked."""
        context = browser.new_context(service_workers="block", bypass_csp=True)
        page = context.new_page()
        page.route("**/api/v1/health", lambda route: route.abort())
        page.goto(dashboard_server)
        page.wait_for_function(
            "document.querySelector('#status-text')?.textContent === 'Disconnected'",
            timeout=10000,
        )
        yield page
        context.close()

    def test_banner_visible_when_disconnected(self, disconnected_page):
        expect(disconnected_page.locator("#config-banner")).to_have_class(
            re.compile(r"\bvisible\b")
        )

    def test_status_shows_disconnected(self, disconnected_page):
        expect(disconnected_page.locator("#status-text")).to_have_text("Disconnected")

    def test_connect_hides_banner(self, disconnected_page, dashboard_server):
        page = disconnected_page
        page.unroute("**/api/v1/health")
        page.fill("#config-url", dashboard_server)
        page.click("#config-connect")
        expect(page.locator("#config-banner")).not_to_have_class(
            re.compile(r"\bvisible\b")
        )
