
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
    }

    async getHistoryData() {
        try {
            // Проверяем, авторизован ли пользователь
            if (!Auth.isAuth()) {
                console.error('Пользователь не авторизован');
                return [];
            }

            const response = await Auth.authenticatedFetch("http://127.0.0.1:8000/notes/");
            
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
        moodBadge.textContent = entry.mood;
        title.textContent = entry.title;
        title.href = `../details.html?id=${entry.id}`;
        text.textContent = entry.text;

        // Очищаем предыдущие классы настроения
        moodIndicator.className = "history__mood-indicator";
        moodIndicator.classList.add(`history__mood-indicator--${entry.moodType}`);

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
            // В реальной реализации это может быть более сложной логикой
            const moodType = this.getMoodType(note.sentiment_label);
            
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
            'POSITIVE': 'happy',
            'NEGATIVE': 'anxiety',
            'NEUTRAL': 'calm'
        };
        
        return moodMap[sentimentLabel] || 'calm';
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
        window.location.href = "../login.html";
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


