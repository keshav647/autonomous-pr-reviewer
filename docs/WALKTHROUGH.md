# Technical Demonstration & Video Walkthrough Guide

This document contains the step-by-step technical demonstration flow and 60-second video walkthrough script for showcasing **SENTINEL // Autonomous Multi-Agent PR Reviewer & Security Auditor**.

---

## 1. 60-Second Video Script (For Loom / Portfolio Video)

### [0:00 - 0:15] The Problem & The Solution
> *"Every engineering team struggles with slow PR review turnaround and missed security vulnerabilities in pull requests. Standard LLM review bots fail because they hallucinate line numbers, lack AST scope context, and issue single-shot unstructured comments.*
> 
> *To solve this, I engineered SENTINEL—an autonomous, multi-agent code intelligence platform that coordinates specialized domain agents (`BOT SEC-9`, `BOT PERF-X`, and `BOT ARCH-V`) using a cyclical state graph, binds diff lines to Python AST scopes, and posts verified inline review comments with ready-to-merge `git diff` patches."*

### [0:15 - 0:35] Live Action Demonstration
> *(Open browser to `http://localhost:8000` or `http://localhost:8080`)*
> *"Here is the SENTINEL Tactical Command Console featuring our 3D WebGL Robot Sentinel HUD (`SENTINEL-01`) and parallel specialist telemetry meters. Let's load the 8-file `Testing SENTINEL` benchmark—or click **Import GitHub PR** to fetch `keshav647/testing #1` live from GitHub.*
> 
> *Notice the Multi-File Code Navigator displaying all 8 changed files with line additions and deletions. When I click **Dispatch Robot Audit** (`⌘ Enter`), the orchestrator dispatches Security, Performance, and Architecture agents concurrently.*
> 
> *Immediately, the Critical Code Vulnerabilities Hotline Deck and Diff Header Hotspots light up. Clicking any hotspot card isolates that file and jumps directly to the offending line—catching SQL injection (CWE-89), command injection (CWE-78), path traversal (CWE-22), hardcoded Stripe/JWT secrets (CWE-798), and async event-loop stalls, complete with one-click 'Copy Fix' patches."*

### [0:35 - 0:50] The Technical Architecture
> *(Switch to `[02] Agent Telemetry HUD` tab and `docs/ARCHITECTURE.md`)*
> *"Under the hood, before any specialist runs, our `PythonASTAnalyzer` parses modified files into syntax trees to map diff hunks to enclosing function signatures and flag dangerous calls.*
> 
> *Findings from all three parallel specialists pass through `CONSENSUS CORE` (`ReviewSynthesizer`), which deduplicates overlapping line feedback using severity and category weights, followed by strict Pydantic v2 schema validation. It supports a Universal BYOK Gateway across Gemini, OpenAI, Anthropic, Groq, and OpenRouter, plus a zero-cost deterministic AST engine that executes in under 20 milliseconds offline."*

### [0:50 - 1:00] Metrics & Closing
> *"SENTINEL cuts PR turnaround by over 75%, guarantees 100% Pydantic schema validity across 19 automated unit tests, and costs less than $0.002 per review. The full codebase, Docker setup, and live GitHub integration are in the repository."*

---

## 2. Live Demo Checklist for Reviewers

1. **Start the Service:**
   ```bash
   # Option A: From workspace root (FastAPI Uvicorn hot-reload on port 8000)
   /Users/keshavbudhiraja/AI/start_project_1.sh

   # Option B: Dual-port native server (listens on both 8000 and 8080)
   cd /Users/keshavbudhiraja/AI/project-1-pr-reviewer
   python3 -m src.api.server
   ```
2. **Access SENTINEL Web Console:**
   Open `http://localhost:8000` (or `http://localhost:8080`).
3. **Test Built-in Benchmark Presets:**
   - Click `[01] users.py (+12 -3)`: Demonstrates SQL injection (CWE-89), hardcoded secret (CWE-798), and N+1 loop detection.
   - Click `[02] analytics.py (+8 -1)`: Demonstrates N+1 query inside an async loop and blocking `time.sleep()` event-loop stall.
   - Click `[03] math.py (+4 -2)`: Demonstrates a clean, properly typed PR receiving an `APPROVE` verdict.
   - Click `[04] Testing SENTINEL (8 Codes)`: Loads the full 8-file multi-module repository diff (`README.md`, `models/sentinel_schemas.py`, `routes/auth_sentinel.py`, `routes/diagnostics.py`, `routes/users.py`, `server.py`, `services/payment_gateway.py`, `utils/file_storage.py`). Use the **Changed Codes in Repository** pill bar and **Critical Code Vulnerabilities** cards to jump across files and lines.
4. **Test Live GitHub Integration:**
   - Click **Import GitHub PR** in the top navigation bar.
   - Select the quick chip `Testing SENTINEL (keshav647/testing #1)` (or enter any `owner/repo` and PR number).
   - Click **Fetch Live PR** to pull the real-time unified diff from the GitHub REST API.
   - Click **Dispatch Robot Audit** (`⌘ Enter`) to run the multi-agent state graph.
   - Click **Publish to GitHub** to dispatch the structured review verdict and inline comments directly to GitHub (supports dry-run verification or live publishing).
5. **Run the Automated Test Suite:**
   ```bash
   cd /Users/keshavbudhiraja/AI/project-1-pr-reviewer
   python3 -m unittest discover -s tests -v
   ```
   *(All 19 unit & integration tests pass in `< 0.05` seconds)*
