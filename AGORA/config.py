from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    BOT_TOKEN: str = "8184110295:AAFo6DkbMkCVlYG1kZMQNHR3zXpzB2WJYec"
    DB_PATH: str = "bot.db"  # Путь к SQLite файлу

    class Config:
        env_file = ".env"

BOT_TOKEN_NO_NE_KLASS = '8184110295:AAFo6DkbMkCVlYG1kZMQNHR3zXpzB2WJYec'

settings = Settings()