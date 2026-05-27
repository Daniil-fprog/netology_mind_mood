import Auth from './auth.js';

const API_BASE_URL = Auth.API_BASE_URL;

class AnalyticsPage {
    constructor() {
        this.apiBaseUrl = API_BASE_URL;
        this.periodSelect = document.querySelector(".mood-chart__select");
        this.exportButton = document.querySelector(".analytics__export-button");
        this.moodIndexValue = document.querySelector(".mood-index__value");
        this.moodIndexChange = document.querySelector(".mood-index__change");
        this.moodIndexProgressFill = document.querySelector(".mood-index__progress-fill");
        this.neuralInsightsList = document.querySelector(".neural-insights__list");
        this.emotionDistributionList = document.querySelector(".emotion-distribution__list");
        this.chartSvg = document.querySelector(".mood-chart__svg");

        this.currentPeriod = "week"; // week, month, quarter
        this.chartData = [];
    }

    async fetchAnalytics() {
        try {
            if (!Auth.isAuth()) {
                window.location.href = "../pages/login.html";
                return null;
            }

            const periodDays = this.getDaysByPeriod();
            const response = await Auth.authenticatedFetch(
                `${this.apiBaseUrl}/analytics/?days=${periodDays}`
            );

            if (!response.ok) {
                throw new Error(`Ошибка загрузки данных: ${response.status}`);
            }

            return await response.json();
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
        this.renderChart(data.chart_data);
        this.renderEmotionDistribution(data.emotion_distribution);
        this.renderNeuralInsights(data.neural_insights);
    }

    renderMoodIndex(data) {
        if (!this.moodIndexValue) return;

        const average = data.average_mood_index;
        this.moodIndexValue.textContent = average;

        // Рассчитываем изменение (простая логика - в реальном приложении нужно сравнение с прошлым периодом)
        const last7Days = data.mood_chart_data.slice(-7);
        if (last7Days.length >= 2) {
            const firstScore = last7Days[0].score;
            const lastScore = last7Days[last7Days.length - 1].score;
            const change = lastScore - firstScore;
            const sign = change >= 0 ? "↗" : "↘";
            const changeText = `${sign} ${Math.abs(change).toFixed(1)} за неделю`;

            if (this.moodIndexChange) {
                this.moodIndexChange.textContent = changeText;
            }
        }

        // Обновляем прогресс-бар
        if (this.moodIndexProgressFill) {
            // Нормализуем значение 0-10 в 0-100%
            const percentage = (average / 10) * 100;
            this.moodIndexProgressFill.style.width = `${percentage}%`;
        }
    }

    renderChart(chartData) {
        this.chartData = chartData;

        if (!this.chartSvg) return;

        // Очищаем существующие элементы (кроме сетки)
        const existingElements = this.chartSvg.querySelectorAll("polyline, circle, g");
        existingElements.forEach(el => el.remove());

        if (!chartData.length) {
            return;
        }

        const width = 600; // 650 - 50
        const height = 200; // 250 - 50
        const paddingX = 50;
        const paddingY = 50;

        // Находим мин и макс значения для масштабирования
        const scores = chartData.map(d => d.score);
        const minScore = Math.min(...scores, 0);
        const maxScore = Math.max(...scores, 10);

        // Функция масштабирования
        const scaleScore = (score) => {
            if (maxScore === minScore) return 150;
            const normalized = (score - minScore) / (maxScore - minScore);
            return 250 - (normalized * height);
        };

        // Строим полилинию
        const stepX = width / (chartData.length - 1 || 1);
        const points = chartData.map((d, i) => {
            const x = paddingX + i * stepX;
            const y = scaleScore(d.score);
            return `${x},${y}`;
        }).join(" ");

        // Создаем полилинию графика
        const polyline = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
        polyline.setAttribute("points", points);
        polyline.setAttribute("fill", "none");
        polyline.setAttribute("stroke", "#667eea");
        polyline.setAttribute("stroke-width", "3");
        polyline.setAttribute("stroke-linejoin", "round");
        this.chartSvg.appendChild(polyline);

        // Создаем точки
        chartData.forEach((d, i) => {
            const x = paddingX + i * stepX;
            const y = scaleScore(d.score);

            const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
            circle.setAttribute("cx", x);
            circle.setAttribute("cy", y);
            circle.setAttribute("r", "5");
            circle.setAttribute("fill", "#667eea");
            this.chartSvg.appendChild(circle);

            // Добавляем tooltip при наведении
            circle.addEventListener("mouseover", () => {
                this.showTooltip(x, y, d.score);
            });

            circle.addEventListener("mouseout", () => {
                this.hideTooltip();
            });
        });

        // Добавляем подписи по оси X
        this.updateXAxisLabels(chartData);
    }

    updateXAxisLabels(chartData) {
        if (!this.chartSvg) return;

        // Удаляем старые подписи
        const oldTexts = this.chartSvg.querySelectorAll(".x-axis-label");
        oldTexts.forEach(el => el.remove());

        if (!chartData.length) return;

        const width = 600;
        const paddingX = 50;
        const stepX = width / (chartData.length - 1 || 1);

        chartData.forEach((d, i) => {
            const x = paddingX + i * stepX;

            const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
            text.textContent = d.day_name;
            text.setAttribute("x", x);
            text.setAttribute("y", "270");
            text.setAttribute("text-anchor", "middle");
            text.setAttribute("font-size", "12");
            text.setAttribute("fill", "#718096");
            text.setAttribute("class", "x-axis-label");
            this.chartSvg.appendChild(text);
        });
    }

    showTooltip(x, y, score) {
        if (!this.chartSvg) return;

        // Удаляем старый tooltip
        const oldTooltip = this.chartSvg.querySelector(".tooltip");
        if (oldTooltip) oldTooltip.remove();

        const tooltip = document.createElementNS("http://www.w3.org/2000/svg", "g");
        tooltip.setAttribute("class", "tooltip");

        const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
        rect.setAttribute("x", x - 30);
        rect.setAttribute("y", y - 35);
        rect.setAttribute("width", "60");
        rect.setAttribute("height", "30");
        rect.setAttribute("rx", "4");
        rect.setAttribute("fill", "#1f2937");
        rect.setAttribute("opacity", "0.9");

        const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
        text.textContent = score;
        text.setAttribute("x", x);
        text.setAttribute("y", y - 15);
        text.setAttribute("text-anchor", "middle");
        text.setAttribute("font-size", "14");
        text.setAttribute("fill", "white");
        text.setAttribute("font-weight", "600");

        const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
        line.setAttribute("x1", x);
        line.setAttribute("y1", y - 5);
        line.setAttribute("x2", x);
        line.setAttribute("y2", y + 10);
        line.setAttribute("stroke", "#1f2937");
        line.setAttribute("stroke-width", "2");

        tooltip.appendChild(rect);
        tooltip.appendChild(text);
        tooltip.appendChild(line);
        this.chartSvg.appendChild(tooltip);
    }

    hideTooltip() {
        if (!this.chartSvg) return;
        const tooltip = this.chartSvg.querySelector(".tooltip");
        if (tooltip) tooltip.remove();
    }

    renderEmotionDistribution(distribution) {
        if (!this.emotionDistributionList) return;

        // Очищаем список
        this.emotionDistributionList.innerHTML = "";

        // Категории для отображения (кастомные категории из HTML)
        const categories = [
            { key: "calm", label: "Спокойствие", class: "calm" },
            { key: "focus", label: "Фокус", class: "focus" },
            { key: "tired", label: "Усталость", class: "tired" },
            { key: "stress", label: "Стресс", class: "stress" }
        ];

        categories.forEach(cat => {
            const percentage = distribution[cat.key] || 0;

            const item = document.createElement("div");
            item.className = "emotion-distribution__item";

            item.innerHTML = `
                <div class="emotion-distribution__row">
                    <div class="emotion-distribution__color emotion-distribution__color--${cat.class}"></div>
                    <span class="emotion-distribution__name">${cat.label}</span>
                    <span class="emotion-distribution__percent">${percentage}%</span>
                </div>
                <div class="emotion-distribution__bar">
                    <div class="emotion-distribution__fill emotion-distribution__fill--${cat.class}" style="width: ${percentage}%"></div>
                </div>
            `;

            this.emotionDistributionList.appendChild(item);
        });
    }

    renderNeuralInsights(insights) {
        if (!this.neuralInsightsList) return;

        // Очищаем список
        this.neuralInsightsList.innerHTML = "";

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

    getDaysByPeriod() {
        switch (this.currentPeriod) {
            case "week":
                return 7;
            case "month":
                return 30;
            case "quarter":
                return 90;
            default:
                return 7;
        }
    }

    handlePeriodChange(event) {
        this.currentPeriod = event.target.value;
        this.renderAnalytics();
    }

    async handleExport() {
        try {
            if (!Auth.isAuth()) {
                window.location.href = "../pages/login.html";
                return;
            }

            const periodDays = this.getDaysByPeriod();
            const response = await Auth.authenticatedFetch(
                `${this.apiBaseUrl}/analytics/export?days=${periodDays}`
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
        // Обработчик выбора периода
        if (this.periodSelect) {
            this.periodSelect.addEventListener("change", (e) => {
                this.handlePeriodChange(e);
            });
        }

        // Обработчик кнопки экспорта
        if (this.exportButton) {
            this.exportButton.addEventListener("click", () => {
                this.handleExport();
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
        window.location.href = "../pages/login.html";
        return;
    }

    try {
        const analyticsPage = new AnalyticsPage();
        analyticsPage.init();
    } catch (error) {
        console.error("Error initializing analytics:", error);
    }
});
