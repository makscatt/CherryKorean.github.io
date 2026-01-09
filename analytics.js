// --- analytics.js ---

// 1. Загрузка библиотеки Google Analytics (gtag.js)
const GA_MEASUREMENT_ID = 'G-DK04WJ72Z7'; // <--- ВСТАВЬ СЮДА СВОЙ ID

// Создаем скрипт динамически, чтобы не засорять HTML
const script = document.createElement('script');
script.src = `https://www.googletagmanager.com/gtag/js?id=${GA_MEASUREMENT_ID}`;
script.async = true;
document.head.appendChild(script);

// Инициализация слоя данных
window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('js', new Date());

// 2. Функция для настройки пользователя (User ID)
// Вызываем её сразу при загрузке скрипта
function initAnalytics() {
    const tg = window.Telegram?.WebApp;
    const telegramId = tg?.initDataUnsafe?.user?.id;

    if (telegramId) {
        // Если есть ID, сообщаем его Гуглу. Это КЛЮЧЕВОЙ момент для Retention.
        gtag('config', GA_MEASUREMENT_ID, {
            'user_id': String(telegramId), // Привязываем ID пользователя
            'debug_mode': true // Включить для тестов (можно убрать в продакшене)
        });
        console.log(`GA initialized for user: ${telegramId}`);
    } else {
        // Если запускаем в браузере без Телеграма
        gtag('config', GA_MEASUREMENT_ID);
        console.log('GA initialized (no user id)');
    }
}

// Запускаем инициализацию
initAnalytics();

// 3. Вспомогательная функция для отправки событий (удобная обертка)
// Используй её в других файлах: trackEvent('lesson_start', { lesson_id: 'b1' });
window.trackEvent = function(eventName, params = {}) {
    gtag('event', eventName, params);
    console.log(`📡 Event sent: ${eventName}`, params);
};