"""Lightweight mock tempestd server for CI testing.

Returns canned JSON responses for all endpoints the dashboard tests exercise.
No database, no WebSocket — just static data shaped like real tempestd responses.
"""

import json
import re
import threading
from datetime import datetime, timedelta, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

STATION_ID = 99999
DEVICE_ID = 88888
STATION_NAME = "Mock Station"


def _now():
    return datetime.now(timezone.utc)


def _iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _make_observation(timestamp, station_id=STATION_ID):
    return {
        "timestamp": _iso(timestamp),
        "station_id": station_id,
        "wind_lull": 1.2,
        "wind_avg": 2.5,
        "wind_gust": 4.1,
        "wind_direction": 225.0,
        "station_pressure": 1013.25,
        "air_temperature": 22.5,
        "relative_humidity": 65.0,
        "uv_index": 5.0,
        "solar_radiation": 800.0,
        "rain_accumulation": 0.0,
        "precipitation_type": 0,
        "lightning_avg_distance": 0.0,
        "lightning_strike_count": 0,
        "battery": 2.6,
        "feels_like": 22.1,
        "dew_point": 15.3,
    }


class MockHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        # GET /api/v1/health
        if path == "/api/v1/health":
            self._json(200, {
                "status": "healthy",
                "version": "mock-1.0.0",
                "uptime": "0m",
                "stations": [{
                    "station_id": STATION_ID,
                    "name": STATION_NAME,
                    "websocket": "connected",
                    "last_observation": _iso(_now()),
                    "observation_age_seconds": 10.0,
                    "data_range_oldest": "2025-01-01",
                    "data_range_newest": _now().strftime("%Y-%m-%d"),
                }],
                "database": {
                    "driver": "sqlite",
                    "status": "ok",
                    "total_observations": 1000,
                },
            })
            return

        # GET /api/v1/stations
        if path == "/api/v1/stations":
            self._json(200, [{
                "station_id": STATION_ID,
                "device_id": DEVICE_ID,
                "name": STATION_NAME,
                "latitude": 37.7749,
                "longitude": -122.4194,
                "elevation": 10.0,
                "status": "online",
                "last_observation": _iso(_now()),
            }])
            return

        # GET /api/v1/stations/{id}
        m = re.match(r"^/api/v1/stations/(\d+)$", path)
        if m:
            sid = int(m.group(1))
            if sid != STATION_ID:
                self._json(404, {"error": "station not found", "code": 404})
                return
            self._json(200, {
                "station_id": STATION_ID,
                "device_id": DEVICE_ID,
                "name": STATION_NAME,
                "latitude": 37.7749,
                "longitude": -122.4194,
                "elevation": 10.0,
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": _iso(_now()),
            })
            return

        # GET /api/v1/stations/{id}/current
        m = re.match(r"^/api/v1/stations/(\d+)/current$", path)
        if m:
            units = params.get("units", ["metric"])[0]
            obs = _make_observation(_now())
            obs["wind_direction_cardinal"] = "SW"
            obs["units"] = units
            if units == "imperial":
                obs["air_temperature"] = 72.5
                obs["feels_like"] = 71.8
                obs["dew_point"] = 59.5
                obs["wind_avg"] = 5.6
                obs["wind_gust"] = 9.2
                obs["wind_lull"] = 2.7
                obs["station_pressure"] = 29.92
                obs["rain_accumulation"] = 0.0
            self._json(200, obs)
            return

        # GET /api/v1/stations/{id}/observations
        m = re.match(r"^/api/v1/stations/(\d+)/observations$", path)
        if m:
            units = params.get("units", ["metric"])[0]
            resolution = params.get("resolution", ["1m"])[0]
            limit = int(params.get("limit", ["1000"])[0])
            offset = int(params.get("offset", ["0"])[0])

            # Generate 10 observations
            now = _now()
            all_obs = []
            for i in range(10):
                t = now - timedelta(minutes=i * 5)
                all_obs.append(_make_observation(t))
            all_obs.reverse()

            total = len(all_obs)
            page = all_obs[offset:offset + limit]

            self._json(200, {
                "station_id": STATION_ID,
                "start": params.get("start", [_iso(now - timedelta(hours=1))])[0],
                "end": params.get("end", [_iso(now)])[0],
                "resolution": resolution,
                "units": units,
                "total": total,
                "limit": limit,
                "offset": offset,
                "observations": page,
            })
            return

        # GET /api/v1/stations/{id}/summary
        m = re.match(r"^/api/v1/stations/(\d+)/summary$", path)
        if m:
            units = params.get("units", ["metric"])[0]
            date = params.get("date", [_now().strftime("%Y-%m-%d")])[0]
            self._json(200, {
                "station_id": STATION_ID,
                "date": date,
                "units": units,
                "temperature": {"high": 28.5, "low": 12.3, "avg": 20.4},
                "humidity": {"high": 85.0, "low": 40.0, "avg": 62.5},
                "wind": {"max": 12.5, "avg": 3.2},
                "pressure": {"high": 1020.0, "low": 1010.0},
                "rain_total": 2.5,
                "uv_max": 8.0,
                "solar_radiation_max": 1100.0,
                "lightning_total": 0,
                "observation_count": 1440,
            })
            return

        # GET /api/v1/stations/{id}/range
        m = re.match(r"^/api/v1/stations/(\d+)/range$", path)
        if m:
            self._json(200, {
                "station_id": STATION_ID,
                "oldest": "2025-01-01T00:00:00Z",
                "newest": _iso(_now()),
                "total_observations": 1000,
            })
            return

        self._json(404, {"error": "not found", "code": 404})

    def _json(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass  # silence logs in CI


def start_mock_server(port=0):
    """Start the mock server on a random port. Returns (server, port)."""
    server = HTTPServer(("127.0.0.1", port), MockHandler)
    actual_port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, actual_port
