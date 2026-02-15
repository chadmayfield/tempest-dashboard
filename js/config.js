// Server URL resolution, defaults, and color palette

const STORAGE_KEY_SERVER = 'tempest-dashboard-server';
const STORAGE_KEY_UNITS = 'tempest-dashboard-units';
const STORAGE_KEY_THEME = 'tempest-dashboard-theme';

/**
 * Resolve the tempestd server URL.
 * Priority: query param > localStorage > same origin
 */
function getServerUrl() {
    const params = new URLSearchParams(window.location.search);
    const paramUrl = params.get('server');
    if (paramUrl) {
        try {
            const url = new URL(paramUrl);
            localStorage.setItem(STORAGE_KEY_SERVER, url.origin);
            return url.origin;
        } catch {
            // invalid URL, fall through
        }
    }

    const stored = localStorage.getItem(STORAGE_KEY_SERVER);
    if (stored) return stored;

    return window.location.origin;
}

function setServerUrl(url) {
    const parsed = new URL(url); // throws on invalid input
    const origin = parsed.origin;
    localStorage.setItem(STORAGE_KEY_SERVER, origin);
    return origin;
}

function getUnits() {
    const params = new URLSearchParams(window.location.search);
    return params.get('units') || localStorage.getItem(STORAGE_KEY_UNITS) || 'metric';
}

function setUnits(units) {
    if (units !== 'metric' && units !== 'imperial') return;
    localStorage.setItem(STORAGE_KEY_UNITS, units);
}

// Resolution auto-selection based on time range duration
function getResolution(hours) {
    if (hours <= 6) return '1m';
    if (hours <= 24) return '5m';
    if (hours <= 168) return '30m';   // 7 days
    if (hours <= 720) return '1h';    // 30 days
    return '3h';                       // 90 days
}

// Time range presets
const TIME_RANGES = {
    '6h':  { hours: 6,    label: '6h'  },
    '24h': { hours: 24,   label: '24h' },
    '7d':  { hours: 168,  label: '7d'  },
    '30d': { hours: 720,  label: '30d' },
    '90d': { hours: 2160, label: '90d' },
};

const POLL_INTERVAL = 60000; // 60 seconds

// Read chart colors from CSS custom properties
function getChartColors() {
    const style = getComputedStyle(document.documentElement);
    const get = (prop, fallback) => style.getPropertyValue(prop).trim() || fallback;
    return {
        temperature: get('--color-temperature', '#ef4444'),
        feelsLike:   get('--color-feels-like', '#f97316'),
        dewPoint:    get('--color-dew-point', '#06b6d4'),
        humidity:    get('--color-humidity', '#3b82f6'),
        windAvg:     get('--color-wind-avg', '#22c55e'),
        windGust:    get('--color-wind-gust', '#ef4444'),
        windLull:    get('--color-wind-lull', '#86efac'),
        pressure:    get('--color-pressure', '#a855f7'),
        rain:        get('--color-rain', '#3b82f6'),
        solar:       get('--color-solar', '#eab308'),
        uv:          get('--color-uv', '#f97316'),
    };
}

// Get CSS color for text/grid/borders
function getUIColors() {
    const style = getComputedStyle(document.documentElement);
    const get = (prop, fallback) => style.getPropertyValue(prop).trim() || fallback;
    return {
        textPrimary:    get('--text-primary', '#e2e8f0'),
        textSecondary:  get('--text-secondary', '#94a3b8'),
        textMuted:      get('--text-muted', '#64748b'),
        gridColor:      get('--chart-grid', '#334155'),
        borderColor:    get('--border-color', '#334155'),
        tooltipBg:      get('--chart-tooltip-bg', 'rgba(15, 23, 42, 0.9)'),
        tooltipTitle:   get('--chart-tooltip-title', '#e2e8f0'),
        tooltipBody:    get('--chart-tooltip-body', '#94a3b8'),
        tooltipBorder:  get('--chart-tooltip-border', 'rgba(51, 65, 85, 0.5)'),
    };
}

export {
    getServerUrl, setServerUrl,
    getUnits, setUnits,
    getResolution, TIME_RANGES, POLL_INTERVAL,
    getChartColors, getUIColors,
    STORAGE_KEY_SERVER, STORAGE_KEY_UNITS, STORAGE_KEY_THEME,
};
