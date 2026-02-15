// Main entry: init, plugin loading, polling loop, event wiring

import { state } from './state.js';
import { setServerUrl, POLL_INTERVAL, STORAGE_KEY_THEME } from './config.js';
import { checkHealth, listStations, getCurrentObservation, getObservations } from './api.js';
import { renderCurrentConditions, showLoadingState } from './current.js';
import { initControls, populateStations, refreshTimeRange } from './controls.js';
import { createCharts, updateCharts, resetZoom, destroyCharts } from './charts.js';
import { loadPlugins, refreshPlugins } from './plugins.js';

let pollTimer = null;
let countdownTimer = null;
let countdown = 60;
let isRefreshing = false;

// --- Status Indicator ---

function setStatus(status, text) {
    const dot = document.getElementById('status-dot');
    const label = document.getElementById('status-text');
    if (dot) {
        dot.className = 'status-dot';
        if (status === 'online') dot.classList.add('online');
        else if (status === 'stale') dot.classList.add('stale');
    }
    if (label) label.textContent = text || status;
}

// --- Config Banner ---

function showConfigBanner() {
    const banner = document.getElementById('config-banner');
    if (banner) banner.classList.add('visible');
}

function hideConfigBanner() {
    const banner = document.getElementById('config-banner');
    if (banner) banner.classList.remove('visible');
}

function initConfigBanner() {
    const connectBtn = document.getElementById('config-connect');
    const urlInput = document.getElementById('config-url');
    const errorEl = document.getElementById('config-error');

    if (!connectBtn || !urlInput) return;

    connectBtn.addEventListener('click', async () => {
        const url = urlInput.value.trim();
        if (!url) return;

        try {
            setServerUrl(url);
        } catch {
            if (errorEl) {
                errorEl.textContent = 'Invalid URL format.';
                errorEl.classList.add('visible');
            }
            return;
        }

        if (errorEl) errorEl.classList.remove('visible');
        connectBtn.disabled = true;
        connectBtn.textContent = 'Connecting...';

        try {
            await checkHealth();
            hideConfigBanner();
            await bootstrap();
        } catch (err) {
            if (errorEl) {
                errorEl.textContent = `Could not connect: ${err.message}`;
                errorEl.classList.add('visible');
            }
        } finally {
            connectBtn.disabled = false;
            connectBtn.textContent = 'Connect';
        }
    });

    // Allow Enter key
    urlInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') connectBtn.click();
    });
}

// --- Last Updated / Countdown ---

function updateLastUpdated() {
    const el = document.getElementById('last-updated');
    if (el) {
        el.textContent = `Last updated: ${new Date().toLocaleTimeString()}`;
    }
}

function startCountdown() {
    stopCountdown();
    countdown = POLL_INTERVAL / 1000;
    updateCountdownDisplay();
    countdownTimer = setInterval(() => {
        countdown--;
        if (countdown < 0) countdown = 0;
        updateCountdownDisplay();
    }, 1000);
}

function stopCountdown() {
    if (countdownTimer) {
        clearInterval(countdownTimer);
        countdownTimer = null;
    }
}

function updateCountdownDisplay() {
    const el = document.getElementById('refresh-countdown');
    if (el) el.textContent = `Next refresh: ${countdown}s`;
}

// --- Data Fetching ---

async function fetchCurrentConditions() {
    const stationId = state.get('stationId');
    const units = state.get('units') || 'metric';
    if (!stationId) return;

    try {
        const obs = await getCurrentObservation(stationId, units);
        state.set('currentObservation', obs);
        renderCurrentConditions(obs);
        setStatus('online', 'Connected');
    } catch (err) {
        console.error('Failed to fetch current conditions:', err);
        if (state.get('currentObservation')) {
            setStatus('stale', 'Cached');
        } else {
            setStatus('offline', 'Error');
        }
    }
}

async function fetchChartData() {
    const stationId = state.get('stationId');
    const units = state.get('units') || 'metric';
    const start = state.get('startTime');
    const end = state.get('endTime');
    if (!stationId || !start || !end) return;

    try {
        const data = await getObservations(stationId, start, end, { units });
        if (data && data.observations) {
            updateCharts(data.observations);
        }
    } catch (err) {
        console.error('Failed to fetch chart data:', err);
    }
}

async function refresh() {
    // Update time range for preset (live) ranges
    // Suppress endTime listener to avoid double-fetching
    isRefreshing = true;
    refreshTimeRange();
    isRefreshing = false;
    await Promise.all([
        fetchCurrentConditions(),
        fetchChartData(),
        refreshPlugins(),
    ]);
    updateLastUpdated();
    startCountdown();
}

// --- Polling ---

function startPolling() {
    stopPolling();
    pollTimer = setInterval(() => {
        // Only refresh preset (live) ranges automatically
        if (state.get('timeRangeType') === 'preset') {
            refresh();
        } else {
            // Custom range: only refresh current conditions
            fetchCurrentConditions();
            updateLastUpdated();
            startCountdown();
        }
    }, POLL_INTERVAL);
    startCountdown();
}

function stopPolling() {
    if (pollTimer) {
        clearInterval(pollTimer);
        pollTimer = null;
    }
    stopCountdown();
}

// --- Visibility API (pause when tab hidden) ---

function initVisibility() {
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            stopPolling();
        } else {
            // Immediate refresh + restart timer
            refresh();
            startPolling();
        }
    });
}

// --- Theme ---

function loadCustomTheme() {
    const params = new URLSearchParams(window.location.search);
    const themeUrl = params.get('theme') || localStorage.getItem(STORAGE_KEY_THEME);
    if (themeUrl) {
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = themeUrl;
        document.head.appendChild(link);
    }
}

function initThemeListener() {
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    mq.addEventListener('change', () => {
        // Re-create charts with updated colors from CSS custom properties
        destroyCharts();
        createCharts();
        // Re-fetch chart data to populate with new colors
        fetchChartData();
    });
}

// --- State Subscriptions ---

function initSubscriptions() {
    // When station changes, refetch everything
    state.on('stationId', () => {
        showLoadingState();
        resetZoom();
        refresh();
    });

    // When units change, refetch everything (server does conversion)
    state.on('units', () => {
        showLoadingState();
        refresh();
    });

    // When time range changes (start/end), refetch chart data + plugins
    state.on('endTime', () => {
        if (isRefreshing) return;
        resetZoom();
        fetchChartData();
        refreshPlugins();
    });
}

// --- Bootstrap ---

async function bootstrap() {
    showLoadingState();

    // Load stations
    try {
        const stations = await listStations();
        populateStations(stations);
    } catch (err) {
        console.error('Failed to load stations:', err);
        setStatus('offline', 'No stations');
        return;
    }

    // Create charts
    createCharts();

    // Initial data fetch
    await refresh();

    // Load plugins
    await loadPlugins();

    // Start auto-refresh
    startPolling();
}

// --- Init ---

async function init() {
    loadCustomTheme();
    initConfigBanner();
    initControls();
    initSubscriptions();
    initVisibility();
    initThemeListener();

    // Register service worker
    if ('serviceWorker' in navigator) {
        try {
            await navigator.serviceWorker.register('/sw.js');
        } catch {
            // SW registration failed — not critical
        }
    }

    // Check server connectivity
    try {
        await checkHealth();
        hideConfigBanner();
        await bootstrap();
    } catch {
        setStatus('offline', 'Disconnected');
        showConfigBanner();
    }
}

init();
