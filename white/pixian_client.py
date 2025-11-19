import requests
from pathlib import Path
from .config import Config

class PixianClient:
    """Клиент для работы с Pixian.AI API"""
    
    def __init__(self):
        self.api_url = Config.PIXIAN_API_URL
        self.auth = (Config.PIXIAN_API_USER, Config.PIXIAN_API_KEY)
        self.timeout = Config.TIMEOUT
    
    def remove_background(self, image_path, logger):
        """
        Удаляет фон изображения и заменяет на белый
        
        Args:
            image_path: Путь к исходному изображению
            logger: Логгер для записи сообщений
            
        Returns:
            tuple: (success: bool, image_data: bytes или None, error_message: str или None)
        """
        try:
            with open(image_path, "rb") as img_file:
                response = requests.post(
                    self.api_url,
                    files={"image": img_file},
                    data={
                        "background.color": Config.BACKGROUND_COLOR,
                        "test": Config.TEST_MODE,
                    },
                    auth=self.auth,
                    timeout=self.timeout,
                )
            
            if response.status_code == requests.codes.ok:
                logger.debug(f"Успешный ответ от API для {image_path.name}")
                return True, response.content, None
            else:
                error_msg = f"Ошибка {response.status_code}: {response.text}"
                logger.error(f"API ошибка для {image_path.name}: {error_msg}")
                return False, None, error_msg
                
        except requests.exceptions.Timeout:
            error_msg = f"Таймаут запроса для {image_path.name}"
            logger.error(error_msg)
            return False, None, error_msg
            
        except requests.exceptions.ConnectionError:
            error_msg = f"Ошибка соединения для {image_path.name}"
            logger.error(error_msg)
            return False, None, error_msg
            
        except Exception as e:
            error_msg = f"Неожиданная ошибка для {image_path.name}: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def save_image(self, image_data, output_path, logger):
        """
        Сохраняет изображение на диск
        
        Args:
            image_data: Данные изображения в bytes
            output_path: Путь для сохранения
            logger: Логгер для записи сообщений
            
        Returns:
            bool: Успешно ли сохранено
        """
        try:
            with open(output_path, "wb") as out_file:
                out_file.write(image_data)
            logger.debug(f"Изображение сохранено: {output_path.name}")
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения {output_path.name}: {str(e)}")
            return False

    def remove_background_in_memory(self, image_data: bytes, filename: str, logger):
        """
        Remove background from image in memory without saving to disk
        
        Args:
            image_data: Image data as bytes
            filename: Original filename for reference
            logger: Logger instance
            
        Returns:
            tuple: (success, image_data, error_message)
        """
        try:
            # Create file-like object from bytes
            img_file = io.BytesIO(image_data)
            
            response = requests.post(
                self.api_url,
                files={"image": (filename, img_file, "image/jpeg")},
                data={
                    "background.color": self.background_color,
                    "test": self.test_mode,
                },
                auth=self.auth,
                timeout=self.timeout,
            )

            if response.status_code == requests.codes.ok:
                logger.debug(f"Успешный ответ от API для {filename}")
                return True, response.content, None
            else:
                error_msg = f"Ошибка {response.status_code}: {response.text}"
                logger.error(f"API ошибка для {filename}: {error_msg}")
                return False, None, error_msg

        except requests.exceptions.Timeout:
            error_msg = f"Таймаут запроса для {filename}"
            logger.error(error_msg)
            return False, None, error_msg
            
        except requests.exceptions.ConnectionError:
            error_msg = f"Ошибка соединения для {filename}"
            logger.error(error_msg)
            return False, None, error_msg
            
        except Exception as e:
            error_msg = f"Неожиданная ошибка для {filename}: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg