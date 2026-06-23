import Auth from './auth.js';



class HomePage {
    constructor() {
        this.noteForm = document.querySelector("#noteForm");
        this.contentDateNow = document.querySelector("#content-date-now");
    }

    init() {
        this.contentDateNow.textContent = this.getCurrentDateFormatted();

        this.displayUserInfo();
        this.noteForm.addEventListener("submit", (evt) => this.createNewNote(evt))
    }

    async createNewNote(evt) {
        evt.preventDefault();

        const formData = new FormData(this.noteForm);

        // Формирует данные
        const data = {
            orig_text: formData.get("orig_text")
        };

        const text = data.orig_text?.trim() || "";

        if (!text) {
            console.log("Введите текст записи");
            this.showToast("Введите текст записи", "error");
            return;
        }

        if (text.length < 50) {
            this.showToast(
                `Текст записи должен содержать минимум 50 символов. Сейчас: ${text.length} символов`,
                "error"
            );
            return;
        }

        try {
            const response = await Auth.authenticatedFetch(`${Auth.API_BASE_URL}/notes`, {
                "method": "POST",
                "body": JSON.stringify(data)
            });

            if (!response.ok) {
                const errorData = await response.json();
                console.log("API error:", errorData);

                const errors = this.normalizeApiErrors(errorData);

                errors.forEach((message) => {
                    this.showToast(message, "error");
                });

                return;
            }

            const result = await response.json()

            console.log("Запись создана:", result);
            this.showToast("Запись успешно создана", "success");

            this.noteForm.reset();
        } catch (err) {
            console.error("Ошибка", err)
            this.showToast(err.message || "Ошибка запроса", "error");
        }
    }


    getCurrentDateFormatted() {
        const date = new Date();

        const weekday = new Intl.DateTimeFormat('ru-RU', {
            weekday: 'long'
        }).format(date);

        const dayMonth = new Intl.DateTimeFormat('ru-RU', {
            day: 'numeric',
            month: 'long'
        }).format(date);

        const time = new Intl.DateTimeFormat('ru-RU', {
            hour: '2-digit',
            minute: '2-digit'
        }).format(date);

        return `${weekday.charAt(0).toUpperCase() + weekday.slice(1)}, ${dayMonth} • ${time}`;
    }

    // Отображение данных пользователя в header__account
    async displayUserInfo() {
        const user = await Auth.getCurrentUser();

        if (!user) {
            return;
        }

        // Обновляем логин и имя пользователя
        const userLoginElement = document.getElementById('user-login');
        const userNameElement = document.getElementById('user-name');

        if (userLoginElement) {
            userLoginElement.textContent = user.login || 'Не указан';
        }

        if (userNameElement) {
            userNameElement.textContent = user.name || 'Не указан';
        }
    }


    showToast(message, type = "error") {
        const container = document.querySelector("#toastContainer");

        if (!container) {
            console.error("Toast container not found");
            return;
        }

        const typeClasses = {
            success: "bg-green-500",
            error: "bg-red-500",
            warning: "bg-yellow-500",
            info: "bg-blue-500",
        };

        const toast = document.createElement("div");

        toast.className = `
            ${typeClasses[type] || typeClasses.info}
            text-white
            px-5
            py-3
            rounded-xl
            shadow-lg
            min-w-[260px]
            max-w-[420px]
            text-sm
            transition
            duration-300
            opacity-100
        `;

        toast.textContent = message;

        container.appendChild(toast);

        setTimeout(() => {
            toast.classList.add("opacity-0", "translate-x-4");

            setTimeout(() => {
                toast.remove();
            }, 300);
        }, 4000);
    }

    normalizeApiErrors(errorData) {
        if (!errorData) {
            return ["Неизвестная ошибка"];
        }

        if (Array.isArray(errorData.detail)) {
            return errorData.detail.map((err) => {
                const field = err.loc?.join(".") || "unknown";
                return `${field}: ${err.msg}`;
            });
        }

        if (typeof errorData.detail === "string") {
            return [errorData.detail];
        }

        if (errorData.detail && typeof errorData.detail === "object") {
            return [JSON.stringify(errorData.detail)];
        }

        if (typeof errorData === "string") {
            return [errorData];
        }

        return ["Ошибка сохранения записи"];
    }
}


// Инициализация класса после загрузки DOM
document.addEventListener('DOMContentLoaded', () => {
    // Проверяем авторизацию пользователя
    if (!Auth.isAuth()) {
        window.location.href = "./login.html";
        return;
    }

    const historyPage = new HomePage();
    historyPage.init();

    // // Добавляем обработчик для кнопки выхода
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            Auth.logout();
        });
    }
});
