// Фиксируем начало сессии при загрузке страницы
window.addEventListener('load', () => {
    fetch('https://honored-graceful-thrill.glitch.me/track_user', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            userId: 'user123', // Уникальный идентификатор пользователя
            startTime: Date.now() // Текущая метка времени
        })
    });
});

// Фиксируем завершение сессии при уходе со страницы
window.addEventListener('beforeunload', () => {
    fetch('https://honored-graceful-thrill.glitch.me/track_user', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            userId: 'user123',
            endTime: Date.now()
        })
    });
});
