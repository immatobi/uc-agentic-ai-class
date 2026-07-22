# Northstar CSA Feature Documentation

## Overview

Northstar CSA is a production-style AI customer support assistant for Northstar CRM, a SaaS CRM platform for small businesses.

The assistant is designed to help customers:

- Answer Northstar CRM product and billing questions.
- Troubleshoot common product issues.
- Prepare onboarding, rollout, and migration plans.
- Escalate urgent or sensitive support cases.
- Ask safe general questions that do not require Northstar CRM knowledge-base retrieval.

The backend is implemented with FastAPI and LangGraph. It loads a local `.txt` knowledge base, creates a Chroma-backed retriever, runs a routed support graph, reviews generated answers, calculates confidence, saves memory updates, and returns a structured API response.

## Main User-Facing Capabilities

### 1. Chat Support API

The project exposes a chat endpoint that accepts a customer question and returns a structured support response.

Endpoint:

```http
POST /v1/chat
```

Request body:

```json
{
  "customer_id": "acct-123",
  "thread_id": "session-abc",
  "question": "I was charged twice this month. What should I do?"
}
```

Response body shape:

```json
{
  "question": "I was charged twice this month. What should I do?",
  "route": "escalation",
  "answer": "...",
  "review": "...",
  "confidence": 0.87,
  "priority": "urgent",
  "assigned_team": "billing_support",
  "sources": [
    {
      "source": "pricing_and_billing.txt",
      "content_preview": "..."
    }
  ],
  "memory_updates": []
}
```

The response is designed for a frontend chat UI that can display:

- Final answer.
- Selected route.
- Review result.
- Confidence score.
- Sources.
- Priority.
- Assigned support team.
- Memory updates.

### 2. Health Checks

The backend exposes health-style routes for service status.

Current routes:

```http
POST /v1
POST /v1/health
```

Both return a standard response envelope containing:

- API name.
- Version.
- Status.
- Message.
- Numeric status code.

## API Schemas

### ChatRequest

`ChatRequest` contains the minimum information needed to run a support conversation:

```python
class ChatRequest(BaseModel):
    question: str
    thread_id: str
    customer_id: str
```

Field behavior:

- `question`: latest customer message.
- `thread_id`: session identifier for short-term memory and checkpointing.
- `customer_id`: stable account/customer identifier for long-term memory.

### ChatResponse

`ChatResponse` returns the graph result in a frontend-friendly structure:

```python
class ChatResponse(BaseModel):
    question: str
    route: str
    answer: str
    review: str
    confidence: float
    priority: str
    assigned_team: str
    sources: List[Source]
    memory_updates: list[Any]
```

### AgentState

The LangGraph state tracks the full support workflow:

```python
class AgentState(BaseModel):
    question: str
    customer_id: str
    thread_id: str
    messages: list[Any]
    route: Literal[
        "knowledge",
        "troubleshooting",
        "escalation",
        "onboarding",
        "general"
    ]
    documents: List[Document]
    answer: str
    review: Optional[ReviewResult]
    revision_count: int
    confidence: float
    priority: Literal["low", "normal", "urgent"]
    assigned_team: str
    sources: list[Any]
    memory_updates: list[Any]
    final_answer: str
```

## LangGraph Workflow

The support assistant is implemented as a LangGraph workflow.

Current node set:

- `question_router_node`
- `retrieve_docs_node`
- `knowledge_answer_node`
- `onboarding_plan_node`
- `troubleshoot_plan_node`
- `escalation_node`
- `general_answer_node`
- `review_answer_node`
- `revise_node`
- `finalize_node`
- `save_memory_node`

Current high-level flow:

```text
START
  -> question_router_node
  -> branch by route
      -> knowledge_answer_node
      -> onboarding_plan_node
      -> troubleshoot_plan_node
      -> escalation_node
      -> general_answer_node
  -> review_answer_node
  -> review_router
      -> finalize_node
      -> revise_node -> review_answer_node
  -> save_memory_node
  -> END
```

The graph is compiled with `MemorySaver` checkpointing:

```python
checkpointer = MemorySaver()
graph = builder.compile(checkpointer)
```

This enables session-level memory keyed by `thread_id` when the graph is invoked with:

```python
config={
    "configurable": {
        "thread_id": body.thread_id
    }
}
```

## Intent Classification and Routing

### Feature

The assistant classifies each question into one of five support routes:

- `knowledge`
- `troubleshooting`
- `escalation`
- `onboarding`
- `general`

### Route Meanings

#### knowledge

Used for product, billing, pricing, plan-limit, integration, settings, and documentation questions.

Example questions:

- "What is included in the Pro plan?"
- "How do I connect my email account?"
- "How do I import contacts from a CSV file?"

#### troubleshooting

Used for product issues that can usually be handled without immediate escalation.

Example questions:

- "Why am I seeing duplicate contacts after import?"
- "My Gmail sync is not working."
- "Some CSV rows failed."

#### escalation

Used for urgent, sensitive, billing, security, account access, or business-impacting support issues.

Example questions:

- "I was charged twice this month."
- "My team cannot log in and we have a sales demo in one hour."
- "I think someone accessed our account without permission."

#### onboarding

Used for rollout planning, setup plans, migration guidance, training plans, and adoption planning.

Example questions:

- "Help me create a 30-day onboarding plan for a five-person sales team."
- "We are migrating from spreadsheets. What checklist should we follow?"

#### general

Used for safe general questions unrelated to Northstar CRM.

Example question:

- "Tell me a harmless joke about sales pipelines."

## Retrieval-Augmented Generation

### Knowledge Base

The backend uses local Northstar CRM `.txt` documents located under:

```text
northstar-backend/src/_data/
```

Included documents:

- `account_access_guide.txt`
- `csv_import_guide.txt`
- `email_sync_guide.txt`
- `escalation_policy.txt`
- `integrations_guide.txt`
- `onboarding_checklist.txt`
- `pricing_and_billing.txt`
- `product_overview.txt`
- `security_policy.txt`
- `sla_and_support_hours.txt`
- `troubleshooting_playbook.txt`

### Document Loading

`doc_service.py` loads every `.txt` file as a LangChain `Document`.

Each document receives metadata:

```python
metadata={
    "source": filename
}
```

This source metadata is used later for citations and frontend source cards.

### Chunking

`rag_service.py` chunks the documents with:

- `chunk_size=1000`
- `chunk_overlap=200`

### Embeddings

The project uses Google Generative AI embeddings:

```python
GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001"
)
```

### Vector Store

The project uses Chroma:

```python
Chroma.from_documents(...)
```

### Retriever

The retriever returns up to five chunks:

```python
store.as_retriever(
    search_kwargs={"k": 5}
)
```

### Intended Retrieval Behavior

Product, billing, support policy, troubleshooting, escalation, and onboarding answers should use retrieved documents when the answer depends on documented Northstar CRM behavior.

Answers should:

- Use retrieved context.
- Mention source documents.
- Avoid inventing product capabilities.
- Avoid unsupported billing, refund, SLA, security, or engineering promises.
- Return a fallback when context is missing.

## Knowledge Answer Branch

### Purpose

The knowledge branch answers product, pricing, billing, plan-limit, integration, and documentation questions.

### Behavior

The node:

1. Reads `state.question`.
2. Reads `state.documents`.
3. Builds a context string from retrieved document chunks.
4. Prompts the LLM to answer only from the provided context.
5. Returns a draft `answer`.

### Guardrails

The knowledge prompt tells the LLM:

- Do not invent information.
- Use only the context.
- If the answer is missing from context, say it could not be found in the Northstar CRM knowledge base.
- Mention source documents when possible.

## Troubleshooting Branch

### Purpose

The troubleshooting branch handles product issues that can usually be resolved without immediate escalation.

### Required Output

The branch generates a structured troubleshooting object with:

- `issue_category`
- `summary`
- `missing_details`
- `troubleshooting_steps`
- `when_to_escalate`
- `customer_message`
- `escalation_needed`
- `priority`
- `assigned_team`

### Supported Issue Categories

- `csv_import`
- `email_sync`
- `login_access`
- `duplicate_contacts`
- `slow_loading`
- `pipeline_issue`
- `integration_issue`
- `general_troubleshooting`

### Markdown Answer

The `customer_message` is Markdown-formatted and intended to be used directly as the user-facing `answer`.

Required sections:

1. `## Likely issue`
2. `## Details I need`, only if missing details are needed
3. `## Troubleshooting steps`
4. `## When to escalate`
5. `## Sources`, only if sources exist

### State Updates

The branch writes:

- `answer`
- `priority`
- `assigned_team`
- `memory_updates`

The memory update captures troubleshooting details such as:

- issue category
- summary
- missing details
- ordered troubleshooting steps
- escalation criteria
- whether escalation is needed

## Escalation Branch

### Purpose

The escalation branch handles urgent, sensitive, billing, security, account access, or business-impacting support requests.

### Required Output

The branch generates a structured escalation object with:

- `priority`
- `assigned_team`
- `next_steps`
- `language`
- `metadata`

### Priority Values

- `low`
- `normal`
- `urgent`

### Assigned Team Values

- `billing_support`
- `technical_support`
- `security_team`
- `customer_success`
- `engineering_on_call`

### Markdown Answer

The `language` field is Markdown-formatted and used as the user-facing `answer`.

Required sections:

1. `## Escalation summary`
2. `## Priority`
3. `## Assigned team`
4. `## Next steps`
5. `## Information needed`
6. `## Sources`, only if sources exist

### Safety Rules

The escalation branch must never ask for:

- passwords
- one-time passcodes
- CVV
- full card numbers
- full bank account numbers
- sensitive secrets

### State Updates

The branch writes:

- `priority`
- `assigned_team`
- `answer`
- `memory_updates`

The memory update stores escalation details for later workflow use.

## Onboarding and Planning Branch

### Purpose

The onboarding branch generates practical rollout, onboarding, migration, and adoption plans.

### Required Output

The branch generates:

- `request_details`
- `missing_information`
- `assumptions`
- `onboarding_plan`
- `checklist`
- `risks`
- `next_actions`
- `customer_message`
- `priority`
- `assigned_team`
- `sources`

### Planning Input Extraction

Before generating the main onboarding plan, the node asks the LLM to extract planning inputs:

- users
- contacts
- companies
- deals
- start date
- target duration in days

Unknown values are represented as `null`.

### Planning Tools

The onboarding branch uses helper tools for planning:

#### calculate_deadline

Calculates a deadline from:

- start date
- duration in days

Returns:

- start date
- duration
- calculated deadline

#### estimate_account_size

Estimates account size and implementation complexity from:

- users
- contacts
- companies
- deals

Returns:

- total records
- account size: `small`, `medium`, or `large`
- implementation complexity: `low`, `moderate`, or `high`

#### plan_implementation_timeline

Generates a recommended rollout timeline from:

- account size
- optional target days

Returns:

- recommended days
- whether the timeline is compressed
- recommended implementation phases

### Markdown Answer

The `customer_message` is Markdown-formatted and used as the final customer-facing plan.

Required sections:

1. `## Onboarding summary`
2. `## Details captured`
3. `## Missing information`, only if missing information exists
4. `## Assumptions`
5. `## Rollout plan`
6. `## Checklist`
7. `## Risks`
8. `## Next actions`
9. `## Sources`, only if sources exist

### State Updates

The onboarding node writes:

- `answer`
- `priority`
- `assigned_team`
- `sources`
- `memory_updates`

The memory update captures the structured plan and the tool context used to generate it.

## General Answer Branch

### Purpose

The general branch handles safe questions unrelated to Northstar CRM.

### Behavior

The node:

1. Receives a general question.
2. Answers clearly and briefly.
3. Avoids inventing Northstar CRM details.
4. Avoids legal, financial, medical, security-invasive, or harmful instructions.
5. Returns a Markdown-formatted answer.

### State Updates

The branch sets:

- `answer`
- empty `documents`
- empty `sources`
- `priority="low"`
- `assigned_team="customer_success"`

## Review and Revision Loop

### Purpose

The review node checks whether a generated answer is safe, useful, complete, and grounded.

### Review Criteria

The review checks:

- Did the answer address the customer question?
- For knowledge answers, is the answer supported by retrieved context?
- Are source references present when needed?
- Does the response avoid unsupported refund, legal, security, or SLA promises?
- Is the answer clear and actionable?
- Should the answer be revised?

### ReviewResult

The review output is structured:

```python
class ReviewResult(BaseModel):
    score: int
    passed: bool
    feedback: str
```

### Review Scores

Scoring guidance:

- `9-10`: strong answer, grounded, complete, ready to send
- `7-8`: acceptable answer with minor issues
- `4-6`: needs revision
- `1-3`: poor, unsafe, unsupported, or missing major requirements

### Revision Behavior

If review fails, `review_router` sends the answer to `revise_node`.

`revise_node`:

- Reads the original question.
- Reads the current answer.
- Reads review feedback.
- Reads retrieved context.
- Produces a revised Markdown answer.
- Increments `revision_count`.

The graph allows revision attempts before finalizing.

### Finalization Behavior

`finalize_node` decides what becomes `final_answer`.

If the review still fails after revision attempts, the node returns a cautious fallback instead of sending an unsupported answer.

## Confidence Scoring

### Purpose

The `confidence` field tells the frontend and user how reliable the answer is.

### Calculation

Confidence is calculated from:

- review score
- whether review passed
- whether retrieved documents were available for non-general routes
- whether sources are present
- revision count

### Behavior

High confidence means:

- review score is high
- review passed
- answer has appropriate grounding
- sources exist when needed
- few or no revisions were needed

Lower confidence means:

- review failed
- required documents were missing
- sources were missing
- multiple revisions were needed

The final API response includes:

```json
{
  "confidence": 0.87
}
```

## Short-Term Memory

### Purpose

Short-term memory allows follow-up questions in the same session.

Example:

```text
Customer: How do I import contacts from CSV?
Assistant: answers with CSV import guidance.
Customer: What if some rows fail?
Assistant: understands that "rows" refers to the CSV import process.
```

### Implementation

The graph is compiled with LangGraph checkpointing:

```python
checkpointer = MemorySaver()
graph = builder.compile(checkpointer)
```

The API route invokes the graph with:

```python
config={
    "configurable": {
        "thread_id": body.thread_id or ""
    }
}
```

The same `thread_id` should be reused across follow-up messages in the same conversation.

## Long-Term Memory

### Purpose

Long-term memory stores stable customer facts across sessions.

The required stable fact categories are:

- company type or industry
- plan tier, such as Starter, Pro, or Enterprise
- team size
- preferred support tone or response style
- active goal, such as migration, onboarding, cleanup, or renewal

### Memory Store

The current implementation uses an in-memory dictionary:

```python
CUSTOMER_MEMORY_STORE: dict[str, dict] = {}
```

Allowed memory fields:

```python
ALLOWED_MEMORY_FIELDS = {
    "company_type",
    "plan_tier",
    "team_size",
    "preferred_support_tone",
    "active_goal",
}
```

### Save Memory Node

`save_memory_node`:

1. Reads `customer_id`.
2. Reads `state.memory_updates`.
3. Filters for updates where `type == "customer_fact"`.
4. Only saves facts whose field is allowed.
5. Only saves facts with confidence of at least `0.75`.
6. Clears `memory_updates`.
7. Appends the assistant final answer to `messages`.

### Memory Update Shape

Stable facts should be staged in this format:

```json
{
  "type": "customer_fact",
  "field": "team_size",
  "value": "5 sales reps",
  "confidence": 0.9
}
```

Operational branch outputs, such as troubleshooting plans or escalation details, can be stored in `memory_updates`, but they are not automatically long-term facts unless they use the `customer_fact` type.

## Source Handling

### Source Metadata

Loaded documents include a `source` metadata field containing the file name.

Example:

```json
{
  "source": "csv_import_guide.txt"
}
```

### API Source Cards

The chat route converts retrieved documents into source cards:

```json
{
  "source": "csv_import_guide.txt",
  "content_preview": "..."
}
```

The frontend can display these as source cards.

## Safety and Support Guardrails

The assistant is designed to avoid:

- invented Northstar CRM product behavior
- unsupported refund promises
- unsupported credit promises
- unsupported SLA remedies
- unsupported legal advice
- unsupported security conclusions
- unsupported engineering fix promises
- requests for unsafe sensitive information

Restricted information includes:

- passwords
- one-time passcodes
- CVV
- full card numbers
- full bank account numbers
- account passwords
- secret credentials

## Observability Fields

The API response includes fields useful for debugging and frontend observability:

- `route`
- `review`
- `confidence`
- `priority`
- `assigned_team`
- `sources`
- `memory_updates`

These fields make it easier to see:

- which graph branch handled the request
- whether the answer passed review
- whether the model had enough grounding
- whether a support case needs escalation
- which team should follow up

## Current Implementation Notes

### Implemented

The current backend includes:

- FastAPI app setup.
- CORS configuration for `http://localhost:3000`.
- health routes.
- chat route.
- Pydantic chat request and response schemas.
- LangGraph state model.
- intent router node.
- knowledge answer node.
- troubleshooting node.
- escalation node.
- onboarding node.
- general answer node.
- review node.
- revision node.
- finalization node.
- save memory node.
- local `.txt` knowledge base.
- document loader.
- text splitter.
- Chroma retriever.
- Google embedding integration.
- Anthropic chat model integration.
- onboarding planning tools.
- confidence calculation helper.
- LangGraph memory checkpointing.

## Feature-to-Requirement Mapping

| Requirement | Project Feature |
| --- | --- |
| Intent classification | `question_router_node` and `decision_router` |
| Conditional routing | LangGraph `add_conditional_edges` |
| RAG | document loader, chunker, embeddings, Chroma retriever |
| Knowledge answer | `knowledge_answer_node` |
| Troubleshooting path | `troubleshoot_plan_node` |
| Escalation path | `escalation_node` |
| Onboarding path | `onboarding_plan_node` |
| Planning tools | deadline, account-size, timeline helpers |
| General answer | `general_answer_node` |
| Review loop | `review_answer_node`, `review_router`, `revise_node` |
| Final answer | `finalize_node` |
| Short-term memory | LangGraph `MemorySaver` with `thread_id` |
| Long-term memory | `CUSTOMER_MEMORY_STORE` and `save_memory_node` |
| API response contract | `ChatRequest`, `ChatResponse`, `/v1/chat` |
| Confidence | `calculate_confidence` and `state.confidence` |
| Source cards | `Source` schema and document metadata |

