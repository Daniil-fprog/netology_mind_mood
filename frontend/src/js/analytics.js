import Auth from './auth.js';

class AnalyticsPage {
    constructor() {
        this.startDateInput = document.getElementById("startDate");
        this.endDateInput = document.getElementById("endDate");
        this.resetDateRangeBtn = document.getElementById("resetDateRange");
        this.exportButton = document.querySelector(".analytics__export-button");
        this.moodIndexValue = document.querySelector(".mood-index__value");
        this.moodIndexChange = document.querySelector(".mood-index__change");
        this.moodIndexProgressFill = document.querySelector(".mood-index__progress-fill");
        this.neuralInsightsList = document.querySelector(".neural-insights__list");
        this.chartCanvas = document.getElementById("moodChart");
        this.neuralInsightsHeader = document.querySelector(".neural-insights__header");
        this.chartInstance = null;

        // Устанавливаем даты по умолчанию (последние 7 дней)
        this.setDefaultDateRange();
        this.chartData = [];
    }

    setDefaultDateRange() {
        const endDate = new Date();
        const startDate = new Date();
        startDate.setDate(endDate.getDate() - 6); // 7 дней включительно

        this.startDateInput.value = this.formatDateToYYYYMMDD(startDate);
        this.endDateInput.value = this.formatDateToYYYYMMDD(endDate);
    }

    formatDateToYYYYMMDD(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, "0");
        const day = String(date.getDate()).padStart(2, "0");
        return `${year}-${month}-${day}`;
    }

    parseDateFromYYYYMMDD(dateStr) {
        const [year, month, day] = dateStr.split("-").map(Number);
        return new Date(year, month - 1, day);
    }

    async fetchAnalytics() {
        try {
            if (!Auth.isAuth()) {
                window.location.href = "./login.html";
                return null;
            }

            const dateQuery = this.getDateRangeQuery();

            // Загружаем данные для графика
            const chartResponse = await Auth.authenticatedFetch(`${Auth.API_BASE_URL}/analytics/chart-data?${dateQuery}`);
            const chartData = await chartResponse.json();

            // Загружаем средний индекс настроения
            const summaryResponse = await Auth.authenticatedFetch(`${Auth.API_BASE_URL}/analytics/summary?${dateQuery}`);
            const summaryData = await summaryResponse.json();

            // Загружаем нейро-инсайты
            const insightsResponse = await Auth.authenticatedFetch(`${Auth.API_BASE_URL}/analytics/insights?${dateQuery}`);
            const insightsData = await insightsResponse.json();

            return {
                average_mood_index: summaryData.average_mood_index,
                trend_analysis: summaryData.trend_analysis || {},
                mood_chart_data: chartData.chart_data,
                neural_insights: insightsData,
            };
        } catch (error) {
            console.error("Error fetching analytics:", error);
            return null;
        }
    }

    async renderAnalytics() {
        const data = await this.fetchAnalytics();

        if (!data) {
            return;
        }

        this.renderMoodIndex(data);
        this.renderChart(data.mood_chart_data || data.chart_data);
        this.renderNeuralInsights(data.neural_insights);
    }

    renderMoodIndex(data) {
        if (!this.moodIndexValue) return;

        const average = data.average_mood_index;
        this.moodIndexValue.textContent = average;

        // Получаем данные трендов только из trend_analysis
        if (data.trend_analysis?.change_percent !== undefined) {
            const changePercent = data.trend_analysis.change_percent;

            // Рассчитываем изменение на основе трендов
            const sign = changePercent >= 0 ? "↗" : "↘";
            const changeText = `${sign} ${Math.abs(changePercent).toFixed(1)}% за неделю`;

            if (this.moodIndexChange) {
                this.moodIndexChange.textContent = changeText;
                // Меняем цвет в зависимости от направления
                this.moodIndexChange.style.color = changePercent >= 0 ? "#10b981" : "#ef4444";
            }
        } else {
            // Если нет данных тренда, скрываем элемент изменения
            if (this.moodIndexChange) {
                this.moodIndexChange.textContent = "";
            }
        }

        // Обновляем прогресс-бар
        if (this.moodIndexProgressFill) {
            // Нормализуем значение 0-100 в 0-100%
            const percentage = (average / 100) * 100;
            this.moodIndexProgressFill.style.width = `${percentage}%`;

            // Меняем цвет прогресс-бара в зависимости от значения
            if (average >= 70) {
                this.moodIndexProgressFill.style.backgroundColor = "#4ade80";
            } else if (average >= 40) {
                this.moodIndexProgressFill.style.backgroundColor = "#facc15";
            } else {
                this.moodIndexProgressFill.style.backgroundColor = "#ef4444";
            }
        }
    }

    renderChart(chartData) {
        this.chartData = chartData;

        if (!this.chartCanvas) return;

        // Уничтожаем старый инстанс, если есть
        if (this.chartInstance) {
            this.chartInstance.destroy();
        }

        if (!chartData.length) {
            // Если нет данных, очищаем canvas
            const ctx = this.chartCanvas.getContext('2d');
            ctx.clearRect(0, 0, this.chartCanvas.width, this.chartCanvas.height);
            return;
        }

        const ctx = this.chartCanvas.getContext('2d');

        // Преобразуем данные для Chart.js
        const labels = chartData.map(d => d.day_name);
        const dataPoints = chartData.map(d => d.score);

        // Сохраняем полные данные для использования в tooltip
        this.chartDataFull = chartData;

        this.chartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Настроение',
                    data: dataPoints,
                    _fullData: chartData, // Сохраняем полные данные
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4,
                    pointRadius: 5,
                    pointHoverRadius: 7,
                    pointBackgroundColor: '#667eea',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointHoverBackgroundColor: '#667eea',
                    pointHoverBorderColor: '#667eea',
                    pointHoverBorderWidth: 3,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: '#1f2937',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: '#4b5563',
                        borderWidth: 1,
                        padding: 10,
                        displayColors: false,
                        callbacks: {
                            label: function (context) {
                                return 'Индекс настроения: ' + context.raw;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: {
                            color: function (context) {
                                if (context.tick.value === 50) {
                                    return '#e5e7eb';
                                }
                                return '#f3f4f6';
                            },
                            lineWidth: function (context) {
                                if (context.tick.value === 50) {
                                    return 1;
                                }
                                return 1;
                            }
                        },
                        ticks: {
                            stepSize: 20,
                            color: '#718096',
                            font: {
                                size: 12
                            },
                            callback: function (value) {
                                return value;
                            }
                        }
                    },
                    x: {
                        display: false,
                        grid: {
                            display: false
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: '#1f2937',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: '#4b5563',
                        borderWidth: 1,
                        padding: 10,
                        displayColors: false,
                        callbacks: {
                            title: function (context) {
                                const dataIndex = context[0].dataIndex;

                                // Используем сохранённые полные данные
                                const fullData = context[0].dataset._fullData || this.chartDataFull;
                                const data = fullData[dataIndex];

                                // Форматируем дату в русский формат
                                const dateObj = new Date(data.date);
                                const day = dateObj.getDate();
                                const month = dateObj.getMonth();
                                const year = dateObj.getFullYear();

                                const months = [
                                    'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                                    'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'
                                ];

                                return `Дата: ${day} ${months[month]} ${year} (${data.day_name})`;
                            },
                            label: function (context) {
                                return 'Индекс настроения: ' + context.raw;
                            }
                        }
                    }
                },
                animation: {
                    duration: 500
                }
            }
        });
    }

    renderNeuralInsights(insightsObj) {
        if (!this.neuralInsightsList) return;

        // Очищаем список
        this.neuralInsightsList.innerHTML = "";

        // Получаем массив инсайтов (может быть как объектом, так и массивом для обратной совместимости)
        let insights = [];
        if (Array.isArray(insightsObj)) {
            insights = insightsObj;
        } else if (insightsObj?.insights) {
            insights = insightsObj.insights;
        }

        if (!insights.length) {
            this.neuralInsightsList.innerHTML = '<p class="neural-insights__text">Недостаточно данных для анализа. Добавьте больше заметок.</p>';
            return;
        }

        insights.forEach(text => {
            const item = document.createElement("div");
            item.className = "neural-insights__item";

            item.innerHTML = `
                <div class="neural-insights__marker"></div>
                <p class="neural-insights__text">${text}</p>
            `;

            this.neuralInsightsList.appendChild(item);
        });
    }

    getDateRangeQuery() {
        const startDateStr = this.startDateInput.value;
        const endDateStr = this.endDateInput.value;

        if (!startDateStr || !endDateStr) {
            this.setDefaultDateRange();
            return this.getDateRangeQuery();
        }

        return new URLSearchParams({
            start_date: startDateStr,
            end_date: endDateStr,
        }).toString();
    }

    handleDateRangeApply() {
        // Принудительно обновляем данные
        this.renderAnalytics();
    }

    async handleExport() {
        try {
            if (!Auth.isAuth()) {
                window.location.href = "./login.html";
                return;
            }

            const dateQuery = this.getDateRangeQuery();
            const response = await Auth.authenticatedFetch(
                `${Auth.API_BASE_URL}/analytics/export?${dateQuery}`
            );

            if (!response.ok) {
                const errorData = await response.json();
                alert(errorData.detail || "Ошибка при экспорте данных");
                return;
            }

            // Скачиваем CSV файл
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `moodsync_analytics_${new Date().toISOString().split("T")[0]}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

        } catch (error) {
            console.error("Error exporting analytics:", error);
            alert("Ошибка при экспорте данных. Попробуйте позже.");
        }
    }

    initEvents() {
        // Обработчик кнопки сброса диапазона дат
        if (this.resetDateRangeBtn) {
            this.resetDateRangeBtn.addEventListener("click", () => {
                this.setDefaultDateRange();
                this.renderAnalytics();
            });
        }

        // Обработчик кнопки экспорта
        if (this.exportButton) {
            this.exportButton.addEventListener("click", () => {
                this.handleExport();
            });
        }

        // Инициализация дат при клике на инпуты (открытие календаря)
        if (this.startDateInput) {
            this.startDateInput.addEventListener("change", () => {
                // Валидация: startDate не должен быть больше endDate
                const startDate = this.parseDateFromYYYYMMDD(this.startDateInput.value);
                const endDate = this.parseDateFromYYYYMMDD(this.endDateInput.value);
                if (startDate > endDate) {
                    // Если startDate > endDate, устанавливаем endDate = startDate
                    this.endDateInput.value = this.startDateInput.value;
                }
                this.renderAnalytics();
            });
        }

        if (this.endDateInput) {
            this.endDateInput.addEventListener("change", () => {
                // Валидация: endDate не должен быть меньше startDate
                const startDate = this.parseDateFromYYYYMMDD(this.startDateInput.value);
                const endDate = this.parseDateFromYYYYMMDD(this.endDateInput.value);
                if (endDate < startDate) {
                    // Если endDate < startDate, устанавливаем startDate = endDate
                    this.startDateInput.value = this.endDateInput.value;
                }
                this.renderAnalytics();
            });
        }
    }

    init() {
        this.initEvents();
        this.renderAnalytics();
    }
}

// Инициализация страницы аналитики
document.addEventListener("DOMContentLoaded", () => {
    if (!Auth.isAuth()) {
        window.location.href = "./login.html";
        return;
    }

    try {
        const analyticsPage = new AnalyticsPage();
        analyticsPage.init();
    } catch (error) {
        console.error("Error initializing analytics:", error);
    }
});
