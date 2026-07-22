# Northstar CSA

Northstar CSA is a production-style AI customer support assistant for **Northstar CRM**, a fictional SaaS CRM platform for small businesses. The project was built as an Agentic AI capstone and combines a FastAPI backend, a LangGraph support workflow, local retrieval-augmented generation, memory, and a Next.js chat frontend.

## Introduction

Modern SaaS support teams handle a mix of simple product questions, troubleshooting requests, onboarding planning, billing issues, and urgent escalations. Northstar CSA models the first version of an AI support assistant that can classify those requests, retrieve relevant product documentation, generate a grounded answer, review the answer for safety and quality, and return structured metadata to a frontend experience.

The goal is not to build a full enterprise helpdesk. The goal is to demonstrate a clean, working support-agent architecture with production-minded boundaries:

- a backend API with typed request and response schemas
- a LangGraph workflow with conditional routing
- a local Northstar CRM knowledge base
- retrieval using embeddings and a vector store
- branch-specific answer generation for knowledge, troubleshooting, onboarding, escalation, and general questions
- answer review, revision, confidence scoring, and finalization
- short-term thread memory and long-term customer fact memory
- a frontend chat interface that displays Markdown answers and support metadata

## Documentation Quick Links

Use this table to find the project documentation and graph assets quickly.

| Document | What It Is For | Link |
| --- | --- | --- |
| Architecture document | Explains the backend, API, LangGraph workflow, retrieval pipeline, memory design, review loop, frontend responsibilities, and deployment tradeoffs. | [Open Architecture](./ARCHITECTURE.md) |
| Feature documentation | Describes the product features, support routes, branch behavior, confidence scoring, observability fields, implementation notes, and requirement mapping. | [Open Feature Docs](./.docs/features/northstar-csa-features.md) |
| Mermaid graph source | Raw Mermaid source for the LangGraph workflow. Use it when copying the graph into Mermaid Live Editor, docs, or slides. | [Open Mermaid Source](./.docs/graph/support-graph.mmd) |
| Markdown graph preview | Markdown file with the Mermaid graph embedded. Use it in Markdown renderers that support Mermaid. | [Open Markdown Graph](./.docs/graph/support-graph.md) |
| HTML graph preview | Standalone browser page that renders the Mermaid graph. Use it to take a screenshot for capstone deliverables. | [Open HTML Graph](./.docs/graph/support-graph.html) |

## What the Product Does

Northstar CSA accepts a customer question and routes it into one of five support paths.

### Knowledge Questions

Used for product, billing, pricing, feature, plan-limit, integration, and documentation questions.

Example:

```text
What is included in the Pro plan?
```

The assistant retrieves relevant documents, answers from the retrieved context, and returns source cards.

### Troubleshooting

Used for product issues that can usually be handled without immediate escalation.

Example:

```text
Why am I seeing duplicate contacts after import?
```

The assistant identifies the likely issue category, asks for missing details when needed, provides ordered troubleshooting steps, and includes when-to-escalate criteria.

### Escalation

Used for urgent, sensitive, billing, account access, security, or business-impacting issues.

Example:

```text
I was charged twice this month. What should I do?
```

The assistant returns a priority level, assigned support team, next steps, escalation language, and safe information the human team should collect.

### Onboarding and Planning

Used for setup plans, migrations, rollout plans, team onboarding, and adoption planning.

Example:

```text
Help me create a 30-day onboarding plan for a five-person sales team.
```

The assistant extracts structured planning details, estimates account size, calculates deadlines, generates a rollout plan, lists assumptions, risks, owners, checklist items, and next actions.

### General Questions

Used for safe general questions unrelated to Northstar CRM.

Example:

```text
Tell me a harmless joke about sales pipelines.
```

General responses do not use retrieval and should not return sources.

## Repository Structure

```text
.
├── README.md
├── ARCHITECTURE.md
├── knowledge_base/
├── .docs/
│   ├── features/
│   └── graph/
├── northstar-backend/
│   ├── pyproject.toml
│   ├── src/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── agents/
│   │   ├── graph/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── utils/
│   │   └── _data/
│   └── uv.lock
└── northstar-frontend/
    ├── package.json
    ├── public/
    └── src/
```

## Project Documentation

This repository includes dedicated documentation files for product features, system architecture, and graph visualization.

### Architecture Document

Path:

[ARCHITECTURE.md](./ARCHITECTURE.md)

Use this document to understand how the full system is designed.

It explains:

- backend startup flow
- FastAPI API structure
- request and response schemas
- LangGraph workflow
- graph nodes and routing
- retrieval pipeline
- memory design
- review and revision loop
- frontend responsibilities
- design tradeoffs and production considerations

Read this when you need to explain the project architecture, prepare a demo walkthrough, or answer capstone reflection questions about graph design, retrieval, memory, and frontend/backend responsibilities.

### Feature Documentation

Path:

[.docs/features/northstar-csa-features.md](./.docs/features/northstar-csa-features.md)

Use this document to understand what the product does from a feature perspective.

It explains:

- user-facing capabilities
- chat API behavior
- supported support routes
- knowledge branch behavior
- troubleshooting branch behavior
- escalation branch behavior
- onboarding branch behavior
- general-answer behavior
- confidence scoring
- observability fields
- current implementation notes and gaps
- requirement-to-feature mapping

Read this when you need a product-level overview or when checking whether a feature maps to a capstone requirement.

### Graph Visualization

Graph visualization files are stored in:

```text
.docs/graph/
```

Available files:

- [.docs/graph/support-graph.mmd](./.docs/graph/support-graph.mmd)
- [.docs/graph/support-graph.md](./.docs/graph/support-graph.md)
- [.docs/graph/support-graph.html](./.docs/graph/support-graph.html)

#### `support-graph.mmd`

Raw Mermaid source for the LangGraph workflow.

Use this file when you want to copy the graph into:

- Mermaid Live Editor
- GitHub Markdown
- documentation tools
- slide decks
- architecture documents

#### `support-graph.md`

Markdown document containing the Mermaid diagram.

Use this file when you want to preview the graph in a Markdown renderer that supports Mermaid.

#### `support-graph.html`

Standalone browser-renderable graph page.

Use this file when you need a graph visualization image or screenshot for the capstone deliverables.

To use it:

1. Open `.docs/graph/support-graph.html` in your browser.
2. Wait for the Mermaid diagram to render.
3. Take a screenshot of the rendered graph.
4. Include the screenshot in your capstone submission or demo materials.

The graph shows:

- request classification
- conditional routing
- retrieval for document-dependent routes
- knowledge, troubleshooting, escalation, onboarding, and general branches
- answer review
- revision loop
- finalization
- memory saving
- graph end state

## Backend Overview

The backend is a FastAPI app in `northstar-backend`.

Key files:

- `src/main.py`: FastAPI app setup, CORS, document loading, vector store creation, graph compilation, route mounting.
- `src/api/chat_route.py`: `/v1/chat` API route.
- `src/api/health_route.py`: health-style API routes.
- `src/graph/support_graph.py`: LangGraph workflow and nodes.
- `src/services/doc_service.py`: loads local `.txt` knowledge-base files.
- `src/services/rag_service.py`: chunks documents, creates embeddings, builds Chroma retriever.
- `src/services/llm_service.py`: creates the chat model.
- `src/agents/tools.py`: graph routers and onboarding planning tools.
- `src/schemas/chat_schema.py`: API request and response schemas.
- `src/schemas/graph_schema.py`: graph state and review schemas.
- `src/_data/`: local Northstar CRM support documents used for retrieval.

## Frontend Overview

The frontend is a Next.js app in `northstar-frontend`.

Key features:

- customer chat input
- API call to the FastAPI backend
- loading state
- Markdown rendering for model answers
- display of answer metadata such as route, review, confidence, priority, assigned team, sources, and memory updates
- local customer and thread identifiers for memory support

## Prerequisites

Install these before running the project:

- Python `3.13+`
- `uv`
- Node.js compatible with Next.js `16`
- npm
- valid model API keys

Backend dependencies are managed by `uv`.

Frontend dependencies are managed by npm.

## Environment Variables

### Backend

Create `northstar-backend/.env`:

```env
ANTHROPIC_API_KEY=your_anthropic_key
GOOGLE_API_KEY=your_google_api_key
```

The current backend uses:

- Anthropic or Gemini for chat generation, depending on `llm_service.py`
- Google Generative AI embeddings for the vector store

Do not commit real API keys.

### Frontend

Create `northstar-frontend/.env`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

If the backend runs on another port, update this value.

Example:

```env
NEXT_PUBLIC_API_URL=http://localhost:8001
```

## Backend Setup

From the repository root:

```bash
cd northstar-backend
uv sync
cp .env.example .env
```

Then edit `.env` and add the required API keys.

Run the backend:

```bash
uv run uvicorn src.main:app --reload
```

The backend runs at:

```text
http://localhost:8000
```

If port `8000` is already in use:

```bash
uv run uvicorn src.main:app --reload --port 8001
```

Then update the frontend `.env` accordingly.

## Frontend Setup

From the repository root:

```bash
cd northstar-frontend
npm install
```

Run the frontend:

```bash
npm run dev
```

The frontend runs at:

```text
http://localhost:3000
```

## Running the Full App

Use two terminals.

Terminal 1:

```bash
cd northstar-backend
uv run uvicorn src.main:app --reload
```

Terminal 2:

```bash
cd northstar-frontend
npm run dev
```

Open:

```text
http://localhost:3000
```

## API Contract

### Chat

```http
POST /v1/chat
```

Request:

```json
{
  "customer_id": "acct-123",
  "thread_id": "session-abc",
  "question": "What is included in the Pro plan?"
}
```

Response:

```json
{
  "error": false,
  "errors": [],
  "data": {
    "question": "What is included in the Pro plan?",
    "customer_id": "acct-123",
    "thread_id": "session-abc",
    "route": "knowledge",
    "answer": "...",
    "review": {
      "score": 9,
      "passed": true,
      "feedback": "The answer is grounded and clear."
    },
    "confidence": 0.9,
    "priority": "normal",
    "assigned_team": "customer_success",
    "sources": [
      {
        "source": "pricing_and_billing.txt",
        "content_preview": "..."
      }
    ],
    "memory_updates": []
  },
  "message": "successful",
  "status": 200
}
```

### Health

Current health routes:

```http
POST /v1
POST /v1/health
```

## Knowledge Base

The backend loads documents from:

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

At startup, the backend:

1. loads these `.txt` files
2. chunks them
3. embeds the chunks
4. stores them in Chroma
5. exposes the retriever to the LangGraph workflow

## Memory

The app uses two memory concepts.

### Short-Term Memory

Short-term memory is based on LangGraph checkpointing and `thread_id`.

Use the same `thread_id` for follow-up questions in the same conversation.

### Long-Term Memory

Long-term memory is keyed by `customer_id`.

The assistant is designed to store stable customer facts when they appear naturally, such as:

- company type or industry
- plan tier
- team size
- preferred support tone
- active goal

The current implementation uses an in-memory store. For production, replace this with SQLite, Postgres, Redis, or another durable store.

## Common Troubleshooting

### Port 8000 Already in Use

Run the backend on another port:

```bash
uv run uvicorn src.main:app --reload --port 8001
```

Then update:

```env
NEXT_PUBLIC_API_URL=http://localhost:8001
```

### Frontend Calls the Wrong Backend Path

The chat route is:

```text
/v1/chat
```

Make sure frontend API calls use:

```text
http://localhost:8000/v1/chat
```

### Knowledge Route Returns "I Could Not Find"

Check that retrieval happens before document-dependent nodes.

The intended flow is:

```text
question_router_node
  -> retrieve_docs_node
  -> knowledge / onboarding / troubleshooting / escalation node
  -> review_answer_node
```

If `knowledge_answer_node` receives empty `documents`, it will correctly fallback because it has no context.

### LLM Response Is a List Instead of a String

Some providers return block-based content instead of plain strings. Normalize LLM response content before calling `.strip()` or `json.loads()`.

### API Keys

If startup fails while creating embeddings or calling the model, verify:

- `.env` exists
- API keys are valid
- the selected model exists
- the key has access to the selected provider

## Useful Commands

Backend syntax check:

```bash
cd northstar-backend
uv run python -m py_compile src/main.py src/graph/support_graph.py
```

Frontend build:

```bash
cd northstar-frontend
npm run build
```

Frontend dev server:

```bash
cd northstar-frontend
npm run dev
```

Backend dev server:

```bash
cd northstar-backend
uv run uvicorn src.main:app --reload
```
