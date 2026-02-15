// tempestd REST API client — wraps all fetch calls

import { getServerUrl, getResolution } from './config.js';

async function fetchJSON(path, params = {}) {
    const base = getServerUrl();
    const url = new URL(path, base);
    for (const [k, v] of Object.entries(params)) {
        if (v !== undefined && v !== null) {
            url.searchParams.set(k, String(v));
        }
    }
    const res = await fetch(url.toString());
    if (!res.ok) {
        const body = await res.json().catch(() => ({ error: res.statusText }));
        throw new Error(body.error || `HTTP ${res.status}`);
    }
    return res.json();
}

export function checkHealth() {
    return fetchJSON('/api/v1/health');
}

export function listStations() {
    return fetchJSON('/api/v1/stations');
}

export function getStation(stationId) {
    return fetchJSON(`/api/v1/stations/${stationId}`);
}

export function getCurrentObservation(stationId, units = 'metric') {
    return fetchJSON(`/api/v1/stations/${stationId}/current`, { units });
}

export function getObservations(stationId, start, end, opts = {}) {
    const { units = 'metric', resolution, limit, offset } = opts;
    const hours = (new Date(end) - new Date(start)) / 3600000;
    const res = resolution || getResolution(hours);
    return fetchJSON(`/api/v1/stations/${stationId}/observations`, {
        start, end, resolution: res, units, limit, offset,
    });
}

export function getDailySummary(stationId, date, units = 'metric') {
    return fetchJSON(`/api/v1/stations/${stationId}/summary`, { date, units });
}

export function getObservationRange(stationId) {
    return fetchJSON(`/api/v1/stations/${stationId}/range`);
}
