import os
from dotenv import load_dotenv

# Загружаем переменные
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
model = os.getenv("MODEL_NAME")

print(f"--- ДИАГНОСТИКА ---")
# Проверяем, нашли ли мы ключ (показываем только первые 5 символов)
if api_key:
    print(f"✅ API Key найден: {api_key[:5]}...")
else:
    print(f"❌ API Key НЕ НАЙДЕН! (None)")

# Проверяем модель
if model:
    print(f"✅ Model Name найдена: '{model}'")
else:
    print(f"❌ Model Name НЕ НАЙДЕНА! (None)")
print(f"-------------------")