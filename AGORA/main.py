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
from config import *
from handlers import *
from database import *
from jobs import *
from scheduler import *

bot = Bot(token=BOT_TOKEN_NO_NE_KLASS)

async def on_start():
    start_scheduler()

async def on_shutdown():
    shutdown_scheduler()

async def main():
    await init_db(drop_existing=False)
    bot = Bot(token=BOT_TOKEN_NO_NE_KLASS)
    dp = Dispatcher()

    dp.startup.register(on_start)
    dp.shutdown.register(on_shutdown)

    dp.include_router(rtr)

    print("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())