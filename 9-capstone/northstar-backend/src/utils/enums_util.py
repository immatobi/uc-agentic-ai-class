from enum import Enum

class RouteEnum(str, Enum):
    KNOWLEDGE = "knowledge"
    TROUBLESHOOTING = "troubleshooting"
    ESCALATION = "escalation"
    ONBOARDING = "onboarding"
    GENERAL = "general"

class PriorityEnum(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    URGENT = "urgent"

class CategoryEnum(str, Enum):
    TECHNICAL = "technical"
    BILLING = "billing"
    SECURITY = "security"
    CUSTOMER = "customer"
    ENGINEERING = "engineering"

class TeamEnum(str, Enum):
    TECHNICAL = "technical_support"
    BILLING = "billing_support"
    SECURITY = "security_team"
    CUSTOMER = "customer_success"
    ENGINEERING = "engineering_on_call"