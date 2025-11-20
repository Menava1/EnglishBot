import asyncio
import logging
import json # Нужно для красивого вывода ошибок
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from config import BOT_TOKEN
from database import create_table, add_user
from ai_service import get_ai_service # Импортируем функцию общения с AI

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Инициализация
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# 🧠 ОПЕРАТИВНАЯ ПАМЯТЬ
# Словарь, где ключ - это ID юзера, а значение - список сообщений
# Пример: { 12345: [{"role": "user", "content": "Hi"}] }
user_histories = {}

# ⚙️ СИСТЕМНЫЙ ПРОМПТ (Твой "Учитель")
SYSTEM_PROMPT = """
Ты — эмпатичный репетитор английского языка.
1. Общайся на английском.
2. Если юзер делает ошибку — сначала исправь её (формат: 🏁 **Correction:** ...), потом ответь.
3. Если ошибок нет — просто поддерживай диалог.
"""

# --- ХЭНДЛЕРЫ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    # 1. Сохраняем в БД
    await add_user(user_id, message.from_user.username)
    
    # 2. Очищаем/Создаем историю для этого юзера
    user_histories[user_id] = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]
    
    await message.answer(f"Hello, {user_name}! I am your English Tutor. Let's talk! (Write something in English)")

@dp.message(Command("clear"))
async def cmd_clear(message: types.Message):
    """Команда для сброса контекста, если бот затупил"""
    user_id = message.from_user.id
    user_histories[user_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    await message.answer("🔄 Context cleared. We can start a new topic.")

@dp.message() 
async def chat_handler(message: types.Message):
    """Обрабатывает ВСЕ остальные сообщения (текст)"""
    user_id = message.from_user.id
    user_text = message.text
    
    # Если юзер пишет первый раз без /start, создаем ему историю
    if user_id not in user_histories:
        user_histories[user_id] = [{"role": "system", "content": SYSTEM_PROMPT}]

    # 1. Показываем юзеру "печатает..." (чтобы он знал, что бот думает)
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    # 2. Добавляем сообщение юзера в память
    user_histories[user_id].append({"role": "user", "content": user_text})
    if len(user_histories[user_id]) > 11:
        user_histories[user_id] = [user_histories[user_id][0]] + user_histories[user_id][-10:]
    # 3. Получаем ответ от AI
    ai_answer = await get_ai_service(user_histories[user_id])

    user_histories[user_id].append({"role": "assistant", "content": ai_answer})

    await message.answer(ai_answer)
    


# --- ЗАПУСК ---
async def main():
    await create_table()
    print("Bot started!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())