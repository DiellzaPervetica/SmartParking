from enum import Enum


class EventType(str, Enum):
    STATE_CHANGE = "state_change"
    HEARTBEAT = "heartbeat"


class ClassificationLabel(str, Enum):
    FREE = "free"
    OCCUPIED = "occupied"
    NORMAL = "normal"
    SUSPICIOUS = "suspicious"
    SENSOR_FAULT = "sensor_fault"


class AnomalyLabel(str, Enum):
    NORMAL = "normal"
    DISTANCE_OUTLIER = "distance_outlier"
    LOW_BATTERY = "low_battery"
    SIGNAL_WEAK = "signal_weak"
    STUCK_SENSOR = "stuck_sensor"
    SEQUENCE_GAP = "sequence_gap"


class PriceTier(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
