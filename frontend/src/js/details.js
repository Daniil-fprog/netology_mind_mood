import Auth from './auth.js';

class DetailsPage {
    MOOD_INSIGHTS = [
        {
            from: 0,
            to: 20,
            text: "Эмоциональный фон выглядит напряжённым. В записи могут присутствовать признаки усталости, тревоги или внутреннего давления."
        },
        {
            from: 21,
            to: 40,
            text: "Настроение ниже среднего. Возможны признаки стресса, переутомления или эмоционального дискомфорта."
        },
        {
            from: 41,
            to: 60,
            text: "Эмоциональное состояние выглядит относительно стабильным. Ярко выраженных позитивных или негативных переживаний не обнаружено."
        },
        {
            from: 61,
            to: 80,
            text: "В записи заметен положительный эмоциональный фон. Присутствуют признаки удовлетворённости, спокойствия или уверенности."
        },
        {
            from: 81,
            to: 100,
            text: "Эмоциональное состояние выглядит очень благоприятным. В тексте прослеживаются высокий уровень ресурса, оптимизма или вдохновения."
        }
    ];

    negative = "negative"

    constructor() {
        this.backButton = document.querySelector(".details__back-button");
        this.pageTitle = document.querySelector(".details__title");
        this.dateElement = document.querySelector(".details__date");

        this.moodBadge = document.querySelector(".mood-card__badge");
        this.moodProgressFill = document.querySelector(".mood-card__progress-fill");
        this.moodValue = document.querySelector(".mood-card__value");

        this.noteContent = document.querySelector(".note-text__content");

        this.confidenceValue = document.querySelector("#stat-percent");
        this.confidenceLabel = document.querySelector("#stat-label");

        this.insightText = document.querySelector(".insight-card__text");

        this.recommendationList = document.querySelector("#recommendation-list");
        this.recommendationCardTemplate = document.querySelector("#recommendationCardTemplate");


        this.noteId = this.getNoteIdFromUrl();

        if (!this.noteId) {
            window.location.href = "../history.html";
            throw new Error("В URL не найден параметр id");
        }
    }

    getNoteIdFromUrl() {
        const params = new URLSearchParams(window.location.search);
        return params.get("id");
    }


    init() {
        this.initEvents();
        this.renderNote();
    }

    initEvents() {
        if (this.backButton) {
            this.backButton.addEventListener("click", () => {
                window.location.href = "./history.html";
            });
        }

        const logoutBtn = document.getElementById("logoutBtn");

        if (logoutBtn) {
            logoutBtn.addEventListener("click", () => {
                Auth.logout();
            });
        }
    }

    async renderNote() {
        const note = await this.getNoteData();
        console.log(note);

        if (!note) {
            return;
        }

        const date = new Date(note.created_at);

        this.pageTitle.textContent = this.generateTitle(note.orig_text);
        this.dateElement.textContent = this.formatDateTime(date);
        this.noteContent.textContent = note.orig_text || "Текст записи отсутствует";

        const sentimentLabel = note.sentiment_label || "NEUTRAL";
        const emotionText = this.getEmotionText(sentimentLabel);
        const sentimentScore = note.sentiment_score / 10;

        this.moodBadge.textContent = emotionText;
        this.moodValue.textContent = `${sentimentScore} / 10`;

        if (this.moodProgressFill) {
            this.moodProgressFill.style.width = `${note.sentiment_score}%`;
        }

        if (this.confidenceValue) {
            this.confidenceValue.textContent = `${Math.round(note.model_confidence)} %`;
        }

        if (this.confidenceLabel) {
            this.confidenceLabel.textContent = emotionText;
        }

        if (this.insightText) {
            this.insightText.textContent = this.generateInsight(note);
        }

        // Рендерит рекомендации
        if (note.recommendations.length > 0) {
            note.recommendations.forEach((recommendation) => {
                const recomendationElement = this.createRecomendation(recommendation);
                this.recommendationList.append(recomendationElement);
            });
        }
    }


    createRecomendation(recomendation) {
        const recomendationElement = this.recommendationCardTemplate.content.cloneNode(true);

        const title = recomendationElement.querySelector(".recommendation-card__item-title");
        const text = recomendationElement.querySelector(".recommendation-card__item-text");

        title.textContent = recomendation.rec_name;
        text.textContent = recomendation.rec_text;

        return recomendationElement;
    }


    async getNoteData() {
        try {
            if (!Auth.isAuth()) {
                window.location.href = "../login.html";
                return null;
            }

            const response = await Auth.authenticatedFetch(
                `${Auth.API_BASE_URL}/notes/${this.noteId}`
            );
            
            if (!response.ok) {
                throw new Error(`Ошибка загрузки записи: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error("Error:", error);
            this.renderError(error.message);
            return null;
        }
    }

    renderError(message) {
        if (this.pageTitle) {
            this.pageTitle.textContent = "Ошибка загрузки";
        }

        if (this.dateElement) {
            this.dateElement.textContent = "";
        }

        if (this.noteContent) {
            this.noteContent.textContent = message || "Не удалось загрузить запись";
        }

        if (this.tagsContainer) {
            this.tagsContainer.innerHTML = "";
        }
    }


    getEmotionText(sentimentLabel) {
        // Простое сопоставление типов настроения
        const moodMap = {
            'negative': 'Плохое',
            'positive': 'Хорошее',
            'neutral': 'Спокойное',
        };

        return moodMap[sentimentLabel] || "Спокойное";
    }

    generateTitle(text) {
        if (!text) {
            return "Детали записи";
        }

        const cleanText = text.trim();
        const firstSentence = cleanText.split(/[.!?]/)[0];

        if (firstSentence.length <= 45) {
            return firstSentence;
        }

        return `${firstSentence.substring(0, 45)}...`;
    }

    generateInsight(note) {
        const score = Number(note.sentiment_score ?? 50);

        const insight = this.MOOD_INSIGHTS.find(item => score >= item.from && score <= item.to);

        return insight?.text ?? "Недостаточно данных для анализа настроения.";
    }

    formatDateTime(date) {
        if (Number.isNaN(date.getTime())) {
            return "Дата не указана";
        }

        return date.toLocaleString("ru-RU", {
            day: "numeric",
            month: "long",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        });
    }
}



document.addEventListener("DOMContentLoaded", () => {
    if (!Auth.isAuth()) {
        window.location.href = "../login.html";
        return;
    }

    try {
        const detailsPage = new DetailsPage();
        detailsPage.init();
    } catch (error) {
        console.error("Error:", error);
    }
});
