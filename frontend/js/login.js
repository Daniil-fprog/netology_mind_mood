const API_BASE_URL = "http://127.0.0.1:8000";

const form = document.querySelector("#loginForm");
const messageBox = document.querySelector("#loginMessage");

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const login = document.querySelector("#login").value.trim();
    const password = document.querySelector("#password").value.trim();

    if (!login) {
        showMessage("Введите логин", "error");
        return;
    }

    if (!password) {
        showMessage("Введите пароль", "error");
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/users/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                login,
                password,
            }),
        });

        const data = await safeParseJson(response);

        if (!response.ok) {
            throw new Error(data.detail || "Ошибка авторизации");
        }

        if (data.access_token) {
            localStorage.setItem("access_token", data.access_token);
            localStorage.setItem("token_type", data.token_type || "bearer");
        }

        showMessage("Вход выполнен успешно", "success");

        setTimeout(() => {
            window.location.href = "../index.html";
        }, 1000);
    } catch (error) {
        showMessage(error.message, "error");
    }
});

async function safeParseJson(response) {
    try {
        return await response.json();
    } catch {
        return {};
    }
}

function showMessage(text, type) {
    messageBox.textContent = text;
    messageBox.className = `auth__message auth__message--${type}`;
    messageBox.style.display = "block";

    setTimeout(() => {
        messageBox.style.display = "none";
    }, 5000);
}