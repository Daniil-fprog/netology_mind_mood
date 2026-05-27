
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

        this.initFilters();
    }

    initFilters() {
        // Создаем контейнер фильтров
        const pageHeader = document.querySelector(".history__page-header");
        if (!pageHeader) return;

        const actionsContainer = pageHeader.querySelector(".history__header-actions");
        if (!actionsContainer) return;

        // Добавляем кнопку поиска и фильтрации
        const headerActions = pageHeader.querySelector(".history__header-actions");
        
        // Добавляем кнопку поиска с выпадающим полем
        const searchBtn = headerActions.querySelector(".history__icon-btn:first-of-type");
        searchBtn.onclick = (e) => {
            e.preventDefault();
            this.toggleSearch();
        };

        // Добавляем кнопку фильтра с выпадающим полем
        const filterBtn = headerActions.querySelector(".history__icon-btn:last-of-type");
        filterBtn.onclick = (e) => {
            e.preventDefault();
            this.toggleFilter();
        };

        // Создаем элементы поиска и фильтра
        this.createFilterUI();
    }

    createFilterUI() {
        const pageHeader = document.querySelector(".history__page-header");
        if (!pageHeader) return;

        const headerActions = pageHeader.querySelector(".history__header-actions");
        if (!headerActions) return;

        // Создаем контейнер поиска
        this.searchContainer = document.createElement("div");
        this.searchContainer.className = "history__search-container";
        this.searchContainer.innerHTML = `
            <div class="history__search-wrapper">
                <i class="fas fa-search history__search-icon"></i>
                <input 
                    type="text" 
                    class="history__search-input" 
                    placeholder="Поиск по заметкам..."
                    id="searchInput"
                >
                <button class="history__search-clear" id="searchClear">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        // Создаем контейнер фильтров
        this.filterContainer = document.createElement("div");
        this.filterContainer.className = "history__filter-container";
        this.filterContainer.innerHTML = `
            <div class="history__filter-wrapper">
                <div class="history__filter-group">
                    <label class="history__filter-label">
                        <i class="fas fa-calendar-alt"></i>
                        <select class="history__filter-select" id="dateFrom">
                            <option value="">С даты</option>
                            ${this.getdateRangeOptions()}
                        </select>
                    </label>
                    <label class="history__filter-label">
                        <i class="fas fa-calendar-check"></i>
                        <select class="history__filter-select" id="dateTo">
                            <option value="">По дату</option>
                            ${this.getdateRangeOptions()}
                        </select>
                    </label>
                </div>
                <div class="history__filter-group">
                    <label class="history__filter-label">
                        <i class="fas fa-smile"></i>
                        <select class="history__filter-select" id="sentimentFilter">
                            <option value="">Настроение</option>
                            <option value="positive">Хорошее</option>
                            <option value="negative">Плохое</option>
                        </select>
                    </label>
                </div>
                <button class="history__filter-apply" id="applyFilters">
                    <i class="fas fa-check"></i>
                </button>
                <button class="history__filter-reset" id="resetFilters">
                    <i class="fas fa-redo"></i>
                </button>
            </div>
        `;

        // Вставляем контейнеры в header
        headerActions.parentNode.insertBefore(this.searchContainer, headerActions);
        headerActions.parentNode.insertBefore(this.filterContainer, headerActions);

        // Добавляем обработчики событий
        this.setupEventListeners();
    }

    getdateRangeOptions() {
        const options = [''];
        const today = new Date();
        
        for (let i = 0; i < 30; i++) {
            const date = new Date(today);
            date.setDate(date.getDate() - i);
            const dateStr = date.toISOString().split('T')[0];
            const displayDate = date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' });
            options.push(`<option value="${dateStr}">${displayDate}</option>`);
        }
        
        return options.join('');
    }

    setupEventListeners() {
        // События для поиска
        const searchInput = document.getElementById("searchInput");
        const searchClear = document.getElementById("searchClear");

        if (searchInput) {
            searchInput.addEventListener("input", (e) => {
                this.applyFilters({
                    search: e.target.value,
                    dateFrom: document.getElementById("dateFrom")?.value || "",
                    dateTo: document.getElementById("dateTo")?.value || "",
                    sentimentLabel: document.getElementById("sentimentFilter")?.value || ""
                });
            });
        }

        if (searchClear) {
            searchClear.addEventListener("click", () => {
                const searchInput = document.getElementById("searchInput");
                if (searchInput) {
                    searchInput.value = "";
                    this.applyFilters({ search: "" });
                }
            });
        }

        // События для фильтров
        document.getElementById("applyFilters")?.addEventListener("click", () => {
            this.applyFilters({
                search: document.getElementById("searchInput")?.value || "",
                dateFrom: document.getElementById("dateFrom")?.value || "",
                dateTo: document.getElementById("dateTo")?.value || "",
                sentimentLabel: document.getElementById("sentimentFilter")?.value || ""
            });
        });

        document.getElementById("resetFilters")?.addEventListener("click", () => {
            document.getElementById("dateFrom").value = "";
            document.getElementById("dateTo").value = "";
            document.getElementById("sentimentFilter").value = "";
            this.applyFilters({});
        });
    }

    toggleSearch() {
        if (this.searchContainer.classList.contains("history__search-container--active")) {
            this.searchContainer.classList.remove("history__search-container--active");
        } else {
            this.searchContainer.classList.add("history__search-container--active");
            document.getElementById("searchInput")?.focus();
        }
    }

    toggleFilter() {
        if (this.filterContainer.classList.contains("history__filter-container--active")) {
            this.filterContainer.classList.remove("history__filter-container--active");
        } else {
            this.filterContainer.classList.add("history__filter-container--active");
        }
    }

    async applyFilters(filters = {}) {
        try {
            if (!Auth.isAuth()) {
                console.error('Пользователь не авторизован');
                return;
            }

            // Формируем URL с параметрами фильтрации
            let url = `${Auth.API_BASE_URL}/notes/`;
            const params = new URLSearchParams();

            if (filters.search) params.append("search", filters.search);
            if (filters.dateFrom) params.append("date_from", filters.dateFrom);
            if (filters.dateTo) params.append("date_to", filters.dateTo);
            if (filters.sentimentLabel) params.append("sentiment_label", filters.sentimentLabel);

            const queryString = params.toString();
            if (queryString) {
                url += `?${queryString}`;
            }

            const response = await Auth.authenticatedFetch(url);

            if (!response.ok) {
                throw new Error(`Ошибка загрузки данных: ${response.status}`);
            }

            const notes = await response.json();
            console.log("Отфильтрованные заметки:", notes);

            this.renderGroups(notes);
        } catch (error) {
            console.error("Error applying filters:", error);
        }
    }

    async getHistoryData() {
        try {
            // Проверяем, авторизован ли пользователь
            if (!Auth.isAuth()) {
                console.error('Пользователь не авторизован');
                return [];
            }

            const response = await Auth.authenticatedFetch(`${Auth.API_BASE_URL}/notes/`);

            if (!response.ok) {
                throw new Error(`Ошибка загрузки данных: ${response.status}`);
            }

            const notes = await response.json();
            console.log(notes);

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
        moodBadge.textContent = entry.moodType;
        title.textContent = entry.title;
        title.href = `./details.html?id=${entry.id}`;
        text.textContent = entry.text;

        // Очищаем предыдущие классы настроения
        moodIndicator.className = "history__mood-indicator";
        if (entry.moodType !== "Не определено") {
            moodIndicator.classList.add(`history__mood-indicator--${entry.moodType}`);
        }

        // Очищаем предыдущие теги
        tagsContainer.innerHTML = "";

        const tags = entry.tags || [];
        console.log(tags);
        

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
            // В реальной реализации это может быть более сложной логикой
            const moodType = this.getMoodType(note.sentiment_label);

            console.log(moodType);
            
            
            groups[dateKey].entries.push({
                id: note.id,
                time: timeString,
                mood: note.sentiment_label || 'Не определено',
                moodType: moodType,
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
        // Простое сопоставление типов настроения
        const moodMap = {
            'negative': 'Плохое',
            'positive': 'Хорошее',
        };

        return moodMap[sentimentLabel] || 'Не определено';
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


