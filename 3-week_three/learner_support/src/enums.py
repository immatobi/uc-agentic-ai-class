from enum import Enum

class StatusEnum(str, Enum):
    RECEIVED = "received"
    ESCALATED = "escalated"
    TRIAGED = "triaged"

class CategoryEnum(str, Enum):
    TECHNICAL = "technical"
    BILLING = "billing"
    COURSE = "course_content"
    GENERAL = "general"

class PriorityEnum(str, Enum):
    LOW = "low"
    HIGH = "high"
    NORMAL = "normal"
    URGENT = "urgent"

# "urgent", "technical", "billing", "learning_support", "general"
class RouteEnum(str, Enum):
    TECHNICAL = "technical"
    BILLING = "billing"
    URGENT = "urgent"
    LEARNING = "learning_support"
    GENERAL = "general"
