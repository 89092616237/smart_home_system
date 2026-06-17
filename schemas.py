from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
from enum import Enum
import json

class DeviceType(str, Enum):
    LIGHT = "light"
    SENSOR_TEMPERATURE = "sensor_temperature"
    SENSOR_HUMIDITY = "sensor_humidity"
    SECURITY_SENSOR = "security_sensor"
    SMART_LOCK = "smart_lock"
    SMART_PLUG = "smart_plug"
    CAMERA = "camera"
    THERMOSTAT = "thermostat"

class TriggerType(str, Enum):
    TIME = "time"
    DEVICE_STATUS = "device_status"
    SENSOR_VALUE = "sensor_value"
    MANUAL = "manual"

class ActionType(str, Enum):
    DEVICE_CONTROL = "device_control"
    NOTIFICATION = "notification"
    SCENE_ACTIVATION = "scene_activation"

# Базовый класс для всех схем
class BaseSchema(BaseModel):
    class Config:
        from_attributes = True

# Схемы для устройств
class DeviceBase(BaseSchema):
    name: str
    device_type: str
    location: str
    description: Optional[str] = None  # Добавляем описание

class DeviceCreate(DeviceBase):
    pass

class Device(DeviceBase):
    id: int
    status: Optional[str] = None
    brightness: Optional[int] = None
    last_value: Optional[float] = None
    unit: Optional[str] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    locked: Optional[bool] = None

class DeviceUpdate(BaseSchema):
    status: Optional[str] = None
    brightness: Optional[int] = None
    locked: Optional[bool] = None
    temperature: Optional[float] = None
    description: Optional[str] = None  # Добавляем для обновления

# Схемы для сценариев
class Trigger(BaseSchema):
    type: TriggerType
    device_id: Optional[int] = None
    condition: Optional[str] = None
    value: Optional[Any] = None
    time: Optional[str] = None

class Action(BaseSchema):
    type: ActionType
    device_id: Optional[int] = None
    command: Optional[Dict[str, Any]] = None
    message: Optional[str] = None

class ScenarioBase(BaseSchema):
    name: str
    description: Optional[str] = None
    enabled: bool = True
    trigger: Trigger
    actions: List[Action]

class ScenarioCreate(ScenarioBase):
    pass

class Scenario(ScenarioBase):
    id: int

class ScenarioResponse(BaseSchema):
    id: int
    name: str
    description: Optional[str] = None
    enabled: bool = True
    trigger: Dict[str, Any]
    actions: List[Dict[str, Any]]

    @validator('trigger', pre=True)
    def validate_trigger(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    @validator('actions', pre=True)
    def validate_actions(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

# Специальная схема для ответа API (совместимая с DeviceManager)
class DeviceResponse(BaseSchema):
    id: int
    name: str
    device_type: str
    location: str
    status: Optional[str] = None
    brightness: Optional[int] = None
    last_value: Optional[float] = None
    unit: Optional[str] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    locked: Optional[bool] = None
    description: Optional[str] = None  # Добавляем описание