const axios = require('axios');

exports.handler = async function(event, context) {
    const BOT_TOKEN = '6974834378:AAEckz1HNBH9RiKvz-uqM2Upcdi7KKjAwe8'; // Твой токен бота
    const CHAT_ID = '-1002123915695'; // Твой ID группы

    let userId;

    // Проверка на наличие тела запроса
    try {
        const body = event.body ? JSON.parse(event.body) : {};
        userId = body.userId;
    } catch (error) {
        return {
            statusCode: 400,
            headers: {
                'Access-Control-Allow-Origin': '*', // Разрешаем запросы с любых доменов
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ error: 'Invalid request body' })
        };
    }

    if (!userId) {
        return {
            statusCode: 400,
            headers: {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
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

        return {
            statusCode: 200,
            headers: {
                'Access-Control-Allow-Origin': '*', // CORS
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ isMember: chatMember && ['member', 'administrator', 'creator'].includes(chatMember.status) })
        };

    } catch (error) {
        return {
            statusCode: 500,
            headers: {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ error: 'Ошибка при проверке пользователя' })
        };
    }
};
