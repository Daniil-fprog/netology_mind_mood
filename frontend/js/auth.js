const API_BASE_URL = "http://127.0.0.1:8000";

/**
 * Проверяет, авторизован ли пользователь
 * @returns {boolean} - true, если пользователь авторизован
 */
function isAuth() {
    const token = localStorage.getItem("access_token");
    return !!token;
}

/**
 * Получает токен авторизации
 * @returns {string|null} - токен или null, если не найден
 */
function getAuthToken() {
    return localStorage.getItem("access_token");
}

/**
 * Получает тип токена
 * @returns {string} - тип токена (обычно "bearer")
 */
function getTokenType() {
    return localStorage.getItem("token_type") || "bearer";
}

/**
 * Сохраняет токен в localStorage
 * @param {string} token - токен доступа
 * @param {string} type - тип токена
 */
function setAuthToken(token, type = "bearer") {
    localStorage.setItem("access_token", token);
    localStorage.setItem("token_type", type);
}

/**
 * Удаляет токен из localStorage
 */
function removeAuthToken() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("token_type");
}

/**
 * Получает заголовки для авторизованных запросов
 * @returns {Object} - объект с заголовками
 */
function getAuthHeaders() {
    const token = getAuthToken();
    const tokenType = getTokenType();
    
    if (!token) {
        return {};
    }
    
    return {
        "Authorization": `${tokenType} ${token}`,
        "Content-Type": "application/json"
    };
}

/**
 * Отправляет запрос с авторизацией
 * @param {string} url - URL для запроса
 * @param {Object} options - опции запроса
 * @returns {Promise<Response>} - ответ от сервера
 */
async function authenticatedFetch(url, options = {}) {
    const headers = options.headers || {};
    const authHeaders = getAuthHeaders();
    
    // Объединяем заголовки, сохраняя кастомные
    const finalHeaders = { ...authHeaders, ...headers };
    
    const finalOptions = {
        ...options,
        headers: finalHeaders
    };
    
    const response = await fetch(url, finalOptions);
    
    // Если токен недействителен, перенаправляем на страницу входа
    if (response.status === 401) {
        removeAuthToken();
        window.location.href = "../pages/login.html";
        throw new Error("Не авторизован");
    }
    
    return response;
}

/**
 * Вход пользователя
 * @param {string} login - логин пользователя
 * @param {string} password - пароль
 * @returns {Promise<Object>} - данные ответа
 */
async function login(login, password) {
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
    
    const data = await response.json();
    
    if (!response.ok) {
        throw new Error(data.detail || "Ошибка авторизации");
    }
    
    if (data.access_token) {
        setAuthToken(data.access_token, data.token_type);
    }
    
    return data;
}

/**
 * Регистрация пользователя
 * @param {Object} userData - данные пользователя
 * @param {string} userData.name - имя пользователя
 * @param {string} userData.phone - телефон
 * @param {string} userData.password - пароль
 * @returns {Promise<Object>} - данные ответа
 */
async function register(userData) {
    const response = await fetch(`${API_BASE_URL}/users/register`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(userData),
    });
    
    const data = await response.json();
    
    if (!response.ok) {
        throw new Error(data.detail || "Ошибка регистрации");
    }
    
    return data;
}

/**
 * Получение данных текущего пользователя
 * @returns {Promise<Object>} - данные пользователя
 */
async function getCurrentUser() {
    const response = await authenticatedFetch(`${API_BASE_URL}/users/me`);
    return await response.json();
}

/**
 * Выход из системы
 */
function logout() {
    removeAuthToken();
    window.location.href = "../pages/login.html";
}

/**
 * Проверяет и обновляет состояние авторизации при загрузке страницы
 */
function checkAuthStatus() {
    // Проверяем, есть ли токен
    if (!isAuth()) {
        // Если мы не на странице входа/регистрации, перенаправляем на вход
        const currentPath = window.location.pathname;
        const isAuthPage = currentPath.includes('login.html') || currentPath.includes('register.html');
        
        if (!isAuthPage) {
            window.location.href = "../pages/login.html";
        }
    }
}

// Экспортируем функции для использования в других модулях
window.Auth = {
    isAuth,
    getAuthToken,
    getTokenType,
    setAuthToken,
    removeAuthToken,
    getAuthHeaders,
    authenticatedFetch,
    login,
    register,
    getCurrentUser,
    logout,
    checkAuthStatus
};