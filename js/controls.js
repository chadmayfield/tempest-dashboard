// Station selector, time range buttons, unit toggle

import { state } from './state.js';
import { getUnits, setUnits, TIME_RANGES } from './config.js';

export function initControls() {
    initUnitToggle();
    initTimePresets();
    initCustomRange();
}

// --- Station Selector ---

export function populateStations(stations) {
    const select = document.getElementById('station-select');
    if (!select) return;

    select.textContent = '';

    if (!stations || stations.length === 0) {
        const opt = document.createElement('option');
        opt.value = '';
        opt.textContent = 'No stations found';
        select.appendChild(opt);
        return;
    }

    for (const s of stations) {
        const opt = document.createElement('option');
        opt.value = String(s.station_id);
        opt.textContent = s.name || `Station ${s.station_id}`;
        select.appendChild(opt);
    }

    // Restore previously selected station or use first
    const savedStation = state.get('stationId');
    if (savedStation && stations.find(s => s.station_id === savedStation)) {
        select.value = String(savedStation);
    } else {
        select.value = String(stations[0].station_id);
        state.set('stationId', stations[0].station_id);
    }

    select.addEventListener('change', () => {
        const id = parseInt(select.value, 10);
        if (!isNaN(id) && id > 0) {
            state.set('stationId', id);
        }
    });
}

// --- Unit Toggle ---

function initUnitToggle() {
    const metricBtn = document.getElementById('unit-metric');
    const imperialBtn = document.getElementById('unit-imperial');
    if (!metricBtn || !imperialBtn) return;

    // Set initial state
    const current = getUnits();
    state.set('units', current);
    updateUnitButtons(current);

    metricBtn.addEventListener('click', () => switchUnits('metric'));
    imperialBtn.addEventListener('click', () => switchUnits('imperial'));
}

function switchUnits(units) {
    setUnits(units);
    state.set('units', units);
    updateUnitButtons(units);
}

function updateUnitButtons(units) {
    const metricBtn = document.getElementById('unit-metric');
    const imperialBtn = document.getElementById('unit-imperial');
    if (metricBtn) metricBtn.classList.toggle('active', units === 'metric');
    if (imperialBtn) imperialBtn.classList.toggle('active', units === 'imperial');
}

// --- Time Range Presets ---

function initTimePresets() {
    const buttons = document.querySelectorAll('.time-presets button[data-range]');

    // Set initial time range
    const defaultRange = '24h';
    state.set('timeRange', defaultRange);
    state.set('timeRangeType', 'preset');
    updateTimeRange(defaultRange);

    for (const btn of buttons) {
        btn.addEventListener('click', () => {
            const range = btn.dataset.range;
            // Update active button
            for (const b of buttons) b.classList.remove('active');
            btn.classList.add('active');

            state.set('timeRange', range);
            state.set('timeRangeType', 'preset');
            updateTimeRange(range);
        });
    }
}

function updateTimeRange(rangeKey) {
    const preset = TIME_RANGES[rangeKey];
    if (!preset) return;

    const end = new Date();
    const start = new Date(end.getTime() - preset.hours * 3600000);
    state.set('startTime', start.toISOString());
    state.set('endTime', end.toISOString());
}

// Recalculate preset time range (called on refresh for live ranges)
export function refreshTimeRange() {
    if (state.get('timeRangeType') === 'preset') {
        updateTimeRange(state.get('timeRange'));
    }
}

// --- Custom Date Range ---

function initCustomRange() {
    const startInput = document.getElementById('custom-start');
    const endInput = document.getElementById('custom-end');
    const applyBtn = document.getElementById('custom-apply');
    if (!startInput || !endInput || !applyBtn) return;

    applyBtn.addEventListener('click', () => {
        const start = startInput.value;
        const end = endInput.value;

        if (!start || !end) return;

        const startDate = new Date(start);
        const endDate = new Date(end);

        if (isNaN(startDate.getTime()) || isNaN(endDate.getTime())) return;
        if (startDate >= endDate) return;
        if (endDate > new Date()) return;

        // Clear preset active state
        const buttons = document.querySelectorAll('.time-presets button[data-range]');
        for (const b of buttons) b.classList.remove('active');

        state.set('timeRangeType', 'custom');
        state.set('startTime', startDate.toISOString());
        state.set('endTime', endDate.toISOString());
    });
}
