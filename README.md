# Parking Assistant

An intelligent parking chatbot system that provides parking information, handles reservation workflows with human-in-the-loop approval, and persists data via an MCP server.

## Architecture

The system consists of 3 main components orchestrated via LangGraph:

```
                         +------------------+
                         |   User Message   |
                         +--------+---------+
                                  |
                         +--------v---------+
                         | Guardrails Input |----> [Blocked] ---> END
                         +--------+---------+
                                  |
                         +--------v---------+
                         | Intent Classify  |
                         +--------+---------+
                                  |
                    +-------------+-------------+
                    |                           |
           +--------v--------+        +--------v-----------+
           | RAG Chatbot     |        | Create Reservation |
           | (Weaviate +LLM) |        +--------+-----------+
           +--------+--------+                 |
                    |                  +--------v-----------+
           +--------v---------+       | Admin Approval     |
           | Guardrails Output |      | (Human-in-the-Loop)|
           +--------+---------+       +--------+-----------+
                    |                           |
                   END              +-----------+-----------+
                                    |                       |
                           +--------v------+       +--------v--------+
                           | MCP Persist   |       | Notify Rejected |
                           | (FastAPI)     |       +---------+-------+
                           +--------+------+                 |
                                    |                       END
                                   END
```

**RAG Chatbot Agent** - Retrieval-Augmented Generation pipeline using Weaviate as the vector database. Answers questions about parking rates, hours, location, availability, and more.

**Human-in-the-Loop Agent** - Pauses the workflow using LangGraph interrupts to request administrator approval for reservations. Supports approve/reject decisions.

**MCP Server** - FastAPI-based server that persists approved reservations to a JSON file. Exposes REST endpoints for reservation CRUD operations.

## Prerequisites

- Python 3.11+
- Docker and Docker Compose
- OpenAI API key

## Setup

### 1. Clone and install

```bash
git clone https://github.com/Sandrog112/parking-assistant.git
cd parking-assistant
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and set your OPENAI_API_KEY
```

### 3. Start Weaviate

```bash
docker-compose up -d
```

### 4. Ingest knowledge base

```bash
python -m parking_assistant.rag.knowledge
```

### 5. Start MCP server

```bash
uvicorn parking_assistant.mcp.server:app --host 0.0.0.0 --port 8000
```

## Usage

### Informational Query

```python
from langchain_core.messages import HumanMessage
from parking_assistant.graph.workflow import graph

config = {"configurable": {"thread_id": "session-1"}}
result = graph.invoke(
    {"messages": [HumanMessage(content="What are the parking rates?")]},
    config=config,
)
print(result["messages"][-1].content)
```

### Reservation Flow

```python
from langchain_core.messages import HumanMessage
from langgraph.types import Command
from parking_assistant.graph.workflow import graph

config = {"configurable": {"thread_id": "session-2"}}

# Step 1: User requests a reservation
result = graph.invoke(
    {"messages": [HumanMessage(
        content="I'd like to reserve a spot. Name: John Doe, car ABC-1234, tomorrow 9am to 5pm"
    )]},
    config=config,
)

# Graph pauses at admin_approval node
state = graph.get_state(config)
print(state.next)  # ('admin_approval',)

# Step 2: Admin approves
result = graph.invoke(
    Command(resume={"approved": True, "reason": "Approved"}),
    config=config,
)
print(result["messages"][-1].content)  # Reservation confirmed
```

### Admin Rejection

```python
# Resume with rejection instead
result = graph.invoke(
    Command(resume={"approved": False, "reason": "No spots available"}),
    config=config,
)
print(result["messages"][-1].content)  # Reservation not approved
```

### MCP Server API

```bash
# Create reservation
curl -X POST http://localhost:8000/reservations \
  -H "Content-Type: application/json" \
  -d '{"name":"John","surname":"Doe","car_number":"ABC-1234","start_time":"2026-04-12T09:00","end_time":"2026-04-12T17:00"}'

# List reservations
curl http://localhost:8000/reservations

# Approve reservation
curl -X POST http://localhost:8000/reservations/{id}/approve \
  -H "Content-Type: application/json" \
  -d '{"reservation_id":"{id}","approved":true,"reason":"Approved"}'
```

## Testing

```bash
pytest tests/ -v
```

Tests cover:
- **test_guardrails.py** - PII redaction, injection blocking, clean input passthrough
- **test_reservation.py** - Reservation model defaults, approval decision model
- **test_mcp.py** - FastAPI endpoints for create, list, approve, reject
- **test_rag.py** - Retrieval with mocked Weaviate, empty query handling
- **test_admin.py** - Full approval/rejection flow with LangGraph interrupt/resume

All tests use mocks — no external services required.

## Evaluation

The evaluation module provides retrieval quality metrics:

```python
from parking_assistant.evaluation.metrics import recall_at_k, precision_at_k, retrieval_quality

relevant = {"doc1", "doc2", "doc3"}
retrieved = ["doc1", "doc3", "doc5"]

print(recall_at_k(relevant, retrieved, k=3))     # 0.667
print(precision_at_k(relevant, retrieved, k=3))   # 0.667
```

## Terraform Deployment

Deploy to AWS EC2:

```bash
cd terraform

# Initialize
terraform init

# Preview changes
terraform plan -var="key_name=your-ssh-key"

# Deploy
terraform apply -var="key_name=your-ssh-key"

# Get outputs
terraform output instance_public_ip
terraform output mcp_url

# Destroy
terraform destroy -var="key_name=your-ssh-key"
```

The deployment provisions:
- VPC with public subnet and internet gateway
- Security group (ports 22, 8000, 8080)
- EC2 instance (t3.medium, Ubuntu 22.04)
- Automatic setup via user_data script (Docker, Python, app install)

## Project Structure

```
parking-assistant/
├── README.md
├── .gitignore
├── pyproject.toml
├── docker-compose.yml
├── .env.example
├── src/parking_assistant/
│   ├── config.py                 # Environment configuration
│   ├── models.py                 # Pydantic data models
│   ├── rag/
│   │   ├── vectorstore.py        # Weaviate client management
│   │   ├── retriever.py          # Semantic search
│   │   └── knowledge.py          # Knowledge base ingestion
│   ├── agents/
│   │   ├── chatbot.py            # RAG chatbot + intent classifier
│   │   └── admin.py              # Human-in-the-loop approval
│   ├── guardrails/
│   │   └── filters.py            # Input/output safety filters
│   ├── mcp/
│   │   └── server.py             # FastAPI reservation server
│   ├── graph/
│   │   ├── state.py              # LangGraph state definition
│   │   └── workflow.py           # Graph orchestration
│   └── evaluation/
│       └── metrics.py            # Retrieval quality metrics
├── tests/
│   ├── conftest.py               # Shared test fixtures
│   ├── test_rag.py
│   ├── test_reservation.py
│   ├── test_admin.py
│   ├── test_mcp.py
│   └── test_guardrails.py
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── user_data.sh
└── data/
    └── parking_knowledge.json    # Parking knowledge base
```
