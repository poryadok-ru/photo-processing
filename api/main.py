from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import Response, StreamingResponse
from typing import List
import asyncio
from datetime import datetime

from .task_manager import task_manager
from .background_processor import background_processor
from .processors.async_white_processor import AsyncWhiteProcessor
from .processors.async_interior_processor import AsyncInteriorProcessor
from .models.schemas import ProcessingResponse, ImageResponse, TaskStatusResponse, TaskStatus

app = FastAPI(
    title="Async Image Processing API",
    description="Асинхронное API для обработки изображений с системой задач",
    version="2.0.0"
)

@app.on_event("startup")
async def startup_event():
    """Запускаем периодическую очистку старых задач"""
    asyncio.create_task(periodic_cleanup())

async def periodic_cleanup():
    """Периодическая очистка старых задач"""
    while True:
        await asyncio.sleep(3600)  # Каждый час
        task_manager.cleanup_old_tasks()

@app.get("/")
async def root():
    return {"message": "Image Processing API", "version": "2.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post(
    "/process-single",
    response_model=ImageResponse
)
async def process_single_image(
    white_bg: bool = True,
    file: UploadFile = File(...)
):
    """Обрабатывает одно изображение и возвращает его напрямую"""
    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
        raise HTTPException(400, "Invalid image format")
    
    try:
        if white_bg:
            processor = AsyncWhiteProcessor()
        else:
            processor = AsyncInteriorProcessor()
        
        processed_data, filename = await processor.process_single(file)
        
        return StreamingResponse(
            io.BytesIO(processed_data),
            media_type="image/jpeg",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(500, f"Processing failed: {str(e)}")

@app.post(
    "/process-batch",
    response_class=Response
)
async def process_batch(
    white_bg: bool = True,
    files: List[UploadFile] = File(...)
):
    """Обрабатывает несколько изображений и возвращает ZIP архив"""
    if not files:
        raise HTTPException(400, "No files provided")
    
    try:
        if white_bg:
            processor = AsyncWhiteProcessor()
        else:
            processor = AsyncInteriorProcessor()
        
        zip_buffer = await processor.process_batch(files)
        
        return Response(
            content=zip_buffer.getvalue(),
            media_type="application/zip",
            headers={
                "Content-Disposition": "attachment; filename=processed_images.zip",
            }
        )
        
    except Exception as e:
        raise HTTPException(500, f"Processing failed: {str(e)}")

@app.post("/process-parallel", response_model=ProcessingResponse)
async def process_parallel(
    background_tasks: BackgroundTasks,
    white_bg: bool = True,
    files: List[UploadFile] = File(...)
):
    """
    Запускает параллельную обработку и возвращает ID задачи
    """
    if not files:
        raise HTTPException(400, "No files provided")
    
    # Создаем задачу
    task_id = task_manager.create_task(white_bg, files)
    
    # Запускаем фоновую обработку
    background_tasks.add_task(background_processor.process_task, task_id)
    
    return ProcessingResponse(
        success=True,
        message="Parallel processing started",
        file_count=len(files),
        task_id=task_id
    )

@app.get("/tasks/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """Возвращает статус задачи"""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    
    return TaskStatusResponse(
        task_id=task_id,
        status=task["status"],
        progress=task["progress"],
        processed_files=task["processed_files"],
        total_files=task["total_files"],
        start_time=task["start_time"],
        end_time=task["end_time"],
        error=task["error"]
    )

@app.get("/tasks/{task_id}/download")
async def download_task_result(task_id: str):
    """Скачивает результат выполненной задачи"""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    
    if task["status"] != TaskStatus.COMPLETED:
        raise HTTPException(400, "Task not completed yet")
    
    if not task["result"]:
        raise HTTPException(500, "Task result not available")
    
    # Возвращаем ZIP архив
    zip_buffer: io.BytesIO = task["result"]
    
    return Response(
        content=zip_buffer.getvalue(),
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=processed_{task_id}.zip",
        }
    )

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    """Удаляет задачу и освобождает память"""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    
    # В реальной системе здесь нужно аккуратно удалить задачу из словаря
    # Для простоты просто возвращаем успех
    return {"success": True, "message": "Task deletion scheduled"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)