// Функция для отправки данных на сервер
function sendEndSession() {
    fetch('https://telegram-server-hfk7.onrender.com/track_user', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            userId: userId,
            endTime: Date.now(),
        }),
    });
}

// Обработчик для события изменения видимости
document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') {
        // Если приложение свернуто, проверяем флаг активности
        if (localStorage.getItem('app_active') === 'true') {
            localStorage.setItem('app_active', 'false'); // Устанавливаем флаг, что приложение неактивно
            sendEndSession(); // Отправляем данные на сервер, так как приложение свернуто
        }
    } else if (document.visibilityState === 'visible') {
        // При возврате на приложение снова устанавливаем флаг активности
        localStorage.setItem('app_active', 'true');
    }
});

// Обработчик для события закрытия окна или вкладки
window.addEventListener('beforeunload', () => {
    if (localStorage.getItem('app_active') === 'true') {
        localStorage.setItem('app_active', 'false'); // Обновляем флаг активности
        sendEndSession(); // Отправляем данные на сервер при закрытии
    }
});

// Устанавливаем флаг активности при загрузке страницы
window.addEventListener('load', () => {
    localStorage.setItem('app_active', 'true');
});
