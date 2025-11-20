import aiosqlite

async def create_table():
    async with aiosqlite.connect('english_bot.db') as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                reg_date TEXT
            )
        ''')
        await db.commit()

# Функция добавления юзера
async def add_user(user_id, username):
    # Подключаемся к файлу базы (он сам создастся, если нет)
    async with aiosqlite.connect('english_bot.db') as db:
        # Выполняем наш SQL с защитой от дублей
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
            (user_id, username) # Вот тут Python подставляет данные вместо вопросов
        )
        # ОБЯЗАТЕЛЬНО сохраняем изменения
        await db.commit()