from pathlib import Path
from log import Log
from .config import Config
from .pixian_client import PixianClient

class WhiteBackgroundProcessor:
    """Основной класс для обработки изображений с белым фоном"""
    
    def __init__(self):
        self.pixian_client = PixianClient()
    
    def process_all_images(self, logger):
        """
        Обрабатывает все изображения в папке input
        
        Returns:
            tuple: (processed_count, error_count)
        """
        # Получаем список изображений
        image_files = self._get_image_files()
        
        if not image_files:
            logger.warning("В папке input нет изображений для обработки.")
            return 0, 0
        
        logger.info(f"Найдено {len(image_files)} изображений для обработки")
        
        processed_count = 0
        error_count = 0
        
        for image_path in image_files:
            result = self._process_single_image(image_path, logger)
            if result:
                processed_count += 1
            else:
                error_count += 1
        
        return processed_count, error_count
    
    def _get_image_files(self):
        """Возвращает список поддерживаемых изображений"""
        image_files = []
        for ext in Config.SUPPORTED_FORMATS:
            image_files.extend(Config.INPUT_DIR.glob(f"*{ext}"))
            image_files.extend(Config.INPUT_DIR.glob(f"*{ext.upper()}"))
        return image_files
    
    def _process_single_image(self, image_path, logger):
        """Обрабатывает одно изображение"""
        logger.info(f"Обработка: {image_path.name}")
        
        # Формируем путь для выходного файла
        output_path = Config.OUTPUT_DIR / f"{image_path.stem}_white_test.png"
        
        # Удаляем фон через API
        success, image_data, error_msg = self.pixian_client.remove_background(
            image_path, logger
        )
        
        if not success:
            logger.error(f"Ошибка обработки {image_path.name}: {error_msg}")
            return False
        
        # Сохраняем результат
        if self.pixian_client.save_image(image_data, output_path, logger):
            logger.info(f"Успешно обработано: {output_path.name}")
            return True
        else:
            logger.error(f"Не удалось сохранить: {output_path.name}")
            return False

def main():
    """Основная функция запуска"""
    # Валидация конфигурации
    try:
        Config.validate_config()
    except (ValueError, FileNotFoundError) as e:
        print(f"Ошибка конфигурации: {e}")
        return
    
    # Запуск с логированием
    with Log(token=Config.PORADOCK_LOG_TOKEN_WHITE) as logger:
        logger.info("Запуск обработки изображений с белым фоном")
        logger.info(f"Папка ввода: {Config.INPUT_DIR.resolve()}")
        logger.info(f"Папка вывода: {Config.OUTPUT_DIR.resolve()}")
        
        # Запуск обработки
        processor = WhiteBackgroundProcessor()
        processed, errors = processor.process_all_images(logger)
        
        # Итоговая статистика
        logger.info("Обработка завершена")
        logger.info(f"Успешно обработано: {processed}")
        logger.info(f"Ошибок: {errors}")
        
        if errors == 0:
            logger.info("Все изображения успешно обработаны")
        else:
            logger.warning(f"Некоторые изображения ({errors}) не были обработаны")

if __name__ == "__main__":
    main()