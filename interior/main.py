import os
from log import Log
from .config import Config
from .image_processor import ImageProcessor
from .ai_client import AIClient

class InteriorProcessor:
    """Основной класс для обработки интерьеров"""
    
    def __init__(self):
        self.image_processor = ImageProcessor()
        self.ai_client = AIClient()
    
    def process_all_images(self, logger):
        """Обрабатывает все изображения в папке input"""
        input_files = list(Config.INPUT_DIR.glob("*.png")) + \
                      list(Config.INPUT_DIR.glob("*.jpg")) + \
                      list(Config.INPUT_DIR.glob("*.jpeg"))
        
        if not input_files:
            logger.warning("В папке input нет изображений для обработки.")
            return 0, 0
        
        logger.info(f"Найдено {len(input_files)} изображений для обработки")
        
        successful_processing = 0
        failed_processing = 0
        
        for i, input_path in enumerate(input_files, 1):
            logger.info(f"Обработка изображения {i}/{len(input_files)}: {input_path.name}")
            
            # Создаем временное форматированное изображение
            temp_formatted_path = Config.TEMP_DIR / f"formatted_{input_path.name}"
            
            # Форматируем изображение в 3:4
            if not self.image_processor.format_image_3_4(input_path, temp_formatted_path, logger):
                logger.error(f"Пропускаем {input_path.name} из-за ошибки форматирования")
                failed_processing += 1
                continue
            
            # Анализируем категорию и подкатегорию
            logger.info("Анализ категории...")
            main_category, subcategory = self.ai_client.analyze_thematic_subcategory(temp_formatted_path, logger)
            logger.info(f"Категория: {main_category}")
            logger.info(f"Подкатегория: {subcategory} - {Config.THEMATIC_SUBCATEGORIES[main_category][subcategory]}")
            
            # Генерируем промпт и изображение
            logger.info("Генерация изображения в контексте...")
            prompt = self.ai_client.generate_context_prompt(main_category, subcategory)
            generated_img = self.ai_client.edit_image_with_gemini(temp_formatted_path, prompt, logger)
            
            # Удаляем временный файл
            self._cleanup_temp_file(temp_formatted_path, logger)
            
            if generated_img:
                # Обрезаем результат до точного соотношения 3:4
                generated_img = self.image_processor.crop_to_3_4(generated_img)
                logger.info(f"Изображение обрезано до 3:4: {generated_img.width}x{generated_img.height}")
                
                output_path = Config.OUTPUT_DIR / f"{input_path.stem}_in_{main_category.lower()}.jpg"
                if self.image_processor.save_image_simple(generated_img, output_path, logger):
                    successful_processing += 1
                else:
                    failed_processing += 1
            else:
                logger.error(f"Не удалось сгенерировать изображение для {input_path.name}")
                failed_processing += 1
                    
            logger.info(f"Обработка {input_path.name} завершена")
        
        return successful_processing, failed_processing
    
    def _cleanup_temp_file(self, temp_path, logger):
        """Удаляет временный файл"""
        try:
            os.remove(temp_path)
            logger.debug(f"Удален временный файл: {temp_path}")
        except Exception as e:
            logger.warning(f"Не удалось удалить временный файл: {e}")



def main():
    """Основная функция запуска"""
    with Log(token=Config.PORADOCK_LOG_TOKEN_INTERIOR) as logger:
        logger.info("Запуск генерации товаров в интерьере...")
        logger.info(f"Временные файлы будут сохраняться в папке: {Config.TEMP_DIR}")
        
        # Вывод доступных категорий
        logger.info("Доступные категории и подкатегории:")
        for category, subcategories in Config.THEMATIC_SUBCATEGORIES.items():
            logger.info(f"Категория {category}:")
            for sub_key, sub_desc in subcategories.items():
                logger.info(f"  - {sub_key}: {sub_desc}")
        
        # Запуск обработки
        processor = InteriorProcessor()
        successful, failed = processor.process_all_images(logger)
        
        # Итоговая статистика
        logger.info(f"Обработка завершена. Успешно: {successful}, Ошибки: {failed}")
        
        if failed == 0:
            logger.info("Все изображения успешно обработаны")
        else:
            logger.warning(f"Некоторые изображения ({failed}) не были обработаны")

if __name__ == "__main__":
    main()