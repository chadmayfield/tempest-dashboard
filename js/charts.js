// Chart.js instance creation, update, and dataset definitions

import { state } from './state.js';
import { getChartColors, getUIColors } from './config.js';

// Store chart instances
const charts = {};

function getUnitLabels() {
    const units = state.get('units') || 'metric';
    const isMetric = units === 'metric';
    return {
        temp: isMetric ? '\u00B0C' : '\u00B0F',
        wind: isMetric ? 'm/s' : 'mph',
        pressure: isMetric ? 'hPa' : 'inHg',
        rain: isMetric ? 'mm' : 'in',
    };
}

// Shared Chart.js defaults for all charts
function baseOptions(yLabel) {
    const ui = getUIColors();
    return {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
            mode: 'index',
            intersect: false,
        },
        plugins: {
            legend: {
                display: true,
                position: 'top',
                labels: {
                    color: ui.textSecondary,
                    boxWidth: 12,
                    padding: 12,
                    font: { size: 11 },
                    usePointStyle: true,
                },
            },
            tooltip: {
                mode: 'index',
                intersect: false,
                backgroundColor: ui.tooltipBg,
                titleColor: ui.tooltipTitle,
                bodyColor: ui.tooltipBody,
                borderColor: ui.tooltipBorder,
                borderWidth: 1,
                padding: 10,
                bodySpacing: 4,
            },
            zoom: {
                pan: {
                    enabled: true,
                    mode: 'x',
                    modifierKey: 'ctrl',
                },
                zoom: {
                    wheel: {
                        enabled: true,
                        modifierKey: 'ctrl',
                    },
                    pinch: { enabled: true },
                    mode: 'x',
                },
            },
        },
        scales: {
            x: {
                type: 'time',
                grid: { color: ui.gridColor, lineWidth: 0.5 },
                ticks: { color: ui.textMuted, maxRotation: 0, autoSkipPadding: 20 },
                border: { color: ui.gridColor },
            },
            y: {
                grid: { color: ui.gridColor, lineWidth: 0.5 },
                ticks: { color: ui.textMuted },
                border: { color: ui.gridColor },
                title: {
                    display: !!yLabel,
                    text: yLabel || '',
                    color: ui.textMuted,
                    font: { size: 11 },
                },
            },
        },
        elements: {
            point: { radius: 0, hoverRadius: 4 },
            line: { borderWidth: 1.5, tension: 0.3 },
        },
    };
}

function makeDataset(label, color, data) {
    return {
        label,
        data,
        borderColor: color,
        backgroundColor: color + '20',
        fill: false,
    };
}

// --- Create Charts ---

export function createCharts() {
    const colors = getChartColors();
    const unitLabels = getUnitLabels();

    // Temperature
    charts.temperature = new Chart(
        document.getElementById('chart-temperature'),
        {
            type: 'line',
            data: {
                datasets: [
                    makeDataset('Temperature', colors.temperature, []),
                    makeDataset('Feels Like', colors.feelsLike, []),
                    makeDataset('Dew Point', colors.dewPoint, []),
                ],
            },
            options: baseOptions(unitLabels.temp),
        }
    );

    // Humidity
    charts.humidity = new Chart(
        document.getElementById('chart-humidity'),
        {
            type: 'line',
            data: {
                datasets: [
                    makeDataset('Humidity', colors.humidity, []),
                ],
            },
            options: {
                ...baseOptions('%'),
                scales: {
                    ...baseOptions('%').scales,
                    y: {
                        ...baseOptions('%').scales.y,
                        min: 0,
                        max: 100,
                        title: { display: true, text: '%', color: getUIColors().textMuted, font: { size: 11 } },
                    },
                },
            },
        }
    );

    // Wind
    charts.wind = new Chart(
        document.getElementById('chart-wind'),
        {
            type: 'line',
            data: {
                datasets: [
                    makeDataset('Average', colors.windAvg, []),
                    makeDataset('Gust', colors.windGust, []),
                    makeDataset('Lull', colors.windLull, []),
                ],
            },
            options: baseOptions(unitLabels.wind),
        }
    );

    // Pressure
    charts.pressure = new Chart(
        document.getElementById('chart-pressure'),
        {
            type: 'line',
            data: {
                datasets: [
                    makeDataset('Pressure', colors.pressure, []),
                ],
            },
            options: baseOptions(unitLabels.pressure),
        }
    );

    // Rain
    charts.rain = new Chart(
        document.getElementById('chart-rain'),
        {
            type: 'line',
            data: {
                datasets: [
                    {
                        ...makeDataset('Rain', colors.rain, []),
                        fill: true,
                        backgroundColor: colors.rain + '40',
                    },
                ],
            },
            options: {
                ...baseOptions(unitLabels.rain),
                scales: {
                    ...baseOptions(unitLabels.rain).scales,
                    y: {
                        ...baseOptions(unitLabels.rain).scales.y,
                        min: 0,
                        title: { display: true, text: unitLabels.rain, color: getUIColors().textMuted, font: { size: 11 } },
                    },
                },
            },
        }
    );

    // Solar / UV (dual y-axis)
    const solarOpts = baseOptions('W/m\u00B2');
    const ui = getUIColors();
    solarOpts.scales.y.position = 'left';
    solarOpts.scales.y.title = {
        display: true,
        text: 'W/m\u00B2',
        color: colors.solar,
        font: { size: 11 },
    };
    solarOpts.scales.y2 = {
        type: 'linear',
        position: 'right',
        grid: { drawOnChartArea: false },
        ticks: { color: ui.textMuted },
        border: { color: ui.gridColor },
        title: {
            display: true,
            text: 'UV Index',
            color: colors.uv,
            font: { size: 11 },
        },
        min: 0,
    };

    charts.solar = new Chart(
        document.getElementById('chart-solar'),
        {
            type: 'line',
            data: {
                datasets: [
                    makeDataset('Solar Radiation', colors.solar, []),
                    {
                        ...makeDataset('UV Index', colors.uv, []),
                        yAxisID: 'y2',
                    },
                ],
            },
            options: solarOpts,
        }
    );
}

// --- Update Charts with observation data ---

export function updateCharts(observations) {
    if (!observations || observations.length === 0) return;

    const unitLabels = getUnitLabels();

    // Map observations to time-series data points
    const tempData = [];
    const feelsLikeData = [];
    const dewPointData = [];
    const humidityData = [];
    const windAvgData = [];
    const windGustData = [];
    const windLullData = [];
    const pressureData = [];
    const rainData = [];
    const solarData = [];
    const uvData = [];

    for (const obs of observations) {
        const t = obs.timestamp;
        tempData.push({ x: t, y: obs.air_temperature });
        feelsLikeData.push({ x: t, y: obs.feels_like });
        dewPointData.push({ x: t, y: obs.dew_point });
        humidityData.push({ x: t, y: obs.relative_humidity });
        windAvgData.push({ x: t, y: obs.wind_avg });
        windGustData.push({ x: t, y: obs.wind_gust });
        windLullData.push({ x: t, y: obs.wind_lull });
        pressureData.push({ x: t, y: obs.station_pressure });
        rainData.push({ x: t, y: obs.rain_accumulation });
        solarData.push({ x: t, y: obs.solar_radiation });
        uvData.push({ x: t, y: obs.uv_index });
    }

    // Temperature
    if (charts.temperature) {
        charts.temperature.data.datasets[0].data = tempData;
        charts.temperature.data.datasets[1].data = feelsLikeData;
        charts.temperature.data.datasets[2].data = dewPointData;
        charts.temperature.options.scales.y.title.text = unitLabels.temp;
        charts.temperature.update('none');
    }

    // Humidity
    if (charts.humidity) {
        charts.humidity.data.datasets[0].data = humidityData;
        charts.humidity.update('none');
    }

    // Wind
    if (charts.wind) {
        charts.wind.data.datasets[0].data = windAvgData;
        charts.wind.data.datasets[1].data = windGustData;
        charts.wind.data.datasets[2].data = windLullData;
        charts.wind.options.scales.y.title.text = unitLabels.wind;
        charts.wind.update('none');
    }

    // Pressure
    if (charts.pressure) {
        charts.pressure.data.datasets[0].data = pressureData;
        charts.pressure.options.scales.y.title.text = unitLabels.pressure;
        charts.pressure.update('none');
    }

    // Rain
    if (charts.rain) {
        charts.rain.data.datasets[0].data = rainData;
        charts.rain.options.scales.y.title.text = unitLabels.rain;
        charts.rain.update('none');
    }

    // Solar / UV
    if (charts.solar) {
        charts.solar.data.datasets[0].data = solarData;
        charts.solar.data.datasets[1].data = uvData;
        charts.solar.update('none');
    }
}

// Reset zoom on all charts
export function resetZoom() {
    for (const chart of Object.values(charts)) {
        if (chart && chart.resetZoom) {
            chart.resetZoom();
        }
    }
}

// Export chart defaults for plugins
export function getChartDefaults() {
    return { baseOptions, makeDataset };
}

// Destroy all charts (for cleanup)
export function destroyCharts() {
    for (const [key, chart] of Object.entries(charts)) {
        if (chart) {
            chart.destroy();
            delete charts[key];
        }
    }
}
