import os
from database import engine
from models import Base


def reset_database():
    # Удаляем старый файл базы данных если он существует
    if os.path.exists("smart_home.db"):
        os.remove("smart_home.db")
        print("🗑️ Старая база данных удалена")

    # Создаем новую базу с обновленной структурой
    Base.metadata.create_all(bind=engine)
    print("✅ Новая база данных создана с обновленной структурой")


if __name__ == "__main__":
    reset_database()