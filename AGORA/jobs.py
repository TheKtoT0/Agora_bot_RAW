import asyncio
import logging
from datetime import datetime
from aiogram import Bot, types
from servicesnstuff import *

logger = logging.getLogger(__name__)



async def send_daily_price(
    bot: Bot,
    chat_id: int,
    ticker: str,
    user_timezone: str | None = None
):
    """Ежедневная отправка цены актива"""
    try:

        tz_info = parse_utc_offset(user_timezone)
        if tz_info is None:
            tz_info = timezone.utc  # fallback

        now_local = datetime.now(tz_info)

        data = await get_price(ticker)  # функция из servicesnstuff
        
        text = (
            f"📅 <b>Ежедневный отчёт</b>\n"
            f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            f"🎯 Актив: <b>{ticker}</b>\n"
            f"💰 Цена: ${data.get('price', 0):.2f}\n"
            f"📈 Изменение: {data.get('change', 0):+.2f}%\n"
        )
        
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="HTML"
        )
        
        logger.info(f"Отправлена ежедневная цена {ticker} пользователю {chat_id}")
        
    except Exception as e:
        logger.error(f"Ошибка при отправке цены {ticker} для {chat_id}: {e}")
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=f"❌ Не удалось получить цену {ticker}. Попробуйте позже."
            )
        except:
            pass

async def send_daily_chart(
        bot: Bot,
        chat_id: int,
        ticker: str,
        user_timezone: str | None = None
):
    """Ежедневная отправка графика цены актива за день"""
    try:

        tz_info = parse_utc_offset(user_timezone)
        if tz_info is None:
            tz_info = timezone.utc  # fallback
        
        data = await get_pricechart_daily(ticker)

        text = (
            f"📅 <b>Ежедневный отчёт</b>\n"
            f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            f"🎯 Актив: <b>{ticker}</b>\n"
            f"💰 График:"
        )

        await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="HTML"
        )

        await bot.send_photo(
            chat_id=chat_id,
            photo=types.BufferedInputFile(
            file=data.getvalue(),          # именно .getvalue() → bytes (я хз бля файлы все дела)
            filename=f"{ticker}_1d.png"
            ),
            caption="таблица"
        )

        logger.info(f"Отправлен ежедневный график цены {ticker} пользователю {chat_id}")

    except Exception as e:
        logger.error(f"Ошибка при отправке графика {ticker} для {chat_id}: {e}")
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=f"❌ Не удалось получить график {ticker}. Попробуйте позже."
            )
        except:
            pass