const API_BASE_URL = "http://127.0.0.1:8000";

const form = document.querySelector("#registerForm");
const messageBox = document.querySelector("#registerMessage");

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const name = document.querySelector("#name").value.trim();
    const phone = document.querySelector("#phone").value.trim();
    const password = document.querySelector("#password").value.trim();
    const passwordRepeat = document.querySelector("#passwordRepeat").value.trim();

    if (!name) {
        showMessage("Введите имя пользователя", "error");
        return;
    }

    if (!phone) {
        showMessage("Введите телефон", "error");
        return;
    }

    if (!password) {
        showMessage("Введите пароль", "error");
        return;
    }

    if (password.length < 6) {
        showMessage("Пароль должен быть не короче 6 символов", "error");
        return;
    }

    if (!passwordRepeat) {
        showMessage("Повторите пароль", "error");
        return;
    }

    if (password !== passwordRepeat) {
        showMessage("Пароли не совпадают", "error");
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/users/register`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                name,
                phone,
                password,
            }),
        });

        const data = await safeParseJson(response);

        if (!response.ok) {
            throw new Error(data.detail || "Ошибка регистрации");
        }

        if (data.access_token) {
            localStorage.setItem("access_token", data.access_token);
            localStorage.setItem("token_type", data.token_type || "bearer");

            showMessage("Регистрация выполнена успешно", "success");

            setTimeout(() => {
                window.location.href = "../index.html";
            }, 1000);

            return;
        }

        if (data.login) {
            showMessage(`Регистрация выполнена успешно. Ваш логин: ${data.login}`, "success");
        } else {
            showMessage("Регистрация выполнена успешно. Теперь войдите в аккаунт.", "success");
        }

        setTimeout(() => {
            window.location.href = "login.html";
        }, 2500);
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