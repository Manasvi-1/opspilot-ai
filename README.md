# OpsPilot AI – Autonomous Business Operations & Exception Management Platform

[![CI](https://github.com/Manasvi-1/opspilot-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/Manasvi-1/opspilot-ai/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A practical AI automation system for UK ecommerce and consumer businesses. Designed to demonstrate real-world engineering for AI Automation roles: business problem → architecture → working automation → reliability → measurable outcomes.

**Not a chatbot.** A controlled operations system with human-in-the-loop gates, auditability, and deterministic safety checks.

## Core Capabilities

1. **AI Customer Operations Agent** – Intent classification, order lookup, evidence-backed responses
2. **Intelligent Refund & Returns Workflow** – Deterministic eligibility + mandatory human approval
3. **Exception Detection** – Stuck orders, delays, policy violations
4. **Business Intelligence** – Answers operational questions from real database queries
5. **Human-in-the-loop Control Centre** – Approve/reject, inspect evidence, full audit trail

## Architecture

```
Customer / Operations Manager
        ↓
FastAPI Backend (Auth · Validation · REST)
        ↓
Agent Orchestration (LangGraph-ready state machine)
        ↓
PostgreSQL / SQLite + Audit Events
        ↓
Controlled Business Actions (Approval-gated)
```

- **Backend**: Python + FastAPI + SQLAlchemy
- **Agent**: Deterministic + structured (LLM upgrade path)
- **Workflow**: n8n / webhook ready
- **Database**: SQLite (dev) → PostgreSQL (prod)
- **Observability**: Audit logs on every decision

## Quick Start

```bash
git clone https://github.com/Manasvi-1/opspilot-ai.git
cd opspilot-ai
pip install -r backend/requirements.txt
python -m backend.models          # seeds sample data
cd backend && uvicorn main:app --reload
```

- API Docs: http://localhost:8000/docs
- Control Centre: http://localhost:8000/dashboard

Or with Docker:

```bash
docker-compose up --build
```

## Demo Scenarios

| Scenario | What it proves |
|----------|----------------|
| Delayed order inquiry | LLM + real data integration |
| Ineligible refund | Business-rule enforcement |
| Eligible refund | Human approval workflow |
| Duplicate webhook | Idempotency |
| API failure | Retry + escalation |

## Engineering Principles

- **Idempotency**: Duplicate events never create duplicate side effects
- **Human authorization**: Sensitive actions (refunds) require explicit approval
- **Auditability**: Every decision has input, evidence, and outcome
- **Structured outputs**: Validated schemas, not free-text execution
- **Escalation**: Uncertainty goes to humans, not automatic execution

## Project Structure

```
opspilot-ai/
├── backend/           # FastAPI application
│   ├── main.py
│   ├── models.py
│   └── requirements.txt
├── tests/             # Pytest suite
├── .github/workflows/ # CI + security scanning
├── Dockerfile
├── docker-compose.yml
└── docs/              # Architecture notes
```

## License

MIT
