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
from datetime import datetime, timezone, timedelta
import re
from pandas import ExcelWriter



def parse_utc_offset(timezone_str: str | None) -> timezone | None:
    """
    Парсит строки вида:
        "UTC+3", "UTC-5", "UTC+0", "UTC+05:30", "UTC-4"
    и возвращает datetime.timezone с правильным offset.
    Если не удалось распарсить — возвращает None (fallback на UTC).
    """
    if not timezone_str:
        return None

    # Нормализуем строкИ (убираем пробелы, приводим к верхнему регистру)
    timezone_str = str(timezone_str)
    tz = timezone_str.strip().upper().replace(" ", "")

    # Регулярка ловит UTC±N или UTC±HH:MM
    match = re.match(r"UTC([+-])(\d{1,2})(?::(\d{2}))?$", tz)
    if not match:
        return None

    sign = match.group(1)        
    hours = int(match.group(2))
    minutes = int(match.group(3)) if match.group(3) else 0

    offset_minutes = hours * 60 + minutes
    if sign == "-":
        offset_minutes = -offset_minutes

    return timezone(timedelta(minutes=offset_minutes))

print(parse_utc_offset("UTC+3"))

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
    
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=120, transparent=True)
    buf.seek(0)
    plt.close(fig)          # ВАЖНОО
    
    return buf

async def get_price(ticker: str):
    data_ticker = yf.Ticker(ticker).history(period="2d")
    close_today = data_ticker["Close"].iloc[-1]
    close_yesterday = data_ticker["Close"].iloc[-2]
    open_today = data_ticker["Close"].iloc[-1]
    open_yesterday = data_ticker["Close"].iloc[-2]
    # return ("Цена финансового актива: " + str(close_today) + '\n' + "Изменение со вчера: " + str(close_today-close_yesterday))
    return {
        "price": close_today,
        "change": close_today-close_yesterday,
        "close today": close_today,
        "close yesterday": close_yesterday,
        "open today": open_today,
        "open yesterday": open_yesterday
        # ... остальные метрики
    }

async def get_pricechart_daily(ticker: str, style: str = "classic"):
    data_ticker = yf.Ticker(ticker).history(period="2d")
    period = "2d"
    df = yf.download(ticker, period=period, progress=False, threads=False)
        
    if df.empty or len(df) < 2:
        return None

    fig, ax = plt.subplots(figsize=(10, 6), dpi=100)

    try:
        period = period.lower().strip()
        if period not in {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"}:
            period = "2d"  

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

        fig.tight_layout()

        buf = BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)

        plt.close(fig)          # ← обязательно освобождаем память!

        return buf
    
    except Exception as e:
        print(f"Ошибка построения графика {ticker}: {e}")
        return None

get_pricechart_daily("AAPL")

def pricechart_comp(ticker1: str, ticker2: str, period: str = "1y", style: str = "classic"):
    try:
        period = period.lower().strip()
        if period not in {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"}:
            period = "1y"  # 

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

        fig.tight_layout()

        buf = BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.15)
        buf.seek(0)

        plt.close(fig)          

        return buf

    except Exception as e:
        print(f"Ошибка построения графика {ticker1}: {e}")
        return None

def create_price_chart(ticker: str, period: str = "1y", style: str = "classic"):
    try:
        period = period.lower().strip()
        if period not in {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"}:
            period = "1y"  

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

        fig.tight_layout()

        buf = BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)

        plt.close(fig)          

        return buf

    except Exception as e:
        print(f"Ошибка построения графика {ticker}: {e}")
        return None

def create_metrics_chart(ticker: str, period: str = "1y", style: str = "classic"):
    try:
        period = period.lower().strip()
        if period not in {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"}:
            period = "1y"

        df = yf.info()

    except Exception as e:
        print(f"Ошибка построения графика {ticker}: {e}")
        return None

def totable(ticker1: str, ticker2: str):
    t1 = yf.Ticker(ticker1)
    t2 = yf.Ticker(ticker2)

    data = {
        'Metric': ['Open', 'Previous Close', 'Day Low', 'Day High', 
                   'Market Cap', 'Trailing PE', 'Return on Equity', 'Dividend Yield'],
        ticker1: [
            t1.info.get('open'),
            t1.info.get('previousClose'),
            t1.info.get('dayLow'),
            t1.info.get('dayHigh'),
            t1.info.get('marketCap'),
            t1.info.get('trailingPE'),
            t1.info.get('returnOnEquity'),
            t1.info.get('dividendYield')
        ],
        ticker2: [
            t2.info.get('open'),
            t2.info.get('previousClose'),
            t2.info.get('dayLow'),
            t2.info.get('dayHigh'),
            t2.info.get('marketCap'),
            t2.info.get('trailingPE'),
            t2.info.get('returnOnEquity'),
            t2.info.get('dividendYield')
        ]
    }

    df = pd.DataFrame(data)

    # fig, ax = plt.subplots(figsize=(10, 10), dpi=100, facecolor="none")
    # ax.axis('off')

    # table = ax.table(cellText=metrics_comp.values, colLabels=metrics_comp.columns, loc='center')

    # buf = BytesIO()
    # fig.savefig(buf)
    # buf.seek(0)

    # plt.close()
    # return buf

    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name='Comparison', index=False)

        worksheet = writer.sheets['Comparison']
        for i, col in enumerate(df.columns):
            max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i, i, max_len)
    
    buf.seek(0)
    return buf   

totable("AAPL", "MSFT")

print(get_price("AAPL"))