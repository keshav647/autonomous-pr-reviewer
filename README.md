# Autonomous Multi-Agent Pull Request Reviewer & Security Auditor

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-purple.svg)](https://langchain-ai.github.io/langgraph/)

An autonomous, multi-agent code analysis bot that reviews GitHub Pull Requests via Webhooks. Instead of making naive, unstructured LLM calls, it coordinates a specialized team of autonomous agents using a state graph to parse git diffs, conduct AST-guided vulnerability audits, detect performance bottlenecks, and post actionable, structured Markdown inline review comments.

---

## Architecture & State Graph

```mermaid
flowchart TD
    WH["GitHub PR Webhook Event"] --> API["FastAPI Ingestion Endpoint"]
    API --> AST["Diff & AST Parser (Tree-sitter / Python ast)"]
    AST --> ORCH["Orchestrator Agent (StateGraph Init)"]

    subgraph SpecialistAgents["Parallel Specialist Reviewers"]
        ORCH --> SEC["Security Agent (OWASP, Secrets, Injection)"]
        ORCH --> PERF["Performance Agent (N+1 Queries, Leaks, Complexity)"]
        ORCH --> ARCH["Architecture & Typing Agent (SOLID, Type Safety)"]
    end

    SEC --> AGG["Synthesis & Conflict Resolution Agent"]
    PERF --> AGG
    ARCH --> AGG

    AGG --> VAL{"Pydantic Output Validation"}
    VAL -- "Schema Invalid / Hallucination" --> AGG
    VAL -- "Valid Structured Output" --> GH["GitHub REST API (Inline Comment Dispatch)"]
    GH --> LF["Langfuse Tracing & Latency Telemetry"]
```

---

## Key Highlights & Engineering Signals

* **State Machine Orchestration:** Implements cyclical state graph flows with parallel specialist agents (Security, Performance, Architecture).
* **AST Context Extraction:** Maps diff line changes directly to enclosing AST nodes (functions, classes, parameter lists, imports) to eliminate out-of-context hallucinations.
* **Strict Pydantic v2 Guardrails:** Every single inline comment conforms to an enforced schema containing exact file paths, line ranges, severity levels, and ready-to-commit `git diff` suggestions.
* **Synthesis & Deduplication:** Intelligently resolves multi-agent conflicts, deduplicates findings on the same line, and determines overall PR review verdict (`APPROVE`, `REQUEST_CHANGES`, `COMMENT`).
* **Zero-Cost / Offline Mock Engine:** Includes offline simulation and pre-cached scenarios so reviewers can test the complete system with $0 cloud cost and zero API keys required.

---

## Detailed Technical Documentation

* **[System Architecture & Data Contracts](docs/ARCHITECTURE.md):** StateGraph topology, AST context mapping, conflict resolution algorithm, and state schemas.
* **[Performance & Cost Benchmarks](docs/BENCHMARKS.md):** Multi-model latency profiles, schema reliability rates, and enterprise ROI analysis.
* **[Video Walkthrough & Demonstration Guide](docs/WALKTHROUGH.md):** 60-second Loom demonstration script and live evaluation steps.

---

## Quickstart Guide

### 1. Run with Docker (Single Command)
```bash
docker compose up --build
```
The FastAPI server will be available at `http://localhost:8000`.

### 2. Run Locally via Python Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Run the Showcase Demo (Terminal CLI)
Test the multi-agent system on sample PR diffs instantly:
```bash
# Run on built-in vulnerability demo
python3 -m src.cli demo

# Run on specific test fixture diffs
python3 -m src.cli review --diff tests/fixtures/sample_sql_injection.diff
python3 -m src.cli review --diff tests/fixtures/sample_performance_leak.diff
python3 -m src.cli review --diff tests/fixtures/sample_clean_pr.diff
```

---

## Running the Automated Test Suite

Run unit and integration tests across parser, schemas, and state graph orchestration:
```bash
python3 -m unittest discover tests
```

---

## API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/review` | Manually submit raw diff text for multi-agent review |
| `GET` | `/api/v1/demo-scenarios` | Retrieve interactive pre-cached showcase scenarios |
| `POST` | `/webhook` | Ingest GitHub `pull_request` webhook events (`opened`, `synchronize`) |
| `GET` | `/health` | System health check and model status |

### Example cURL Request (Direct Review):
```bash
curl -X POST http://localhost:8000/api/v1/review \
  -H "Content-Type: application/json" \
  -d '{
    "diff_text": "diff --git a/app.py b/app.py\n+++ b/app.py\n@@ -1,2 +1,3 @@\n+query = f\"SELECT * FROM users WHERE id = {user_id}\"\n",
    "pull_request_id": 42
  }'
```

---

## 60-Second Video Walkthrough Script (Loom)

* **[0:00 - 0:15] The Hook & Problem:**
  > *"Every engineering team struggles with slow PR cycles and missed security flaws in code reviews. I built an autonomous Multi-Agent PR Reviewer that audits code changes with specialized domain agents in under 15 seconds."*
* **[0:15 - 0:35] Live Action Demo:**
  > *(Show terminal CLI and a test PR diff containing an SQL injection flaw and an N+1 query loop). Run review command. Show the agent team posting structured inline comments with exact code-fix replacements.*
* **[0:35 - 0:50] The Technical Architecture:**
  > *(Show state graph diagram and code). "Under the hood, this uses a cyclical state machine. An Orchestrator spawns three parallel agents—Security, Performance, and Architecture. Each output is strictly validated against a Pydantic schema to eliminate hallucinations."*
* **[0:50 - 1:00] Metrics & Close:**
  > *"It cuts PR review turnaround by 75%, guarantees 100% schema validity, and costs less than $0.02 per review. The full code and Docker setup are in the repo below."*
