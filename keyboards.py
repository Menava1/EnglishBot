from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Создаем кнопки
btn_clear = KeyboardButton(text="🔄 Сбросить чат")
btn_profile = KeyboardButton(text="👤 Профиль")
btn_help = KeyboardButton(text="🆘 Справка")
btn_modes = KeyboardButton(text="🎭 Режимы")

# Собираем их в клавиатуру
# resize_keyboard=True — чтобы кнопки были маленькими и аккуратными
# input_field_placeholder — подсказка в строке ввода
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [btn_clear, btn_profile], # Первый ряд (две кнопки)
        [btn_modes, btn_help]                # Второй ряд (одна кнопка во всю ширину)
    ],
    resize_keyboard=True,
    input_field_placeholder="Жду сообщения..."
)

modes_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🦉 Просто Учитель (Default)", callback_data="mode_tutor")],
    [InlineKeyboardButton(text="✈️ Путешествия (Travel)", callback_data="mode_travel")],
    [InlineKeyboardButton(text="💼 Собеседование (Job Interview)", callback_data="mode_job")]
])