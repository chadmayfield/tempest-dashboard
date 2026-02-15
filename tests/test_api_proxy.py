"""Integration tests: verify the proxy returns correct data from tempestd."""

import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta, timezone

import pytest


def fetch_json(url):
    resp = urllib.request.urlopen(url, timeout=15)
    assert resp.status == 200
    return json.loads(resp.read())


class TestHealthEndpoint:
    """GET /api/v1/health"""

    def test_health_returns_healthy(self, dashboard_server):
        data = fetch_json(f"{dashboard_server}/api/v1/health")
        assert data["status"] == "healthy"

    def test_health_has_stations(self, dashboard_server):
        data = fetch_json(f"{dashboard_server}/api/v1/health")
        assert "stations" in data
        assert isinstance(data["stations"], list)
        assert len(data["stations"]) > 0

    def test_health_has_database(self, dashboard_server):
        data = fetch_json(f"{dashboard_server}/api/v1/health")
        assert "database" in data
        assert data["database"]["status"] == "ok"

    def test_health_station_fields(self, dashboard_server):
        data = fetch_json(f"{dashboard_server}/api/v1/health")
        station = data["stations"][0]
        assert "station_id" in station
        assert "name" in station
        assert "websocket" in station


class TestStationsEndpoint:
    """GET /api/v1/stations"""

    def test_returns_list(self, dashboard_server):
        data = fetch_json(f"{dashboard_server}/api/v1/stations")
        assert isinstance(data, list)
        assert len(data) > 0

    def test_station_fields(self, dashboard_server):
        data = fetch_json(f"{dashboard_server}/api/v1/stations")
        station = data[0]
        required = ["station_id", "name", "status"]
        for field in required:
            assert field in station, f"Missing field: {field}"

    def test_station_id_is_integer(self, dashboard_server):
        data = fetch_json(f"{dashboard_server}/api/v1/stations")
        for station in data:
            assert isinstance(station["station_id"], int)


class TestCurrentObservation:
    """GET /api/v1/stations/{id}/current"""

    @pytest.fixture(scope="class")
    def station_id(self, dashboard_server):
        stations = fetch_json(f"{dashboard_server}/api/v1/stations")
        return stations[0]["station_id"]

    def test_returns_observation(self, dashboard_server, station_id):
        data = fetch_json(f"{dashboard_server}/api/v1/stations/{station_id}/current")
        assert "timestamp" in data
        assert "air_temperature" in data

    def test_observation_fields(self, dashboard_server, station_id):
        data = fetch_json(f"{dashboard_server}/api/v1/stations/{station_id}/current")
        expected_fields = [
            "timestamp", "station_id", "air_temperature", "relative_humidity",
            "wind_avg", "wind_gust", "wind_lull", "wind_direction",
            "station_pressure", "uv_index", "solar_radiation",
            "rain_accumulation", "feels_like", "dew_point",
        ]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"

    def test_has_wind_direction_cardinal(self, dashboard_server, station_id):
        data = fetch_json(f"{dashboard_server}/api/v1/stations/{station_id}/current")
        assert "wind_direction_cardinal" in data

    def test_has_units_field(self, dashboard_server, station_id):
        data = fetch_json(f"{dashboard_server}/api/v1/stations/{station_id}/current")
        assert data["units"] == "metric"

    def test_imperial_units(self, dashboard_server, station_id):
        data = fetch_json(
            f"{dashboard_server}/api/v1/stations/{station_id}/current?units=imperial"
        )
        assert data["units"] == "imperial"


class TestObservations:
    """GET /api/v1/stations/{id}/observations"""

    @pytest.fixture(scope="class")
    def station_id(self, dashboard_server):
        stations = fetch_json(f"{dashboard_server}/api/v1/stations")
        return stations[0]["station_id"]

    def _obs_url(self, base, station_id, hours=6, **extra):
        now = datetime.now(timezone.utc)
        start = now - timedelta(hours=hours)
        params = {"start": start.isoformat(), "end": now.isoformat()}
        params.update(extra)
        qs = urllib.parse.urlencode(params)
        return f"{base}/api/v1/stations/{station_id}/observations?{qs}"

    def test_returns_envelope(self, dashboard_server, station_id):
        data = fetch_json(self._obs_url(dashboard_server, station_id))
        assert "observations" in data
        assert "total" in data
        assert "resolution" in data

    def test_observations_are_list(self, dashboard_server, station_id):
        data = fetch_json(self._obs_url(dashboard_server, station_id))
        assert isinstance(data["observations"], list)

    def test_observation_has_fields(self, dashboard_server, station_id):
        data = fetch_json(self._obs_url(dashboard_server, station_id, hours=1, resolution="1m"))
        if data["observations"]:
            obs = data["observations"][0]
            assert "timestamp" in obs
            assert "air_temperature" in obs
            assert "station_id" in obs

    def test_resolution_parameter(self, dashboard_server, station_id):
        data = fetch_json(self._obs_url(dashboard_server, station_id, hours=24, resolution="5m"))
        assert data["resolution"] == "5m"

    def test_imperial_units(self, dashboard_server, station_id):
        data = fetch_json(self._obs_url(dashboard_server, station_id, hours=1, units="imperial"))
        assert data["units"] == "imperial"

    def test_pagination_fields(self, dashboard_server, station_id):
        data = fetch_json(self._obs_url(dashboard_server, station_id, limit=10, offset=0))
        assert "limit" in data
        assert "offset" in data
        assert data["limit"] == 10
        assert data["offset"] == 0


class TestObservationRange:
    """GET /api/v1/stations/{id}/range"""

    @pytest.fixture(scope="class")
    def station_id(self, dashboard_server):
        stations = fetch_json(f"{dashboard_server}/api/v1/stations")
        return stations[0]["station_id"]

    def test_returns_range(self, dashboard_server, station_id):
        data = fetch_json(f"{dashboard_server}/api/v1/stations/{station_id}/range")
        assert "oldest" in data
        assert "newest" in data
        assert "total_observations" in data

    def test_total_is_positive(self, dashboard_server, station_id):
        data = fetch_json(f"{dashboard_server}/api/v1/stations/{station_id}/range")
        assert data["total_observations"] > 0
