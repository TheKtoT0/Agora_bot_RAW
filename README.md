# Финансовый Telegram-бот

Современный Telegram-бот для отслеживания акций, криптовалюты, портфеля и ежедневных отчётов.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![aiogram](https://img.shields.io/badge/aiogram-3.x-blue)
![SQLite](https://img.shields.io/badge/SQLite-3.x-blue)

## Возможности

- Получение актуальной цены, метрик и информации по акциям/крипте
- Построение интерактивных графиков цены (1d–max)
- Сравнение двух активов (график + Excel-таблица)
- Ежедневные подписки на цену и график по расписанию
- Поддержка таймзон пользователей (UTC±N)
- Сохранение данных пользователей и портфеля в SQLite
- Удобное меню и состояния (FSM)

## Технологический стек

- **Python 3.10+**
- **aiogram 3.x** (асинхронный)
- **SQLAlchemy 2.0** + **aiosqlite**
- **APScheduler** — планировщик задач
- **yfinance** — данные о рынках
- **pandas**, **matplotlib**, **xlsxwriter** — обработка и визуализация данных
- **Pydantic Settings** — конфигурация

## Как запустить локально

### 1. Клонирование репозитория
```bash
git clone https://github.com/TheKtoT0/Agora_bot_RAW.git
cd Agora_bot_RAW
