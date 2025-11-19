import asyncio
import io
import zipfile
from typing import List
from fastapi import UploadFile
from .task_manager import task_manager
from .processors.async_white_processor import AsyncWhiteProcessor
from .processors.async_interior_processor import AsyncInteriorProcessor
from .models.schemas import TaskStatus
from .logging import CustomLogger

class BackgroundProcessor:
    """Обработчик фоновых задач"""
    
    async def process_task(self, task_id: str):
        """Обрабатывает задачу в фоновом режиме"""
        task = task_manager.get_task(task_id)
        if not task:
            return
        
        # Создаем логгер для задачи
        processing_type = "white" if task["white_bg"] else "interior"
        logger = CustomLogger(processing_type)
        task_manager.update_task_status(task_id, TaskStatus.PROCESSING, logger=logger)
        
        try:
            logger.info(f"Начало фоновой обработки задачи {task_id}")
            logger.info(f"Файлов для обработки: {task['total_files']}")
            
            # Выбираем процессор
            if task["white_bg"]:
                processor = AsyncWhiteProcessor()
            else:
                processor = AsyncInteriorProcessor()
            
            # Обрабатываем файлы
            zip_buffer = await self._process_with_progress(processor, task["files"], task_id, logger)
            
            # Сохраняем результат
            task_manager.set_task_result(task_id, zip_buffer)
            task_manager.update_task_status(task_id, TaskStatus.COMPLETED, progress=100)
            
            logger.info(f"Фоновая обработка завершена успешно: {task_id}")
            logger.finish_success(
                processed_count=task["total_files"],
                task_id=task_id
            )
            
        except Exception as e:
            error_msg = f"Ошибка фоновой обработки: {str(e)}"
            logger.error(error_msg)
            task_manager.set_task_error(task_id, error_msg)
            logger.finish_error(error=error_msg, task_id=task_id)
    
    async def _process_with_progress(self, processor, files: List[UploadFile], task_id: str, logger: CustomLogger) -> io.BytesIO:
        """Обрабатывает файлы с обновлением прогресса"""
        total_files = len(files)
        processed_files = []
        
        for i, file in enumerate(files):
            try:
                # Обновляем прогресс
                progress = int((i / total_files) * 100)
                task_manager.update_task_status(
                    task_id, 
                    TaskStatus.PROCESSING, 
                    progress=progress,
                    processed_files=i
                )
                
                logger.info(f"Обработка файла {i+1}/{total_files}: {file.filename}")
                
                # Обрабатываем файл
                processed_data, filename = await processor.process_single(file)
                processed_files.append((filename, processed_data))
                
                logger.debug(f"Успешно обработан: {file.filename}")
                
            except Exception as e:
                logger.error(f"Ошибка обработки файла {file.filename}: {e}")
                # Продолжаем обработку остальных файлов
        
        # Создаем ZIP архив
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for filename, file_data in processed_files:
                zip_file.writestr(filename, file_data)
        
        zip_buffer.seek(0)
        return zip_buffer

# Глобальный экземпляр обработчика
background_processor = BackgroundProcessor()