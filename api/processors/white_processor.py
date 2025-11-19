import io
from pathlib import Path
from typing import List
from fastapi import UploadFile, HTTPException
import asyncio

from .base import BaseProcessor
from white.main import WhiteBackgroundProcessor
from white.config import Config
from ..logging import CustomLogger

class WhiteProcessor(BaseProcessor):
    """Обработчик для белого фона"""
    
    def __init__(self):
        super().__init__("white")
    
    async def process_batch(self, files: List[UploadFile]) -> io.BytesIO:
        """Обрабатывает батч файлов для белого фона"""
        logger = CustomLogger("white")
        
        try:
            logger.info("Начало обработки белого фона")
            logger.info(f"Получено файлов: {len(files)}")
            
            batch_dir, input_paths = await self.save_uploaded_files(files, logger)
            
            if not input_paths:
                await self.cleanup(batch_dir, logger)
                logger.finish_error(error="Нет валидных изображений для обработки")
                raise HTTPException(400, "No valid image files provided")
            
            # Создаем временную выходную папку
            output_dir = batch_dir / "output"
            output_dir.mkdir(exist_ok=True)
            
            # Обрабатываем файлы
            processor = WhiteBackgroundProcessor()
            
            # Запускаем в отдельном потоке, т.к. код синхронный
            processed_count, error_count = await asyncio.get_event_loop().run_in_executor(
                None, 
                self._process_images_sync,
                processor, 
                input_paths, 
                output_dir,
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
            logger.error(f"Ошибка при обработке белого фона: {e}")
            logger.finish_error(error=str(e))
            raise HTTPException(500, f"Processing failed: {str(e)}")
        finally:
            # Очистка в фоне
            if 'batch_dir' in locals():
                asyncio.create_task(self.cleanup(batch_dir, logger))
    
    def _process_images_sync(self, processor: WhiteBackgroundProcessor, 
                           input_paths: List[Path], output_dir: Path, logger: CustomLogger):
        """Синхронная обработка изображений (для запуска в executor)"""
        
        # Временно переопределяем пути в конфиге
        original_input_dir = Config.INPUT_DIR
        original_output_dir = Config.OUTPUT_DIR
        
        try:
            Config.INPUT_DIR = input_paths[0].parent if input_paths else Path()
            Config.OUTPUT_DIR = output_dir
            
            # Обрабатываем каждый файл
            processed = 0
            errors = 0
            
            for input_path in input_paths:
                try:
                    output_path = output_dir / f"{input_path.stem}_white_test.png"
                    logger.info(f"Обработка: {input_path.name}")
                    
                    # Используем существующую логику из white модуля
                    success, image_data, error_msg = processor.pixian_client.remove_background(
                        input_path, logger
                    )
                    
                    if success:
                        if processor.pixian_client.save_image(image_data, output_path, logger):
                            processed += 1
                            logger.info(f"Успешно обработан: {input_path.name}")
                        else:
                            errors += 1
                            logger.error(f"Ошибка сохранения: {input_path.name}")
                    else:
                        errors += 1
                        logger.error(f"Ошибка обработки {input_path.name}: {error_msg}")
                        
                except Exception as e:
                    errors += 1
                    logger.error(f"Ошибка обработки {input_path.name}: {e}")
            
            return processed, errors
            
        finally:
            # Восстанавливаем оригинальные пути
            Config.INPUT_DIR = original_input_dir
            Config.OUTPUT_DIR = original_output_dir