from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Создаем кнопки
btn_clear = KeyboardButton(text="🔄 Сбросить чат")
btn_profile = KeyboardButton(text="👤 Профиль")
btn_help = KeyboardButton(text="🆘 Справка")

# Собираем их в клавиатуру
# resize_keyboard=True — чтобы кнопки были маленькими и аккуратными
# input_field_placeholder — подсказка в строке ввода
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [btn_clear, btn_profile], # Первый ряд (две кнопки)
        [btn_help]                # Второй ряд (одна кнопка во всю ширину)
    ],
    resize_keyboard=True,
    input_field_placeholder="Напиши что-нибудь на английском..."
)