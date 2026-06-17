Веб-приложение на Python (FastAPI) для управления устройствами умного дома. Поддерживает REST API и гибкую архитектуру для подключения разных протоколов связи.

Технологии
- Python 3.10
- FastAPI
- SQLite
- REST API
- Uvicorn

Запуск проекта
1. Установить зависимости: `pip install -r requirements.txt`
2. Запустить сервер: `uvicorn main:app --reload`
3. Открыть в браузере: `http://localhost:8000/docs`

Структура проекта
- `/app` — основная логика приложения
- `/database` — работа с SQLite
- `/routes` — эндпоинты API
