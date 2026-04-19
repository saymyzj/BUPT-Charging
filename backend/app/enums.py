"""V3 public enum definitions for the active Flask app."""

from enum import Enum


class RequestStatus(Enum):
    WAITING_AREA = "WAITING_AREA"
    QUEUED = "QUEUED"
    CHARGING = "CHARGING"
    COMPLETED = "COMPLETED"
    COMPLETED_EARLY = "COMPLETED_EARLY"
    CANCELLED = "CANCELLED"
    FAULT_INTERRUPTED = "FAULT_INTERRUPTED"


class StationStatus(Enum):
    RUNNING = "RUNNING"
    SHUTDOWN = "SHUTDOWN"
    FAULT = "FAULT"


class ChargeMode(Enum):
    FAST = "FAST"
    SLOW = "SLOW"


class SessionStatus(Enum):
    PENDING = "PENDING"
    CHARGING = "CHARGING"
    COMPLETED = "COMPLETED"
    COMPLETED_EARLY = "COMPLETED_EARLY"
    FAULT_INTERRUPTED = "FAULT_INTERRUPTED"


class UserRole(Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class DispatchMode(Enum):
    NORMAL = "NORMAL"
    EXT_SINGLE_BATCH = "EXT_SINGLE_BATCH"
    EXT_FULL_BATCH = "EXT_FULL_BATCH"


class FaultDispatchMode(Enum):
    PRIORITY = "PRIORITY"
    TIME_ORDER = "TIME_ORDER"


class BatchEventType(Enum):
    FAULT = "FAULT"
    RECOVER = "RECOVER"
    RESTORE = "RESTORE"
    START = "START"
    SHUTDOWN = "SHUTDOWN"
    DISPATCH_MODE = "DISPATCH_MODE"
    FAULT_DISPATCH_MODE = "FAULT_DISPATCH_MODE"
