import Auth from './auth.js';

const form = document.querySelector("#registerForm");
const messageBox = document.querySelector("#registerMessage");

// Проверка состояния авторизации при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    // Если уже авторизованы, перенаправляем на главную
    if (Auth.isAuth()) {
        window.location.href = "./home.html";
    }
});

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const name = document.querySelector("#name").value.trim();
    const login = document.querySelector("#login").value.trim();
    const phone = document.querySelector("#phone").value.trim();
    const password = document.querySelector("#password").value.trim();
    const passwordRepeat = document.querySelector("#passwordRepeat").value.trim();

    if (!name) {
        showMessage("Введите имя", "error");
        return;
    }
   
    if (!login) {
        showMessage("Введите логин", "error");
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
        const data = await Auth.register({
            name,
            login,
            phone,
            password,
        });

        showMessage("Регистрация выполнена успешно", "success");

        if (data.login) {
            showMessage(`Ваш логин: ${data.login}`, "success");
        }

        setTimeout(() => {
            window.location.href = "./login.html";
        }, 2500);
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
