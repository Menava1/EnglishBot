import aiosqlite
import time

# Имя базы. Оставляем v5, чтобы создалась новая структура.
DB_NAME = 'english_bot_v5.db' 

async def create_table():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT, 
                messages_count INTEGER DEFAULT 0,
                last_active INTEGER
            )
        ''')
        await db.commit()

async def add_user(user_id, username, first_name):
    async with aiosqlite.connect(DB_NAME) as db:
        current_time = int(time.time())
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name, messages_count, last_active) VALUES (?, ?, ?, 0, ?)",
            (user_id, username, first_name, current_time)
        )
        await db.commit()

# 👇 ВОТ ОНА! Вернули родную.
# Теперь она делает ДВА дела сразу: +1 сообщение и обновляет время.
async def increment_counter(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        current_time = int(time.time())
        await db.execute(
            "UPDATE users SET messages_count = messages_count + 1, last_active = ? WHERE user_id = ?",
            (current_time, user_id)
        )
        await db.commit()

async def get_user_stats(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT messages_count FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

async def get_inactive_users(interval_seconds):
    async with aiosqlite.connect(DB_NAME) as db:
        limit_time = int(time.time()) - interval_seconds
        async with db.execute("SELECT user_id, first_name FROM users WHERE last_active < ?", (limit_time,)) as cursor:
            return await cursor.fetchall()