import io
from pathlib import Path
from typing import List
from fastapi import UploadFile, HTTPException
import asyncio

from .base import BaseProcessor
from interior.main import InteriorProcessor
from interior.config import Config
from ..logging import CustomLogger

class InteriorProcessorWrapper(BaseProcessor):
    """Обработчик для интерьеров"""
    
    def __init__(self):
        super().__init__("interior")
    
    async def process_batch(self, files: List[UploadFile]) -> io.BytesIO:
        """Обрабатывает батч файлов для интерьеров"""
        logger = CustomLogger("interior")
        
        try:
            logger.info("Начало обработки интерьеров")
            logger.info(f"Получено файлов: {len(files)}")
            
            batch_dir, input_paths = await self.save_uploaded_files(files, logger)
            
            if not input_paths:
                await self.cleanup(batch_dir, logger)
                logger.finish_error(error="Нет валидных изображений для обработки")
                raise HTTPException(400, "No valid image files provided")
            
            # Создаем временные папки
            output_dir = batch_dir / "output"
            temp_dir = batch_dir / "temp"
            output_dir.mkdir(exist_ok=True)
            temp_dir.mkdir(exist_ok=True)
            
            # Обрабатываем файлы
            processor = InteriorProcessor()
            
            # Запускаем в отдельном потоке
            processed_count, error_count = await asyncio.get_event_loop().run_in_executor(
                None, 
                self._process_images_sync,
                processor, 
                input_paths, 
                output_dir,
                temp_dir,
                logger
            )
            
            if processed_count == 0:
                logger.error("Не удалось обработать ни одного изображения")
                await self.cleanup(batch_dir, logger)
                logger.finish_error(error="Failed to process any images")
                raise HTTPException(500, "Failed to process any images")
            
            logger.info(f"Успешно обработано: {processed_count}, ошибок: {error_count}")
            
            # Собираем обработанные файлы
            processed_files = list(output_dir.glob("*.*"))
            
            # Создаем zip
            zip_buffer = await self.create_zip_response(processed_files, logger)
            
            # Финализируем лог
            logger.finish_success(
                processed_count=processed_count,
                error_count=error_count,
                total_files=len(files)
            )
            
            return zip_buffer
            
        except Exception as e:
            logger.error(f"Ошибка при обработке интерьеров: {e}")
            logger.finish_error(error=str(e))
            raise HTTPException(500, f"Processing failed: {str(e)}")
        finally:
            # Очистка в фоне
            if 'batch_dir' in locals():
                asyncio.create_task(self.cleanup(batch_dir, logger))
    
    def _process_images_sync(self, processor: InteriorProcessor, 
                           input_paths: List[Path], output_dir: Path, temp_dir: Path, logger: CustomLogger):
        """Синхронная обработка изображений для интерьеров"""
        
        # Временно переопределяем пути в конфиге
        original_input_dir = Config.INPUT_DIR
        original_output_dir = Config.OUTPUT_DIR
        original_temp_dir = Config.TEMP_DIR
        
        try:
            Config.INPUT_DIR = input_paths[0].parent if input_paths else Path()
            Config.OUTPUT_DIR = output_dir
            Config.TEMP_DIR = temp_dir
            
            # Обрабатываем каждый файл
            processed = 0
            errors = 0
            
            for input_path in input_paths:
                try:
                    logger.info(f"Обработка: {input_path.name}")
                    
                    # Создаем временное форматированное изображение
                    temp_formatted_path = temp_dir / f"formatted_{input_path.name}"
                    
                    # Форматируем в 3:4
                    if not processor.image_processor.format_image_3_4(input_path, temp_formatted_path, logger):
                        errors += 1
                        logger.error(f"Ошибка форматирования: {input_path.name}")
                        continue
                    
                    # Анализируем категорию
                    logger.debug(f"Анализ категории: {input_path.name}")
                    main_category, subcategory = processor.ai_client.analyze_thematic_subcategory(temp_formatted_path, logger)
                    logger.info(f"Категория для {input_path.name}: {main_category} - {subcategory}")
                    
                    # Генерируем изображение
                    logger.debug(f"Генерация изображения: {input_path.name}")
                    prompt = processor.ai_client.generate_context_prompt(main_category, subcategory)
                    generated_img = processor.ai_client.edit_image_with_gemini(temp_formatted_path, prompt, logger)
                    
                    # Удаляем временный файл
                    try:
                        temp_formatted_path.unlink()
                        logger.debug(f"Удален временный файл: {temp_formatted_path.name}")
                    except Exception as e:
                        logger.warning(f"Не удалось удалить временный файл: {e}")
                    
                    if generated_img:
                        # Обрезаем до точного 3:4
                        generated_img = processor.image_processor.crop_to_3_4(generated_img)
                        logger.debug(f"Обрезано до 3:4: {input_path.name}")
                        
                        output_path = output_dir / f"{input_path.stem}_in_{main_category.lower()}.jpg"
                        if processor.image_processor.save_image_simple(generated_img, output_path, logger):
                            processed += 1
                            logger.info(f"Успешно обработан: {input_path.name}")
                        else:
                            errors += 1
                            logger.error(f"Ошибка сохранения: {input_path.name}")
                    else:
                        errors += 1
                        logger.error(f"Не удалось сгенерировать изображение: {input_path.name}")
                        
                except Exception as e:
                    errors += 1
                    logger.error(f"Ошибка обработки {input_path.name}: {e}")
            
            return processed, errors
            
        finally:
            # Восстанавливаем оригинальные пути
            Config.INPUT_DIR = original_input_dir
            Config.OUTPUT_DIR = original_output_dir
            Config.TEMP_DIR = original_temp_dir