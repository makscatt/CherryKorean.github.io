const axios = require('axios');

exports.handler = async function(event, context) {
    const BOT_TOKEN = '6974834378:AAEckz1HNBH9RiKvz-uqM2Upcdi7KKjAwe8'; // Вставьте ваш токен бота
    const CHAT_ID = '-1002123915695'; // Вставьте ID группы/чата

    let userId;

    // Проверка на наличие тела запроса
    try {
        const body = event.body ? JSON.parse(event.body) : {};
        userId = body.userId;
    } catch (error) {
        return {
            statusCode: 400,
            body: JSON.stringify({ error: 'Invalid request body' })
        };
    }

    if (!userId) {
        return {
            statusCode: 400,
            body: JSON.stringify({ error: 'User ID not provided' })
        };
    }

    try {
        // Ваш запрос к Telegram API для проверки члена группы
        const response = await axios.get(`https://api.telegram.org/bot${BOT_TOKEN}/getChatMember`, {
            params: {
                chat_id: CHAT_ID,
                user_id: userId
            }
        });

        const chatMember = response.data.result;

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
            body: JSON.stringify({ error: 'Ошибка при проверке пользователя' })
        };
    }
};
