import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Конфигурация для обработки белого фона"""
    
    # API настройки
    PIXIAN_API_URL = os.getenv("PIXIAN_API_URL")
    PIXIAN_API_USER = os.getenv("PIXIAN_API_USER")
    PIXIAN_API_KEY = os.getenv("PIXIAN_API_KEY")
    PORADOCK_LOG_TOKEN_WHITE = os.getenv("PORADOCK_LOG_TOKEN_WHITE")
    
    # Пути
    BASE_DIR = Path(__file__).parent.parent
    INPUT_DIR = BASE_DIR / "input"
    OUTPUT_DIR = BASE_DIR / "output_white"
    
    # Поддерживаемые форматы изображений
    SUPPORTED_FORMATS = [".jpg", ".jpeg", ".png", ".webp"]
    
    # Параметры API
    BACKGROUND_COLOR = "FFFFFF"  # Белый фон
    TEST_MODE = "true"
    TIMEOUT = 120
    
    @classmethod
    def validate_config(cls):
        """Проверяет корректность конфигурации"""
        if not cls.PIXIAN_API_USER or not cls.PIXIAN_API_KEY:
            raise ValueError("Переменные окружения PIXIAN_API_USER и PIXIAN_API_KEY не заданы.")
        
        if not cls.INPUT_DIR.exists():
            raise FileNotFoundError(f"Папка {cls.INPUT_DIR} не найдена.")
        
        # Создаем папку вывода
        cls.OUTPUT_DIR.mkdir(exist_ok=True)