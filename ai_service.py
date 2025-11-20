from openai import AsyncOpenAI
from config import OPENAI_API_KEY, MODEL_NAME

# Настраиваем клиента на адрес OpenRouter
client = AsyncOpenAI(
    api_key=OPENAI_API_KEY,
    base_url="https://openrouter.ai/api/v1", # 👈 Важная строчка! Иначе он постучится в OpenAI и получит бан.
)

async def get_ai_service(messages_history: list):
    try:
        # Делаем запрос
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages_history,
        )

        # Вытаскиваем текст ответа
        return response.choices[0].message.content

    except Exception as e:
        print(f"Ошибка AI: {e}")
        return "Извини, мои нейронные связи сейчас перегружены. Попробуй позже."