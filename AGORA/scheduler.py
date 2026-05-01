import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot
from jobs import send_daily_price, send_daily_chart
from crud import *
from datetime import datetime
from servicesnstuff import *

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="Europe/Moscow")  # МСК ЗАГЛУШКА

def start_scheduler():
    """Запуск планировщика"""
    if scheduler.running:
        return
    
    scheduler.start()
    logger.info("APScheduler запущен")

def convert_user_time_to_utc(
    local_hour: int, 
    local_minute: int, 
    user_timezone: str | None
) -> tuple[int, int]:
    """Конвертирует час:минуту по таймзоне пользователя в UTC час:минуту"""
    offset = parse_utc_offset(user_timezone)
    if offset is None:
        return local_hour, local_minute  # fallback — считаем, что уже UTC

    # Создаём "фиктивную" дату сегодня в локальном времени пользователя
    now = datetime.now(timezone.utc)
    local_dt = now.replace(hour=local_hour, minute=local_minute, second=0, microsecond=0) + offset
    
    # Переводим в UTC
    utc_dt = local_dt - offset
    return utc_dt.hour, utc_dt.minute

async def add_daily_price_job(
    bot: Bot,
    chat_id: int,
    ticker: str,
    hour: int,
    minute: int = 0,
    job_id: str | None = None
):
    """Добавляет ежедневную отправку цены в указанное время (по UTC)"""
    if job_id is None:
        job_id = f"daily_price_{chat_id}_{ticker}"
    
    # Удаляем старое задание, если существует (чтобы не дублировать)
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    
    user_timezone = await get_user_timezone(user_id=chat_id)

    utc_hour, utc_minute = convert_user_time_to_utc(hour, minute, timezone)

    trigger = CronTrigger(
        hour=hour,
        minute=minute,
        timezone=parse_utc_offset(user_timezone)
    )
    
    scheduler.add_job(
        send_daily_price,
        trigger=trigger,
        args=[bot, chat_id, ticker, user_timezone],
        id=job_id,
        replace_existing=True,   # важно!!!!
        misfire_grace_time=300,  # 5 минут tolerance
        coalesce=True
    )
    
    logger.info(f"Добавлено ежедневное задание для {ticker} в {hour:02d}:{minute:02d} UTC для чата {chat_id}")
    return job_id



async def add_daily_chart_job(
        bot: Bot,
        chat_id: int,
        ticker: str,
        hour: int,
        minute: int,
        job_id: str | None = None
):
    """Добавляет ежедневную отправку графика цены в указвнное время"""
    if job_id is None:
        job_id = f"daily_chart_{chat_id}_{ticker}"

    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    user_timezone = await get_user_timezone(user_id=chat_id)

    utc_hour, utc_minute = convert_user_time_to_utc(hour, minute, timezone)

    trigger = CronTrigger(
        hour=hour,
        minute=minute,
        timezone=parse_utc_offset(user_timezone)
    )

    scheduler.add_job(
        send_daily_chart,
        trigger=trigger,
        args=[bot, chat_id, ticker, user_timezone],
        id=job_id,
        replace_existing=True,
        misfire_grace_time=300,
        coalesce=True
    )

    logger.info(f"Добавлено ежедневное задание для {ticker} в {hour:02d}:{minute:02d} UTC для чата {chat_id}")
    return job_id

def remove_job(job_id: str):
    """Удаление задания"""
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logger.info(f"Задание {job_id} удалено")


def shutdown_scheduler():
    """Корректное завершение"""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler остановлен")