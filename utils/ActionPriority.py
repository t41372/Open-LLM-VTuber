from enum import Enum


class ActionPriority(Enum):
    REALTIME = 0  # Highest priority
    NORMAL = 1
    LOW = 2  # Lowest priority