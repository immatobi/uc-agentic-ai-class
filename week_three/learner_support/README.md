# Learner Support Triage

## Overview

This project is a small LangGraph workflow that simulates how a learner support team could triage incoming requests before handing them off to the right internal team.

The workflow receives a learner request, scores its urgency, decides the most appropriate route, assigns the request to a team, and produces a final summarized response with an audit trail. The implementation is intentionally simple, but it models a realistic support flow:

- intake of learner details
- priority calculation based on business rules
- conditional routing based on urgency and request category
- route-specific handling
- final summarization

The code is implemented as a graph instead of a plain sequence so the workflow can branch intelligently depending on the state of the request.

## Introduction

Support operations are a good fit for agentic workflows because they rarely follow a single fixed path. A learner can ask a technical question, report a billing issue, request help with course content, or submit a general inquiry. Some cases are routine, while others are time-sensitive and require escalation.

This project uses LangGraph to model that decision-making process. Each node handles one focused step in the triage lifecycle, and each step returns only the fields it is responsible for updating. The state moves through the graph until the request is fully triaged.

The project is useful as a learning exercise because it combines:

- `TypedDict` state design
- `Enum` usage for controlled values
- business-rule scoring
- conditional graph routing
- audit logging
- route-specific responses

## What The Project Does

At a high level, the workflow performs the following steps:

1. Receives a learner request with information such as name, email, category, message, deadline urgency, and payment status.
2. Records that the request was received.
3. Calculates a priority score and a priority label.
4. Routes the request to the appropriate branch.
5. Assigns the request to a specific support team.
6. Produces a learner-facing response.
7. Appends audit-log entries at every major step.
8. Produces a final triage summary with the final status, team assignment, and priority.

The workflow currently supports these request categories:

- `technical`
- `billing`
- `course_content`
- `general`

It currently supports these route outcomes:

- `urgent`
- `technical`
- `billing`
- `learning_support`
- `general`

## Technical Details

### Project Structure

The main files are:

- [src/main.py](/Users/immanuel/Documents/Learning/unlimited-code/agentic_ai_class/week_three/learner_support/src/main.py:1)
- [src/enums.py](/Users/immanuel/Documents/Learning/unlimited-code/agentic_ai_class/week_three/learner_support/src/enums.py:1)
- [support_triage.ipynb](/Users/immanuel/Documents/Learning/unlimited-code/agentic_ai_class/week_three/learner_support/support_triage.ipynb:1)

[src/main.py](/Users/immanuel/Documents/Learning/unlimited-code/agentic_ai_class/week_three/learner_support/src/main.py:1) contains the state definition, business logic, nodes, graph wiring, and runnable example.

[src/enums.py](/Users/immanuel/Documents/Learning/unlimited-code/agentic_ai_class/week_three/learner_support/src/enums.py:1) contains the enums used to keep status, category, priority, and route values consistent.

[support_triage.ipynb](/Users/immanuel/Documents/Learning/unlimited-code/agentic_ai_class/week_three/learner_support/support_triage.ipynb:1) mirrors the workflow in notebook form and displays the compiled graph with `draw_mermaid_png()`.

### State Design

The graph uses a `TypedDict` called `AgentState`. This state contains all the fields the workflow needs to read or update while processing a learner request.

Current fields include:

- `learner_name`
- `email`
- `category`
- `message`
- `days_until_deadline`
- `is_paid_student`
- `priority_score`
- `priority`
- `route`
- `assigned_team`
- `status`
- `response`
- `audit_log`

This state shape gives every node a shared contract. Each node knows what data is available and what values it is expected to produce.

### Enums

The project uses string enums for consistency:

- `StatusEnum`
- `CategoryEnum`
- `PriorityEnum`
- `RouteEnum`

These enums reduce accidental typos such as `"urgnt"` instead of `"urgent"` and make routing logic more explicit and easier to understand.

### Priority Logic

The core scoring logic lives in `calculate_priority(state)`.

The current business rules are:

1. Requests with `days_until_deadline <= 1` receive a large urgency boost.
2. `technical` issues score higher than `general` requests.
3. Emergency phrases such as `"blocked"`, `"cannot submit"`, `"charged twice"`, and `"deadline"` increase the score.
4. Paid learners receive a smaller additional boost.

The resulting numeric score is converted into one of these labels:

- `low`
- `normal`
- `high`
- `urgent`

This split between score and label is important. The score gives detail for future analysis, while the label gives a simpler routing signal for the graph.

### Routing Logic

The routing function is `route_request(state)`.

It applies these routing rules:

1. Any `urgent` priority request routes to `urgent`, regardless of category.
2. Non-urgent `technical` requests route to `technical`.
3. Non-urgent `billing` requests route to `billing`.
4. Non-urgent `course_content` requests route to `learning_support`.
5. All remaining requests route to `general`.

This is the key decision point that makes the workflow dynamic rather than linear.

### Node Responsibilities

Each node has a narrow responsibility.

`intake_node`

- reads core learner input fields
- sets the initial status to `received`
- appends an audit-log entry confirming receipt

`calculate_priority_node`

- calls `calculate_priority`
- stores `priority_score`
- stores `priority`
- appends an audit-log entry describing the result

`route_request_node`

- computes the route
- stores `route`
- appends an audit-log entry showing where the request is being sent

`urgent_node`

- assigns the request to the urgent branch
- sets the assigned team to the urgent handler
- escalates the status
- produces an urgent learner response

`technical_node`

- assigns the request to technical support
- produces a technical-support response

`billing_node`

- assigns the request to billing operations
- produces a billing response

`learning_support_node`

- assigns the request to learning support
- produces a course-content support response

`general_node`

- assigns the request to general support
- produces a general learner response

`summary_node`

- runs after every route-specific branch
- preserves `escalated` for urgent requests
- sets non-urgent requests to `triaged`
- appends a final audit-log entry
- enhances the final learner response with team and priority information

### Graph Flow

The workflow graph is wired in this order:

`START -> intake_node -> calculate_priority_node -> route_request_node -> branch node -> summary_node -> END`

The conditional branch happens after `route_request_node`.

Possible branch paths are:

- `urgent_node`
- `technical_node`
- `billing_node`
- `learning_support_node`
- `general_node`

Every branch converges into `summary_node`, which provides a consistent final state shape before the workflow ends.

### Why Partial State Updates Matter

Each node returns only the fields it needs to change instead of rebuilding the entire state dictionary. This matters because:

- it keeps each node focused on a single responsibility
- it reduces the chance of accidentally overwriting unrelated state
- it makes the graph easier to debug
- it aligns with how LangGraph merges node updates into the shared state

For example, the billing node should not need to rebuild `learner_name`, `email`, or `priority_score`. It only needs to update fields related to billing assignment and response.

## Graph Walkthrough

To understand the workflow, it helps to trace one request through the graph.

Example path:

1. A learner submits a technical request.
2. `intake_node` records that the request was received.
3. `calculate_priority_node` scores the request.
4. `route_request_node` decides whether the request is urgent or category-routed.
5. If the score is urgent, the request goes to `urgent_node`.
6. The urgent branch assigns the learner to the urgent handling team.
7. `summary_node` finalizes the response and status.

This means the graph is both sequential and conditional:

- sequential in the early stages where every request must be received and scored
- conditional in the routing stage where the path depends on the state

## Test Input

The current runnable example in [src/main.py](/Users/immanuel/Documents/Learning/unlimited-code/agentic_ai_class/week_three/learner_support/src/main.py:1) uses this test input:

```python
{
    "learner_name": "Ada",
    "email": "ada@example.com",
    "category": "technical",
    "message": "My project will not run and the submission is due tonight.",
    "days_until_deadline": 0,
    "is_paid_student": True,
    "priority_score": 0,
    "priority": "normal",
    "route": "general",
    "assigned_team": "",
    "status": "new",
    "response": "",
    "audit_log": []
}
```

This input is expected to become urgent because:

- the deadline is immediate
- the request is technical
- the message contains time-sensitive wording
- the learner is a paid student

Expected outcomes include:

- a high `priority_score`
- final `priority` of `urgent`
- final `route` of `urgent`
- assignment to the urgent team
- final status of `escalated`

## Reflection

### Why Is `TypedDict` Useful For LangGraph State?

`TypedDict` is useful because LangGraph workflows depend on a shared state object being passed from node to node. Without a defined structure, it becomes very easy to make mistakes such as:

- using the wrong key name
- forgetting a required field
- mixing incompatible value types
- losing track of what each node expects

`TypedDict` gives the workflow a clear schema-like contract while still keeping the state as a normal Python dictionary. It improves readability, editor support, and static checking without adding the overhead of a more complex object model.

### Why Should Nodes Return Only Updates Instead Of Rebuilding Unrelated State Fields?

Nodes should return only updates because a node should own only the part of the state it is responsible for. Rebuilding unrelated fields is risky and unnecessary.

If a node rewrites fields it does not own, it can:

- accidentally erase earlier values
- introduce stale data
- create hidden coupling between nodes
- make debugging much harder

Returning only updates makes the workflow more modular. Each node becomes easier to reason about because its output is limited to the decisions it actually made.

### How Does The Conditional Edge Make This Workflow More Useful Than A Linear Graph?

A linear graph treats every request the same way. That is unrealistic for support triage because all requests should not receive the same handling.

The conditional edge makes the workflow useful because it allows the graph to adapt based on state. An urgent technical request should not follow the same path as a general question about course access. Conditional routing allows:

- escalation of urgent requests
- specialization by support function
- cleaner separation of responsibilities
- more realistic support operations

This is the main reason LangGraph is a strong fit for triage-style systems.

### Which Additional Branch Or State Field Would You Add In A Real Support System?

A strong next addition would be a `fraud_or_account_security` branch. Real support systems often need to distinguish standard billing issues from suspicious account events such as:

- unauthorized purchases
- password-reset abuse
- account lockouts
- identity mismatch

I would also add a `learner_tier` or `service_level` state field. That would allow the workflow to treat enterprise learners, scholarship learners, or high-priority cohorts differently from standard cases. In a real system, service level often affects routing speed, escalation policy, and team assignment.

Other useful future fields would be:

- `ticket_id`
- `created_at`
- `language`
- `region`
- `previous_contact_count`
- `attachments_present`

## How To Run The App

### Install Dependencies

From the project root:

```bash
uv sync
```

If you want environment variables available locally:

```bash
cp .env.example .env
```

### Run The Python App

Run the graph example from the command line:

```bash
uv run src/main.py
```

This compiles the LangGraph workflow, invokes it with the sample test input, runs a few assertions, and prints the final state as formatted JSON.

### Run The Notebook

Open [support_triage.ipynb](/Users/immanuel/Documents/Learning/unlimited-code/agentic_ai_class/week_three/learner_support/support_triage.ipynb:1) in VS Code or Jupyter and select the project interpreter from:

`week_three/learner_support/.venv`

Then run the notebook cells in order. The notebook includes:

- the same triage logic as the Python script
- graph compilation
- graph visualization with `draw_mermaid_png()`
- a sample invocation with formatted output

