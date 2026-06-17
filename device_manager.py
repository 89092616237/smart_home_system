import asyncio
import random
import time
import json
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from . import models


class DeviceManager:
    def __init__(self):
        self.db = None
        self._devices = {}
        self._initialized = False

    def initialize(self, db: Session):
        """Инициализация диспетчера с базой данных"""
        self.db = db
        self._load_devices_from_db()
        self._initialized = True
        print(f"DeviceManager initialized with {len(self._devices)} devices")

    def _load_devices_from_db(self):
        """Загружаем устройства из базы данных при старте."""
        if not self.db:
            return

        db_devices = self.db.query(models.Device).all()
        for device in db_devices:
            self._devices[device.id] = device.to_dict()  # Используем метод модели
        print(f"Loaded {len(self._devices)} devices from DB.")

    def get_all_devices(self) -> list:
        """Возвращает список всех устройств."""
        if not self._initialized:
            return []
        return list(self._devices.values())

    def get_all_devices_as_dicts(self) -> list:
        """Возвращает список всех устройств в виде словарей."""
        if not self._initialized or not self.db:
            return []

        db_devices = self.db.query(models.Device).all()
        return [device.to_dict() for device in db_devices]

    def get_device(self, device_id: int) -> Optional[Dict[str, Any]]:
        """Возвращает устройство по ID."""
        if not self._initialized:
            return None
        return self._devices.get(device_id)

    def update_device(self, device_id: int, updates: Dict[str, Any]):
        """Обновляет состояние устройства (эмуляция команды по ZigBee)."""
        if not self._initialized or device_id not in self._devices:
            print(f"❌ Device {device_id} not found for update")
            return

        device_data = self._devices[device_id]
        device_data.update(updates)

        # Обновляем также в базе данных
        if self.db:
            db_device = self.db.query(models.Device).filter(models.Device.id == device_id).first()
            if db_device:
                for key, value in updates.items():
                    if hasattr(db_device, key):
                        setattr(db_device, key, value)
                self.db.commit()

                # Обновляем кэш актуальными данными из БД
                self._devices[device_id] = db_device.to_dict()

                print(f"✅ Device {device_id} updated: {updates}")
            else:
                print(f"❌ Device {device_id} not found in database")

    async def start_sensor_emulation(self):
        """Фоновая задача: эмуляция работы датчиков."""
        if not self._initialized:
            return

        while True:
            await asyncio.sleep(10)
            if not self.db:
                continue

            for device_id, device_data in self._devices.items():
                device_type = device_data['device_type']

                if device_type == 'sensor_temperature':
                    new_temp = round(random.uniform(18.0, 25.0), 1)
                    self._update_sensor_value(device_id, new_temp, "°C")
                    print(f"🌡️ Sensor {device_id} new temperature: {new_temp}°C")

                elif device_type == 'sensor_humidity':
                    new_humidity = round(random.uniform(30.0, 70.0), 1)
                    self._update_sensor_value(device_id, new_humidity, "%")
                    print(f"💧 Sensor {device_id} new humidity: {new_humidity}%")

                elif device_type == 'thermostat' and device_data.get('temperature'):
                    # Термостат поддерживает заданную температуру
                    current_temp = device_data.get('last_value', 20.0)
                    target_temp = device_data.get('temperature', 21.0)

                    # Плавное изменение температуры к целевой
                    if current_temp < target_temp:
                        new_temp = min(current_temp + 0.5, target_temp)
                    else:
                        new_temp = max(current_temp - 0.5, target_temp)

                    self._update_sensor_value(device_id, new_temp, "°C")
                    print(f"🔥 Thermostat {device_id} current: {new_temp}°C (target: {target_temp}°C)")

    def _update_sensor_value(self, device_id: int, value: float, unit: str):
        """Обновляет значение датчика в БД и кэше"""
        if self.db:
            db_device = self.db.query(models.Device).filter(models.Device.id == device_id).first()
            if db_device:
                db_device.last_value = value
                db_device.unit = unit

                # Логируем показание
                log_entry = models.SensorLog(sensor_id=device_id, value=value, unit=unit)
                self.db.add(log_entry)
                self.db.commit()

                # Обновляем кэш
                self._devices[device_id] = db_device.to_dict()

    async def check_scenarios(self):
        """Проверка и выполнение сценариев"""
        if not self._initialized or not self.db:
            return

        while True:
            await asyncio.sleep(5)

            scenarios = self.db.query(models.Scenario).filter(models.Scenario.enabled == True).all()

            for scenario in scenarios:
                try:
                    scenario_data = scenario.to_dict()
                    if self._check_trigger(scenario_data['trigger']):
                        await self._execute_actions(scenario_data['actions'])
                        print(f"🎭 Scenario '{scenario.name}' executed")
                except Exception as e:
                    print(f"❌ Error executing scenario {scenario.name}: {e}")

    def _check_trigger(self, trigger: Dict[str, Any]) -> bool:
        """Проверяет условие триггера сценария"""
        trigger_type = trigger.get('type')

        if trigger_type == 'device_status':
            device_id = trigger.get('device_id')
            condition = trigger.get('condition')
            value = trigger.get('value')

            device = self.get_device(device_id)
            if device and device.get('status') == value:
                return True

        elif trigger_type == 'sensor_value':
            device_id = trigger.get('device_id')
            condition = trigger.get('condition')
            value = trigger.get('value')

            device = self.get_device(device_id)
            if device and device.get('last_value'):
                device_value = device['last_value']

                if condition == 'greater' and device_value > value:
                    return True
                elif condition == 'less' and device_value < value:
                    return True
                elif condition == 'equals' and device_value == value:
                    return True

        elif trigger_type == 'time':
            current_time = time.strftime('%H:%M')
            if current_time == trigger.get('time'):
                return True

        return False

    async def _execute_actions(self, actions: List[Dict[str, Any]]):
        """Выполняет действия сценария"""
        for action in actions:
            action_type = action.get('type')

            if action_type == 'device_control':
                device_id = action.get('device_id')
                command = action.get('command', {})
                self.update_device(device_id, command)

            elif action_type == 'notification':
                message = action.get('message')
                print(f"📢 Notification: {message}")

    async def start_security_monitoring(self):
        """Фоновая задача: мониторинг охранной системы."""
        if not self._initialized:
            return

        while True:
            await asyncio.sleep(5)
            if not self.db:
                continue

            for device_id, device_data in self._devices.items():
                if device_data['device_type'] == 'security_sensor' and device_data['status'] == 'armed':
                    if random.random() < 0.01:
                        event_type = "Обнаружено движение" if "движен" in device_data['name'] else "Открытие двери"
                        event_value = f"{event_type} - {time.strftime('%H:%M:%S')}"

                        db_device = self.db.query(models.Device).filter(models.Device.id == device_id).first()
                        if db_device:
                            db_device.last_value = event_value
                            self.db.commit()
                            self._devices[device_id] = db_device.to_dict()

                        print(f"🔒 Событие безопасности: {device_data['name']} - {event_value}")


# Глобальный экземпляр диспетчера
device_manager = DeviceManager()