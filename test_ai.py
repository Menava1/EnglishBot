import asyncio
from ai_service import get_ai_response

async def test():
    print("Отправляю запрос в нейросеть...")
    answer = await get_ai_response("Hello! How are you?")
    print(f"Ответ AI: {answer}")

if __name__ == "__main__":
    asyncio.run(test())