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

my_token = "8184110295:AAFo6DkbMkCVlYG1kZMQNHR3zXpzB2WJYec"
button_new_asset = KeyboardButton(text="Добавить актив")
builder = ReplyKeyboardBuilder()
builder.add(button_new_asset)
builder.adjust(1)
# keyboard = builder.as_markup(resize_keyboard=True)
keyboard = ReplyKeyboardMarkup(keyboard=[[button_new_asset]], resize_keyboard=True)

def create_plot():
    fig, ax = plt.subplots(figsize=(8, 5), dpi=100)
    
    x = np.linspace(0, 10, 500)
    y1 = np.sin(x)
    y2 = np.cos(x)
    
    ax.plot(x, y1, label='sin(x)', linewidth=2)
    ax.plot(x, y2, label='cos(x)', linewidth=2)
    ax.set_title("Простой график sin и cos", fontsize=14)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # Сохраняем в память (не на диск!)
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=120, transparent=True)
    buf.seek(0)
    plt.close(fig)          # очень важно закрывать фигуру!
    
    return buf

def pricechart_comp(ticker1: str, ticker2: str, period: str = "1y", style: str = "classic"):
    try:
        period = period.lower().strip()
        if period not in {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"}:
            period = "1y"  # или raise ValueError("Неверный период")

        df1 = yf.download(ticker1, period=period, progress=False, threads=False)
        df2 = yf.download(ticker2, period=period, progress=False, threads=False)

        if df1.empty or len(df1) < 2:
            return None
        
        if df2.empty or len(df2) < 2:
            return None

        plt.style.use(style)
        fig, ax = plt.subplots(figsize=(10, 6), dpi=100)

        close1 = df1['Close'].to_numpy().ravel()
        close2 = df2['Close'].to_numpy().ravel()
        print("ну пока все ок")
        ax.plot(df1.index, close1, label='Close', color='#2962ff', linewidth=2)
        ax.fill_between(df1.index, close1, alpha=0.08, color='#2962ff')

        ax.plot(df2.index, close2, label='Close', color="#ff2929", linewidth=2)
        ax.fill_between(df2.index, close2, alpha=0.08, color="#ff2929")

        ax.set_title(f"{ticker2.upper()} and {ticker1.upper()}  |  {period}", fontsize=16, pad=15)
        ax.set_xlabel("Дата")
        ax.set_ylabel("Цена (USD)")
        ax.grid(True, alpha=0.3, linestyle="--")
        ax.legend()

        # Важно: tight_layout помогает избежать обрезки подписей
        fig.tight_layout()

        buf = BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.15)
        buf.seek(0)

        plt.close(fig)          # ← обязательно освобождаем память!

        return buf

    except Exception as e:
        print(f"Ошибка построения графика {ticker1}: {e}")
        return None

def create_price_chart(ticker: str, period: str = "1y", style: str = "classic"):
    try:
        period = period.lower().strip()
        if period not in {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"}:
            period = "1y"  # или raise ValueError("Неверный период")

        df = yf.download(ticker, period=period, progress=False, threads=False)
        
        if df.empty or len(df) < 2:
            return None

        plt.style.use(style)
        fig, ax = plt.subplots(figsize=(10, 6), dpi=100)

        close = df['Close'].to_numpy().ravel()

        ax.plot(df.index, close, label='Close', color='#2962ff', linewidth=2)
        ax.fill_between(df.index, close, alpha=0.08, color='#2962ff')

        ax.set_title(f"{ticker.upper()}  |  {period}", fontsize=16, pad=15)
        ax.set_xlabel("Дата")
        ax.set_ylabel("Цена (USD)")
        ax.grid(True, alpha=0.3, linestyle="--")
        ax.legend()

        # Важно: tight_layout помогает избежать обрезки подписей
        fig.tight_layout()

        buf = BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)

        plt.close(fig)          # ← обязательно освобождаем память!

        return buf

    except Exception as e:
        print(f"Ошибка построения графика {ticker}: {e}")
        return None

def create_metrics_chart(ticker: str, period: str = "1y", style: str = "classic"):
    try:
        period = period.lower().strip()
        if period not in {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"}:
            period = "1y"  # или raise ValueError("Неверный период")

        df = yf.info()

    except Exception as e:
        print(f"Ошибка построения графика {ticker}: {e}")
        return None

def totable(ticker1: str, ticker2: str):
    ticker1 = yf.Ticker(ticker1)
    ticker2 = yf.Ticker(ticker2)

    metrics_comp = {'open': [ticker1.info['open'], ticker2.info['open']],
           'close': [ticker1.info['previousClose'], ticker2.info['previousClose']],
           'Low': [ticker1.info['dayLow'], ticker2.info['dayLow']],
           'High': [ticker1.info['dayHigh'], ticker2.info['dayHigh']],
           'Market Cap': [ticker1.info['marketCap'], ticker2.info['marketCap']],
           'PE': [ticker1.info['trailingPE'], ticker2.info['trailingPE']],
           'ROE': [ticker1.info['returnOnEquity'], ticker2.info['returnOnEquity']],
           'Dividend Yield': [ticker1.info['dividendYield'], ticker2.info['dividendYield']]}

    metrics_comp = pd.DataFrame(metrics_comp)

    fig, ax = plt.subplots(figsize=(10, 10), dpi=100, facecolor="none")
    ax.axis('off')

    table = ax.table(cellText=metrics_comp.values, colLabels=metrics_comp.columns, loc='center')

    buf = BytesIO()
    fig.savefig(buf)
    buf.seek(0)

    plt.close()
    return buf


botik = Bot(token = my_token)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message:Message):
    await message.answer('Привет, я финансовый бот', reply_markup=keyboard)

@dp.message(F.text == "Добавить актив")
async def add_asset(message: Message):
    await message.answer("Введите тикер, например: AAPL, TSLA, BTC-USD")

@dp.message(Command("price"))
async def price(message: Message, command: CommandObject):
    ticker = command.args
    data = yf.Ticker(ticker).history(period="2d")
    close_today = data["Close"].iloc[-1]
    close_yesterday = data["Close"].iloc[-2]
    await message.answer("Цена финансового актива: " + str(close_today) + '\n' + "Изменение со вчера: " + str(close_today-close_yesterday))

@dp.message(Command("plottest"))
async def send_plot(message: types.Message):
    photo_bytes = create_plot()
    
    await message.answer_photo(
        photo=types.BufferedInputFile(
            file=photo_bytes.read(),
            filename="график.png"          # Telegram любит расширение
        ),
        caption="Вот твой график sin(x) и cos(x) 🎨"
    )

@dp.message(Command("pricechart"))
async def cmd_price(message: Message, command: CommandObject):
    if not command.args:
        await message.answer("введи тикер еблан")
        return

    parts = command.args.split()
    ticker = parts[0].upper()
    period = parts[1] if len(parts) > 1 else "1y"

    # Поддерживаемые периоды yfinance: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
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

@dp.message(Command("compare"))
async def cmd_compare(message: Message, command: CommandObject):
    if not command.args:
        await message.answer("введи тикеры еблан")
        return
    
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

    await message.answer_photo(
        photo=types.BufferedInputFile(
            file=chart_buf.getvalue(),          # именно .getvalue() → bytes (я хз бля файлы все дела)
            filename=f"{ticker1}_{ticker2}.png"
        ),
        caption=f"График {ticker1} и {ticker2} за год"
    )

@dp.message(Command("metrics"))
async def metriki(message: Message, command: CommandObject):
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

@dp.message(Command("info"))
async def metriki(message: Message, command: CommandObject):
    ticker = command.args
    info = {
        'name': yf.Ticker(ticker).info['displayName'],
        'sector': yf.Ticker(ticker).info['sector'],
        'industry': yf.Ticker(ticker).info['industry'],
        '52-week high': yf.Ticker(ticker).info['fiftyTwoWeekHigh'],
        '52-week low': yf.Ticker(ticker).info['fiftyTwoWeekLow'],
        'volume': yf.Ticker(ticker).infop['volume']
        }
    await message.answer(str(info))

# @dp.message(Command("metricschart"))
# async def metricschart(message: Message, command: CommandObject):


async def main():
    await dp.start_polling(botik)
if __name__ == "__main__":
    asyncio.run(main())