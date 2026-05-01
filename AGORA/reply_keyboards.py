from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="/price"), KeyboardButton(text="/metrics")],
        [KeyboardButton(text="/info"), KeyboardButton(text="/pricechart")],
        [KeyboardButton(text="/compare"), KeyboardButton(text="/subscribe")],
        [KeyboardButton(text="/get_timezone"), KeyboardButton(text="/set_timezone"),
         KeyboardButton(text="/help"), KeyboardButton(text="/add_to_portfolio (В РАЗРАБОТКЕ)"),
         KeyboardButton(text="/subscribe_chart"), KeyboardButton(text="/subscribe_price")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, persistent=True)