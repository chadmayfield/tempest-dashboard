// Plugin loader: reads plugins.json, dynamic import(), lifecycle management

import { state } from './state.js';
import { getChartDefaults } from './charts.js';
import { getChartColors, getUIColors } from './config.js';

const loadedPlugins = [];

function getPluginServerUrl(name) {
    const params = new URLSearchParams(window.location.search);
    const paramUrl = params.get(name);
    if (paramUrl) {
        try {
            const url = new URL(paramUrl);
            const key = `tempest-plugin-${name}-server`;
            localStorage.setItem(key, url.origin);
            return url.origin;
        } catch {
            // invalid URL
        }
    }
    const key = `tempest-plugin-${name}-server`;
    return localStorage.getItem(key) || null;
}

function buildContext() {
    const { baseOptions, makeDataset } = getChartDefaults();
    return {
        state,
        chartDefaults: { baseOptions, makeDataset },
        formatters: {
            formatTemp: (v, units) => {
                if (v === null || v === undefined) return '--';
                const u = units || state.get('units') || 'metric';
                return `${Number(v).toFixed(1)}${u === 'metric' ? '\u00B0C' : '\u00B0F'}`;
            },
            formatTimestamp: (ts) => {
                if (!ts) return '--';
                return new Date(ts).toLocaleString();
            },
        },
        get units() { return state.get('units') || 'metric'; },
        get timeRange() {
            return {
                type: state.get('timeRangeType'),
                range: state.get('timeRange'),
                start: state.get('startTime'),
                end: state.get('endTime'),
            };
        },
        getServerUrl: (name) => getPluginServerUrl(name),
        chartColors: getChartColors(),
        uiColors: getUIColors(),
    };
}

export async function loadPlugins() {
    const container = document.getElementById('plugin-sections');
    if (!container) return;

    let manifest;
    try {
        const res = await fetch('plugins.json');
        if (!res.ok) return;
        manifest = await res.json();
    } catch {
        // No plugins.json or invalid — that's fine
        return;
    }

    if (!Array.isArray(manifest) || manifest.length === 0) return;

    const ctx = buildContext();

    for (const entry of manifest) {
        if (!entry.name || !entry.url) continue;

        try {
            const mod = await import(entry.url);
            const plugin = mod.default;
            if (!plugin) continue;

            // Init
            if (plugin.init) plugin.init(ctx);

            // Render HTML into collapsible section
            if (plugin.render) {
                const section = document.createElement('div');
                section.className = 'plugin-section';
                section.dataset.plugin = entry.name;

                const header = document.createElement('div');
                header.className = 'plugin-header';

                const title = document.createElement('h3');
                title.textContent = plugin.label || entry.name;
                header.appendChild(title);

                const toggle = document.createElement('span');
                toggle.className = 'toggle-icon';
                toggle.textContent = '\u25BC';
                header.appendChild(toggle);

                header.addEventListener('click', () => {
                    section.classList.toggle('collapsed');
                });

                const content = document.createElement('div');
                content.className = 'plugin-content';

                // Plugin render() returns HTML string — trust boundary documented in README
                const html = plugin.render();
                if (html) {
                    content.innerHTML = html;
                }

                section.appendChild(header);
                section.appendChild(content);
                container.appendChild(section);
            }

            // Create charts
            if (plugin.createCharts) plugin.createCharts(ctx);

            loadedPlugins.push(plugin);
        } catch (err) {
            console.error(`Failed to load plugin "${entry.name}":`, err);
        }
    }
}

export async function refreshPlugins() {
    const ctx = buildContext();
    for (const plugin of loadedPlugins) {
        try {
            if (plugin.refresh) await plugin.refresh(ctx);
        } catch (err) {
            console.error(`Plugin "${plugin.name}" refresh error:`, err);
        }
    }
}

export function destroyPlugins() {
    for (const plugin of loadedPlugins) {
        try {
            if (plugin.destroy) plugin.destroy();
        } catch (err) {
            console.error(`Plugin "${plugin.name}" destroy error:`, err);
        }
    }
    loadedPlugins.length = 0;
}
