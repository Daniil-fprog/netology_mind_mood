class DetailsPage {
    constructor() {
        this.apiBaseUrl = "http://127.0.0.1:8000";

        this.backButton = document.querySelector(".details__back-button");
        this.pageTitle = document.querySelector(".details__title");
        this.dateElement = document.querySelector(".details__date");

        this.moodBadge = document.querySelector(".mood-card__badge");
        this.moodProgressFill = document.querySelector(".mood-card__progress-fill");
        this.moodValue = document.querySelector(".mood-card__value");

        this.noteContent = document.querySelector(".note-text__content");
        this.tagsContainer = document.querySelector(".note-text__tags");

        this.confidenceValue = document.querySelector(
            ".ai-analysis__stat--accent .ai-analysis__stat-value"
        );

        this.emotionValue = document.querySelector(
            ".ai-analysis__cards .ai-analysis__stat:not(.ai-analysis__stat--accent) .ai-analysis__stat-value"
        );

        this.insightText = document.querySelector(".insight-card__text");

        this.noteId = this.getNoteIdFromUrl();

        if (!this.noteId) {
            window.location.href = "../pages/history.html";
            throw new Error("В URL не найден параметр id");
        }
    }

    getNoteIdFromUrl() {
        const params = new URLSearchParams(window.location.search);
        return params.get("id");
    }

    async getNoteData() {
        try {
            if (!Auth.isAuth()) {
                window.location.href = "../pages/login.html";
                return null;
            }

            const response = await Auth.authenticatedFetch(
                `${this.apiBaseUrl}/notes/${this.noteId}`
            );

            if (response.status === 404) {
                throw new Error("Запись не найдена");
            }

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

    async renderNote() {
        const note = await this.getNoteData();

        if (!note) {
            return;
        }

        const date = new Date(note.created_at);

        this.pageTitle.textContent = this.generateTitle(note.orig_text);
        this.dateElement.textContent = this.formatDateTime(date);

        this.noteContent.textContent = note.orig_text || "Текст записи отсутствует";

        const sentimentLabel = note.sentiment_label || "NEUTRAL";
        const emotionText = this.getEmotionText(sentimentLabel);
        const moodScore = this.normalizeMoodScore(note.sentiment_score, sentimentLabel);

        this.moodBadge.textContent = emotionText;
        this.moodValue.textContent = `${moodScore} / 10`;

        if (this.moodProgressFill) {
            this.moodProgressFill.style.width = `${moodScore * 10}%`;
        }

        if (this.confidenceValue) {
            this.confidenceValue.textContent = this.getConfidenceText(note.sentiment_score);
        }

        if (this.emotionValue) {
            this.emotionValue.textContent = emotionText;
        }

        if (this.insightText) {
            this.insightText.textContent = this.generateInsight(note);
        }

        this.renderTags(note);
    }

    renderTags(note) {
        if (!this.tagsContainer) {
            return;
        }

        this.tagsContainer.innerHTML = "";

        const tags = this.buildTags(note);

        tags.forEach((tag) => {
            const tagElement = document.createElement("span");
            tagElement.classList.add("note-text__tag");
            tagElement.textContent = tag;

            this.tagsContainer.append(tagElement);
        });
    }

    buildTags(note) {
        const tagsFromText = this.extractTags(note.orig_text);
        const sentimentTag = this.getEmotionText(note.sentiment_label || "NEUTRAL");

        const tags = [sentimentTag, ...tagsFromText];

        if (note.translate_status) {
            tags.push(this.getTranslateStatusText(note.translate_status));
        }

        return [...new Set(tags)].filter(Boolean);
    }

    extractTags(text) {
        if (!text) {
            return [];
        }

        const tags = text.match(/#[а-яА-ЯёЁa-zA-Z0-9]+/g);

        return tags ? tags.map((tag) => tag.substring(1)) : [];
    }

    getEmotionText(sentimentLabel) {
        const emotionMap = {
            POSITIVE: "Позитивное",
            NEGATIVE: "Негативное",
            NEUTRAL: "Нейтральное",
        };

        return emotionMap[sentimentLabel] || "Нейтральное";
    }

    getTranslateStatusText(status) {
        const statusMap = {
            pending: "Перевод ожидает",
            processing: "Переводится",
            done: "Переведено",
            error: "Ошибка перевода",
        };

        return statusMap[status] || status;
    }

    normalizeMoodScore(sentimentScore, sentimentLabel) {
        if (typeof sentimentScore === "number") {
            if (sentimentScore >= 0 && sentimentScore <= 10) {
                return Math.round(sentimentScore);
            }

            if (sentimentScore >= 0 && sentimentScore <= 100) {
                return Math.round(sentimentScore / 10);
            }
        }

        const fallbackScores = {
            POSITIVE: 8,
            NEUTRAL: 6,
            NEGATIVE: 3,
        };

        return fallbackScores[sentimentLabel] || 6;
    }

    getConfidenceText(sentimentScore) {
        if (typeof sentimentScore !== "number") {
            return "—";
        }

        if (sentimentScore >= 0 && sentimentScore <= 1) {
            return `${Math.round(sentimentScore * 100)} %`;
        }

        if (sentimentScore >= 0 && sentimentScore <= 100) {
            return `${Math.round(sentimentScore)} %`;
        }

        return `${sentimentScore} %`;
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
        const sentimentLabel = note.sentiment_label || "NEUTRAL";

        if (sentimentLabel === "POSITIVE") {
            return "Запись имеет положительную эмоциональную окраску. В тексте заметны признаки спокойствия, ресурса или удовлетворённости текущим состоянием.";
        }

        if (sentimentLabel === "NEGATIVE") {
            return "Запись имеет негативную эмоциональную окраску. Стоит обратить внимание на возможные источники стресса и добавить восстановительные действия.";
        }

        return "Запись имеет нейтральную эмоциональную окраску. Состояние выглядит стабильным, без ярко выраженного эмоционального смещения.";
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

    initEvents() {
        if (this.backButton) {
            this.backButton.addEventListener("click", () => {
                window.location.href = "../pages/history.html";
            });
        }

        const logoutBtn = document.getElementById("logoutBtn");

        if (logoutBtn) {
            logoutBtn.addEventListener("click", () => {
                Auth.logout();
            });
        }
    }

    init() {
        this.initEvents();
        this.renderNote();
    }
}

document.addEventListener("DOMContentLoaded", () => {
    if (!Auth.isAuth()) {
        window.location.href = "../pages/login.html";
        return;
    }

    try {
        const detailsPage = new DetailsPage();
        detailsPage.init();
    } catch (error) {
        console.error("Error:", error);
    }
});