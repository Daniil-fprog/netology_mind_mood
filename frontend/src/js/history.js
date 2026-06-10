
import Auth from './auth.js';

class HistoryPage {
    constructor() {
        this.historyList = document.querySelector("#historyList");
        this.groupTemplate = document.querySelector("#historyDateGroupTemplate");
        this.entryTemplate = document.querySelector("#historyEntryTemplate");

        if (!this.historyList) {
            throw new Error("Не найден элемент #historyList");
        }

        if (!this.groupTemplate) {
            throw new Error("Не найден шаблон #historyDateGroupTemplate");
        }

        if (!this.entryTemplate) {
            throw new Error("Не найден шаблон #historyEntryTemplate");
        }

        this.searchInput = document.getElementById("searchInput");
        this.searchClear = document.getElementById("searchClear");
        this.filterBtn = document.getElementById("filterBtn");
        this.filterPopup = document.getElementById("filterPopup");
        this.filterPopupContent = document.querySelector(".history__filter-popup-content");
        this.filterPopupClose = document.getElementById("filterPopupClose");
        this.filterReset = document.getElementById("filterReset");
        this.filterApply = document.getElementById("filterApply");
        this.filterBadge = document.getElementById("filterBadge");

        this.filters = {
            search: "",
            period: "all",
            sort: "newest",
            mood: "all"
        };

        this.initEventListeners();
    }

    initEventListeners() {
        // События для поиска
        if (this.searchInput) {
            this.searchInput.addEventListener("input", (e) => {
                this.filters.search = e.target.value;
                this.updateSearchClear();
                this.applyFilters();
            });
        }

        if (this.searchClear) {
            this.searchClear.addEventListener("click", () => {
                this.searchInput.value = "";
                this.filters.search = "";
                this.updateSearchClear();
                this.applyFilters();
            });
        }

        // События для кнопки фильтра
        if (this.filterBtn) {
            this.filterBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                console.log('КЛик');
                
                this.toggleFilterPopup();
            });
        }

        if (this.filterPopupClose) {
            this.filterPopupClose.addEventListener("click", () => {
                this.closeFilterPopup();
            });
        }

        // Закрытие попапа при клике вне
        document.addEventListener("click", (e) => {
            if (this.filterPopup && this.filterPopup.classList.contains("history__filter-popup--active")) {
                const isClickInsidePopup = this.filterPopupContent.contains(e.target);
                const isClickOnFilterBtn = e.target.closest("#filterBtn");

                if (!isClickInsidePopup && !isClickOnFilterBtn) {
                    this.closeFilterPopup();
                }
            }
        });

        // Закрытие при Escape
        document.addEventListener("keydown", (e) => {
            if (e.key === "Escape" && this.filterPopup.classList.contains("history__filter-popup--active")) {
                this.closeFilterPopup();
            }
        });

        // Кнопки попапа
        if (this.filterApply) {
            this.filterApply.addEventListener("click", (e) => {
                e.stopPropagation();

                this.syncFiltersFromPopup();
                this.applyFilters();
                this.closeFilterPopup();
            });
        }

        if (this.filterReset) {
            this.filterReset.addEventListener("click", (e) => {
                e.stopPropagation();
                this.resetFilters();
                this.closeFilterPopup();
            });
        }
    }

    updateSearchClear() {
        if (this.searchClear && this.searchInput) {
            this.searchClear.style.display = this.searchInput.value ? "flex" : "none";
        }
    }

    toggleFilterPopup() {
        if (this.filterPopup) {
            if (this.filterPopup.classList.contains("history__filter-popup--active")) {
                this.closeFilterPopup();
            } else {
                this.openFilterPopup();
            }
        }
    }

    openFilterPopup() {
        if (this.filterPopup) {
            this.filterPopup.classList.add("history__filter-popup--active");
        }
    }

    closeFilterPopup() {
        if (this.filterPopup) {
            this.filterPopup.classList.remove("history__filter-popup--active");
        }
    }

    resetFilters() {
        // Сброс поиска
        if (this.searchInput) {
            this.searchInput.value = "";
        }
        this.filters.search = "";

        // Сброс радио-кнопок
        const periodRadios = document.querySelectorAll('input[name="period"]');
        periodRadios.forEach(radio => {
            if (radio.value === "all") {
                radio.checked = true;
            }
        });
        this.filters.period = "all";

        const sortRadios = document.querySelectorAll('input[name="sort"]');
        sortRadios.forEach(radio => {
            if (radio.value === "newest") {
                radio.checked = true;
            }
        });
        this.filters.sort = "newest";

        const moodRadios = document.querySelectorAll('input[name="mood"]');
        moodRadios.forEach(radio => {
            if (radio.value === "all") {
                radio.checked = true;
            }
        });
        this.filters.mood = "all";

        this.updateFilterBadge();
        this.applyFilters();
    }

    getPeriodDateRange() {
        const today = new Date();
        let startDate;

        switch (this.filters.period) {
            case "today":
                startDate = new Date(today);
                startDate.setHours(0, 0, 0, 0);
                break;
            case "week":
                startDate = new Date(today);
                startDate.setDate(today.getDate() - 7);
                break;
            case "month":
                startDate = new Date(today);
                startDate.setMonth(today.getMonth() - 1);
                break;
            default:
                return { dateFrom: "", dateTo: "" };
        }

        const dateFrom = startDate.toISOString().split('T')[0];
        return { dateFrom, dateTo: "" };
    }

    getActiveFiltersCount() {
        let count = 0;
        if (this.filters.search) count++;
        if (this.filters.period !== "all") count++;
        if (this.filters.mood !== "all") count++;
        return count;
    }

    updateFilterBadge() {
        if (this.filterBadge) {
            const count = this.getActiveFiltersCount();
            this.filterBadge.textContent = count;
            this.filterBadge.style.display = count > 0 ? "inline-block" : "none";
        }

        if (this.filterBtn) {
            if (this.getActiveFiltersCount() > 0) {
                this.filterBtn.classList.add("active");
            } else {
                this.filterBtn.classList.remove("active");
            }
        }
    }

    syncFiltersFromPopup() {
        const selectedPeriod = document.querySelector('input[name="period"]:checked');
        const selectedSort = document.querySelector('input[name="sort"]:checked');
        const selectedMood = document.querySelector('input[name="mood"]:checked');

        if (selectedPeriod) {
            this.filters.period = selectedPeriod.value;
        }

        if (selectedSort) {
            this.filters.sort = selectedSort.value;
        }

        if (selectedMood) {
            this.filters.mood = selectedMood.value;
        }
    }

    async applyFilters() {
        try {
            if (!Auth.isAuth()) {
                console.error('Пользователь не авторизован');
                return;
            }

            // Получаем даты из периода
            const { dateFrom, dateTo } = this.getPeriodDateRange();

            // Формируем URL с параметрами фильтрации
            let url = `${Auth.API_BASE_URL}/notes/`;
            const params = new URLSearchParams();

            if (this.filters.search) params.append("search", this.filters.search);
            if (dateFrom) params.append("date_from", dateFrom);
            if (dateTo) params.append("date_to", dateTo);

            if (this.filters.mood !== "all") {
                params.append("sentiment_label", this.filters.mood);
            }

            if (this.filters.sort) params.append("sort", this.filters.sort);

            const queryString = params.toString();

            if (queryString) {
                url += `?${queryString}`;
            }
            // console.log("URL: ", url);

            const response = await Auth.authenticatedFetch(url);

            if (!response.ok) {
                throw new Error(`Ошибка загрузки данных: ${response.status}`);
            }

            const notes = await response.json();
            console.log("Отфильтрованные заметки:", notes);

            this.updateFilterBadge();
            this.renderGroups(notes);
        } catch (error) {
            console.error("Error applying filters:", error);
        }
    }

    async getHistoryData() {
        try {
            if (!Auth.isAuth()) {
                console.error('Пользователь не авторизован');
                return [];
            }

            const response = await Auth.authenticatedFetch(`${Auth.API_BASE_URL}/notes/`);

            if (!response.ok) {
                throw new Error(`Ошибка загрузки данных: ${response.status}`);
            }

            const notes = await response.json();

            return this.groupNotesByDate(notes);
        } catch (error) {
            console.error('Error:', error);
            return [];
        }
    }

    async renderGroups(notes) {
        this.historyList.innerHTML = "";

        if (!notes.length) {
            this.historyList.innerHTML = "<p>Записей не найдено</p>";
            return;
        }

        const groups = this.groupNotesByDate(notes);

        groups.forEach((group) => {
            const groupElement = this.createDateGroup(group);
            this.historyList.append(groupElement);
        });
    }

    async renderHistoryData() {
        const groups = await this.getHistoryData();

        this.historyList.innerHTML = "";

        if (!groups.length) {
            this.historyList.innerHTML = "<p>Записей пока нет</p>";
            return;
        }

        groups.forEach((group) => {
            const groupElement = this.createDateGroup(group);
            this.historyList.append(groupElement);
        });
    }

    createEntry(entry) {
        const entryElement = this.entryTemplate.content.cloneNode(true);

        const time = entryElement.querySelector(".history__entry-time");
        const moodIndicator = entryElement.querySelector(".history__mood-indicator");
        const moodBadge = entryElement.querySelector(".history__mood-badge");
        const title = entryElement.querySelector(".history__entry-title");
        const text = entryElement.querySelector(".history__entry-text");
        const tagsContainer = entryElement.querySelector(".history__entry-tags");

        time.textContent = entry.time;
        moodBadge.textContent = entry.moodLabel;
        title.textContent = entry.title;
        title.href = `./details.html?id=${entry.id}`;
        text.textContent = entry.text;

        // Очищаем предыдущие классы настроения
        moodIndicator.className = "history__mood-indicator";
        if (entry.moodClass) {
            moodIndicator.classList.add(`history__mood-indicator--${entry.moodClass}`);
        }

        // Очищаем предыдущие теги
        tagsContainer.innerHTML = "";

        const tags = entry.tags || [];

        tags.forEach((tag) => {
            const tagElement = document.createElement("span");
            tagElement.classList.add("history__tag");
            tagElement.textContent = tag;

            tagsContainer.append(tagElement);
        });

        return entryElement;
    }

    createDateGroup(group) {
        const groupElement = this.groupTemplate.content.cloneNode(true);

        const dateTitle = groupElement.querySelector(".history__date-title");
        const entriesContainer = groupElement.querySelector(".history__entries");

        dateTitle.textContent = group.dateTitle;

        // Очищаем предыдущие записи
        entriesContainer.innerHTML = "";

        group.entries.forEach((entry) => {
            const entryElement = this.createEntry(entry);
            entriesContainer.append(entryElement);
        });

        return groupElement;
    }

    groupNotesByDate(notes) {
        // Группируем заметки по датам
        const groups = {};

        notes.forEach(note => {
            // Преобразуем дату из ISO формата в объект Date
            const date = new Date(note.created_at);
            const dateKey = date.toISOString().split('T')[0]; // Получаем YYYY-MM-DD

            if (!groups[dateKey]) {
                groups[dateKey] = {
                    dateTitle: this.formatDateTitle(date),
                    entries: []
                };
            }

            // Форматируем время как HH:MM
            const timeString = date.toTimeString().substring(0, 5);

            // Определяем тип настроения на основе sentiment_label
            const moodInfo = this.getMoodType(note.sentiment_label);

            groups[dateKey].entries.push({
                id: note.id,
                time: timeString,
                mood: note.sentiment_label || 'Не определено',
                moodClass: moodInfo.class,
                moodLabel: moodInfo.label,
                title: this.generateTitle(note.orig_text),
                text: note.orig_text,
                tags: this.extractTags(note.orig_text)
            });
        });

        // Преобразуем объект в массив и сортируем по дате (новые первыми)
        return Object.keys(groups)
            .map(key => groups[key])
            .sort((a, b) => {
                return new Date(b.dateTitle.split(', ')[1]) - new Date(a.dateTitle.split(', ')[1]);
            });
    }

    formatDateTitle(date) {
        const today = new Date();
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);

        const options = { day: 'numeric', month: 'long' };
        const dateString = date.toLocaleDateString('ru-RU', options).toUpperCase();

        // Проверяем, является ли дата сегодняшней или вчерашней
        if (date.toDateString() === today.toDateString()) {
            return `СЕГОДНЯ, ${dateString}`;
        } else if (date.toDateString() === yesterday.toDateString()) {
            return `ВЧЕРА, ${dateString}`;
        } else {
            // Для других дат добавляем день недели
            const weekdays = ['ВОСКРЕСЕНЬЕ', 'ПОНЕДЕЛЬНИК', 'ВТОРНИК', 'СРЕДА', 'ЧЕТВЕРГ', 'ПЯТНИЦА', 'СУББОТА'];
            const weekday = weekdays[date.getDay()];
            return `${weekday}, ${dateString}`;
        }
    }

    getMoodType(sentimentLabel) {
        // Сопоставление типов настроения с CSS классами и русским названием
        const moodMap = {
            'negative': { class: 'tired', label: 'Плохое' },
            'positive': { class: 'joy', label: 'Хорошее' },
            'neutral': { class: 'calm', label: 'Спокойное' },
        };

        return moodMap[sentimentLabel] || { class: 'calm', label: 'Не определено' };
    }

    generateTitle(text) {
        // Простое создание заголовка из первых слов текста
        if (!text) return 'Без названия';

        // Берем первые 3 слова или до точки
        const words = text.split(' ');
        const titleWords = words.slice(0, 3).join(' ');
        return titleWords.length > 30 ? titleWords.substring(0, 30) + '...' : titleWords;
    }

    extractTags(text) {
        // Простое извлечение тегов из текста
        // В реальной реализации это может быть более сложной логикой
        if (!text) return [];

        // Ищем слова в нижнем регистре, начинающиеся с #
        const tags = text.match(/#[а-яА-ЯёЁa-zA-Z0-9]+/g);
        return tags ? tags.map(tag => tag.substring(1)) : [];
    }

}

// Инициализация класса после загрузки DOM
document.addEventListener('DOMContentLoaded', () => {
    // Проверяем авторизацию пользователя
    if (!Auth.isAuth()) {
        window.location.href = "./login.html";
        return;
    }

    const historyPage = new HistoryPage();
    historyPage.renderHistoryData();

    // Добавляем обработчик для кнопки выхода
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            Auth.logout();
        });
    }
});


