const axios = require('axios');

exports.handler = async function(event, context) {
    const BOT_TOKEN = '6974834378:AAEckz1HNBH9RiKvz-uqM2Upcdi7KKjAwe8'; // Вставьте ваш токен бота
    const CHAT_ID = 'ВАШ_CHAT_ID'; // Вставьте ID группы/чата
    const userId = JSON.parse(event.body).userId;

    try {
        // Отправляем запрос к Telegram API, чтобы проверить, является ли пользователь членом группы
        const response = await axios.get(`https://api.telegram.org/bot${BOT_TOKEN}/getChatMember`, {
            params: {
                chat_id: CHAT_ID,
                user_id: userId
            }
        });

        const chatMember = response.data.result;

        // Проверяем статус пользователя
        if (chatMember && ['member', 'administrator', 'creator'].includes(chatMember.status)) {
            return {
                statusCode: 200,
                body: JSON.stringify({ isMember: true })
            };
        } else {
            return {
                statusCode: 200,
                body: JSON.stringify({ isMember: false })
            };
        }

    } catch (error) {
        console.error('Ошибка при проверке пользователя:', error);
        return {
            statusCode: 500,
            body: JSON.stringify({ isMember: false, error: 'Ошибка на сервере' })
        };
    }
};