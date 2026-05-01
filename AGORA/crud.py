from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select, text
from models import User
from database import AsyncSessionLocal
import datetime

async def upsert_user(
    user_id: int,
    username: str | None,
    first_name: str | None,
    chat_id: int
):
    """Создаёт или обновляет пользователя"""
    query = text("""
        INSERT INTO users (id, username, first_name, chat_id, created_at)
        VALUES (:id, :username, :first_name, :chat_id, CURRENT_TIMESTAMP)
        ON CONFLICT(id) DO UPDATE SET
            username = excluded.username,
            first_name = excluded.first_name,
            chat_id = excluded.chat_id
    """)
    
    async with AsyncSessionLocal() as session:
        await session.execute(query, {
            "id": user_id,
            "username": username,
            "first_name": first_name,
            "chat_id": chat_id
        })
        await session.commit()

async def update_timezone(user_id: int, timezone: str) -> None:
    """Обновляет таймзону пользователя"""
    query = text("""
        UPDATE users 
        SET timezone = :timezone 
        WHERE id = :user_id
    """)
    
    async with AsyncSessionLocal() as session:
        await session.execute(query, {"user_id": user_id, "timezone": timezone})
        await session.commit()

async def get_user_timezone(user_id: int) -> str | None:
    """Возвращает таймзону пользователя"""
    query = text("SELECT timezone FROM users WHERE id = :user_id")
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(query, {"user_id": user_id})
        row = result.fetchone()
        return row[0] if row else None

async def get_user_timezone(user_id: int) -> str | None:
    """Возвращает таймзону пользователя"""
    query = text("SELECT timezone FROM users WHERE id = :user_id")
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(query, {"user_id": user_id})
        row = result.fetchone()
        return row[0] if row else None
    
# Пример получения chat_id (если понадобится)
async def get_chat_id(user_id: int) -> int | None:
    query = text("SELECT chat_id FROM users WHERE id = :user_id")
    async with AsyncSessionLocal() as session:
        result = await session.execute(query, {"user_id": user_id})
        row = result.fetchone()
        return row[0] if row else None

async def add_to_portfolio(
                            user_id: int,
                            ticker: str, 
                            quantity: int,
                            avg_buy_price: int
                            ):
    query = text("""INSERT INTO portfolios (id, user_id, ticker, quantity, avg_buy_price, created_at)
                    VALUES (:id, :user_id, :ticker, :quantity, :avg_buy_price, CURRENT_TIMESTAMP)""")