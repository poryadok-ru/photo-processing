#!/usr/bin/env python3
"""
Скрипт для создания первого администратора API
"""
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from api.auth import AuthManager

def main():
    """Создает администратора и выдает API ключ"""
    auth_manager = AuthManager()
    
    data = auth_manager._load_users()
    admin_users = [u for u in data.get("users", []) if u.get("is_admin")]
    
    if admin_users:
        print("Администраторы уже существуют:")
        for admin in admin_users:
            print(f"- {admin['username']}: {admin['api_key']}")
        return

    username = input("Введите имя администратора [admin]: ").strip() or "admin"
    
    try:
        api_key = auth_manager.create_user(username, is_admin=True, rate_limit=1000)
        print(f"\n✅ Администратор создан успешно!")
        print(f"👤 Имя пользователя: {username}")
        print(f"🔑 API ключ: {api_key}")
        print(f"\n⚠️  Сохраните этот ключ! Он больше не будет показан.")
        print(f"📖 Используйте ключ в Swagger UI: http://localhost:8000/docs")
        
    except Exception as e:
        print(f"❌ Ошибка при создании администратора: {e}")

if __name__ == "__main__":
    main()