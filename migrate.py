from sqlalchemy import create_engine, text
from database import SQLALCHEMY_DATABASE_URL, Base
from models import Device, SensorLog, Scenario


def migrate_database():
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

    # Создаем новые таблицы
    Base.metadata.create_all(bind=engine)

    print("✅ База данных успешно обновлена!")


if __name__ == "__main__":
    migrate_database()