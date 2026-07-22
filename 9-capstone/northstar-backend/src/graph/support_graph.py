from typing import Literal
import json
from datetime import date

from langgraph.graph import StateGraph, START, END
from ..schemas.graph_schema import AgentState, ReviewResult
from ..services.llm_service import get_llm, get_llm_text
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.vectorstores import VectorStoreRetriever
from ..utils.constants_util import CUSTOMER_MEMORY_STORE, ALLOWED_MEMORY_FIELDS
from ..agents.tools import (
    decision_router, 
    review_router,
    calculate_deadline,
    estimate_account_size,
    plan_implementation_timeline,
    calculate_confidence,
    after_retrieval_router
)


def parse_llm_json(content: str, fallback: dict | None = None) -> dict:
    text = content.strip()

    if text.startswith("```"):
        text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1:
        text = text[start:end + 1]

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        if fallback is not None:
            return fallback
        raise ValueError(f"LLM returned invalid JSON: {content[:500]}") from exc


# question router node
def question_router_node(state: AgentState) -> dict:
    question = state.question
    llm = get_llm()

    prompt = f"""
    You are NorthstarAI's routing assistant and a highly intelligent request classifier.

    Your job is to decide the intent of the question supplied and determine wether the user's question is about
    - troubleshooting an issue, 
    - needs grounded knowledge about the platform, 
    - about general knowledge,
    - about onboarding on the platform or
    - needs an escalation for support

    ROUTE AS:
    - "knowledge" if the question is about product features, pricing, plan limits, integrations, settings, documentation questions.
    - "esacalation" if question intent is about billing disputes, urgent outages, locked accounts, security concerns, angry customer requests, time-sensitive business impact.
    - "onboarding" if question intent is about setup plans, team rollout, migration checklist, training plan, adoption planning.
    - "troubleshooting" if question is about login problems, duplicate data, imports failing, email sync not working, workflow automation issues.
    - "general" if the question is a safe general questions unrelated to Northstar CRM.

    QUESTION:
    {question}

    Return only one word in the list: knowledge, escalation, onboarding, troubleshooting or general.
    """

    response = llm.invoke(prompt)
    route = get_llm_text(response.content).strip().lower()

    return {
        "route": route
    }

# Retrieve docs node
# Usage: graph.add_node("retrieve_docs_node", retrieve_docs_node(retriever))
def retrieve_docs_node(retriever: VectorStoreRetriever):
    def get_docs(state: AgentState) -> dict:
        question = state.question
        documents = retriever.invoke(question)
        return {"documents": documents}

    return get_docs

# Knowledge answer node
def knowledge_answer_node(state: AgentState) -> dict:
    question = state.question
    documents = state.documents
    llm = get_llm()

    # Define the context -> The Augmentation part of the R-A-G
    context = "\n\n".join(
        [
            f"Source: {doc.metadata.get('source')}\nContent: {doc.page_content}"
            for doc in documents
        ]
    )

    prompt = f"""
    You are NorthstarAI, a customer support professional for a growing software business.
    You have 15+ years of experience in leading customer support teams in different companies.
    Your job is to answer the customer's question using the context provided.

    Answer the customer's question using ONLY the context below.

    Rules:
    - Do not invent information.
    - If the answer is not found in the context, say:
      "I could not find this information in the Northstar CRM knowledge base."
    - Mention the source document when possible.
    - Be clear and helpful.

    User Question:
    {question}

    Context:
    {context}
    """

    response = llm.invoke(prompt)

    return {
        "answer": response.content
    }

# Onboarding node
def onboarding_plan_node(state: AgentState) -> dict:
    question = state.question
    documents = state.documents
    llm = get_llm()
    today = date.today().isoformat()

    # Define the context -> The Augmentation part of the R-A-G
    context = "\n\n".join(
        [
            f"Source: {doc.metadata.get('source')}\nContent: {doc.page_content}"
            for doc in documents
        ]
    )


    extract_prompt = f"""
    Extract onboarding planning inputs from the user request.

    Return ONLY valid JSON with this shape:

    {{
        "users": 5,
        "contacts": 0,
        "companies": 0,
        "deals": 0,
        "start_date": "{today}",
        "target_days": 30
    }}

    Rules:
    - Use null for unknown values.
    - Infer target_days only when the user gives a clear timeline.
    - Do not invent record counts.
    - If start_date is not provided, use today's date: {today}.

    User Request:
    {question}
    """

    extract_response = llm.invoke(extract_prompt)
    planning_inputs = parse_llm_json(
        extract_response.content,
        fallback={
            "users": None,
            "contacts": None,
            "companies": None,
            "deals": None,
            "start_date": today,
            "target_days": None,
        },
    )

    tool_context = {
        "deadline": None,
        "account_size": None,
        "implementation_timeline": None,
    }

    users = planning_inputs.get("users") or 1
    contacts = planning_inputs.get("contacts") or 0
    companies = planning_inputs.get("companies") or 0
    deals = planning_inputs.get("deals") or 0
    start_date = planning_inputs.get("start_date") or today
    target_days = planning_inputs.get("target_days") or 30

    account_size_result = estimate_account_size.invoke(
        {
            "users": users,
            "contacts": contacts,
            "companies": companies,
            "deals": deals,
        }
    )

    timeline_result = plan_implementation_timeline.invoke(
        {
            "account_size": account_size_result["account_size"],
            "target_days": target_days,
        }
    )

    deadline_result = calculate_deadline.invoke(
        {
            "start_date": start_date,
            "duration_days": target_days,
        }
    )

    tool_context = {
        "planning_inputs": planning_inputs,
        "account_size": account_size_result,
        "implementation_timeline": timeline_result,
        "deadline": deadline_result,
    }

    prompt = f"""
    You are NorthstarAI, a senior customer success onboarding specialist for Northstar CRM.

    Your job is to generate a practical onboarding or rollout plan from the customer's request,
    the retrieved knowledge-base context, and the available planning tool outputs.

    The onboarding branch must:
    1. Extract structured details from the user request.
    2. Identify missing information.
    3. Generate a practical onboarding or rollout plan.
    4. Include assumptions, checklist, risks, owners, and next actions.
    5. Use tool outputs for deadline calculations, account-size estimates, and implementation timeline planning.
    6. Produce a plan that can be reviewed and improved by a later review node.

    Use ONLY the context provided when describing Northstar CRM product behavior,
    onboarding steps, migration guidance, setup expectations, or success criteria.
    Do not invent product capabilities, policies, plan limits, or internal processes.

    Use the tool outputs as planning support:
    - Use "planning_inputs" to understand extracted users, records, start date, and target timeline.
    - Use "account_size" to estimate rollout complexity.
    - Use "implementation_timeline" to shape the phased rollout plan.
    - Use "deadline" to mention calculated launch dates when available.
    - If "timeline_is_compressed" is true, include it as a risk and propose a mitigation.

    Return ONLY valid JSON.
    Do not wrap the JSON in markdown.
    Do not add commentary before or after the JSON.

    Return this exact object shape:

    {{
        "request_details": {{
            "team_size": "5 sales reps",
            "use_case": "Move a small sales team from spreadsheets into Northstar CRM.",
            "timeline": "30 days",
            "start_date": "2026-07-17",
            "target_deadline": "2026-08-16",
            "current_tools": [
            "spreadsheets"
            ],
            "goals": [
            "Import contacts",
            "Set up pipeline tracking",
            "Train the sales team"
            ],
            "estimated_account_size": "small",
            "implementation_complexity": "low"
        }},
        "missing_information": [
            {{
            "field": "admin_owner",
            "question": "Who will be the internal admin or rollout owner?",
            "required": true
            }},
            {{
            "field": "data_source",
            "question": "Where are the existing contacts and deals stored today?",
            "required": true
            }}
        ],
        "assumptions": [
            "The team wants to begin with core CRM setup before advanced automation.",
            "The rollout can be completed in phases over the requested timeline."
        ],
        "onboarding_plan": [
            {{
            "phase": "Week 1",
            "goal": "Prepare workspace and data",
            "tasks": [
                "Confirm the rollout owner.",
                "Review the existing spreadsheet structure.",
                "Prepare contacts for CSV import."
            ],
            "owner": "customer_success"
            }},
            {{
            "phase": "Week 2",
            "goal": "Configure CRM basics",
            "tasks": [
                "Set up users and roles.",
                "Configure pipeline stages.",
                "Import cleaned contact data."
            ],
            "owner": "customer_success"
            }}
        ],
        "checklist": [
            "Confirm rollout owner",
            "Clean spreadsheet data",
            "Prepare CSV import file",
            "Invite team members",
            "Configure pipeline stages",
            "Train users on daily workflow"
        ],
        "risks": [
            {{
            "risk": "Poor spreadsheet data quality may delay import.",
            "mitigation": "Review required fields and clean duplicate or incomplete records before import."
            }}
        ],
        "next_actions": [
            "Confirm the rollout owner.",
            "Share the current spreadsheet structure.",
            "Choose a target go-live date."
        ],
        "customer_message": "## Onboarding summary\\nThis plan helps your team move from spreadsheets into Northstar CRM over 30 days.\\n\\n## Details captured\\n- Team size: 5 sales reps\\n- Timeline: 30 days\\n- Estimated account size: small\\n- Implementation complexity: low\\n- Current tool: spreadsheets\\n\\n## Missing information\\n- Who will be the internal admin or rollout owner?\\n- Where are the existing contacts and deals stored today?\\n\\n## Assumptions\\n- The team wants to begin with core CRM setup before advanced automation.\\n\\n## Rollout plan\\n1. **Week 1: Prepare workspace and data**\\n   - Confirm the rollout owner.\\n   - Review the spreadsheet structure.\\n   - Prepare contacts for CSV import.\\n\\n## Checklist\\n- Confirm rollout owner\\n- Clean spreadsheet data\\n- Prepare CSV import file\\n\\n## Risks\\n- Poor spreadsheet data quality may delay import. Mitigation: clean duplicate or incomplete records before import.\\n\\n## Next actions\\n1. Confirm the rollout owner.\\n2. Share the current spreadsheet structure.\\n3. Choose a target go-live date.\\n\\n## Sources\\n- `onboarding_checklist.txt`",
        "priority": "normal",
        "assigned_team": "customer_success",
        "sources": [
            "onboarding_checklist.txt"
        ]
    }}

    Markdown requirements for "customer_message":
    - Use Markdown headings.
    - Include this section order exactly:
    1. "## Onboarding summary"
    2. "## Details captured"
    3. "## Missing information" only if missing_information is not empty
    4. "## Assumptions"
    5. "## Rollout plan"
    6. "## Checklist"
    7. "## Risks"
    8. "## Next actions"
    9. "## Sources" only if sources is not empty
    - Use numbered phases for the rollout plan.
    - Use bullet points for checklist, risks, and captured details.
    - Mention calculated deadlines when deadline tool output is available.
    - Mention account size and implementation complexity when account-size tool output is available.
    - Call out compressed timelines as risks when implementation_timeline.timeline_is_compressed is true.
    - Keep the tone practical, direct, and customer-success oriented.
    - Do not expose raw JSON inside customer_message.

    Allowed priority values:
    - "low"
    - "normal"
    - "urgent"

    Allowed assigned_team values:
    - "technical_support"
    - "billing_support"
    - "security_team"
    - "customer_success"
    - "engineering_on_call"

    Field rules:
    - "request_details" must extract useful structured details from the user's request.
    - Use null for request_details fields that are not provided or cannot be inferred.
    - "request_details.start_date" should come from tool_context.deadline.start_date when available.
    - "request_details.target_deadline" should come from tool_context.deadline.deadline when available.
    - "request_details.estimated_account_size" should come from tool_context.account_size.account_size when available.
    - "request_details.implementation_complexity" should come from tool_context.account_size.implementation_complexity when available.
    - "missing_information" must include questions needed to improve the plan.
    - "assumptions" must clearly state reasonable assumptions made because of missing details.
    - "onboarding_plan" must be practical and phased.
    - Prefer phases from tool_context.implementation_timeline.phases when available, but adapt them to the customer's request and retrieved context.
    - "checklist" must contain concrete setup or rollout tasks.
    - "risks" must include likely rollout risks and mitigations.
    - If tool_context.implementation_timeline.timeline_is_compressed is true, include a timeline compression risk.
    - "next_actions" must list the immediate next steps.
    - "customer_message" must be valid Markdown and ready to show directly to the customer.
    - "priority" should usually be "normal" unless the onboarding request is time-sensitive.
    - "assigned_team" should usually be "customer_success".
    - "sources" must list the source document names used from the context.
    - If the context is empty or does not contain onboarding guidance, still create a safe high-level onboarding plan, but do not claim it is documented Northstar CRM behavior. Keep "sources" as an empty list.

    User Request:
    {question}

    Context:
    {context}

    Tool Outputs:
    {json.dumps(tool_context, indent=2)}
    """

    response = llm.invoke(prompt)
    onboarding = parse_llm_json(response.content)

    return {
        "answer": onboarding["customer_message"],
        "priority": onboarding["priority"],
        "assigned_team": onboarding["assigned_team"],
        "sources": onboarding.get("sources", []),
        "memory_updates": [
            {
                "type": "onboarding",
                "request_details": onboarding["request_details"],
                "missing_information": onboarding["missing_information"],
                "assumptions": onboarding["assumptions"],
                "onboarding_plan": onboarding["onboarding_plan"],
                "checklist": onboarding["checklist"],
                "risks": onboarding["risks"],
                "next_actions": onboarding["next_actions"],
                "tool_context": tool_context,
            }
        ],
    }

# troubleshooting node
def troubleshoot_plan_node(state: AgentState) -> dict:
    question = state.question
    documents = state.documents
    llm = get_llm()

    # Define the context -> The Augmentation part of the R-A-G
    context = "\n\n".join(
        [
            f"Source: {doc.metadata.get('source')}\nContent: {doc.page_content}"
            for doc in documents
        ]
    )

    prompt = f"""
    You are NorthstarAI, a senior customer support troubleshooting specialist for Northstar CRM.

    Your job is to build a troubleshooting response for product issues that can usually be handled
    without immediate escalation.

    You must:
    1. Identify the likely issue category.
    2. Ask for missing details when necessary.
    3. Provide ordered troubleshooting steps.
    4. Include clear "when to escalate" criteria.
    5. Use retrieved documentation when the issue depends on documented Northstar CRM behavior.

    Use ONLY the context provided when describing Northstar CRM product behavior.
    Do not invent product behavior, internal tools, policies, plan limits, or unsupported fixes.

    Return ONLY valid JSON.
    Do not wrap the JSON in markdown.
    Do not add commentary before or after the JSON.

    Return this exact object shape:

    {{
        "issue_category": "email_sync",
        "summary": "A short summary of the likely issue.",
        "missing_details": [
            {{
            "field": "email_provider",
            "question": "Are you syncing Gmail or Microsoft 365?",
            "required": true
            }}
        ],
        "troubleshooting_steps": [
            {{
            "step": 1,
            "title": "Confirm the connected account",
            "instruction": "Check that the correct email account is connected in Northstar CRM.",
            "expected_result": "The intended mailbox is connected and available for sync."
            }}
        ],
        "when_to_escalate": [
            "Escalate if the issue affects multiple users.",
            "Escalate if the documented steps do not resolve the issue.",
            "Escalate if the issue is urgent, security-sensitive, or causing business-critical impact."
        ],
        "customer_message": "## Likely issue\\nThis appears to be an email sync issue.\\n\\n## Details I need\\n- Are you syncing Gmail or Microsoft 365?\\n\\n## Troubleshooting steps\\n1. **Confirm the connected account**\\n   Check that the correct email account is connected in Northstar CRM.\\n   Expected result: The intended mailbox is connected and available for sync.\\n\\n## When to escalate\\n- Escalate if the issue affects multiple users.\\n- Escalate if the documented steps do not resolve the issue.",
        "escalation_needed": false,
        "priority": "normal",
        "assigned_team": "technical_support",
    }}

    Markdown requirements for "customer_message":
    - Use Markdown headings.
    - Include this section order exactly:
    1. "## Likely issue"
    2. "## Details I need" only if missing_details is not empty
    3. "## Troubleshooting steps"
    4. "## When to escalate"
    5. "## Sources" only if sources is not empty
    - Use numbered steps for troubleshooting.
    - Bold each troubleshooting step title.
    - Include expected results where useful.
    - Keep the tone professional, direct, and helpful.
    - Do not expose raw JSON inside customer_message.

    Allowed issue_category values:
    - "csv_import"
    - "email_sync"
    - "login_access"
    - "duplicate_contacts"
    - "slow_loading"
    - "pipeline_issue"
    - "integration_issue"
    - "general_troubleshooting"

    Allowed priority values:
    - "low"
    - "normal"
    - "urgent"

    Allowed assigned_team values:
    - "technical_support"
    - "billing_support"
    - "security_team"
    - "customer_success"
    - "engineering_on_call"

    Field rules:
    - "issue_category" must be the closest matching category.
    - "summary" must briefly describe the likely issue.
    - "missing_details" must include only details needed to troubleshoot safely.
    - If no details are missing, return an empty list for "missing_details".
    - "troubleshooting_steps" must be ordered and practical.
    - "when_to_escalate" must explain when the customer should be routed to a human team.
    - "customer_message" must be valid Markdown and ready to show directly to the customer.
    - "escalation_needed" should usually be false for normal troubleshooting.
    - Set "escalation_needed" to true only when the issue is urgent, security-sensitive, affects multiple users, has major business impact, or cannot be handled with documented steps.
    - "priority" must reflect urgency.
    - "assigned_team" should usually be "technical_support" unless the issue clearly belongs to another allowed team.
    - "sources" must list the source document names used from the context.
    - Never ask for passwords, one-time passcodes, full card numbers, CVV, full bank account numbers, or secret credentials.

    If the context is empty or does not contain relevant troubleshooting guidance, still help with safe general troubleshooting, but do not claim it is documented Northstar CRM behavior. In that case:
    - Use "general_troubleshooting" as the issue_category.
    - Ask for the missing details needed to continue.
    - Keep "sources" as an empty list.

    User Question:
    {question}

    Context:
    {context}
    """

    response = llm.invoke(prompt)
    troubleshooting = parse_llm_json(response.content)

    return {
        "answer": troubleshooting["customer_message"],
        "priority": troubleshooting["priority"],
        "assigned_team": troubleshooting["assigned_team"],
        "memory_updates": [
            {
                "type": "troubleshooting",
                "issue_category": troubleshooting["issue_category"],
                "summary": troubleshooting["summary"],
                "missing_details": troubleshooting["missing_details"],
                "troubleshooting_steps": troubleshooting["troubleshooting_steps"],
                "when_to_escalate": troubleshooting["when_to_escalate"],
                "escalation_needed": troubleshooting["escalation_needed"],
            }
        ],
    }

# escalation node
def escalation_node(state: AgentState) -> dict:
    question = state.question
    documents = state.documents
    llm = get_llm()

    # Define the context -> The Augmentation part of the R-A-G
    context = "\n\n".join(
        [
            f"Source: {doc.metadata.get('source')}\nContent: {doc.page_content}"
            for doc in documents
        ]
    )

    prompt = f"""
    You are NorthstarAI, a customer support escalation specialist for Northstar CRM.

    Your job is to review the customer's question and the provided knowledge-base context,
    then produce a structured escalation object for urgent, sensitive, billing, access,
    security, technical, or customer-success issues.

    Use ONLY the context provided. Do not invent policy, SLA, team names, priorities,
    or collection requirements that are not supported by the context.

    Escalation examples include:
    - "I was charged twice this month."
    - "My team cannot log in and we have a sales demo in one hour."
    - "I think someone accessed our account without permission."
    - "Our email sync has been down all day and we are losing deals."

    Allowed priority values:
    - "low"
    - "normal"
    - "urgent"

    Allowed assigned_team values:
    - "billing_support"
    - "technical_support"
    - "security_team"
    - "customer_success"
    - "engineering_on_call"

    Return ONLY valid JSON.
    Do not wrap the JSON in markdown.
    Do not add commentary before or after the JSON.

    The JSON object must match this shape exactly:

    {{
        "priority": "urgent",
        "assigned_team": "technical_support",
        "next_steps": [
            "A clear action the customer should take now.",
            "Another clear action the support team should take next."
        ],
        "language": "## Escalation summary\\nThis issue should be escalated because it is urgent and affects business activity.\\n\\n## Priority\\nUrgent\\n\\n## Assigned team\\nTechnical support\\n\\n## Next steps\\n1. Collect the affected workspace or account ID.\\n2. Confirm how many users are affected.\\n3. Route the case to technical support for immediate review.\\n\\n## Information needed\\n- Workspace or account ID\\n- A short issue summary\\n- Time the issue started\\n\\n## Sources\\n- `escalation_policy.txt`",
        "metadata": [
            {{
            "field": "customer_id",
            "description": "The customer's account or workspace identifier.",
            "required": true
            }},
            {{
            "field": "issue_summary",
            "description": "A short summary of the reported issue.",
            "required": true
            }}
        ],
    }}

    Markdown requirements for "language":
    - Use Markdown headings.
    - Include this section order exactly:
    1. "## Escalation summary"
    2. "## Priority"
    3. "## Assigned team"
    4. "## Next steps"
    5. "## Information needed"
    6. "## Sources" only if sources is not empty
    - Use numbered steps for "Next steps".
    - Use bullet points for "Information needed".
    - Keep the tone calm, professional, and action-oriented.
    - Do not expose raw JSON inside language.
    - Do not tell the customer that internal systems or private tools were used.

    Field rules:
    - "priority" must be one of the allowed priority values.
    - "assigned_team" must be one of the allowed assigned_team values.
    - "next_steps" must be a list of practical steps for the customer or support team.
    - "language" must be valid Markdown and ready to show directly to the customer.
    - "metadata" must list only safe information the human team should collect next.
    - "sources" must list the source document names used from the context.
    - Never request passwords, one-time passcodes, full card numbers, CVV, full bank account numbers, or sensitive secrets.
    - If the context does not contain escalation guidance, return this JSON object:

    {{
        "priority": "normal",
        "assigned_team": "customer_success",
        "next_steps": [
            "Collect a short summary of the issue.",
            "Route the case to the support team for manual review."
        ],
        "language": "## Escalation summary\\nI could not find escalation guidance for this issue in the Northstar CRM knowledge base. This should be routed to the support team for manual review.\\n\\n## Priority\\nNormal\\n\\n## Assigned team\\nCustomer success\\n\\n## Next steps\\n1. Collect a short summary of the issue.\\n2. Confirm the affected account or workspace.\\n3. Route the case to the support team for manual review.\\n\\n## Information needed\\n- Issue summary\\n- Affected account or workspace ID",
        "metadata": [
            {{
            "field": "issue_summary",
            "description": "A short summary of the customer's issue.",
            "required": true
            }},
            {{
            "field": "customer_id",
            "description": "The affected account or workspace identifier.",
            "required": false
            }}
        ],
    }}

    User Question:
    {question}

    Context:
    {context}
    """

    response = llm.invoke(prompt)
    escalation = parse_llm_json(response.content)

    return {
        "priority": escalation["priority"],
        "assigned_team": escalation["assigned_team"],
        "answer": escalation["language"],
        "memory_updates": [
            {
                "type": "escalation",
                "priority": escalation["priority"],
                "assigned_team": escalation["assigned_team"],
                "next_steps": escalation["next_steps"],
                "metadata": escalation["metadata"],
            }
        ],
    }

# Generate general answer to general questions
def general_answer_node(state: AgentState) -> dict:
    question = state.question
    llm = get_llm()

    prompt = f"""
    You are NorthstarAI, a customer support assistant for Northstar CRM.

    The user's question was classified as general, meaning it does not require retrieved
    Northstar CRM knowledge-base context.

    Answer clearly and briefly.

    Rules:
    - If the question is a safe general question, answer it directly.
    - If the user asks about Northstar CRM product behavior, pricing, security, billing,
    onboarding, troubleshooting, or account-specific details, say that you need to check
    the Northstar CRM knowledge base or route the question to the right support path.
    - Do not invent Northstar CRM product details.
    - Do not provide legal, financial, medical, security-invasive, or harmful instructions.
    - Keep the response concise and professional.
    - Return a Markdown-formatted answer.

    Question:
    {question}
    """

    response = llm.invoke(prompt)

    return {
        "answer": response.content,
        "documents": [],
        "sources": [],
        "priority": "low",
        "assigned_team": "customer_success",
    }

# review answer node
def review_answer_node(state: AgentState) -> dict:
    question = state.question
    answer = state.answer
    documents = state.documents
    llm = get_llm()

    if state.route == 'general':
        return {
            "review": {
                "score": 10,
                "passed": True,
                "feedback": "General answer. No document grounding required.",
            },
            "confidence": 0.85,
        }
    
    # Define the context -> The Augmentation R-A-G part
    context = "\n\n".join(
        [
            f"Source: {doc.metadata.get('source')}\nContent: {doc.page_content}"
            for doc in documents
        ]
    )

    prompt = f"""
    You are reviewing a Northstar CSA support answer before it is sent to the customer.

    Review the generated answer for:
    1. Grounding in the retrieved context.
    2. Helpfulness and clarity.
    3. No invented Northstar CRM product behavior.
    4. No unsafe requests for passwords, OTPs, CVV, full card numbers, full bank account numbers, or secret credentials.
    5. Correct handling for the route: {state.route}.
    6. For onboarding, the answer should include assumptions, checklist, risks, owners, and next actions.
    7. For troubleshooting, the answer should include likely issue category, missing details, ordered steps, and when-to-escalate criteria.
    8. For escalation, the answer should include priority, assigned team, next steps, and safe information needed.

    Return ONLY valid JSON with this exact shape:

    {{
        "score": 8,
        "passed": true,
        "feedback": "The answer is grounded, clear, and ready to send."
    }}

    Scoring:
    - 9-10: Strong answer, grounded, complete, ready to send.
    - 7-8: Acceptable answer with minor issues.
    - 4-6: Needs revision.
    - 1-3: Poor, unsafe, unsupported, or missing major requirements.

    Set "passed" to true only if the answer is safe, useful, and sufficiently grounded.
    Set "passed" to false if the answer invents unsupported details, misses key requirements,
    or asks for unsafe sensitive information.

    Question:
    {question}

    Route:
    {state.route}

    Retrieved Context:
    {context}

    Generated Answer:
    {answer}
    """

    try:
        response = llm.invoke(prompt)
        review = parse_llm_json(response.content)
    except Exception as exc:
        review = {
            "score": 5,
            "passed": True,
            "feedback": f"Review service unavailable. The answer was not fully reviewed: {type(exc).__name__}",
        }

    confidence = calculate_confidence(
        route=state.route,
        review_score=review["score"],
        review_passed=review["passed"],
        documents=documents,
        sources=state.sources or [],
        revision_count=state.revision_count or 0,
    )

    return {
        "review": {
            "score": review["score"],
            "passed": review["passed"],
            "feedback": review["feedback"],
        },
        "confidence": confidence,
    }

# revise answer node
def revise_node(state: AgentState) -> dict:
    question = state.question
    answer = state.answer
    documents = state.documents or []
    review = state.review
    revision_count = state.revision_count or 0
    llm = get_llm()

    context = "\n\n".join(
        [
            f"Source: {doc.metadata.get('source')}\nContent: {doc.page_content}"
            for doc in documents
        ]
    )

    review_feedback = review.feedback if review else "No review feedback provided."

    prompt = f"""
    You are NorthstarAI, revising a customer support answer before it is sent.

    Your job is to improve the answer based on the review feedback.

    Revision requirements:
    - Make sure the answer actually addresses the customer's question.
    - For knowledge, onboarding, troubleshooting, and escalation answers, use only the retrieved context when describing Northstar CRM behavior.
    - Add source references when the answer depends on retrieved context.
    - Remove unsupported refund, legal, security, SLA, billing, or policy promises.
    - Make the answer clear, practical, and actionable.
    - Preserve Markdown formatting.
    - Do not expose internal review notes, raw JSON, or chain-of-thought.
    - Do not ask for passwords, one-time passcodes, CVV, full card numbers, full bank account numbers, or secret credentials.

    Route:
    {state.route}

    Customer Question:
    {question}

    Retrieved Context:
    {context}

    Current Answer:
    {answer}

    Review Feedback:
    {review_feedback}

    Return only the revised customer-facing answer in Markdown.
    """

    response = llm.invoke(prompt)

    return {
        "answer": response.content,
        "revision_count": revision_count + 1,
    }

# Finalize node
def finalize_node(state: AgentState) -> dict:
    answer = state.answer
    review: ReviewResult = state.review

    if review and not review.passed:
        final_answer = """
        I’m not confident enough to send the previous answer as-is.

        I could not verify enough information in the Northstar CRM knowledge base to answer this accurately. Please route this to the appropriate Northstar support team for manual review.
        Review note: {review.feedback}
        """.strip()
    else:
        final_answer = answer

    return {
        "final_answer": final_answer
    }

# Save memory node
def save_memory_node(state: AgentState) -> dict:
    customer_id = state.customer_id
    updates = state.memory_updates or []

    if customer_id not in CUSTOMER_MEMORY_STORE:
        CUSTOMER_MEMORY_STORE[customer_id] = {
            "company_type": None,
            "plan_tier": None,
            "team_size": None,
            "preferred_support_tone": None,
            "active_goal": None,
        }

    saved_facts = []

    for update in updates:
        if update.get("type") != "customer_fact":
            continue

        field = update.get("field")
        value = update.get("value")
        confidence = update.get("confidence", 0)

        if field not in ALLOWED_MEMORY_FIELDS:
            continue

        if not value or confidence < 0.75:
            continue

        CUSTOMER_MEMORY_STORE[customer_id][field] = value

        saved_facts.append(
            {
                "field": field,
                "value": value,
                "confidence": confidence,
            }
        )

    return {
        "memory_updates": [],
        "messages": [
            *state.messages,
            {
                "role": "assistant",
                "content": state.final_answer,
            },
        ],
    }

# Build graph and workflow
def build_graph(retriever: VectorStoreRetriever):
    builder = StateGraph(AgentState)

    # Add the nodes
    builder.add_node("question_router_node", question_router_node)
    builder.add_node("retrieve_docs_node", retrieve_docs_node(retriever))
    builder.add_node("knowledge_answer_node", knowledge_answer_node)
    builder.add_node("onboarding_plan_node", onboarding_plan_node)
    builder.add_node("troubleshoot_plan_node", troubleshoot_plan_node)
    builder.add_node("escalation_node", escalation_node)
    builder.add_node("general_answer_node", general_answer_node)
    builder.add_node("review_answer_node", review_answer_node)
    builder.add_node("finalize_node", finalize_node)
    builder.add_node("revise_node", revise_node)
    builder.add_node("save_memory_node", save_memory_node)
    

    # Build the workflow
    builder.add_edge(START, "question_router_node")

    # Router - Add conditional edges to retrieve first
    builder.add_conditional_edges(
        "question_router_node",
        decision_router,
        {
            "knowledge": "retrieve_docs_node",
            "onboarding":"retrieve_docs_node",
            "troubleshooting":"retrieve_docs_node",
            "escalation":"retrieve_docs_node",
            "general":"general_answer_node"
        }
    )

    # Router - Add conditional edges to route to node
    builder.add_conditional_edges(
        "retrieve_docs_node",
        after_retrieval_router,
        {
            "knowledge": "knowledge_answer_node",
            "onboarding": "onboarding_plan_node",
            "troubleshooting": "troubleshoot_plan_node",
            "escalation": "escalation_node",
        },
    )

    builder.add_edge("knowledge_answer_node", "review_answer_node")
    builder.add_edge("onboarding_plan_node", "review_answer_node")
    builder.add_edge("troubleshoot_plan_node", "review_answer_node")
    builder.add_edge("escalation_node", "review_answer_node")
    builder.add_edge("general_answer_node", "review_answer_node")
    
    # Review Router - Add conditional edges
    builder.add_conditional_edges(
        "review_answer_node",
        review_router,
        {
            "finalize": "finalize_node",
            "revise":"revise_node",
        }
    )

    builder.add_edge("revise_node", "review_answer_node")
    builder.add_edge("finalize_node", "save_memory_node")
    builder.add_edge("save_memory_node", END)

    checkpointer = MemorySaver()
    graph = builder.compile(checkpointer)

    return graph
