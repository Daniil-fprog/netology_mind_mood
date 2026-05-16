
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
            const response = await fetch('/notes');

            if (!response.ok) {
                throw new Error(`Ошибка загрузки данных: ${response.status}`);
            }

            const result = await response.json();
            return result;
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

        const card = entryElement.querySelector(".history__entry-card");
        const time = entryElement.querySelector(".history__entry-time");
        const moodIndicator = entryElement.querySelector(".history__mood-indicator");
        const moodBadge = entryElement.querySelector(".history__mood-badge");
        const title = entryElement.querySelector(".history__entry-title");
        const text = entryElement.querySelector(".history__entry-text");
        const tagsContainer = entryElement.querySelector(".history__entry-tags");

        time.textContent = entry.time;
        moodBadge.textContent = entry.mood;
        title.textContent = entry.title;
        text.textContent = entry.text;

        moodIndicator.classList.add(`history__mood-indicator--${entry.moodType}`);

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

        group.entries.forEach((entry) => {
            const entryElement = this.createEntry(entry);
            entriesContainer.append(entryElement);
        });

        return groupElement;
    }

}

const historyData = [
    {
        dateTitle: "СЕГОДНЯ, 24 ОКТЯБРЯ",
        entries: [
            {
                time: "14:30",
                mood: "Спокойствие",
                moodType: "calm",
                title: "Рабочий фокус",
                text: "Удалось сосредоточиться на сложной задаче без отвлечений. Практика глубокого дыхания перед началом сессии помогла настроиться на нужный лад.",
                tags: ["Работа", "Фокус"]
            },
            {
                time: "10:15",
                mood: "Радость",
                moodType: "happy",
                title: "Хорошее утро",
                text: "Начал день спокойно, сделал зарядку и выпил кофе без спешки.",
                tags: ["Утро", "Энергия"]
            }
        ]
    },
    {
        dateTitle: "ВЧЕРА, 23 ОКТЯБРЯ",
        entries: [
            {
                time: "21:40",
                mood: "Тревога",
                moodType: "anxiety",
                title: "Вечерние мысли",
                text: "Было сложно расслабиться после насыщенного дня.",
                tags: ["Вечер", "Стресс"]
            },
            {
                time: "21:40",
                mood: "Тревога",
                moodType: "anxiety",
                title: "Вечерние мысли",
                text: "Было сложно расслабиться после насыщенного дня.",
                tags: ["Вечер", "Стресс"]
            },
            {
                time: "21:40",
                mood: "Тревога",
                moodType: "anxiety",
                title: "Вечерние мысли",
                text: "Было сложно расслабиться после насыщенного дня.",
                tags: ["Вечер", "Стресс"]
            },
            {
                time: "21:40",
                mood: "Тревога",
                moodType: "anxiety",
                title: "Вечерние мысли",
                text: "Было сложно расслабиться после насыщенного дня.",
                tags: ["Вечер", "Стресс"]
            },
        ]
    }
];


// Инициализация класса
const historyPage = new HistoryPage();
historyPage.renderHistoryData();


