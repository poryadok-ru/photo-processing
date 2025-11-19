from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(None)):
    """
    Зависимость для проверки API ключа
    В будущем можно добавить аутентификацию
    """
    if not x_api_key:
        raise HTTPException(401, "API key required")
    # Здесь можно добавить проверку ключа
    return Trueы