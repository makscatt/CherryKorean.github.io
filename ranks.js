const RANKS = [
    { id: 1, name: "Турист", minXP: 0, icon: "🎒" },
    { id: 2, name: "Новичок", minXP: 500, icon: "🐣" },
    { id: 3, name: "Ученик", minXP: 2000, icon: "📚" },
    { id: 4, name: "Фанат", minXP: 5000, icon: "🎧" },
    { id: 5, name: "Дорамщик", minXP: 12000, icon: "📺" },
    { id: 6, name: "Трейни", minXP: 25000, icon: "🎤" },
    { id: 7, name: "Дебютант", minXP: 50000, icon: "🎬" },
    { id: 8, name: "Айдол", minXP: 100000, icon: "✨" },
    { id: 9, name: "Суперзвезда", minXP: 200000, icon: "🌟" },
    { id: 10, name: "Король Кимчи", minXP: 500000, icon: "👑" }
];

function getRankInfo(xp) {
    xp = parseInt(xp) || 0;
    let current = RANKS[0];
    let next = null;

    for (let i = RANKS.length - 1; i >= 0; i--) {
        if (xp >= RANKS[i].minXP) {
            current = RANKS[i];
            next = RANKS[i + 1] || null; // Если следующего нет, next = null
            break;
        }
    }

    // Если достигли максимума, прогресс 100%
    let progress = 100;
    if (next) {
        progress = Math.min(100, Math.floor(((xp - current.minXP) / (next.minXP - current.minXP)) * 100));
    }

    return {
        current: current,
        next: next,
        progress: progress,
        xp: xp,
        isMax: !next // Флаг, что достигнут потолок
    };
}
function checkAndSaveRankUp(currentXp) {
    const rankInfo = getRankInfo(currentXp);
    const currentRankId = rankInfo.current.id;
    
    // Получаем ID ранга, который пользователь уже "принял" (видел поздравление)
    // Если нет, считаем, что он был на 1 уровне
    const lastAckRankId = parseInt(localStorage.getItem('lastAckRankId')) || 1;

    // Если текущий ранг выше последнего принятого
    if (currentRankId > lastAckRankId) {
        // Сохраняем объект ранга в "очередь" на показ
        localStorage.setItem('pendingRankReward', JSON.stringify(rankInfo.current));
    }
}