import asyncio
import aiofiles
import zipfile
import io
from pathlib import Path
from typing import List, Tuple
from fastapi import UploadFile, HTTPException
from ..logging import CustomLogger

class BaseProcessor:
    """Базовый класс для обработчиков изображений"""
    
    def __init__(self, processing_type: str):
        self.temp_dir = Path("temp_api")
        self.temp_dir.mkdir(exist_ok=True)
        self.processing_type = processing_type
    
    async def save_uploaded_files(self, files: List[UploadFile], logger: CustomLogger) -> Tuple[Path, List[Path]]:
        """Сохраняет загруженные файлы во временную папку"""
        batch_id = str(hash(tuple(f.filename for f in files)))
        batch_dir = self.temp_dir / batch_id
        batch_dir.mkdir(exist_ok=True)
        
        saved_paths = []
        
        for file in files:
            if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                logger.warning(f"Пропущен неподдерживаемый файл: {file.filename}")
                continue
                
            file_path = batch_dir / file.filename
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            saved_paths.append(file_path)
            logger.debug(f"Сохранен файл: {file.filename}")
        
        logger.info(f"Сохранено {len(saved_paths)} файлов для обработки")
        return batch_dir, saved_paths
    
    async def create_zip_response(self, processed_files: List[Path], logger: CustomLogger) -> io.BytesIO:
        """Создает zip-архив с обработанными файлами"""
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in processed_files:
                async with aiofiles.open(file_path, 'rb') as f:
                    file_data = await f.read()
                    zip_file.writestr(file_path.name, file_data)
                    logger.debug(f"Добавлен в архив: {file_path.name}")
        
        zip_buffer.seek(0)
        logger.info(f"Создан ZIP архив с {len(processed_files)} файлами")
        return zip_buffer
    
    async def cleanup(self, batch_dir: Path, logger: CustomLogger):
        """Очищает временные файлы"""
        import shutil
        try:
            if batch_dir.exists():
                shutil.rmtree(batch_dir)
                logger.debug(f"Очищена временная папка: {batch_dir}")
        except Exception as e:
            logger.warning(f"Ошибка при очистке {batch_dir}: {e}")
    
    async def process_batch(self, files: List[UploadFile]) -> io.BytesIO:
        """Основной метод обработки батча файлов"""
        raise NotImplementedError("Subclasses must implement process_batch")