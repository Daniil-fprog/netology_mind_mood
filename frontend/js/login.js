const form = document.querySelector("#loginForm");
const messageBox = document.querySelector("#loginMessage");

// Проверка состояния авторизации при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    // Если уже авторизованы, перенаправляем на главную
    if (Auth.isAuth()) {
        window.location.href = "../pages/home.html";
    }
});

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
        const data = await Auth.login(login, password);
        showMessage("Вход выполнен успешно", "success");

        setTimeout(() => {
            window.location.href = "../pages/home.html";
        }, 1000);
    } catch (error) {
        showMessage(error.message, "error");
    }
});

function showMessage(text, type) {
    messageBox.textContent = text;
    messageBox.className = `auth__message auth__message--${type}`;
    messageBox.style.display = "block";

    setTimeout(() => {
        messageBox.style.display = "none";
    }, 5000);
}