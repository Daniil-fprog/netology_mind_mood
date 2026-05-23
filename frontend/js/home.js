import Auth from './auth.js';

const logOut = document.querySelector("#logoutBtn");
if (logOut) {
    logOut.addEventListener('click', Auth.logout)
}

// Отображение данных пользователя в header__account
async function displayUserInfo() {
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

// Выполняем загрузку данных пользователя при загрузке страницы
document.addEventListener('DOMContentLoaded', displayUserInfo);




function showToast(message, type = "error") {
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

function normalizeApiErrors(errorData) {
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


const noteForm = document.querySelector("#noteForm");

async function createNewNote(evt) {
    evt.preventDefault();

    const formData = new FormData(noteForm);

    // Формирует данные
    const data = {
        orig_text: formData.get("orig_text")
    };
    console.log(data);

    if (!data.orig_text || !data.orig_text.trim()) {
        console.log("Введите текст записи");
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

            const errors = normalizeApiErrors(errorData);

            errors.forEach((message) => {
                showToast(message, "error");
            });

            return;
        }

        const result = await response.json()
        
        console.log("Запись создана:", result);
        showToast("Запись успешно создана", "success");

        noteForm.reset();
    } catch (err) {
        console.error("Ошибка", err)
        showToast(err.message || "Ошибка запроса", "error");
    }
}


noteForm.addEventListener("submit", createNewNote)