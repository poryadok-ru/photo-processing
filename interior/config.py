import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# --- Конфигурация ---
class Config:
    # API ключи
    API_KEY = os.getenv("OPENAI_API_KEY")
    MODEL_NAME = os.getenv("MODEL_NAME")
    IMAGE_MODEL = os.getenv("IMAGE_MODEL")
    BASE_URL = os.getenv("BASE_URL")
    PORADOCK_LOG_TOKEN_INTERIOR = os.getenv("PORADOCK_LOG_TOKEN_INTERIOR")
    
    # Пути
    BASE_DIR = Path(__file__).parent.parent
    INPUT_DIR = BASE_DIR / "input"
    OUTPUT_DIR = BASE_DIR / "output_interior"
    TEMP_DIR = BASE_DIR / "temp_formatted"
    
    # Создание директорий
    INPUT_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    TEMP_DIR.mkdir(exist_ok=True)
    
    # Тематические категории
    THEMATIC_SUBCATEGORIES = {
        "KITCHEN": {
            "COOKWARE": "Кастрюли, сковороды, посуда для готовки",
            "UTENSILS": "Столовые приборы, ножи, кухонные инструменты",
            "APPLIANCES": "Кухонная техника, тостеры, блендеры",
            "STORAGE": "Контейнеры, банки, системы хранения",
            "DINNERWARE": "Тарелки, чашки, сервировочная посуда",
            "DECOR": "Кухонный декор, полотенца, аксессуары"
        },
        "BATHROOM": {
            "TOWELS": "Полотенца, банные халаты",
            "HYGIENE": "Средства личной гигиены, мыло, шампуни",
            "FURNITURE": "Ванная мебель, шкафчики, полки",
            "STORAGE": "Органайзеры, корзины, системы хранения",
            "ACCESSORIES": "Держатели, крючки, аксессуары",
            "CLEANING": "Средства для уборки, щетки"
        },
        "LIVING_ROOM": {
            "FURNITURE": "Диваны, кресла, столы, стеллажи",
            "LIGHTING": "Лампы, светильники, торшеры",
            "DECOR": "Декор, вазы, картины, зеркала",
            "TEXTILES": "Подушки, покрывала, ковры",
            "STORAGE": "Полки, тумбы, системы хранения",
            "ELECTRONICS": "Телевизоры, аудиосистемы"
        },
        "BEDROOM": {
            "BEDDING": "Постельное белье, подушки, одеяла",
            "FURNITURE": "Кровати, тумбочки, шкафы",
            "LIGHTING": "Прикроватные лампы, светильники",
            "DECOR": "Декор, картины, аксессуары",
            "STORAGE": "Комоды, органайзеры, коробки",
            "TEXTILES": "Пледы, покрывала, коврики"
        },
        "OFFICE": {
            "FURNITURE": "Столы, стулья, полки",
            "ORGANIZATION": "Органайзеры, лотки, системы хранения",
            "STATIONERY": "Канцелярия, ручки, блокноты",
            "TECH": "Компьютерные аксессуары, настольные лампы",
            "DECOR": "Офисный декор, растения, картины"
        },
        "HOLIDAY": {
            "CHRISTMAS": "Ёлочные игрушки, рождественские украшения, гирлянды",
            "EASTER": "Пасхальные украшения, фигурки, корзины, яйца",
            "HALLOWEEN": "Хэллоуинский декор, тыквы, свечи, тематические фигурки",
            "NEW_YEAR": "Украшения к Новому году, мишура, шары, звёзды",
            "VALENTINE": "Украшения ко Дню Святого Валентина, сердечки, свечи",
            "GENERAL": "Праздничный декор и универсальные украшения"
        }
    }