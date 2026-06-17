from fastapi import FastAPI, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
import asyncio
import os

from .database import get_db, engine
from . import models
from .device_manager import device_manager
from .routers import devices_router, scenarios_router

# Принудительно пересоздаем таблицы с новой структурой
try:
    # Удаляем все таблицы
    models.Base.metadata.drop_all(bind=engine)
    # Создаем заново с новой структурой
    models.Base.metadata.create_all(bind=engine)
    print("✅ Таблицы базы данных пересозданы с новой структурой")
except Exception as e:
    print(f"❌ Ошибка пересоздания таблиц: {e}")

app = FastAPI(
    title="Smart Home System",
    description="Распределенная система управления умным домом",
    version="1.0.0"
)

# Создаем папки если они не существуют
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)

# Монтируем статические файлы и шаблоны
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Подключаем роутеры
app.include_router(devices_router)
app.include_router(scenarios_router)


@app.on_event("startup")
async def startup_event():
    print("🔄 Инициализация системы...")

    # Получаем сессию базы данных
    db = next(get_db())

    # Инициализируем device_manager
    device_manager.initialize(db)

    # Создаем тестовые устройства, если их нет
    if not device_manager.get_all_devices():
        print("📝 Создаем тестовые устройства...")
        db_devices = [
            models.Device(
                name="Свет в гостиной",
                device_type="light",
                location="Гостиная",
                status="off",
                brightness=100,
                description="Основное освещение в гостиной"
            ),
            models.Device(
                name="Датчик температуры в зале",
                device_type="sensor_temperature",
                location="Зал",
                last_value=21.5,
                unit="°C",
                status="active",
                description="Измерение температуры в основном зале"
            ),
            models.Device(
                name="Датчик влажности в спальне",
                device_type="sensor_humidity",
                location="Спальня",
                last_value=45.0,
                unit="%",
                status="active",
                description="Контроль влажности в спальне"
            ),
            models.Device(
                name="Датчик движения в прихожей",
                device_type="security_sensor",
                location="Прихожая",
                status="disarmed",
                description="Обнаружение движения при входе"
            ),
            models.Device(
                name="Датчик открытия двери",
                device_type="security_sensor",
                location="Входная дверь",
                status="disarmed",
                description="Контроль открытия входной двери"
            ),
            models.Device(
                name="Умный замок",
                device_type="smart_lock",
                location="Входная дверь",
                status="locked",
                locked=True,
                description="Электронный замок входной двери"
            ),
            models.Device(
                name="Умная розетка",
                device_type="smart_plug",
                location="Кухня",
                status="off",
                description="Управление питанием кухонной техники"
            ),
            models.Device(
                name="Термостат",
                device_type="thermostat",
                location="Гостиная",
                status="active",
                temperature=21.0,
                last_value=21.0,
                unit="°C",
                description="Контроль температуры в гостиной"
            ),
        ]
        db.add_all(db_devices)
        db.commit()

        # Перезагружаем устройства в диспетчере
        device_manager._load_devices_from_db()

        # Выводим созданные устройства для проверки
        devices = device_manager.get_all_devices()
        print("✅ Тестовые устройства созданы:")
        for device in devices:
            print(f"  - {device['name']} ({device['device_type']}) в {device['location']}")

    # Запускаем фоновые задачи
    asyncio.create_task(device_manager.start_sensor_emulation())
    asyncio.create_task(device_manager.start_security_monitoring())
    asyncio.create_task(device_manager.check_scenarios())

    print("🚀 Система Умный Дом запущена!")


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db: Session = Depends(get_db)):
    """Главная страница с веб-интерфейсом."""
    # Получаем актуальные данные из базы
    devices = db.query(models.Device).all()
    devices_data = [device.to_dict() for device in devices]

    return templates.TemplateResponse("index.html", {
        "request": request,
        "devices": devices_data
    })

@app.get("/debug/devices")
def debug_devices():
    devices = device_manager.get_all_devices()
    return {
        "device_count": len(devices),
        "devices": devices
    }


@app.get("/health")
def health_check():
    """Проверка работоспособности системы"""
    devices_count = len(device_manager.get_all_devices())
    return {
        "status": "healthy",
        "devices_count": devices_count,
        "initialized": device_manager._initialized
    }


@app.get("/api")
def api_root():
    return {
        "message": "Smart Home System API",
        "version": "1.0.0",
        "endpoints": {
            "web_interface": "/",
            "api_docs": "/docs",
            "health_check": "/health",
            "devices": "/devices/",
            "scenarios": "/scenarios/"
        }
    }