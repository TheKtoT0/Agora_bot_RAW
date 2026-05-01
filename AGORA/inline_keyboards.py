from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню"""
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Цена актива", callback_data="price")
    builder.button(text="📬 Рассылка цен", callback_data="subscription_menu")
    builder.button(text="📈 График цены", callback_data="pricechart")
    builder.button(text="⚖️ Сравнение активов", callback_data="compare")
    builder.button(text="🧮 Ключевые метрики актива", callback_data="metrics")
    builder.button(text="📄 Общая информация об активе", callback_data="info")
    builder.adjust(2)
    return builder.as_markup()

def subscription_menu_keyboard(has_subscription: bool = False) -> InlineKeyboardMarkup:
    """Меню управления рассылкой"""
    builder = InlineKeyboardBuilder()
    if has_subscription:
        builder.button(text="✅ Подписка активна", callback_data="dummy")
        builder.button(text="⏹ Отключить рассылку", callback_data="unsubscribe")
    else:
        builder.button(text="🕒 Подписаться на рассылку", callback_data="subscribe")
    

    builder.button(text="🔙 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()
