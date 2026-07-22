from typing import Literal
from langchain_core.tools import tool
from ..schemas.graph_schema import AgentState, ReviewResult
from datetime import date, datetime, timedelta

def decision_router(state: AgentState) -> Literal["knowledge","troubleshooting","escalation","onboarding","general"]:
    """Route the graph to the selected support branch, defaulting to general for invalid routes."""
    if state.route not in { "knowledge","troubleshooting","escalation","onboarding","general" }:
        return "general"
    return state.route

def review_router(state: AgentState) -> Literal["finalize", "revise"]:
    """Decide whether to finalize the answer or send it through another revision cycle."""
    review: ReviewResult = state.review
    count = state.revision_count or 0

    if review and review.passed:
        return "finalize"
    
    if count >= 2:
        return "finalize"
    
    return "revise"

def after_retrieval_router(state: AgentState) -> Literal["knowledge", "onboarding", "troubleshooting", "escalation"]:
    if state.route in {"knowledge", "onboarding", "troubleshooting", "escalation"}:
        return state.route

    return "knowledge"

@tool
def calculate_deadline(start_date: str, duration_days: int) -> dict:
    """
    Calculate an implementation deadline from a start date and duration.

    Args:
        start_date: Start date in YYYY-MM-DD format.
        duration_days: Number of calendar days for the rollout.

    Returns:
        A dictionary containing the start date, duration, and calculated deadline.
    """
    parsed_start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    deadline = parsed_start_date + timedelta(days=duration_days)

    return {
        "start_date": parsed_start_date.isoformat(),
        "duration_days": duration_days,
        "deadline": deadline.isoformat(),
    }

@tool
def estimate_account_size(
    users: int,
    contacts: int = 0,
    companies: int = 0,
    deals: int = 0,
) -> dict:
    """
    Estimate the customer account size for onboarding planning.

    Args:
        users: Number of users who will use Northstar CRM.
        contacts: Estimated number of contacts to migrate.
        companies: Estimated number of companies/accounts to migrate.
        deals: Estimated number of deals or opportunities to migrate.

    Returns:
        A dictionary with an account size label and onboarding complexity estimate.
    """
    total_records = contacts + companies + deals

    if users <= 5 and total_records <= 1000:
        size = "small"
        complexity = "low"
    elif users <= 25 and total_records <= 10000:
        size = "medium"
        complexity = "moderate"
    else:
        size = "large"
        complexity = "high"

    return {
        "users": users,
        "contacts": contacts,
        "companies": companies,
        "deals": deals,
        "total_records": total_records,
        "account_size": size,
        "implementation_complexity": complexity,
    }

def calculate_confidence(
    *,
    route: str,
    review_score: int,
    review_passed: bool,
    documents: list,
    sources: list,
    revision_count: int,
) -> float:
    
    """Calculate a normalized confidence score from review, retrieval, source, and revision signals."""
    confidence = review_score / 10

    if not review_passed:
        confidence = min(confidence, 0.65)

    if route != "general" and not documents:
        confidence = min(confidence, 0.35)

    if route in {"knowledge", "troubleshooting", "onboarding", "escalation"} and not sources:
        confidence -= 0.15

    if revision_count > 0:
        confidence -= min(revision_count * 0.05, 0.15)

    confidence = max(0.0, min(confidence, 1.0))

    return round(confidence, 2)

@tool
def plan_implementation_timeline(
    account_size: Literal["small", "medium", "large"],
    target_days: int | None = None,
) -> dict:
    """
    Generate a practical onboarding timeline based on account size.

    Args:
        account_size: Estimated account size: small, medium, or large.
        target_days: Optional target rollout duration in days.

    Returns:
        A dictionary containing recommended phases for implementation.
    """
    if account_size == "small":
        recommended_days = 14
        phases = [
            {
                "phase": "Days 1-2",
                "goal": "Confirm goals and rollout owner",
                "tasks": [
                    "Confirm business goals",
                    "Assign an internal rollout owner",
                    "Identify users and required permissions",
                ],
            },
            {
                "phase": "Days 3-5",
                "goal": "Prepare and import data",
                "tasks": [
                    "Review spreadsheet structure",
                    "Clean duplicate or incomplete records",
                    "Prepare CSV import file",
                    "Import contacts",
                ],
            },
            {
                "phase": "Days 6-10",
                "goal": "Configure sales workflow",
                "tasks": [
                    "Set up pipeline stages",
                    "Invite users",
                    "Connect email if needed",
                    "Validate imported records",
                ],
            },
            {
                "phase": "Days 11-14",
                "goal": "Train and launch",
                "tasks": [
                    "Train users on daily workflows",
                    "Review adoption blockers",
                    "Confirm launch readiness",
                ],
            },
        ]

    elif account_size == "medium":
        recommended_days = 30
        phases = [
            {
                "phase": "Week 1",
                "goal": "Discovery and rollout planning",
                "tasks": [
                    "Confirm goals and success criteria",
                    "Assign rollout owner",
                    "Review existing tools and data sources",
                    "Map user roles and permissions",
                ],
            },
            {
                "phase": "Week 2",
                "goal": "Data preparation and CRM setup",
                "tasks": [
                    "Clean contacts, companies, and deals",
                    "Prepare CSV import files",
                    "Configure pipeline stages",
                    "Invite pilot users",
                ],
            },
            {
                "phase": "Week 3",
                "goal": "Pilot and training",
                "tasks": [
                    "Run pilot import",
                    "Validate records",
                    "Train sales users",
                    "Collect feedback from pilot users",
                ],
            },
            {
                "phase": "Week 4",
                "goal": "Launch and optimization",
                "tasks": [
                    "Complete final import",
                    "Launch team workflow",
                    "Monitor adoption",
                    "Resolve rollout blockers",
                ],
            },
        ]

    else:
        recommended_days = 45
        phases = [
            {
                "phase": "Week 1",
                "goal": "Discovery and implementation planning",
                "tasks": [
                    "Confirm executive sponsor",
                    "Assign implementation owner",
                    "Define rollout scope",
                    "Document success criteria",
                ],
            },
            {
                "phase": "Weeks 2-3",
                "goal": "Data audit and configuration",
                "tasks": [
                    "Audit existing data sources",
                    "Clean and normalize records",
                    "Configure roles, permissions, and pipeline stages",
                    "Plan staged migration",
                ],
            },
            {
                "phase": "Week 4",
                "goal": "Pilot rollout",
                "tasks": [
                    "Invite pilot users",
                    "Run test import",
                    "Validate records and workflows",
                    "Collect pilot feedback",
                ],
            },
            {
                "phase": "Weeks 5-6",
                "goal": "Full rollout and adoption",
                "tasks": [
                    "Complete production migration",
                    "Train all users",
                    "Monitor adoption",
                    "Review risks and unresolved issues",
                ],
            },
        ]

    return {
        "account_size": account_size,
        "target_days": target_days,
        "recommended_days": recommended_days,
        "timeline_is_compressed": target_days is not None and target_days < recommended_days,
        "phases": phases,
    }
