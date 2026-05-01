import asyncio
import yfinance as yf
from aiogram import Bot, Dispatcher, Router, F, types
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
import os
from io import BytesIO
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from servicesnstuff import *
from crud import upsert_user, update_timezone, get_user_timezone
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from states import AssetStates
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
import logging
from scheduler import *
from jobs import *
from inline_keyboards import *
from reply_keyboards import *

rtr = Router(name="user")

menu_keyboard = main_menu_keyboard()

@rtr.message(Command("get_timezone"))
async def cmd_get_timezone(message:Message):
    timezone = await get_user_timezone(user_id=message.chat.id)
    await message.answer(timezone)

@rtr.message(Command("start"))
async def cmd_start(message: Message):
    user = message.from_user
    chat_id = message.chat.id
    
    await upsert_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        chat_id=chat_id
    )

    await message.answer(
        f"👋 Привет, <b>{user.first_name}</b>!\n\n"
        "Я — финансовый помощник. Помогу следить за акциями, тикерами и портфелем.\n\n"
        "Используй команды:\n"
        "• /help — полный список команд\n"
        "• /menu — меню с кнопками",
        parse_mode="HTML",
        reply_markup=get_main_menu()
    )

@rtr.message(Command("set_timezone"))
async def cmd_set_timezone(message: Message, command: CommandObject, state: FSMContext):
    if command.args:
        ticker = command.args
        data_ticker = yf.Ticker(ticker).history(period="2d")
        close_today = data_ticker["Close"].iloc[-1]
        close_yesterday = data_ticker["Close"].iloc[-2]
        await message.answer("Цена финансового актива: " + str(close_today) + '\n' + "Изменение со вчера: " + str(close_today-close_yesterday))

    if not command.args:
        await message.answer("Введите свой часовой пояс в разнице от UTC (н.п. UTC+3, UTC-2)")
        await state.set_state(AssetStates.waiting_for_timezone)
        await state.update_data(action="set_timezone")



@rtr.message(Command("set_timezone_NEW"))
async def cmd_set_timezone(message: Message):
    try:
        tz_input = message.text.split(maxsplit=1)[1].strip()
        
        tz_info = parse_utc_offset(tz_input)
        if tz_info is None:
            await message.answer(
                "❌ Неправильный формат.\n\n"
                "Поддерживается:\n"
                "• UTC\n"
                "• UTC+3\n"
                "• UTC-5\n"
                "• UTC+03"
            )
            return

        # Сохраняем ориг строку для пользователz
        await update_timezone(message.from_user.id, tz_input)   # сохраняем "UTC+3"
        
        await message.answer(
            f"✅ Таймзона сохранена: {tz_input}\n"
            f"Смещение: {tz_info.utcoffset(None)} от UTC"
        )
        
    except Exception:
        await message.answer("Использование: /set_timezone UTC+3")




@rtr.message(Command("menu"))
async def menu(message: Message):
    await message.answer("Выберите действие:", reply_markup=get_main_menu())

@rtr.message(F.text == "Добавить актив")
async def add_asset(message: Message):
    await message.answer("Введите тикер, например: AAPL, TSLA, BTC-USD")

@rtr.message(AssetStates.waiting_for_timezone)
async def handle_timezone(message: Message, state: FSMContext):
    timezone = message.text
    data = await state.get_data()
    action = data.get("action")
    try:
        if action == "set_timezone":
            await update_timezone(
            user_id=message.chat.id,
            timezone=timezone
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка с часовым поясом {timezone}. Проверь правильность.")

@rtr.message(Command("price"))
async def price(message: Message, command: CommandObject, state: FSMContext):

    if command.args:
        ticker = command.args
        data_ticker = yf.Ticker(ticker).history(period="2d")
        close_today = data_ticker["Close"].iloc[-1]
        close_yesterday = data_ticker["Close"].iloc[-2]
        await message.answer("Цена финансового актива: " + str(close_today) + '\n' + "Изменение со вчера: " + str(close_today-close_yesterday))

    if not command.args:
        await message.reply("Отправь тикер (например: AAPL, TSLA, SBER):")
        await state.set_state(AssetStates.waiting_for_ticker)
        await state.update_data(action="price")

@rtr.message(AssetStates.waiting_for_ticker)
async def handle_1_ticker(message: Message, state: FSMContext):
    ticker = message.text.strip().upper()
    data = await state.get_data()
    action = data.get("action")
    try:
        if action == 'price':
            data_ticker = yf.Ticker(ticker).history(period="2d")
            close_today = data_ticker["Close"].iloc[-1]
            close_yesterday = data_ticker["Close"].iloc[-2]
            await message.answer("Цена финансового актива: " + str(close_today) + '\n' + "Изменение со вчера: " + str(close_today-close_yesterday))

        if action == "pricechart":

            chart_buf = create_price_chart(ticker)

            if chart_buf is None:
                await message.answer(f"Не удалось загрузить данные по {ticker}")
                return

            # подход 1
            await message.answer_photo(
                photo=types.BufferedInputFile(
                    file=chart_buf.getvalue(),          # именно .getvalue() → bytes (я хз бля файлы все дела)
                    filename=f"{ticker}_1y.png"
                ),
                caption="таблица"
            )

        if action == "metrics":

            metrics = {'open': yf.Ticker(ticker).info['open'], 
           'close': yf.Ticker(ticker).info['previousClose'], 
           'Low': yf.Ticker(ticker).info['dayLow'], 
           'High': yf.Ticker(ticker).info['dayHigh'], 
           'Market Cap': yf.Ticker(ticker).info['marketCap'], 
           'PE': yf.Ticker(ticker).info['trailingPE'], 
           'ROE': yf.Ticker(ticker).info['returnOnEquity'], 
           'Dividend Yield': yf.Ticker(ticker).info['dividendYield']}
            await message.answer(str(metrics))

        if action == "info":
            
            info = {
            'name': yf.Ticker(ticker).info['displayName'],
            'sector': yf.Ticker(ticker).info['sector'],
            'industry': yf.Ticker(ticker).info['industry'],
            '52-week high': yf.Ticker(ticker).info['fiftyTwoWeekHigh'],
            '52-week low': yf.Ticker(ticker).info['fiftyTwoWeekLow'],
            'volume': yf.Ticker(ticker).info['volume']
            }
            await message.answer(str(info))

    except Exception as e:
        await message.answer(f"❌ Ошибка с тикером {ticker}. Проверь правильность.")

    finally:
        await state.clear()   # обязательно 

@rtr.message(AssetStates.waiting_for_two_tickers)
async def handle_2_tickers(message: Message, state: FSMContext):
    parts = message.text.strip().upper().split()
    ticker1 = parts[0]
    ticker2 = parts[1]
    print(ticker1, '\n', ticker2, '\n', "asdasd")
    data = await state.get_data()
    action = data.get("action")
    try:
        if action == "compare":

            chart_buf = pricechart_comp(ticker1, ticker2)

            if chart_buf is None:
                await message.answer(f"Не удалось загрузить данные по {ticker1} и {ticker2}")
                return

            await message.answer_photo(
                photo=types.BufferedInputFile(
                    file=chart_buf.getvalue(),          # именно .getvalue() → bytes (я хз бля файлы все дела)
                    filename=f"{ticker1}_{ticker2}.png"
                ),
                caption=f"График {ticker1} и {ticker2} за год"
            )

            await message.answer(f"сравнение метрик:")

            chart_buf = totable(ticker1, ticker2)

            file = types.BufferedInputFile(
            chart_buf.getvalue(), 
            filename=f"{ticker1}_vs_{ticker2}_comparison.xlsx"
            )
            
            await message.answer_document(
                document=file,
                caption=f"Сравнение {ticker1} и {ticker2}"
            )

    except Exception as e:
        await message.answer(f"❌ Ошибка с тикерами {ticker1} и {ticker2}. Проверь правильность.")

    finally:
        await state.clear()   # <---- обязательно 

@rtr.message(Command("plottest"))
async def send_plot(message: types.Message):
    photo_bytes = create_plot()
    
    await message.answer_photo(
        photo=types.BufferedInputFile(
            file=photo_bytes.read(),
            filename="график.png"          # Telegram любит расширение
        ),
        caption="Вот твой график sin(x) и cos(x) 🎨"
    )

@rtr.message(Command("pricechart"))
async def cmd_price(message: Message, command: CommandObject, state: FSMContext):
    if command.args:

        parts = command.args.split()
        ticker = parts[0].upper()
        period = parts[1] if len(parts) > 1 else "1y"

        # Шпора на периоды yfinance: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
        chart_buf = create_price_chart(ticker, period)

        if chart_buf is None:
            await message.answer(f"Не удалось загрузить данные по {ticker}")
            return

        # подход 1
        await message.answer_photo(
            photo=types.BufferedInputFile(
                file=chart_buf.getvalue(),          # именно .getvalue() → bytes (я хз бля файлы все дела)
                filename=f"{ticker}_{period}.png"
            ),
            caption="таблица"
        )

    else:
        await message.reply("Отправь тикер (например: AAPL, TSLA, SBER):")
        await state.set_state(AssetStates.waiting_for_ticker)
        await state.update_data(action="pricechart")

@rtr.message(Command("compare"))
async def cmd_compare(message: Message, command: CommandObject, state: FSMContext):
    if command.args:

        parts = command.args.split()
        ticker1 = parts[0].upper()
        ticker2 = parts[1].upper()

        chart_buf = pricechart_comp(ticker1, ticker2)

        if chart_buf is None:
            await message.answer(f"Не удалось загрузить данные по {ticker1} и {ticker2}")
            return

        await message.answer_photo(
            photo=types.BufferedInputFile(
                file=chart_buf.getvalue(),          # именно .getvalue() → bytes (я хз бля файлы все дела)
                filename=f"{ticker1}_{ticker2}.png"
            ),
            caption=f"График {ticker1} и {ticker2} за год"
        )

        await message.answer(f"сравнение метрик:")

        chart_buf = totable(ticker1, ticker2)

        file = types.BufferedInputFile(
        chart_buf.getvalue(), 
        filename=f"{ticker1}_vs_{ticker2}_comparison.xlsx"
        )
        
        await message.answer_document(
            document=file,
            caption=f"Сравнение {ticker1} и {ticker2}"
        )

    else:
        await message.reply("Отправь тикеры (например: AAPL, TSLA, SBER) через пробел:")
        await state.set_state(AssetStates.waiting_for_two_tickers)
        await state.update_data(action="compare")

@rtr.message(Command("metrics"))
async def metriki(message: Message, command: CommandObject, state: FSMContext):
    if command.args:
        ticker = command.args
        metrics = {'open': yf.Ticker(ticker).info['open'], 
           'close': yf.Ticker(ticker).info['previousClose'], 
           'Low': yf.Ticker(ticker).info['dayLow'], 
           'High': yf.Ticker(ticker).info['dayHigh'], 
           'Market Cap': yf.Ticker(ticker).info['marketCap'], 
           'PE': yf.Ticker(ticker).info['trailingPE'], 
           'ROE': yf.Ticker(ticker).info['returnOnEquity'], 
           'Dividend Yield': yf.Ticker(ticker).info['dividendYield']}
        await message.answer(str(metrics))

    else:
        await message.reply("Отправь тикер (например: AAPL, TSLA, SBER):")
        await state.set_state(AssetStates.waiting_for_ticker)
        await state.update_data(action="metrics")

@rtr.message(Command("info"))
async def info(message: Message, command: CommandObject, state: FSMContext):
    if command.args:
        ticker = command.args
        info = {
            'name': yf.Ticker(ticker).info['displayName'],
            'sector': yf.Ticker(ticker).info['sector'],
            'industry': yf.Ticker(ticker).info['industry'],
            '52-week high': yf.Ticker(ticker).info['fiftyTwoWeekHigh'],
            '52-week low': yf.Ticker(ticker).info['fiftyTwoWeekLow'],
            'volume': yf.Ticker(ticker).info['volume']
            }
        await message.answer(str(info))

    else:
        await message.reply("Отправь тикер (например: AAPL, TSLA, SBER):")
        await state.set_state(AssetStates.waiting_for_ticker)
        await state.update_data(action="info")

@rtr.message(Command("subscribe_price"))
async def cmd_subscribe_price(message: Message, state: FSMContext):
    await message.answer("Отправь тикер и время в форме:\nAAPL 9:30\n(время по UTC пока)")
    await state.set_state(AssetStates.waiting_for_schedule_command_price)

@rtr.message(AssetStates.waiting_for_schedule_command_price)
async def process_schedule_command_price(message: Message, state: FSMContext, bot: Bot):
    # try:
        parts = message.text.strip().split()
        ticker = parts[0].upper()
        time_str = parts[1]

        timezone = await get_user_timezone(user_id=message.chat.id)

        hour, minute = map(int, time_str.split(':'))

        await add_daily_price_job(bot, message.chat.id, ticker, hour, minute, timezone)
        
        await message.answer(
            f"✅ Подписка создана!\n"
            f"Каждый день в {hour:02d}:{minute:02d} UTC я буду присылать цену {ticker}"
        )
    # except:
    #     await message.answer("❌ Неверный формат. Пример: AAPL 9:30")
    # finally:
    #     await state.clear()
        
@rtr.message(Command("subscribe_chart"))
async def cmd_subscribe_price(message: Message, state: FSMContext):
    await message.answer("Отправь тикер и время в форме:\nAAPL 9:30\n(время по UTC пока)")
    await state.set_state(AssetStates.waiting_for_schedule_command_chart)

@rtr.message(AssetStates.waiting_for_schedule_command_chart)
async def process_schedule_command_chart(message: Message, state: FSMContext, bot: Bot):
    # try:
        parts = message.text.strip().split()
        ticker = parts[0].upper()
        time_str = parts[1]

        timezone = await get_user_timezone(user_id=message.chat.id)

        hour, minute = map(int, time_str.split(':'))

        await add_daily_chart_job(bot, message.chat.id, ticker, hour, minute, timezone)
        
        await message.answer(
            f"✅ Подписка создана!\n"
            f"Каждый день в {hour:02d}:{minute:02d} UTC я буду присылать график {ticker}"
        )
    # except:
    #     await message.answer("❌ Неверный формат. Пример: AAPL 9:30")
    # finally:
    #     await state.clear()

# scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

# @rtr.message(Command("regulardata_price"))
# async def regulalrdata_price(message: Message, chat_id: int, command: CommandObject, state: FSMContext):
#     try:
#         price_data = await get_price(ticker)  # функция из services
#         current_price = price_data.get("close_today")

# @rtr.callback_query(F.data == "")
# async def show_subscribe_menu(callback: CallbackQuery):
#     await callback.message.edit_text("Что хочешь получать каждый день?", reply_markup=get_subscribe_menu())
#     await callback.answer()

# @rtr.message(Command("add_to_portfolio"))
# async def cmd_add_to_portfolio(message: Message, bot: Bot):
#     parts = message.text.strip().split()
#     ticker = parts[0].upper()
#     quantity = parts[1]

        
@rtr.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "🤖 <b>Финансовый Telegram-бот</b>\n\n"
        "Вот все доступные команды:\n\n"
        
        "📌 <b>Основные команды</b>\n"
        "/start — приветствие и регистрация\n"
        "/menu — показать главное меню с кнопками\n"
        "/help — показать это сообщение\n\n"
        
        "💰 <b>Информация по тикеру</b>\n"
        "/price [тикер] — текущая цена + изменение\n"
        "/metrics [тикер] — ключевые финансовые метрики\n"
        "/info [тикер] — информация о компании (сектор, отрасль и т.д.)\n"
        "/pricechart [тикер] [период] — график цены\n"
        "   Периоды: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max\n\n"
        
        "🔄 <b>Сравнение</b>\n"
        "/compare ТИКЕР1 ТИКЕР2 — график сравнения + таблица метрик\n\n"
        
        "🔔 <b>Подписки и уведомления</b>\n"
        "/subscribe_price ТИКЕР ЧАС:МИНУТА — ежедневная цена в указанное время\n"
        "/subscribe_chart ТИКЕР ЧАС:МИНУТА — ежедневный график цены\n\n"
        
        "🌍 <b>Таймзона</b>\n"
        "/set_timezone UTC+3 — установить свой часовой пояс\n"
        "/get_timezone — посмотреть текущую таймзону\n\n"
        
        "📁 <b>Портфель</b>\n"
        "/add_to_portfolio ТИКЕР КОЛИЧЕСТВО — добавить актив в портфель (В РАЗРАБОТКЕ)\n\n"
        
        "❗ <b>Важно:</b>\n"
        "• Если не указывать тикер после команды — бот попросит ввести его отдельно\n"
        "• Поддерживаются акции, ETF и криптовалюта (например: AAPL, SBER.ME, BTC-USD)\n"
        "• Время в подписках пока указывается по UTC\n"
    )

    await message.answer(help_text, parse_mode="HTML", disable_web_page_preview=True)