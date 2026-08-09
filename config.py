"""
Единый конфигурационный файл для GetGems WebApp
Содержит все настройки приложения, бота и клиента
"""

import os
from typing import List, Optional
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()


class Config:
    """Основная конфигурация приложения"""
    
    # === TELEGRAM API НАСТРОЙКИ ===
    TELEGRAM_API_ID: int = int(os.getenv("TELEGRAM_API_ID", "2040"))
    TELEGRAM_API_HASH: str = os.getenv("TELEGRAM_API_HASH", "b18441a1ff607e10a989891a5462e627")
    
    # === BOT НАСТРОЙКИ ===
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", os.getenv("GETGEMS_BOT_TOKEN", "8891151257:AAHOlp-6T5Z0Kz70JckW2cZjM6Du2Y6UqA8"))
    BOT_USERNAME: str = os.getenv("BOT_USERNAME", "LupaLjpajcbfbot")
    
    # === WEB APP НАСТРОЙКИ ===
    WEBAPP_URL: str = os.getenv("WEBAPP_URL", "https://t.me/LupaLjpajcbfbot/frxjfj")
    SECRET_KEY: str = os.getenv("GETGEMS_SECRET_KEY", "your_secret_key_here")
    
    # === FLASK НАСТРОЙКИ ===
    FLASK_HOST: str = os.getenv("FLASK_HOST", "0.0.0.0")
    FLASK_PORT: int = int(os.getenv("FLASK_PORT", "5000"))
    FLASK_DEBUG: bool = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    
    # === DATABASE НАСТРОЙКИ ===
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "getgems.db")
    
    # === LOGGING НАСТРОЙКИ ===
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_GROUP_ID: str = os.getenv("LOG_GROUP_ID", "-46gd61847")
    LOG_CHAT_ID: str = os.getenv("LOG_CHAT_ID", "-46887dg847")
    
    # === ADMIN НАСТРОЙКИ ===
    ADMIN_IDS: List[int] = [
        int(admin_id.strip()) for admin_id in os.getenv("ADMIN_IDS", "7374883367").split(",")
        if admin_id.strip().isdigit()
    ]
    
    # === TELEGRAM AUTH НАСТРОЙКИ ===
    INIT_DATA_STRICT: bool = os.getenv("INIT_DATA_STRICT", "false").lower() == "true"
    
    # === SESSION НАСТРОЙКИ ===
    SESSION_DIR: str = os.getenv("SESSION_DIR", "sessions")
    SESSION_DATA_FILE: str = os.getenv("SESSION_DATA_FILE", "session_data.json")
    
    # === TIMEOUT НАСТРОЙКИ ===
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    CODE_REQUEST_TIMEOUT: int = int(os.getenv("CODE_REQUEST_TIMEOUT", "60"))
    LOTTIE_REQUEST_TIMEOUT: int = int(os.getenv("LOTTIE_REQUEST_TIMEOUT", "10"))
    
    # === PROXY НАСТРОЙКИ ===
    PROXIES: List[dict] = []  # Можно добавить прокси из переменных окружения
    
    # === MOBILE DEVICES КОНФИГУРАЦИЯ ===
    MOBILE_DEVICES: List[dict] = [
        {
            'device_model': 'SM-G973F',
            'system_version': '10',
            'app_version': '8.4.1',
            'lang_code': 'en',
            'system_lang_code': 'en-US'
        },
        {
            'device_model': 'iPhone12,1',
            'system_version': '14.6',
            'app_version': '8.4.1',
            'lang_code': 'en',
            'system_lang_code': 'en-US'
        },
        {
            'device_model': 'Pixel 5',
            'system_version': '11',
            'app_version': '8.4.1',
            'lang_code': 'en',
            'system_lang_code': 'en-US'
        }
    ]
    
    @classmethod
    def is_admin(cls, user_id: int) -> bool:
        """Проверяет, является ли пользователь администратором"""
        return user_id in cls.ADMIN_IDS
    
    @classmethod
    def validate_bot_token(cls) -> bool:
        """Проверяет валидность токена бота"""
        if cls.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
            print("❌ Токен бота не установлен!")
            print("Получите токен у @BotFather и установите переменную окружения BOT_TOKEN")
            return False
        if not cls.BOT_TOKEN or len(cls.BOT_TOKEN) < 40:
            print("❌ Неверный токен бота!")
            return False
        return True
    
    @classmethod
    def ensure_directories(cls) -> None:
        """Создает необходимые директории"""
        if not os.path.exists(cls.SESSION_DIR):
            os.makedirs(cls.SESSION_DIR)
    
    @classmethod
    def get_api_url(cls, endpoint: str = "") -> str:
        """Возвращает URL для API запросов"""
        base_url = f"http://{cls.FLASK_HOST}:{cls.FLASK_PORT}"
        if endpoint:
            return f"{base_url}/{endpoint.lstrip('/')}"
        return base_url
    
    @classmethod
    def print_config_info(cls) -> None:
        """Выводит информацию о конфигурации"""
        print("🔧 Конфигурация GetGems WebApp:")
        print(f"   BOT_TOKEN: {'✅ Установлен' if cls.BOT_TOKEN and cls.BOT_TOKEN != 'YOUR_BOT_TOKEN_HERE' else '❌ Не установлен'}")
        print(f"   WEBAPP_URL: {cls.WEBAPP_URL}")
        print(f"   DATABASE_PATH: {cls.DATABASE_PATH}")
        print(f"   LOG_LEVEL: {cls.LOG_LEVEL}")
        print(f"   LOG_GROUP_ID: {cls.LOG_GROUP_ID}")
        print(f"   ADMIN_IDS: {len(cls.ADMIN_IDS)} администраторов")
        print(f"   FLASK: {cls.FLASK_HOST}:{cls.FLASK_PORT} (debug={cls.FLASK_DEBUG})")

    @classmethod
    def print_config(cls) -> None:
        """Обратная совместимость: старое имя метода."""
        cls.print_config_info()


# Создаем экземпляр конфигурации для обратной совместимости
config = Config()

# Инициализируем необходимые директории
Config.ensure_directories()