from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    device_type = Column(String)  # 'light', 'sensor_temperature', 'sensor_humidity', etc.
    location = Column(String)
    status = Column(String)  # 'on', 'off', 'locked', 'unlocked'

    communication_protocol = Column(String, default='wifi')  # zigbee, wifi, zwave, bluetooth
    protocol_device_id = Column(String)  # ID устройства в сети протокола
    protocol_config = Column(JSON)

    # Для лампочек
    brightness = Column(Integer, default=100)
    # Для датчиков
    last_value = Column(Float, nullable=True)
    unit = Column(String, nullable=True)
    # Для термостатов и датчиков влажности
    temperature = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    # Для умных замков
    locked = Column(Boolean, default=False)
    # Описание устройства (добавляем новое поле)
    description = Column(Text, nullable=True)

    manufacturer = Column(String, nullable=True)
    model = Column(String, nullable=True)
    firmware_version = Column(String, nullable=True)
    signal_strength = Column(Integer, nullable=True)

    online = Column(Boolean, default=True)
    last_seen = Column(DateTime, nullable=True)

    def to_dict(self):
        """Преобразует объект Device в словарь"""
        return {
            "id": self.id,
            "name": self.name,
            "device_type": self.device_type,
            "location": self.location,
            "status": self.status,
            "communication_protocol": self.communication_protocol,
            "protocol_device_id": self.protocol_device_id,
            "brightness": self.brightness,
            "last_value": self.last_value,
            "unit": self.unit,
            "temperature": self.temperature,
            "humidity": self.humidity,
            "locked": self.locked,
            "description": self.description,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "firmware_version": self.firmware_version,
            "signal_strength": self.signal_strength,
            "online": self.online,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None
        }

    def __repr__(self):
        return f"Device(id={self.id}, name='{self.name}', type='{self.device_type}')"


class SensorLog(Base):
    __tablename__ = "sensor_logs"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(Integer, index=True)
    value = Column(Float)
    unit = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())


class Scenario(Base):
    __tablename__ = "scenarios"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text)
    enabled = Column(Boolean, default=True)
    trigger = Column(Text)  # JSON с условием запуска
    actions = Column(Text)  # JSON со списком действий

    def to_dict(self):
        """Преобразует объект Scenario в словарь"""
        import json
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "trigger": json.loads(self.trigger) if self.trigger else {},
            "actions": json.loads(self.actions) if self.actions else []
        }