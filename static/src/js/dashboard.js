/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onWillStart, onMounted, useRef, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class CronDashboard extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.action = useService("action");
        this.state = useState({
            stats: {
                summary: {
                    total_runs: 0,
                    success_rate: 0,
                    slowest_job_name: "None",
                    slowest_job_duration: "0s",
                },
                trend: [],
                heatmap: [],
            },
        });

        this.trendChartRef = useRef("trendChart");
        this.heatmapChartRef = useRef("heatmapChart");

        onWillStart(async () => {
            await this.loadStats();
        });

        onMounted(() => {
            this.renderCharts();
        });
    }

    async loadStats() {
        const stats = await this.rpc("/web/dataset/call_kw/cron.log/get_dashboard_stats", {
            model: "cron.log",
            method: "get_dashboard_stats",
            args: [],
            kwargs: {},
        });
        this.state.stats = stats;
    }

    renderCharts() {
        this.renderTrendChart();
        this.renderHeatmapChart();
    }

    renderTrendChart() {
        const ctx = this.trendChartRef.el;
        const labels = this.state.stats.trend.map(d => d.date);
        const successData = this.state.stats.trend.map(d => d.success);
        const failedData = this.state.stats.trend.map(d => d.failed);

        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Success',
                        data: successData,
                        backgroundColor: '#10b981', // green-500
                        borderRadius: 5,
                    },
                    {
                        label: 'Failed',
                        data: failedData,
                        backgroundColor: '#ef4444', // red-500
                        borderRadius: 5,
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1 }
                    },
                    x: {
                        grid: { display: false }
                    }
                },
                plugins: {
                    legend: { position: 'bottom' }
                }
            }
        });
    }

    renderHeatmapChart() {
        const ctx = this.heatmapChartRef.el;
        const labels = this.state.stats.heatmap.map(d => d.hour);
        const data = this.state.stats.heatmap.map(d => d.count);

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Failures',
                    data: data,
                    borderColor: '#f59e0b', // amber-500
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#f59e0b',
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1 }
                    },
                    x: {
                        grid: { display: false },
                        ticks: {
                            callback: function(val, index) {
                                // Show only every 3 hours to avoid clutter
                                return index % 3 === 0 ? this.getLabelForValue(val) : '';
                            }
                        }
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }
}

CronDashboard.template = "scheduled_actions_tracker.CronDashboard";

registry.category("actions").add("cron_dashboard_client_action", CronDashboard);
