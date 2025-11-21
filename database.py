import aiosqlite

async def create_table():
    async with aiosqlite.connect('english_bot.db') as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                reg_date TEXT,
                messages_count INTEGER DEFAULT 0
            )
        ''')
        await db.commit()
        

# Функция добавления юзера
async def add_user(user_id, username):
    # Подключаемся к файлу базы (он сам создастся, если нет)
    async with aiosqlite.connect('english_bot.db') as db:
        # Выполняем наш SQL с защитой от дублей
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, messages_count) VALUES (?, ?, 0)",
            (user_id, username) # Вот тут Python подставляет данные вместо вопросов
        )
        # ОБЯЗАТЕЛЬНО сохраняем изменения
        await db.commit()

# 👇 НОВАЯ ФУНКЦИЯ: Увеличить счетчик сообщений
async def increment_counter(user_id):
    async with aiosqlite.connect('english_bot.db') as db:
        await db.execute(
            "UPDATE users SET messages_count = messages_count + 1 WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()

# 👇 НОВАЯ ФУНКЦИЯ: Получить статистику
async def get_user_stats(user_id):
    async with aiosqlite.connect('english_bot.db') as db:
        async with db.execute("SELECT messages_count FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return row[0] # Возвращаем число (например, 5)
            return 0