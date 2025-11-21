import asyncio
import logging
import json # Нужно для красивого вывода ошибок
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from config import BOT_TOKEN
from ai_service import get_ai_service # Импортируем функцию общения с AI
from keyboards import main_kb
import os
import speech_recognition as sr
from aiogram import F
from pydub import AudioSegment
from gtts import gTTS  # 👈 NEW: Библиотека озвучки
from aiogram.types import FSInputFile # 👈 NEW: Для отправки файлов
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database import create_table, add_user, get_user_stats, get_inactive_users, increment_counter
import os
from groq import AsyncGroq # 👈 НОВАЯ БИБЛИОТЕКА
from config import GROQ_API_KEY # Не забудь добавить это в config.py!

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Инициализация
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# 🧠 ОПЕРАТИВНАЯ ПАМЯТЬ
# Словарь, где ключ - это ID юзера, а значение - список сообщений
# Пример: { 12345: [{"role": "user", "content": "Hi"}] }
user_histories = {}

# ⚙️ СИСТЕМНЫЙ ПРОМПТ 
SYSTEM_PROMPT = """
Ты — эмпатичный репетитор английского языка.
1. Общайся на английском.
2. Если юзер делает ошибку — ТВОЙ ОТВЕТ ДОЛЖЕН НАЧИНАТЬСЯ С БЛОКА ИСПРАВЛЕНИЯ, где ты показываешь ошибку и правильный вариант, \n
исправляй не только ошибки в словах, но и в построении предложения.
   Используй строго такой формат:
   🏁 <b>Correction:</b> <s>Текст с ошибкой</s> -> <b>Правильный текст</b>
   ПОСЛЕ блока исправления ОБЯЗАТЕЛЬНО поставь разделитель: |||
   Пример:
   🏁 <b>Correction:</b> ... ||| Oh, I see! Let's talk about it.
   
3. Если ошибок нет — просто поддерживай диалог.
4. ВАЖНО: Делай перенос строки после исправления
5. Ответь на русском языке, если пользователь попросил что-то объяснить, но после ВСЕГДА предлагай продолжить диалог на английском.
6. НЕ ЗАБЫВАЙ про флажочек перед словом Correction.
7. Используй HTML-теги: <b>bold</b> для правильного варианта, <s>strike</s> для зачеркивания ошибки.
"""

# --- ХЭНДЛЕРЫ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name # 1. Достаем имя
    
    # 2. Передаем ТРИ аргумента
    await add_user(user_id, message.from_user.username, user_name)
    
    # 2. Очищаем/Создаем историю для этого юзера
    user_histories[user_id] = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]
    
    await message.answer(
        f"Привет, {user_name}! Я твой ИИ-репетитор по английскому. 🇬🇧\n\n"
        f"Мы можем общаться голосом или текстом. Я буду исправлять твои ошибки.\n"
        f"Просто напиши или скажи мне что-нибудь на английском!",
        reply_markup=main_kb 
    )
    
@dp.message(Command("clear"))
async def cmd_clear(message: types.Message):
    """Команда для сброса контекста, если бот затупил"""
    user_id = message.from_user.id
    user_histories[user_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    await message.answer("🔄 История очищена, можем начать сначала!")

# --- НОВЫЙ ХЭНДЛЕР ДЛЯ ГОЛОСОВЫХ ---
@dp.message(F.voice)
async def voice_handler(message: types.Message):
    user_id = message.from_user.id
    
    # 1. Защита от потери памяти
    if user_id not in user_histories:
        personal_prompt = SYSTEM_PROMPT + f"\nUser's name is: {message.from_user.first_name}."
        user_histories[user_id] = [{"role": "system", "content": personal_prompt}]

    status_msg = await message.reply("🎧 Listening (Whisper V3)...")
    
    # Мы сохраним файл как .m4a (Groq отлично его понимает)
    filename = f"voice_{user_id}.m4a" 

    try:
        # 2. Скачиваем файл
        file_id = message.voice.file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path
        await bot.download_file(file_path, filename)

        # 3. ОТПРАВЛЯЕМ В GROQ (WHISPER)
        client = AsyncGroq(api_key=GROQ_API_KEY)
        
        with open(filename, "rb") as file:
            transcription = await client.audio.transcriptions.create(
                file=(filename, file.read()),
                model="whisper-large-v3", # Самая мощная модель
                prompt="Context: English lesson.", # Подсказка нейросети
                response_format="json",
                language="en", # Принудительно английский
                temperature=0.0
            )
        
        user_text = transcription.text

        # 4. Показываем результат (Идеальный текст с запятыми!)
        await status_msg.edit_text(f"🗣 <b>You said:</b> {user_text}", parse_mode="HTML")

        # --- ДАЛЬШЕ ТВОЙ СТАРЫЙ КОД (AI + TTS) ---
        
        await increment_counter(user_id)
        
        # ... (код истории и Llama 3) ...
        user_histories[user_id].append({"role": "user", "content": user_text})
        if len(user_histories[user_id]) > 11:
            user_histories[user_id] = [user_histories[user_id][0]] + user_histories[user_id][-10:]
            
        ai_answer = await get_ai_service(user_histories[user_id])
        user_histories[user_id].append({"role": "assistant", "content": ai_answer})

        # Отправляем текст
        clean_answer = ai_answer.replace("|||", "")
        await message.answer(clean_answer, parse_mode="HTML")

        # Озвучка (TTS)
        await bot.send_chat_action(chat_id=message.chat.id, action="record_voice")
        
        if "|||" in ai_answer:
            text_for_voice = ai_answer.split("|||")[1]
        else:
            text_for_voice = ai_answer

        import re
        clean_voice_text = re.sub(r'<[^>]+>', '', text_for_voice).strip()

        if clean_voice_text:
            reply_audio_filename = f"reply_{user_id}.mp3"
            tts = gTTS(text=clean_voice_text, lang='en')
            tts.save(reply_audio_filename)
            voice_file = FSInputFile(reply_audio_filename)
            await message.answer_voice(voice_file)
            os.remove(reply_audio_filename)

    except Exception as e:
        await status_msg.edit_text(f"Error: {e}")
    
    finally:
        if os.path.exists(filename):
            os.remove(filename)

@dp.message() 
async def chat_handler(message: types.Message):
    """Обрабатывает ВСЕ остальные сообщения (текст)"""
    user_id = message.from_user.id
    user_text = message.text
    
    if user_text == "🔄 Сбросить чат":
        # Логика сброса (копируем из cmd_clear)
        personal_prompt = SYSTEM_PROMPT + f"\nUser's name is: {message.from_user.first_name}."
        user_histories[user_id] = [{"role": "system", "content": personal_prompt}]
        await message.answer("История очищена, можем начать сначала!", reply_markup=main_kb)
        return # 👈 ВАЖНО: Выходим из функции, чтобы не отправлять это в AI

    elif user_text == "👤 Профиль":
        # 👇 ТЫ ПРОПУСТИЛ ВОТ ЭТУ СТРОЧКУ 👇
        # Мы создаем переменную total_msgs и кладем туда результат из базы
        total_msgs = await get_user_stats(user_id) 
        
        # И только ТЕПЕРЬ мы можем её использовать внутри f-строки:
        profile_text = (
            f"👤 <b>Твой профиль</b>\n\n"
            f"Имя: {message.from_user.first_name}\n"
            f"Всего сообщений: <b>{total_msgs}</b> 🔥\n\n" # <--- Здесь она подставляется
            f"<i>Продолжай практиковаться!</i>"
        )
        await message.answer(profile_text, parse_mode="HTML")
        return

    elif user_text == "🆘 Справка":
        help_text = (
            "🤖 <b>Как пользоваться ботом:</b>\n\n"
            "1. 🗣 <b>Голосовые:</b> Отправь мне голосовое сообщение. Я послушаю произношение, исправлю ошибки и отвечу голосом!\n"
            "2. ✍️ <b>Текст:</b> Просто пиши на английском. Я поддержу диалог и укажу на грамматику.\n"
            "3. 🔄 <b>Новая тема:</b> Нажми эту кнопку, если хочешь сменить тему разговора.\n\n"
            "<i>Я использую искусственный интеллект (GPT4o-mini), поэтому иногда могу ошибаться. Учимся вместе!</i>"
        )
        await message.answer(help_text, parse_mode="HTML")
        return
    
    await increment_counter(user_id)
    
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
    clean_text = ai_answer.replace("|||", "")
    await message.answer(clean_text, parse_mode="HTML")
    
async def send_daily_reminders(bot: Bot):
    # Ищем тех, кто молчал 24 часа (86400 секунд)
    # Для теста поставь 10 секунд, чтобы проверить сразу!
    inactive_users = await get_inactive_users(86400) 
    
    for user_id, first_name in inactive_users:
        try:
            await bot.send_message(
                user_id,
                f"Привет, {first_name}! 👋\n\n"
                f"Кажется, ты давно не практиковался в английском! Давай ко мне, пообщаемся, за одно полезным делом займемся 🇬🇧\n"
            )
            # После отправки напоминания можно "обновить" активность, чтобы не спамить каждые 5 минут
            # Но лучше оставить как есть, пусть пишет сам.
            print(f"Reminded user {user_id}")
        except Exception as e:
            print(f"Failed to remind user {user_id}: {e}")

# --- ЗАПУСК ---
async def main():
    # 1. СНАЧАЛА СОЗДАЕМ ТАБЛИЦУ (Покупаем яйца)
    await create_table() 
    
    # 2. ПОТОМ ЗАПУСКАЕМ ПЛАНИРОВЩИК (Включаем плиту)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_daily_reminders, 'cron', hour=19, minute=00, args=(bot,)) # Для теста 30 сек
    scheduler.start()

    print("Bot started with Scheduler!")

    # 3. В КОНЦЕ ЗАПУСКАЕМ БОТА (Жарим)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())