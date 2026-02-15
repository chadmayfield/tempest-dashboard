// Current conditions card rendering

import { state } from './state.js';

const UV_LEVELS = [
    { max: 2,  label: 'Low',       className: 'uv-low' },
    { max: 5,  label: 'Moderate',  className: 'uv-moderate' },
    { max: 7,  label: 'High',      className: 'uv-high' },
    { max: 10, label: 'Very High', className: 'uv-very-high' },
    { max: Infinity, label: 'Extreme', className: 'uv-extreme' },
];

function getUVLevel(index) {
    return UV_LEVELS.find(l => index <= l.max) || UV_LEVELS[UV_LEVELS.length - 1];
}

function formatValue(val, decimals = 1) {
    if (val === null || val === undefined) return '--';
    return Number(val).toFixed(decimals);
}

function createStatBox(label, value, unit, secondary) {
    const box = document.createElement('div');
    box.className = 'stat-box';

    const labelEl = document.createElement('div');
    labelEl.className = 'stat-label';
    labelEl.textContent = label;

    const valueEl = document.createElement('div');
    valueEl.className = 'stat-value';
    valueEl.textContent = value;
    if (unit) {
        const unitSpan = document.createElement('span');
        unitSpan.className = 'unit';
        unitSpan.textContent = ' ' + unit;
        valueEl.appendChild(unitSpan);
    }

    box.appendChild(labelEl);
    box.appendChild(valueEl);

    if (secondary) {
        const secEl = document.createElement('div');
        secEl.className = 'stat-secondary';
        secEl.textContent = secondary;
        box.appendChild(secEl);
    }

    return box;
}

export function renderCurrentConditions(obs) {
    const grid = document.getElementById('stats-grid');
    if (!grid) return;

    const units = state.get('units') || 'metric';
    const isMetric = units === 'metric';
    const tempUnit = isMetric ? '\u00B0C' : '\u00B0F';
    const windUnit = isMetric ? 'm/s' : 'mph';
    const pressureUnit = isMetric ? 'hPa' : 'inHg';
    const rainUnit = isMetric ? 'mm' : 'in';
    const pressureDecimals = isMetric ? 1 : 2;

    // Clear existing
    grid.textContent = '';

    if (!obs) {
        grid.appendChild(createStatBox('Temperature', '--', tempUnit));
        return;
    }

    const uv = getUVLevel(obs.uv_index || 0);

    // Temperature
    grid.appendChild(createStatBox(
        'Temperature',
        formatValue(obs.air_temperature),
        tempUnit,
        `Feels like ${formatValue(obs.feels_like)}${tempUnit}`
    ));

    // Humidity
    grid.appendChild(createStatBox(
        'Humidity',
        formatValue(obs.relative_humidity, 0),
        '%',
        `Dew point ${formatValue(obs.dew_point)}${tempUnit}`
    ));

    // Wind
    const windDir = obs.wind_direction_cardinal || '';
    grid.appendChild(createStatBox(
        'Wind',
        formatValue(obs.wind_avg),
        windUnit,
        `Gust ${formatValue(obs.wind_gust)} ${windUnit} ${windDir}`
    ));

    // Pressure
    grid.appendChild(createStatBox(
        'Pressure',
        formatValue(obs.station_pressure, pressureDecimals),
        pressureUnit
    ));

    // UV Index
    const uvBox = createStatBox(
        'UV Index',
        formatValue(obs.uv_index, 0),
        '',
        uv.label
    );
    const uvSec = uvBox.querySelector('.stat-secondary');
    if (uvSec) uvSec.classList.add(uv.className);
    grid.appendChild(uvBox);

    // Rain
    grid.appendChild(createStatBox(
        'Rain',
        formatValue(obs.rain_accumulation, isMetric ? 1 : 2),
        rainUnit
    ));

    // Solar Radiation
    grid.appendChild(createStatBox(
        'Solar Radiation',
        formatValue(obs.solar_radiation, 0),
        'W/m\u00B2'
    ));

    // Lightning
    if (obs.lightning_strike_count > 0) {
        const distUnit = isMetric ? 'km' : 'mi';
        grid.appendChild(createStatBox(
            'Lightning',
            obs.lightning_strike_count,
            'strikes',
            `Avg distance ${formatValue(obs.lightning_avg_distance)} ${distUnit}`
        ));
    }
}

export function showLoadingState() {
    const grid = document.getElementById('stats-grid');
    if (!grid) return;
    grid.textContent = '';
    const labels = ['Temperature', 'Humidity', 'Wind', 'Pressure', 'UV Index', 'Rain'];
    for (const label of labels) {
        const box = createStatBox(label, '--', '');
        const val = box.querySelector('.stat-value');
        if (val) val.classList.add('loading');
        grid.appendChild(box);
    }
}
