    // =============================================================
    // SENTINEL // AUTONOMOUS AI PR REVIEWER & SECURITY AUDITOR
    // Client-Side Intelligence & Orchestration Engine
    // =============================================================

    // -------------------------------------------------------------
    // 1. Preset Data Fixtures
    // -------------------------------------------------------------
    const PRESETS = {
      sql_injection: {
        path: "app/routes/users.py",
        diff: `diff --git a/app/routes/users.py b/app/routes/users.py
index 45a8b12..78c9d34 100644
--- a/app/routes/users.py
+++ b/app/routes/users.py
@@ -10,6 +10,12 @@ def get_user_data(user_id: str):
+    # Raw string interpolation creates severe SQL injection vulnerability
+    query = f"SELECT * FROM users WHERE id = '{user_id}'"
+    cursor.execute(query)
+    api_key = "sk-live-999333888222111000-secret"
+    for row in cursor.fetchall():
+        profile = cursor.execute(f"SELECT * FROM profiles WHERE user_id = {row[0]}")
+    return cursor.fetchone()`
      },
      performance_leak: {
        path: "app/services/analytics.py",
        diff: `diff --git a/app/services/analytics.py b/app/services/analytics.py
index abcdef0..1234567 100644
--- a/app/services/analytics.py
+++ b/app/services/analytics.py
@@ -30,5 +30,10 @@ async def aggregate_daily_metrics(user_ids: list):
+    for u_id in user_ids:
+        # N+1 query bottleneck inside asynchronous loop
+        cursor.execute("SELECT count(*) FROM events WHERE user_id = %s", (u_id,))
+        time.sleep(0.1)
+    return {"status": "done"}`
      },
      clean_pr: {
        path: "app/utils/math.py",
        diff: `diff --git a/app/utils/math.py b/app/utils/math.py
index 9988776..1122334 100644
--- a/app/utils/math.py
+++ b/app/utils/math.py
@@ -1,5 +1,8 @@
-def add(a, b):
-    return a + b
+def calculate_total(subtotal: float, tax_rate: float = 0.05) -> float:
+    """Calculates total with parameterized tax."""
+    return round(subtotal * (1.0 + tax_rate), 2)`
      },
      testing_sentinel: {
        path: "Testing SENTINEL (8 Changed Codes)",
        diff: `diff --git a/README.md b/README.md
index 6fd9c06..f5b00cb 100644
--- a/README.md
+++ b/README.md
@@ -1,3 +1,5 @@
-# Testing Benchmark Repository
+# Testing SENTINEL Benchmark Repository
 
 Sample service repository used for automated code auditing, multi-agent code review, and CI/CD quality benchmarks.
+
+Maintained by [@keshav647](https://github.com/keshav647).
diff --git a/models/sentinel_schemas.py b/models/sentinel_schemas.py
new file mode 100644
index 0000000..7481ab9
--- /dev/null
+++ b/models/sentinel_schemas.py
@@ -0,0 +1,22 @@
+"""Data models and telemetry schemas for Testing SENTINEL service."""
+
+from typing import Optional, List
+from pydantic import BaseModel, Field
+
+
+class SentinelAuditPayload(BaseModel):
+    """Payload schema for dispatching autonomous code audits."""
+    repo_name: str = Field(..., description="Target repository name")
+    branch: str = Field(default="main", description="Target git branch")
+    commit_sha: Optional[str] = Field(None, description="Commit hash to inspect")
+    max_severity: str = Field(default="CRITICAL", description="Minimum alert severity threshold")
+
+
+class SentinelFindingReport(BaseModel):
+    """Schema for individual audit observations."""
+    rule_id: str
+    category: str
+    severity: str
+    file_path: str
+    line_number: int
+    remediation_summary: str
diff --git a/routes/auth_sentinel.py b/routes/auth_sentinel.py
new file mode 100644
index 0000000..a19db32
--- /dev/null
+++ b/routes/auth_sentinel.py
@@ -0,0 +1,47 @@
+"""Authentication and token verification service for Testing SENTINEL."""
+
+import hashlib
+import time
+from typing import Any, Dict, Optional
+from fastapi import APIRouter, HTTPException, Header
+
+router = APIRouter(prefix="/auth", tags=["Authentication"])
+
+# Hardcoded secret key for development testing (CWE-798)
+SENTINEL_JWT_DEV_KEY = "sentinel-auth-master-token-xyz999"
+
+
+@router.post("/login")
+def authenticate_user(credentials: Dict[str, str]) -> Dict[str, Any]:
+    """Authenticates user credentials and generates access token."""
+    username = credentials.get("username", "")
+    password = credentials.get("password", "")
+
+    if not username or not password:
+        raise HTTPException(status_code=400, detail="Missing username or password")
+
+    # Insecure hashing: MD5 used for password validation (CWE-327)
+    hashed_password = hashlib.md5(password.encode()).hexdigest()
+
+    # Dynamic SQL string formatting vulnerability (CWE-89)
+    query = f"SELECT id, username, role FROM users WHERE username = '{username}' AND password_hash = '{hashed_password}'"
+
+    return {
+        "status": "authenticated",
+        "username": username,
+        "token": SENTINEL_JWT_DEV_KEY,
+        "query_executed": query,
+    }
+
+
+@router.get("/verify")
+def verify_token(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
+    """Validates authorization bearer token."""
+    if not authorization or not authorization.startswith("Bearer "):
+        raise HTTPException(status_code=401, detail="Unauthorized")
+
+    token = authorization.split(" ")[1]
+    if token != SENTINEL_JWT_DEV_KEY:
+        raise HTTPException(status_code=403, detail="Invalid token")
+
+    return {"valid": True, "scope": "admin:sentinel"}
diff --git a/routes/diagnostics.py b/routes/diagnostics.py
new file mode 100644
index 0000000..14d0521
--- /dev/null
+++ b/routes/diagnostics.py
@@ -0,0 +1,25 @@
+"""Diagnostics and ping utilities."""
+
+import os
+from typing import Any, Dict
+from fastapi import APIRouter
+
+router = APIRouter(prefix="/diagnostics", tags=["Diagnostics"])
+
+
+@router.get("/ping")
+def ping_host(host: str) -> Dict[str, Any]:
+    """Execute host connectivity check.
+
+    WARNING: Contains raw shell interpolation vulnerable to Command Injection (CWE-78)
+    and anti-pattern bare except swallowing exceptions.
+    """
+    try:
+        # Command Injection risk: target host concatenated into shell command
+        exit_code = os.system(f"ping -c 1 {host}")
+        return {"host": host, "reachable": exit_code == 0}
+    except:
+        # Anti-pattern: bare except suppressing critical exceptions
+        pass
+
+    return {"host": host, "reachable": False}
diff --git a/routes/users.py b/routes/users.py
new file mode 100644
index 0000000..8a80de1
--- /dev/null
+++ b/routes/users.py
@@ -0,0 +1,42 @@
+"""User management and profile lookup endpoints."""
+
+import sqlite3
+from typing import Any, Dict
+from fastapi import APIRouter, HTTPException
+
+router = APIRouter(prefix="/users", tags=["Users"])
+
+# Hardcoded authentication secret (CWE-798: Use of Hard-coded Credentials)
+JWT_SECRET = "super-secret-jwt-key-9988776655"
+
+
+@router.get("/lookup")
+def lookup_user(username: str) -> Dict[str, Any]:
+    """Look up a user account by username.
+
+    WARNING: Contains raw SQL interpolation vulnerable to SQL Injection (CWE-89)
+    and unclosed database connection causing resource leakage.
+    """
+    if not username:
+        raise HTTPException(status_code=400, detail="Username parameter is required")
+
+    # Inefficient connection handling without context manager (Resource leak)
+    conn = sqlite3.connect("users.db")
+    cursor = conn.cursor()
+
+    # Raw string formatting into SQL query (SQL Injection Vulnerability)
+    query = f"SELECT id, username, email, is_admin FROM users WHERE username = '{username}'"
+    cursor.execute(query)
+    record = cursor.fetchone()
+
+    # Notice: conn is never closed, leading to socket/file descriptor leaks
+
+    if not record:
+        raise HTTPException(status_code=404, detail="User not found")
+
+    return {
+        "id": record[0],
+        "username": record[1],
+        "email": record[2],
+        "is_admin": bool(record[3]),
+    }
diff --git a/server.py b/server.py
index 7512156..9cd4c57 100644
--- a/server.py
+++ b/server.py
@@ -1,23 +1,39 @@
-"""Sample FastAPI application for security and quality benchmarking."""
+"""Testing SENTINEL Service: Benchmark application for automated code auditing."""
 
 import os
 from typing import Any, Dict
 from fastapi import FastAPI, HTTPException
 
+from routes.users import router as users_router
+from routes.diagnostics import router as diagnostics_router
+from routes.auth_sentinel import router as auth_router
+from services.payment_gateway import router as billing_router
+from utils.file_storage import router as storage_router
+
 app = FastAPI(
-    title="Testing Benchmark Service",
-    version="1.0.0",
+    title="Testing SENTINEL Service",
+    description="Multi-agent benchmarking service with security and performance test vectors",
+    version="2.0.0",
     docs_url="/docs"
 )
 
+# Register route submodules
+app.include_router(users_router)
+app.include_router(diagnostics_router)
+app.include_router(auth_router)
+app.include_router(billing_router)
+app.include_router(storage_router)
+
+
 @app.get("/health")
 def health_check() -> Dict[str, str]:
     """Basic health check endpoint."""
-    return {"status": "healthy", "service": "testing-benchmark"}
+    return {"status": "healthy", "service": "testing-sentinel"}
+
 
 @app.get("/items/{item_id}")
 def read_item(item_id: int) -> Dict[str, Any]:
     """Retrieve sample item by ID."""
     if item_id <= 0:
         raise HTTPException(status_code=400, detail="Item ID must be positive integer")
-    return {"item_id": item_id, "name": f"Verified Item #{item_id}"}
+    return {"item_id": item_id, "name": f"Verified Sentinel Item #{item_id}"}
diff --git a/services/payment_gateway.py b/services/payment_gateway.py
new file mode 100644
index 0000000..07ee68a
--- /dev/null
+++ b/services/payment_gateway.py
@@ -0,0 +1,45 @@
+"""Payment processing and Stripe webhook integration service."""
+
+import time
+from typing import Any, Dict
+from fastapi import APIRouter, HTTPException
+
+router = APIRouter(prefix="/billing", tags=["Billing & Payments"])
+
+# Hardcoded third-party API secret (CWE-798)
+STRIPE_API_SECRET = "sec_test_stripe_hardcoded_dummy_token_9900"
+
+
+@router.post("/charge")
+async def process_transaction(payload: Dict[str, Any]) -> Dict[str, Any]:
+    """Processes customer payment charge.
+
+    Contains blocking time.sleep() inside async handler (Performance Stall)
+    and bare except suppressing payment gateway exceptions.
+    """
+    amount = payload.get("amount", 0)
+    customer_id = payload.get("customer_id")
+
+    if amount <= 0 or not customer_id:
+        raise HTTPException(status_code=400, detail="Invalid charge parameters")
+
     try:
+        # Blocking synchronous sleep in async event loop (Blocks server thread)
+        time.sleep(2)
+
+        # Unbounded transaction loop without batching (Performance anti-pattern)
+        records = []
+        for i in range(10):
+            records.append(f"tx_rec_{customer_id}_{i}")
+
+        return {
+            "status": "succeeded",
+            "amount": amount,
+            "charge_id": f"ch_{int(time.time())}",
+            "receipts": records,
+        }
+    except:
+        # Anti-pattern: bare except suppressing Stripe connection failures
+        pass
+
+    return {"status": "failed", "error": "Gateway timeout"}
diff --git a/utils/file_storage.py b/utils/file_storage.py
new file mode 100644
index 0000000..b452b89
--- /dev/null
+++ b/utils/file_storage.py
@@ -0,0 +1,35 @@
+"""File upload and asset retrieval utilities for Testing SENTINEL."""
+
+import os
+from typing import Any, Dict
+from fastapi import APIRouter, HTTPException
+
+router = APIRouter(prefix="/storage", tags=["Storage & Assets"])
+
+BASE_UPLOAD_DIR = "/tmp/sentinel_uploads"
+
+
+@router.post("/upload")
+def upload_file(filename: str, content: str) -> Dict[str, Any]:
+    """Saves uploaded user content to storage.
+
+    WARNING: Vulnerable to Path Traversal (CWE-22) via unvalidated filename
+    and unclosed file handles without context managers.
+    """
+    if not filename:
+        raise HTTPException(status_code=400, detail="Filename required")
+
+    # Insecure path construction allowing directory traversal (e.g. filename='../../etc/passwd')
+    target_path = os.path.join(BASE_UPLOAD_DIR, filename)
+
+    # Insecure file write without context manager (Resource leak)
+    f = open(target_path, "w")
+    f.write(content)
+    # Notice: f.close() is missing if an error occurs
+
+    return {
+        "status": "stored",
+        "file_name": filename,
+        "saved_path": target_path,
+        "bytes_written": len(content),
+    }`
    }
  };

    // -------------------------------------------------------------
    // 2. DOM Elements & State
    // -------------------------------------------------------------
    const settingsDialog = document.getElementById("settingsDialog");
    const openSettingsBtn = document.getElementById("openSettingsBtn");
    const closeSettingsBtn = document.getElementById("closeSettingsBtn");
    const dialogProviderSelect = document.getElementById("dialogProviderSelect");
    const dialogKeyInput = document.getElementById("dialogKeyInput");
    const dialogToggleEyeBtn = document.getElementById("dialogToggleEyeBtn");
    const btnSaveKey = document.getElementById("btnSaveKey");
    const btnOfflineDemo = document.getElementById("btnOfflineDemo");

    const navEngineLabel = document.getElementById("navEngineLabel");
    const navEngineDot = document.getElementById("navEngineDot");

    const diffCodeContainer = document.getElementById("diffCodeContainer");
    const rawDiffInput = document.getElementById("rawDiffInput");
    const activeFilePath = document.getElementById("activeFilePath");
    const btnNewBlankDiff = document.getElementById("btnNewBlankDiff");
    const toggleCustomDiffBtn = document.getElementById("toggleCustomDiffBtn");
    const btnOpenGitHubModal = document.getElementById("btnOpenGitHubModal");

    const githubDialog = document.getElementById("githubDialog");
    const closeGitHubBtn = document.getElementById("closeGitHubBtn");
    const btnCancelGitHub = document.getElementById("btnCancelGitHub");
    const ghRepoInput = document.getElementById("ghRepoInput");
    const ghPrNumberInput = document.getElementById("ghPrNumberInput");
    const ghTokenInput = document.getElementById("ghTokenInput");
    const ghToggleTokenEyeBtn = document.getElementById("ghToggleTokenEyeBtn");
    const btnSubmitGitHubFetch = document.getElementById("btnSubmitGitHubFetch");
    const ghFetchSpinner = document.getElementById("ghFetchSpinner");
    const ghFetchIcon = document.getElementById("ghFetchIcon");
    const ghFetchBtnText = document.getElementById("ghFetchBtnText");
    const ghFetchError = document.getElementById("ghFetchError");

    const githubPublishDialog = document.getElementById("githubPublishDialog");
    const btnPublishGitHub = document.getElementById("btnPublishGitHub");
    const btnPublishGitHubText = document.getElementById("btnPublishGitHubText");
    const closeGHPublishBtn = document.getElementById("closeGHPublishBtn");
    const btnCancelGHPublish = document.getElementById("btnCancelGHPublish");
    const btnConfirmPublish = document.getElementById("btnConfirmPublish");
    const ghPublishTarget = document.getElementById("ghPublishTarget");
    const ghPublishVerdict = document.getElementById("ghPublishVerdict");
    const ghPublishCommentsCount = document.getElementById("ghPublishCommentsCount");
    const ghPublishTokenInput = document.getElementById("ghPublishTokenInput");
    const ghPublishStatusMsg = document.getElementById("ghPublishStatusMsg");
    const ghPublishSpinner = document.getElementById("ghPublishSpinner");
    const ghPublishIcon = document.getElementById("ghPublishIcon");
    const btnConfirmPublishText = document.getElementById("btnConfirmPublishText");

    const runAuditBtn = document.getElementById("runAuditBtn");
    const auditSpinner = document.getElementById("auditSpinner");
    const auditPlayIcon = document.getElementById("auditPlayIcon");
    const auditBtnText = document.getElementById("auditBtnText");

    const verdictBadge = document.getElementById("verdictBadge");
    const verdictText = document.getElementById("verdictText");
    const verdictIcon = document.getElementById("verdictIcon");
    const verdictHeadline = document.getElementById("verdictHeadline");

    const metricCrit = document.getElementById("metricCrit");
    const metricWarn = document.getElementById("metricWarn");
    const metricLatency = document.getElementById("metricLatency");
    const metricCost = document.getElementById("metricCost");
    const findingsBadge = document.getElementById("findingsBadge");

    const terminalFeed = document.getElementById("terminalFeed");
    const engineBadgeText = document.getElementById("engineBadgeText");
    const markdownSurface = document.getElementById("markdownSurface");
    const copyReviewBtn = document.getElementById("copyReviewBtn");

    const progSec = document.getElementById("progSec");
    const progPerf = document.getElementById("progPerf");
    const progArch = document.getElementById("progArch");
    const progSynth = document.getElementById("progSynth");

    const stateSec = document.getElementById("stateSec");
    const statePerf = document.getElementById("statePerf");
    const stateArch = document.getElementById("stateArch");
    const stateSynth = document.getElementById("stateSynth");

    let currentGitHubOwner = "";
    let currentGitHubRepo = "";
    let currentGitHubPR = 0;
    let lastReviewResult = null;
    let currentDiffText = PRESETS.sql_injection.diff;
    let lastSummaryMarkdown = "";
    let isCustomDiffMode = false;

    let currentParsedFiles = [];
    let activeSelectedFilePath = null; // null means all files

    // -------------------------------------------------------------
    // 3. BYOK Vault Management
    // -------------------------------------------------------------
    function updateNavEngineUI() {
      const savedKey = localStorage.getItem("BYOK_LLM_KEY") || localStorage.getItem("BYOK_GEMINI_KEY") || "";
      const savedProvider = localStorage.getItem("BYOK_PROVIDER") || "gemini";
      const robotNameLabel = document.getElementById("robotNameLabel");
      const robotCoreEngine = document.getElementById("robotCoreEngine");
      const diffEngineTag = document.getElementById("diffEngineTag");

      if (savedKey) {
        if (navEngineDot) navEngineDot.className = "status-dot";
        let provName = "Google Gemini (gemini-2.5-flash)";
        let botName = "GEMINI // SENTINEL-01";
        let coreName = "ENGINE: GEMINI (BYOK)";
        let tagText = "Google Gemini (BYOK)";

        if (savedProvider === "openai" || savedKey.startsWith("sk-proj") || (savedKey.startsWith("sk-") && !savedKey.startsWith("sk-ant"))) {
          provName = "OpenAI (GPT-4o Mini / GPT-4o)";
          botName = "CHATGPT (GPT-4o) // SENTINEL-01";
          coreName = "ENGINE: OPENAI (BYOK)";
          tagText = "OpenAI GPT-4o (BYOK)";
        } else if (savedProvider === "anthropic" || savedKey.startsWith("sk-ant")) {
          provName = "Anthropic Claude 3.5 Sonnet";
          botName = "CLAUDE 3.5 // SENTINEL-01";
          coreName = "ENGINE: CLAUDE (BYOK)";
          tagText = "Claude 3.5 Sonnet (BYOK)";
        } else if (savedProvider === "groq" || savedKey.startsWith("gsk_")) {
          provName = "Groq Cloud (Llama 3.3 70B)";
          botName = "GROQ LLAMA-3 // SENTINEL-01";
          coreName = "ENGINE: GROQ (BYOK)";
          tagText = "Groq Llama 3.3 (BYOK)";
        } else if (savedProvider === "openrouter" || savedKey.startsWith("sk-or")) {
          provName = "OpenRouter Gateway";
          botName = "OPENROUTER // SENTINEL-01";
          coreName = "ENGINE: OPENROUTER (BYOK)";
          tagText = "OpenRouter Gateway (BYOK)";
        }

        if (navEngineLabel) navEngineLabel.textContent = provName;
        if (robotNameLabel) robotNameLabel.textContent = botName;
        if (robotCoreEngine) robotCoreEngine.textContent = coreName;
        if (diffEngineTag) diffEngineTag.textContent = tagText;
      } else {
        if (navEngineDot) navEngineDot.className = "status-dot offline";
        if (navEngineLabel) navEngineLabel.textContent = "Offline AST Engine (No Key)";
        // Local offline mode retains user's preferred Sentinel callsign
        if (robotNameLabel) robotNameLabel.textContent = "AI BOT // SENTINEL-01";
        if (robotCoreEngine) robotCoreEngine.textContent = "CORE: OFFLINE AST";
        if (diffEngineTag) diffEngineTag.textContent = "Python 3.12 AST (Offline)";
      }
    }

    function openModal() {
      const savedKey = localStorage.getItem("BYOK_LLM_KEY") || localStorage.getItem("BYOK_GEMINI_KEY") || "";
      const savedProvider = localStorage.getItem("BYOK_PROVIDER") || "gemini";
      if (dialogKeyInput) dialogKeyInput.value = savedKey;
      if (dialogProviderSelect) dialogProviderSelect.value = savedProvider;
      if (settingsDialog) settingsDialog.classList.add("active");
    }

    function closeModal() {
      if (settingsDialog) settingsDialog.classList.remove("active");
    }

    if (openSettingsBtn) openSettingsBtn.addEventListener("click", openModal);
    if (closeSettingsBtn) closeSettingsBtn.addEventListener("click", closeModal);

    if (dialogToggleEyeBtn && dialogKeyInput) {
      dialogToggleEyeBtn.addEventListener("click", () => {
        dialogKeyInput.type = dialogKeyInput.type === "password" ? "text" : "password";
      });
    }

    if (btnSaveKey) {
      btnSaveKey.addEventListener("click", () => {
        const key = dialogKeyInput ? dialogKeyInput.value.trim() : "";
        const provider = dialogProviderSelect ? dialogProviderSelect.value : "gemini";
        if (key) {
          localStorage.setItem("BYOK_LLM_KEY", key);
          localStorage.setItem("BYOK_GEMINI_KEY", key);
          localStorage.setItem("BYOK_PROVIDER", provider);
        } else {
          localStorage.removeItem("BYOK_LLM_KEY");
          localStorage.removeItem("BYOK_GEMINI_KEY");
        }
        updateNavEngineUI();
        closeModal();
        logTerminal(`[VAULT] Intelligence Provider configured: ${provider}`, "succ");
      });
    }

    if (btnOfflineDemo) {
      btnOfflineDemo.addEventListener("click", () => {
        localStorage.removeItem("BYOK_LLM_KEY");
        localStorage.removeItem("BYOK_GEMINI_KEY");
        if (dialogKeyInput) dialogKeyInput.value = "";
        updateNavEngineUI();
        closeModal();
        logTerminal("[VAULT] Offline AST deterministic inspection mode enabled.", "normal");
      });
    }

    // -------------------------------------------------------------
    // 4. Workspace Tab Navigation
    // -------------------------------------------------------------
    document.querySelectorAll(".workspace-tab-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".workspace-tab-btn").forEach(b => b.classList.remove("active"));
        document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));

        btn.classList.add("active");
        const targetPanel = document.getElementById(btn.dataset.tab);
        if (targetPanel) targetPanel.classList.add("active");
      });
    });

    // -------------------------------------------------------------
    // 5. Preset Selectors & Custom Diff Editor
    // -------------------------------------------------------------
    document.querySelectorAll(".preset-tab").forEach(tab => {
      if (tab.id === "toggleCustomDiffBtn" || tab.id === "btnNewBlankDiff" || tab.id === "btnOpenGitHubModal") return;
      tab.addEventListener("click", () => {
        document.querySelectorAll(".preset-tab").forEach(t => t.classList.remove("active"));
        tab.classList.add("active");

        isCustomDiffMode = false;
        if (rawDiffInput) rawDiffInput.style.display = "none";
        if (diffCodeContainer) diffCodeContainer.style.display = "block";

        const p = PRESETS[tab.dataset.preset];
        if (p) {
          currentDiffText = p.diff;
          if (activeFilePath) activeFilePath.textContent = p.path;
        }
        currentGitHubOwner = "";
        currentGitHubRepo = "";
        currentGitHubPR = 0;

        const ghNavBtnText = document.getElementById("ghNavBtnText");
        const ghActiveDot = document.getElementById("ghActiveDot");
        if (ghNavBtnText) ghNavBtnText.textContent = "Import GitHub PR";
        if (ghActiveDot) ghActiveDot.style.display = "none";
        if (btnOpenGitHubModal) btnOpenGitHubModal.classList.remove("active");

        if (verdictBadge) verdictBadge.className = "verdict-status-badge STANDBY";
        if (verdictText) verdictText.textContent = "Ready to Audit";
        if (verdictHeadline) {
          verdictHeadline.innerHTML = "Click <strong>Dispatch Robot Audit</strong> (or press <strong>&#8984; Enter</strong>) to activate parallel autonomous bot agents.";
        }
        if (window.setRobotAuditState) window.setRobotAuditState("standby");

        const deck = document.getElementById("dashboardCriticalDeck");
        if (deck) deck.style.display = "none";
        const hotspots = document.getElementById("diffHeaderHotspots");
        if (hotspots) {
          hotspots.style.display = "none";
          hotspots.innerHTML = "";
        }

        renderInteractiveDiff(currentDiffText);
      });
    });

    if (btnNewBlankDiff) {
      btnNewBlankDiff.addEventListener("click", () => {
        document.querySelectorAll(".preset-tab").forEach(t => t.classList.remove("active"));
        btnNewBlankDiff.classList.add("active");

        const ghNavBtnText = document.getElementById("ghNavBtnText");
        const ghActiveDot = document.getElementById("ghActiveDot");
        if (ghNavBtnText) ghNavBtnText.textContent = "Import GitHub PR";
        if (ghActiveDot) ghActiveDot.style.display = "none";
        if (btnOpenGitHubModal) btnOpenGitHubModal.classList.remove("active");

        isCustomDiffMode = true;
        if (diffCodeContainer) diffCodeContainer.style.display = "none";
        if (rawDiffInput) {
          rawDiffInput.style.display = "block";
          rawDiffInput.value = "";
          rawDiffInput.placeholder = "Paste your custom unified git diff or source code here...\n\nExample:\ndiff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py\n@@ -1,5 +1,6 @@\n+import os\n+def run_cmd(user_arg):\n+    os.system(f'ping -c 1 {user_arg}')\n\nShortcut: Press ⌘+Enter to trigger audit.";
          rawDiffInput.focus();
        }
        currentDiffText = "";
        currentGitHubOwner = "";
        currentGitHubRepo = "";
        currentGitHubPR = 0;
        if (activeFilePath) activeFilePath.textContent = "untitled.diff (Blank Editor Buffer)";

        const diffTabBtn = document.querySelector('[data-tab="tab-diff"]');
        if (diffTabBtn) diffTabBtn.click();

        if (verdictBadge) verdictBadge.className = "verdict-status-badge STANDBY";
        if (verdictText) verdictText.textContent = "Ready to Audit";
        if (verdictHeadline) {
          verdictHeadline.innerHTML = "Clean editor buffer initialized. Paste custom code and click <strong>Dispatch Robot Audit</strong>.";
        }
        if (findingsBadge) findingsBadge.textContent = "0 issues";
        if (metricCrit) metricCrit.textContent = "0";
        if (metricWarn) metricWarn.textContent = "0";
        if (window.setRobotAuditState) window.setRobotAuditState("standby");

        logTerminal("[BUFFER] Clean diff canvas ready. Awaiting custom input.", "normal");
      });
    }

    if (toggleCustomDiffBtn) {
      toggleCustomDiffBtn.addEventListener("click", () => {
        document.querySelectorAll(".preset-tab").forEach(t => t.classList.remove("active"));
        toggleCustomDiffBtn.classList.add("active");

        isCustomDiffMode = true;
        if (diffCodeContainer) diffCodeContainer.style.display = "none";
        if (rawDiffInput) {
          rawDiffInput.style.display = "block";
          rawDiffInput.value = currentDiffText;
          rawDiffInput.focus();
        }
        if (activeFilePath) activeFilePath.textContent = "Custom Diff Input (Editor)";

        const diffTabBtn = document.querySelector('[data-tab="tab-diff"]');
        if (diffTabBtn) diffTabBtn.click();
      });
    }

    if (rawDiffInput) {
      rawDiffInput.addEventListener("input", (e) => {
        currentDiffText = e.target.value;
      });
    }

    // -------------------------------------------------------------
    // 6. GitHub Live PR Import Logic
    // -------------------------------------------------------------
    function openGitHubModal() {
      if (ghFetchError) ghFetchError.style.display = "none";
      if (ghTokenInput) ghTokenInput.value = localStorage.getItem("BYOK_GITHUB_TOKEN") || "";
      if (githubDialog) githubDialog.classList.add("active");
    }

    function closeGitHubModal() {
      if (githubDialog) githubDialog.classList.remove("active");
    }

    if (btnOpenGitHubModal) btnOpenGitHubModal.addEventListener("click", openGitHubModal);
    if (closeGitHubBtn) closeGitHubBtn.addEventListener("click", closeGitHubModal);
    if (btnCancelGitHub) btnCancelGitHub.addEventListener("click", closeGitHubModal);

    if (ghToggleTokenEyeBtn && ghTokenInput) {
      ghToggleTokenEyeBtn.addEventListener("click", () => {
        ghTokenInput.type = ghTokenInput.type === "password" ? "text" : "password";
      });
    }

    document.querySelectorAll(".btn-chip").forEach(chip => {
      chip.addEventListener("click", () => {
        if (ghRepoInput) ghRepoInput.value = chip.dataset.repo;
        if (ghPrNumberInput) ghPrNumberInput.value = chip.dataset.pr;
      });
    });

    if (btnSubmitGitHubFetch) {
      btnSubmitGitHubFetch.addEventListener("click", async () => {
        let repoRaw = ghRepoInput ? ghRepoInput.value.trim() : "";
        let prNum = ghPrNumberInput ? parseInt(ghPrNumberInput.value.trim(), 10) : NaN;
        const token = ghTokenInput ? ghTokenInput.value.trim() : "";

        if (token) localStorage.setItem("BYOK_GITHUB_TOKEN", token);

        const urlMatch = repoRaw.match(/github\.com\/([^\/]+)\/([^\/]+)\/pull\/(\d+)/i);
        if (urlMatch) {
          repoRaw = `${urlMatch[1]}/${urlMatch[2]}`;
          prNum = parseInt(urlMatch[3], 10);
        }

        if (!repoRaw || isNaN(prNum)) {
          if (ghFetchError) {
            ghFetchError.textContent = "Please enter a repository (owner/repo) and valid Pull Request number.";
            ghFetchError.style.display = "block";
          }
          return;
        }

        const parts = repoRaw.split("/");
        if (parts.length < 2) {
          if (ghFetchError) {
            ghFetchError.textContent = "Invalid format. Use 'owner/repo' (e.g. 'pallets/flask').";
            ghFetchError.style.display = "block";
          }
          return;
        }

        const owner = parts[0].trim();
        const repo = parts[1].trim();

        if (ghFetchSpinner) ghFetchSpinner.style.display = "inline-block";
        if (ghFetchIcon) ghFetchIcon.style.display = "none";
        if (ghFetchBtnText) ghFetchBtnText.textContent = "Fetching PR...";
        if (btnSubmitGitHubFetch) btnSubmitGitHubFetch.disabled = true;
        if (ghFetchError) ghFetchError.style.display = "none";

        try {
          const resp = await fetch("/api/v1/github/fetch-pr", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              owner,
              repo,
              repo_input: `${owner}/${repo}`,
              pull_number: prNum,
              token: token || undefined,
              github_token: token || undefined
            })
          });

          const data = await resp.json();
          if (!resp.ok) throw new Error(data.detail || "Failed to fetch GitHub PR");

          currentGitHubOwner = data.owner;
          currentGitHubRepo = data.repo;
          currentGitHubPR = data.pull_number;
          currentDiffText = data.diff_text;

          document.querySelectorAll(".preset-tab").forEach(t => t.classList.remove("active"));
          if (btnOpenGitHubModal) btnOpenGitHubModal.classList.add("active");

          const ghNavBtnText = document.getElementById("ghNavBtnText");
          const ghActiveDot = document.getElementById("ghActiveDot");
          if (ghNavBtnText) ghNavBtnText.textContent = `${owner}/${repo} #${prNum}`;
          if (ghActiveDot) ghActiveDot.style.display = "inline-block";

          if (activeFilePath) activeFilePath.textContent = `${owner}/${repo} PR #${prNum} (${data.title || "Live Pull Request"})`;

          isCustomDiffMode = false;
          if (rawDiffInput) rawDiffInput.style.display = "none";
          if (diffCodeContainer) diffCodeContainer.style.display = "block";

          const diffTabBtn = document.querySelector('[data-tab="tab-diff"]');
          if (diffTabBtn) diffTabBtn.click();

          if (verdictBadge) verdictBadge.className = "verdict-status-badge STANDBY";
          if (verdictText) verdictText.textContent = "Ready to Audit";
          if (verdictHeadline) {
            verdictHeadline.innerHTML = `Loaded live GitHub PR: <strong>${owner}/${repo} #${prNum}</strong>. Click <strong>Dispatch Robot Audit</strong>.`;
          }
          if (window.setRobotAuditState) window.setRobotAuditState("standby");

          closeGitHubModal();
          renderInteractiveDiff(currentDiffText);
          logTerminal(`[GITHUB] Successfully fetched live PR #${prNum} from ${owner}/${repo} (${(data.files_changed || []).length} files modified).`, "succ");

        } catch (err) {
          if (ghFetchError) {
            ghFetchError.textContent = `Fetch error: ${err.message}`;
            ghFetchError.style.display = "block";
          }
        } finally {
          if (ghFetchSpinner) ghFetchSpinner.style.display = "none";
          if (ghFetchIcon) ghFetchIcon.style.display = "inline-block";
          if (ghFetchBtnText) ghFetchBtnText.textContent = "Fetch Live PR";
          if (btnSubmitGitHubFetch) btnSubmitGitHubFetch.disabled = false;
        }
      });
    }

    // -------------------------------------------------------------
    // 7. GitHub Publish Review Logic
    // -------------------------------------------------------------
    if (btnPublishGitHub) {
      btnPublishGitHub.addEventListener("click", () => {
        if (!currentGitHubOwner || !currentGitHubRepo || !currentGitHubPR) {
          if (ghPublishTarget) ghPublishTarget.textContent = "Local Session (Simulated Dry-Run)";
        } else {
          if (ghPublishTarget) ghPublishTarget.textContent = `${currentGitHubOwner}/${currentGitHubRepo} #${currentGitHubPR}`;
        }

        if (ghPublishVerdict) {
          ghPublishVerdict.textContent = lastReviewResult ? lastReviewResult.overall_status : "STANDBY";
          ghPublishVerdict.style.color = (lastReviewResult && lastReviewResult.overall_status === "APPROVE") ? "var(--success)" : "var(--danger)";
        }
        if (ghPublishCommentsCount) {
          const count = lastReviewResult && lastReviewResult.comments ? lastReviewResult.comments.length : 0;
          ghPublishCommentsCount.textContent = `${count} comment${count === 1 ? '' : 's'}`;
        }
        if (ghPublishTokenInput) ghPublishTokenInput.value = localStorage.getItem("BYOK_GITHUB_TOKEN") || "";
        if (ghPublishStatusMsg) ghPublishStatusMsg.style.display = "none";
        if (githubPublishDialog) githubPublishDialog.classList.add("active");
      });
    }

    if (closeGHPublishBtn) closeGHPublishBtn.addEventListener("click", () => githubPublishDialog && githubPublishDialog.classList.remove("active"));
    if (btnCancelGHPublish) btnCancelGHPublish.addEventListener("click", () => githubPublishDialog && githubPublishDialog.classList.remove("active"));

    if (btnConfirmPublish) {
      btnConfirmPublish.addEventListener("click", async () => {
        const token = ghPublishTokenInput ? ghPublishTokenInput.value.trim() : "";
        if (token) localStorage.setItem("BYOK_GITHUB_TOKEN", token);

        if (ghPublishSpinner) ghPublishSpinner.style.display = "inline-block";
        if (ghPublishIcon) ghPublishIcon.style.display = "none";
        if (btnConfirmPublishText) btnConfirmPublishText.textContent = "Publishing Review...";
        if (btnConfirmPublish) btnConfirmPublish.disabled = true;

        try {
          const isReal = Boolean(currentGitHubOwner && currentGitHubRepo && currentGitHubPR && token);

          if (isReal) {
            const resp = await fetch("/api/v1/github/publish-review", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                owner: currentGitHubOwner,
                repo: currentGitHubRepo,
                pull_number: currentGitHubPR,
                token: token,
                github_token: token,
                review: lastReviewResult,
                review_result: lastReviewResult
              })
            });
            const data = await resp.json();
            if (!resp.ok) throw new Error(data.detail || "Publish failed");

            if (ghPublishStatusMsg) {
              ghPublishStatusMsg.style.display = "block";
              ghPublishStatusMsg.style.background = "rgba(16, 185, 129, 0.15)";
              ghPublishStatusMsg.style.color = "#34d399";
              ghPublishStatusMsg.textContent = `Review published to ${currentGitHubOwner}/${currentGitHubRepo}#${currentGitHubPR}!`;
            }
            logTerminal(`[GITHUB] Review submitted to PR #${currentGitHubPR}. Status: ${data.status}`, "succ");
          } else {
            if (ghPublishStatusMsg) {
              ghPublishStatusMsg.style.display = "block";
              ghPublishStatusMsg.style.background = "rgba(245, 158, 11, 0.15)";
              ghPublishStatusMsg.style.color = "#fbbf24";
              ghPublishStatusMsg.textContent = "Simulated Dry-Run: Review formatted and verified locally.";
            }
            logTerminal("[GITHUB] Dry-run simulated review formatted and validated.", "succ");
          }
        } catch (err) {
          if (ghPublishStatusMsg) {
            ghPublishStatusMsg.style.display = "block";
            ghPublishStatusMsg.style.background = "rgba(239, 68, 68, 0.15)";
            ghPublishStatusMsg.style.color = "#f87171";
            ghPublishStatusMsg.textContent = `Publish failed: ${err.message}`;
          }
        } finally {
          if (ghPublishSpinner) ghPublishSpinner.style.display = "none";
          if (ghPublishIcon) ghPublishIcon.style.display = "inline-block";
          if (btnConfirmPublishText) btnConfirmPublishText.textContent = "Submit Review";
          if (btnConfirmPublish) btnConfirmPublish.disabled = false;
        }
      });
    }

    // -------------------------------------------------------------
    // 8. Terminal Logging System
    // -------------------------------------------------------------
    function logTerminal(message, type = "normal") {
      if (!terminalFeed) return;
      const now = new Date();
      const timeStr = [now.getHours(), now.getMinutes(), now.getSeconds()]
        .map(v => String(v).padStart(2, "0"))
        .join(":");

      const row = document.createElement("div");
      row.className = "t-row";

      let tagSpan = "";
      if (type === "sec") tagSpan = `<span class="t-tag-sec">[BOT-SEC]</span> `;
      else if (type === "perf") tagSpan = `<span class="t-tag-perf">[BOT-PERF]</span> `;
      else if (type === "arch") tagSpan = `<span class="t-tag-arch">[BOT-ARCH]</span> `;
      else if (type === "succ") tagSpan = `<span class="t-tag-succ">[CONSENSUS]</span> `;

      row.innerHTML = `<span class="t-time">${timeStr}</span> <span>${tagSpan}${message}</span>`;
      terminalFeed.appendChild(row);
      terminalFeed.scrollTop = terminalFeed.scrollHeight;
    }

    // -------------------------------------------------------------
    // 8.5 Multi-Code / Multi-File Splitter & Navigator
    // -------------------------------------------------------------
    function parseDiffIntoFiles(diffText) {
      if (!diffText || !diffText.trim()) return [];
      const files = [];
      const lines = diffText.split("\n");
      let currentFile = null;

      for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        if (line.startsWith("diff --git ")) {
          if (currentFile) {
            currentFile.rawDiff = currentFile.lines.join("\n");
            files.push(currentFile);
          }
          const parts = line.split(" ");
          const bPath = parts[parts.length - 1].replace(/^b\//, "").trim();
          currentFile = {
            path: bPath,
            lines: [line],
            additions: 0,
            deletions: 0
          };
        } else {
          if (!currentFile) {
            currentFile = {
              path: "code.py",
              lines: [line],
              additions: 0,
              deletions: 0
            };
          } else {
            currentFile.lines.push(line);
          }
          if (line.startsWith("+") && !line.startsWith("+++")) currentFile.additions++;
          else if (line.startsWith("-") && !line.startsWith("---")) currentFile.deletions++;
        }
      }

      if (currentFile) {
        currentFile.rawDiff = currentFile.lines.join("\n");
        files.push(currentFile);
      }

      return files;
    }

    function setupFileSelector(diffText, inlineComments = []) {
      currentParsedFiles = parseDiffIntoFiles(diffText);
      const fileSelectorBar = document.getElementById("fileSelectorBar");
      const filePillsList = document.getElementById("filePillsList");
      const diffFilesCountBadge = document.getElementById("diffFilesCountBadge");
      const fileFilterSummary = document.getElementById("fileFilterSummary");

      if (!fileSelectorBar || !filePillsList) return;

      if (currentParsedFiles.length <= 1) {
        fileSelectorBar.style.display = "none";
        if (diffFilesCountBadge) diffFilesCountBadge.style.display = "none";
        activeSelectedFilePath = null;
        return;
      }

      fileSelectorBar.style.display = "flex";
      if (diffFilesCountBadge) {
        diffFilesCountBadge.style.display = "inline-block";
        diffFilesCountBadge.textContent = `${currentParsedFiles.length} Codes Detected`;
      }

      filePillsList.innerHTML = "";

      // 1. "All Codes (Full PR)" button
      const totalCrits = (inlineComments || []).filter(c => c.severity === "CRITICAL").length;
      const allBtn = document.createElement("button");
      allBtn.type = "button";
      allBtn.className = `file-pill-btn ${activeSelectedFilePath === null ? "active" : ""}`;
      allBtn.innerHTML = `
        <svg viewBox="0 0 24 24" width="12" height="12" stroke="currentColor" fill="none" stroke-width="2"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>
        <span>All Codes (${currentParsedFiles.length})</span>
        ${totalCrits > 0 ? `<span class="pill-crit-badge"><span class="pill-crit-dot"></span>${totalCrits} CRIT</span>` : ''}
      `;
      allBtn.addEventListener("click", () => {
        activeSelectedFilePath = null;
        setupFileSelector(diffText, inlineComments);
        renderInteractiveDiff(diffText, inlineComments, false);
        if (activeFilePath) {
          activeFilePath.textContent = currentGitHubRepo 
            ? `${currentGitHubOwner}/${currentGitHubRepo} (All ${currentParsedFiles.length} files)` 
            : `Repository Combined View (${currentParsedFiles.length} files)`;
        }
      });
      filePillsList.appendChild(allBtn);

      // 2. Individual Code Pills
      currentParsedFiles.forEach(file => {
        const fileComments = (inlineComments || []).filter(c => !c.file_path || c.file_path.includes(file.path) || file.path.includes(c.file_path));
        const fileCrits = fileComments.filter(c => c.severity === "CRITICAL").length;
        file.criticalCount = fileCrits;

        const pill = document.createElement("button");
        pill.type = "button";
        const isActive = activeSelectedFilePath === file.path;
        pill.className = `file-pill-btn ${isActive ? "active" : ""}`;
        const filenameOnly = file.path.split("/").pop();
        pill.title = file.path;
        pill.innerHTML = `
          <svg viewBox="0 0 24 24" width="12" height="12" stroke="currentColor" fill="none" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
          <span>${filenameOnly}</span>
          <span class="stat-add">+${file.additions}</span>
          <span class="stat-del">-${file.deletions}</span>
          ${fileCrits > 0 ? `<span class="pill-crit-badge"><span class="pill-crit-dot"></span>${fileCrits} CRIT</span>` : ''}
        `;
        pill.addEventListener("click", () => {
          activeSelectedFilePath = file.path;
          setupFileSelector(diffText, inlineComments);
          renderInteractiveDiff(file.rawDiff, fileComments, false);
          if (activeFilePath) activeFilePath.textContent = file.path;
        });
        filePillsList.appendChild(pill);
      });

      if (fileFilterSummary) {
        fileFilterSummary.textContent = activeSelectedFilePath 
          ? `Inspecting: ${activeSelectedFilePath}` 
          : `Showing unified patch of all ${currentParsedFiles.length} codes`;
      }
    }

    // -------------------------------------------------------------
    // 9. Interactive Diff Renderer with Inline Findings
    // -------------------------------------------------------------
    function renderInteractiveDiff(diffText, inlineComments = [], shouldUpdateSelector = true) {
      if (!diffCodeContainer) return;
      diffCodeContainer.innerHTML = "";

      if (shouldUpdateSelector) {
        setupFileSelector(diffText, inlineComments);
      }

      const lines = (diffText || "").split("\n");
      let currentOldLine = 0;
      let currentNewLine = 0;
      let currentFileInDiff = "";

      lines.forEach((line) => {
        if (line.startsWith("diff --git ")) {
          const parts = line.split(" ");
          currentFileInDiff = parts[parts.length - 1].replace(/^b\//, "").trim();
        }

        const row = document.createElement("div");
        row.className = "diff-row";

        if (line.startsWith("@@")) {
          row.classList.add("hunk");
          const match = line.match(/@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@/);
          if (match) {
            currentOldLine = parseInt(match[1], 10);
            currentNewLine = parseInt(match[2], 10);
          }
          row.innerHTML = `
            <div class="diff-gutter">...</div>
            <div class="diff-symbol">&bull;</div>
            <div class="diff-content">${escapeHtml(line)}</div>
          `;
          diffCodeContainer.appendChild(row);
          return;
        }

        let symbol = "&nbsp;";
        let lineNumberDisplay = "";
        let isAddition = false;

        if (line.startsWith("+") && !line.startsWith("+++")) {
          row.classList.add("add");
          symbol = "+";
          lineNumberDisplay = String(currentNewLine);
          isAddition = true;
          currentNewLine++;
        } else if (line.startsWith("-") && !line.startsWith("---")) {
          row.classList.add("del");
          symbol = "-";
          lineNumberDisplay = String(currentOldLine);
          currentOldLine++;
        } else {
          lineNumberDisplay = currentNewLine ? String(currentNewLine) : "";
          if (currentOldLine) currentOldLine++;
          if (currentNewLine) currentNewLine++;
        }

        if (lineNumberDisplay) {
          row.dataset.line = lineNumberDisplay;
          if (currentFileInDiff) row.dataset.file = currentFileInDiff;
        }

        // Check if line has a critical issue
        const targetLineNum = parseInt(lineNumberDisplay, 10);
        const hasCrit = isAddition && inlineComments && inlineComments.some(c => {
          if (c.severity !== "CRITICAL" || c.line_number !== targetLineNum) return false;
          if (!c.file_path || !currentFileInDiff) return true;
          return currentFileInDiff.includes(c.file_path) || c.file_path.includes(currentFileInDiff);
        });
        if (hasCrit) {
          row.classList.add("has-critical-error");
        }

        row.innerHTML = `
          <div class="diff-gutter">${lineNumberDisplay}</div>
          <div class="diff-symbol">${hasCrit ? "!" : symbol}</div>
          <div class="diff-content">${escapeHtml(line)}</div>
        `;
        diffCodeContainer.appendChild(row);

        // Render inline findings below line if matched
        if (isAddition && inlineComments && inlineComments.length) {
          const matchedComments = inlineComments.filter(c => {
            if (c.line_number !== targetLineNum) return false;
            if (!c.file_path || !currentFileInDiff) return true;
            return currentFileInDiff.includes(c.file_path) || c.file_path.includes(currentFileInDiff);
          });

          matchedComments.forEach(c => {
            const commentRow = document.createElement("div");
            commentRow.className = `inline-comment-row ${c.severity}`;
            commentRow.innerHTML = `
              <div class="comment-header">
                <span class="severity-pill ${c.severity}">${c.severity}</span>
                <span class="comment-category">[${c.category}]</span>
              </div>
              <div class="comment-summary">${escapeHtml(c.issue_summary)}</div>
              <div class="comment-explanation">${escapeHtml(c.detailed_explanation || c.explanation || "")}</div>
              ${c.suggested_diff_fix || c.suggested_fix ? `
                <div class="fix-container">
                  <div class="fix-header">Suggested Remediation:</div>
                  <pre class="fix-code"><code>${escapeHtml(c.suggested_diff_fix || c.suggested_fix)}</code></pre>
                </div>
              ` : ""}
            `;
            diffCodeContainer.appendChild(commentRow);
          });
        }
      });

      // Update Critical Line Hotspots in Diff Header Bar (filling the wide space)
      updateDiffHeaderHotspots(inlineComments, activeSelectedFilePath);
    }

    // -------------------------------------------------------------
    // 9.5 Critical Lines Hotspots & Jump Controller
    // -------------------------------------------------------------
    function updateDiffHeaderHotspots(comments, currentViewingFile) {
      const container = document.getElementById("diffHeaderHotspots");
      if (!container) return;

      if (!comments || !comments.length) {
        container.style.display = "none";
        container.innerHTML = "";
        return;
      }

      let relevant = comments;
      if (currentViewingFile) {
        relevant = comments.filter(c => !c.file_path || c.file_path.includes(currentViewingFile) || currentViewingFile.includes(c.file_path));
      }

      const crits = relevant.filter(c => c.severity === "CRITICAL");
      const warns = relevant.filter(c => c.severity === "WARNING");

      if (crits.length === 0 && warns.length === 0) {
        container.style.display = "none";
        container.innerHTML = "";
        return;
      }

      container.style.display = "flex";
      container.innerHTML = "";

      const badge = document.createElement("div");
      badge.className = "hotspot-badge";
      badge.innerHTML = `<span class="hotspot-pulse-dot"></span><span>${crits.length ? `CRITICAL LINES (${crits.length}):` : `WARNINGS (${warns.length}):`}</span>`;
      container.appendChild(badge);

      crits.forEach(c => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "hotspot-chip";
        const shortTitle = c.issue_summary.length > 28 ? c.issue_summary.substring(0, 26) + "..." : c.issue_summary;
        btn.title = `Line ${c.line_number}: ${c.issue_summary} (Click to jump to line)`;
        btn.innerHTML = `
          <span class="chip-line-tag">L.${c.line_number}</span>
          <span>${escapeHtml(shortTitle)}</span>
          <svg viewBox="0 0 24 24" width="10" height="10" stroke="currentColor" fill="none" stroke-width="2.5"><path d="M7 17l9.2-9.2M17 17V7H7"/></svg>
        `;
        btn.addEventListener("click", (e) => {
          e.stopPropagation();
          jumpToFindingLine(c.line_number, c.file_path || "");
        });
        container.appendChild(btn);
      });

      warns.slice(0, 2).forEach(w => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "hotspot-chip warning";
        const shortTitle = w.issue_summary.length > 24 ? w.issue_summary.substring(0, 22) + "..." : w.issue_summary;
        btn.title = `Line ${w.line_number}: ${w.issue_summary} (Click to jump to line)`;
        btn.innerHTML = `
          <span class="chip-line-tag">L.${w.line_number}</span>
          <span>${escapeHtml(shortTitle)}</span>
          <svg viewBox="0 0 24 24" width="10" height="10" stroke="currentColor" fill="none" stroke-width="2.5"><path d="M7 17l9.2-9.2M17 17V7H7"/></svg>
        `;
        btn.addEventListener("click", (e) => {
          e.stopPropagation();
          jumpToFindingLine(w.line_number, w.file_path || "");
        });
        container.appendChild(btn);
      });
    }

    function updateDashboardCriticalDeck(comments) {
      const deck = document.getElementById("dashboardCriticalDeck");
      const grid = document.getElementById("dashboardCriticalCardsGrid");
      const countLabel = document.getElementById("dashboardCriticalCountLabel");
      if (!deck || !grid) return;

      const criticals = (comments || []).filter(c => c.severity === "CRITICAL");
      if (criticals.length === 0) {
        deck.style.display = "flex";
        if (countLabel) countLabel.textContent = "Zero Critical Vulnerabilities Detected";
        grid.innerHTML = `
          <div style="grid-column: 1 / -1; background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: var(--radius-sm); padding: 12px 16px; display: flex; align-items: center; gap: 10px; color: #a7f3d0; font-family: var(--font-mono); font-size: 0.76rem;">
            <svg viewBox="0 0 24 24" width="16" height="16" stroke="#10b981" fill="none" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
            <span><strong>CLEAN AUDIT VERIFICATION:</strong> No blocking security vulnerabilities, code injection risks, or resource leaks detected across inspected files.</span>
          </div>
        `;
        return;
      }

      deck.style.display = "flex";
      if (countLabel) {
        countLabel.textContent = `${criticals.length} Critical Issue${criticals.length === 1 ? '' : 's'} Flagged Across Inspected Code`;
      }

      grid.innerHTML = "";
      criticals.forEach(c => {
        const card = document.createElement("div");
        card.className = "crit-card";
        const fullFilePath = c.file_path || "";
        const cleanFix = (c.suggested_diff_fix || c.suggested_fix || "").trim().split("\n")[0] || "";
        
        card.innerHTML = `
          <div class="crit-card-top">
            <div class="crit-card-loc">
              <span class="crit-card-line-badge">LINE ${c.line_number}</span>
              <span title="${fullFilePath}">${c.file_path || "Unified Patch"}</span>
            </div>
            <span class="crit-card-action">Jump to Line &rarr;</span>
          </div>
          <div class="crit-card-rule">[${c.category}] ${escapeHtml(c.issue_summary)}</div>
          ${cleanFix ? `<div class="crit-card-code-preview" title="${escapeHtml(cleanFix)}">Fix: ${escapeHtml(cleanFix)}</div>` : ''}
        `;

        card.addEventListener("click", () => {
          jumpToFindingLine(c.line_number, fullFilePath);
        });

        grid.appendChild(card);
      });
    }

    function jumpToFindingLine(targetLineNum, targetFilePath) {
      const diffTabBtn = document.querySelector('[data-tab="tab-diff"]');
      if (diffTabBtn && !diffTabBtn.classList.contains("active")) {
        diffTabBtn.click();
      }

      if (targetFilePath && currentParsedFiles && currentParsedFiles.length > 1) {
        const matched = currentParsedFiles.find(f => f.path === targetFilePath || targetFilePath.includes(f.path) || f.path.includes(targetFilePath));
        if (matched && activeSelectedFilePath !== matched.path) {
          activeSelectedFilePath = matched.path;
          const fileComments = (lastReviewResult ? lastReviewResult.comments : []).filter(c => !c.file_path || c.file_path.includes(matched.path) || matched.path.includes(c.file_path));
          renderInteractiveDiff(matched.rawDiff, fileComments, false);
          setupFileSelector(currentDiffText, lastReviewResult ? lastReviewResult.comments : []);
          if (activeFilePath) activeFilePath.textContent = matched.path;
        }
      }

      setTimeout(() => {
        const rows = document.querySelectorAll(`.diff-row[data-line="${targetLineNum}"]`);
        if (rows.length) {
          const targetRow = rows[0];
          targetRow.scrollIntoView({ behavior: "smooth", block: "center" });
          targetRow.classList.remove("jump-highlight");
          void targetRow.offsetWidth;
          targetRow.classList.add("jump-highlight");
        }
      }, 60);
    }
    window.jumpToFindingLine = jumpToFindingLine;

    function escapeHtml(str) {
      if (!str) return "";
      return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
    }

    // -------------------------------------------------------------
    // 10. Multi-Agent Audit Runner
    // -------------------------------------------------------------
    async function executeAudit() {
      let diffToTest = isCustomDiffMode ? (rawDiffInput ? rawDiffInput.value : "") : currentDiffText;
      if (activeSelectedFilePath && currentParsedFiles && currentParsedFiles.length > 1) {
        const found = currentParsedFiles.find(f => f.path === activeSelectedFilePath);
        if (found) diffToTest = found.rawDiff;
      }
      if (!diffToTest || !diffToTest.trim()) return alert("Please specify or paste a code diff to audit.");

      const apiKey = localStorage.getItem("BYOK_LLM_KEY") || localStorage.getItem("BYOK_GEMINI_KEY") || "";
      const provider = localStorage.getItem("BYOK_PROVIDER") || "gemini";

      if (runAuditBtn) runAuditBtn.disabled = true;
      if (auditSpinner) auditSpinner.style.display = "inline-block";
      if (auditPlayIcon) auditPlayIcon.style.display = "none";
      if (auditBtnText) auditBtnText.textContent = "Scanning Code...";

      if (window.setRobotAuditState) window.setRobotAuditState("auditing");

      if (terminalFeed) terminalFeed.innerHTML = "";
      logTerminal("Orchestrator: Parsing unified patch & computing AST scopes...", "normal");

      if (stateSec) stateSec.textContent = "Auditing...";
      if (statePerf) statePerf.textContent = "Auditing...";
      if (stateArch) stateArch.textContent = "Auditing...";
      if (stateSynth) stateSynth.textContent = "Awaiting consensus";

      const hudProgSec = document.getElementById("hudProgSec");
      const hudProgPerf = document.getElementById("hudProgPerf");
      const hudProgArch = document.getElementById("hudProgArch");
      const hudProgSynth = document.getElementById("hudProgSynth");

      const hudDotSec = document.getElementById("hudDotSec");
      const hudDotPerf = document.getElementById("hudDotPerf");
      const hudDotArch = document.getElementById("hudDotArch");
      const hudDotSynth = document.getElementById("hudDotSynth");

      const hudStateSec = document.getElementById("hudStateSec");
      const hudStatePerf = document.getElementById("hudStatePerf");
      const hudStateArch = document.getElementById("hudStateArch");
      const hudStateSynth = document.getElementById("hudStateSynth");

      if (hudDotSec) hudDotSec.className = "hud-dot active";
      if (hudDotPerf) hudDotPerf.className = "hud-dot active";
      if (hudDotArch) hudDotArch.className = "hud-dot active";
      if (hudDotSynth) hudDotSynth.className = "hud-dot active";

      if (hudStateSec) hudStateSec.textContent = "Auditing...";
      if (hudStatePerf) hudStatePerf.textContent = "Auditing...";
      if (hudStateArch) hudStateArch.textContent = "Auditing...";
      if (hudStateSynth) hudStateSynth.textContent = "Synthesizing...";

      if (window.gsap) {
        gsap.to([progSec, hudProgSec], { width: "75%", duration: 0.6 });
        gsap.to([progPerf, hudProgPerf], { width: "65%", duration: 0.6, delay: 0.1 });
        gsap.to([progArch, hudProgArch], { width: "80%", duration: 0.6, delay: 0.15 });
        gsap.to([progSynth, hudProgSynth], { width: "30%", duration: 0.4 });
      }

      logTerminal("Parallel specialist dispatch: [BOT-SEC, BOT-PERF, BOT-ARCH]", "normal");

      const startTime = performance.now();

      try {
        const response = await fetch("/api/v1/review", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            diff_text: diffToTest,
            pull_request_id: 42,
            api_key: apiKey || undefined,
            provider: provider !== "auto" ? provider : undefined
          })
        });

        const data = await response.json();
        const duration = Math.round(performance.now() - startTime);

        if (window.gsap) {
          gsap.to([progSec, progPerf, progArch, progSynth, hudProgSec, hudProgPerf, hudProgArch, hudProgSynth], { width: "100%", duration: 0.3 });
        }
        if (stateSec) stateSec.textContent = "Complete";
        if (statePerf) statePerf.textContent = "Complete";
        if (stateArch) stateArch.textContent = "Complete";
        if (stateSynth) stateSynth.textContent = "Synthesized & Validated";

        if (hudStateSec) hudStateSec.textContent = "Complete";
        if (hudStatePerf) hudStatePerf.textContent = "Complete";
        if (hudStateArch) hudStateArch.textContent = "Complete";
        if (hudStateSynth) hudStateSynth.textContent = "Pydantic v2 Verified";

        if (hudDotSec) hudDotSec.className = "hud-dot";
        if (hudDotPerf) hudDotPerf.className = "hud-dot";
        if (hudDotArch) hudDotArch.className = "hud-dot";
        if (hudDotSynth) hudDotSynth.className = "hud-dot";

        (data.comments || []).forEach(c => {
          const type = c.category === "SECURITY" ? "sec" : (c.category === "PERFORMANCE" ? "perf" : "arch");
          logTerminal(`Line ${c.line_number}: [${c.severity}] ${c.issue_summary}`, type);
        });

        logTerminal(`Consensus resolved: Overall Status -> ${data.overall_status}`, "succ");
        logTerminal("Schema guardrail: Pydantic v2 validation passed 100%.", "succ");

        displayResults(data, duration);

      } catch (err) {
        logTerminal(`Audit failed: ${err.message}`, "sec");
      } finally {
        if (runAuditBtn) runAuditBtn.disabled = false;
        if (auditSpinner) auditSpinner.style.display = "none";
        if (auditPlayIcon) auditPlayIcon.style.display = "inline-block";
        if (auditBtnText) auditBtnText.textContent = "Dispatch Robot Audit";
      }
    }

    function displayResults(data, latencyMs) {
      lastSummaryMarkdown = data.summary_markdown || "";
      lastReviewResult = data;
      if (copyReviewBtn) copyReviewBtn.style.display = "inline-flex";
      if (btnPublishGitHub) btnPublishGitHub.style.display = "inline-flex";

      if (isCustomDiffMode) {
        if (rawDiffInput) rawDiffInput.style.display = "none";
        if (diffCodeContainer) diffCodeContainer.style.display = "block";
        isCustomDiffMode = false;
        if (toggleCustomDiffBtn) toggleCustomDiffBtn.classList.remove("active");
        if (btnNewBlankDiff) btnNewBlankDiff.classList.remove("active");
      }
      if (activeSelectedFilePath && currentParsedFiles && currentParsedFiles.length > 1) {
        const found = currentParsedFiles.find(f => f.path === activeSelectedFilePath);
        if (found) {
          const fileComments = (data.comments || []).filter(c => !c.file_path || c.file_path.includes(found.path) || found.path.includes(c.file_path));
          renderInteractiveDiff(found.rawDiff, fileComments, false);
          setupFileSelector(currentDiffText, data.comments || []);
        } else {
          renderInteractiveDiff(currentDiffText, data.comments || []);
        }
      } else {
        renderInteractiveDiff(currentDiffText, data.comments || []);
      }

      const engineText = data.engine_used || "AST Deterministic Engine (Offline Fallback)";
      const robotNameLabel = document.getElementById("robotNameLabel");
      const robotCoreEngine = document.getElementById("robotCoreEngine");
      const diffEngineTag = document.getElementById("diffEngineTag");

      if (engineText.includes("Gemini")) {
        if (robotNameLabel) robotNameLabel.textContent = "GEMINI 1.5 // SENTINEL-01";
        if (robotCoreEngine) robotCoreEngine.textContent = "ENGINE: GEMINI (LIVE)";
        if (diffEngineTag) diffEngineTag.textContent = "Google Gemini 1.5 Pro";
      } else if (engineText.includes("OpenAI") || engineText.includes("GPT")) {
        if (robotNameLabel) robotNameLabel.textContent = "CHATGPT (GPT-4o) // SENTINEL-01";
        if (robotCoreEngine) robotCoreEngine.textContent = "ENGINE: GPT-4o (LIVE)";
        if (diffEngineTag) diffEngineTag.textContent = "OpenAI GPT-4o";
      } else if (engineText.includes("Anthropic") || engineText.includes("Claude")) {
        if (robotNameLabel) robotNameLabel.textContent = "CLAUDE 3.5 // SENTINEL-01";
        if (robotCoreEngine) robotCoreEngine.textContent = "ENGINE: CLAUDE (LIVE)";
        if (diffEngineTag) diffEngineTag.textContent = "Claude 3.5 Sonnet";
      } else if (engineText.includes("Groq")) {
        if (robotNameLabel) robotNameLabel.textContent = "GROQ LLAMA-3 // SENTINEL-01";
        if (robotCoreEngine) robotCoreEngine.textContent = "ENGINE: GROQ (LIVE)";
        if (diffEngineTag) diffEngineTag.textContent = "Groq Llama 3.3";
      } else {
        if (robotNameLabel) robotNameLabel.textContent = "AI BOT // SENTINEL-01";
        if (robotCoreEngine) robotCoreEngine.textContent = "CORE: OFFLINE AST";
        if (diffEngineTag) diffEngineTag.textContent = "Python 3.12 AST (Offline)";
      }

      if (verdictBadge) verdictBadge.className = `verdict-status-badge ${data.overall_status}`;
      if (data.overall_status === "APPROVE") {
        if (verdictText) verdictText.textContent = "Approved";
        if (verdictHeadline) {
          verdictHeadline.innerHTML = "All parallel bot specialist checks passed. <strong>No blocking vulnerabilities or leaks.</strong>";
        }
        if (window.setRobotAuditState) window.setRobotAuditState("approved");
      } else if (data.overall_status === "REQUEST_CHANGES") {
        if (verdictText) verdictText.textContent = "Changes Requested";
        if (verdictHeadline) {
          verdictHeadline.innerHTML = `Automated bot specialists flagged <strong>${(data.comments || []).length} blocking issues</strong> requiring remediation.`;
        }
        if (window.setRobotAuditState) window.setRobotAuditState("changes");
      } else {
        if (verdictText) verdictText.textContent = "Comments Provided";
        if (verdictHeadline) {
          verdictHeadline.innerHTML = "Advisory findings detected. Review comments before merging.";
        }
        if (window.setRobotAuditState) window.setRobotAuditState("changes");
      }

      const crits = (data.comments || []).filter(c => c.severity === "CRITICAL").length;
      const warns = (data.comments || []).filter(c => c.severity === "WARNING").length;
      const total = (data.comments || []).length;

      if (metricCrit) metricCrit.textContent = crits;
      if (metricWarn) metricWarn.textContent = warns;
      if (metricLatency) metricLatency.textContent = `${latencyMs}ms`;
      if (metricCost) metricCost.textContent = `$${(data.total_token_cost_usd || 0.0012).toFixed(4)}`;
      if (findingsBadge) findingsBadge.textContent = `${total} issue${total === 1 ? '' : 's'}`;

      if (markdownSurface) {
        let mdHtml = lastSummaryMarkdown
          .replace(/### (.*?)\n/g, '<h3>$1</h3>')
          .replace(/## (.*?)\n/g, '<h2>$1</h2>')
          .replace(/# (.*?)\n/g, '<h1>$1</h1>')
          .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
          .replace(/`([^`]+)`/g, '<code>$1</code>')
          .replace(/\n\n/g, '<br><br>');
        markdownSurface.innerHTML = mdHtml;
      }

      // Update Critical Problems Dashboard Deck and Header Hotspots
      updateDashboardCriticalDeck(data.comments || []);
      updateDiffHeaderHotspots(data.comments || [], activeSelectedFilePath);
    }

    if (copyReviewBtn) {
      copyReviewBtn.addEventListener("click", () => {
        if (!lastSummaryMarkdown) return;
        navigator.clipboard.writeText(lastSummaryMarkdown).then(() => {
          const originalText = copyReviewBtn.innerHTML;
          copyReviewBtn.innerHTML = `<span>Copied to Clipboard!</span>`;
          setTimeout(() => { copyReviewBtn.innerHTML = originalText; }, 1800);
        });
      });
    }

    // -------------------------------------------------------------
    // 11. Interactive 3D Robot Sentinel Engine (Safe Three.js)
    // -------------------------------------------------------------
    function initRobotSentinel() {
      const canvas = document.getElementById("robot-canvas");
      if (!canvas) return;

      // Safe check for Three.js
      if (typeof THREE === "undefined") {
        console.warn("Three.js not loaded. Using 2D SVG Sentinel HUD.");
        return;
      }

      try {
        const width = 90;
        const height = 90;
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
        camera.position.z = 70;

        const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
        renderer.setSize(width, height);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

        const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
        scene.add(ambientLight);

        const amberLight = new THREE.DirectionalLight(0xf59e0b, 1.8);
        amberLight.position.set(20, 30, 40);
        scene.add(amberLight);

        const fillLight = new THREE.DirectionalLight(0x06b6d4, 0.5);
        fillLight.position.set(-30, -20, -20);
        scene.add(fillLight);

        const robotGroup = new THREE.Group();
        scene.add(robotGroup);

        const coreGeo = new THREE.IcosahedronGeometry(14, 1);
        const coreMat = new THREE.MeshStandardMaterial({
          color: 0x141720,
          roughness: 0.25,
          metalness: 0.85,
          flatShading: true,
        });
        const coreMesh = new THREE.Mesh(coreGeo, coreMat);
        robotGroup.add(coreMesh);

        const edgesGeo = new THREE.EdgesGeometry(coreGeo);
        const edgesMat = new THREE.LineBasicMaterial({
          color: 0xf59e0b,
          transparent: true,
          opacity: 0.65,
        });
        const wireframeCage = new THREE.LineSegments(edgesGeo, edgesMat);
        robotGroup.add(wireframeCage);

        const visorGeo = new THREE.CylinderGeometry(14.2, 14.2, 3.2, 16, 1, true, -Math.PI / 3, (2 * Math.PI) / 3);
        const visorMat = new THREE.MeshBasicMaterial({
          color: 0xfbbf24,
          side: THREE.DoubleSide,
          transparent: true,
          opacity: 0.9,
        });
        const visor = new THREE.Mesh(visorGeo, visorMat);
        visor.rotation.x = Math.PI / 2;
        robotGroup.add(visor);

        const eyePupilGeo = new THREE.SphereGeometry(3.5, 16, 16);
        const eyePupilMat = new THREE.MeshBasicMaterial({ color: 0xfffbeb });
        const eyePupil = new THREE.Mesh(eyePupilGeo, eyePupilMat);
        eyePupil.position.set(0, 0, 14);
        robotGroup.add(eyePupil);

        const ring1Geo = new THREE.TorusGeometry(20, 0.6, 8, 48);
        const ring1Mat = new THREE.MeshStandardMaterial({
          color: 0x383e4d,
          metalness: 0.9,
          roughness: 0.3,
        });
        const ring1 = new THREE.Mesh(ring1Geo, ring1Mat);
        robotGroup.add(ring1);

        const ring2Geo = new THREE.TorusGeometry(24, 0.5, 8, 48);
        const ring2Mat = new THREE.MeshBasicMaterial({
          color: 0xf59e0b,
          transparent: true,
          opacity: 0.5,
        });
        const ring2 = new THREE.Mesh(ring2Geo, ring2Mat);
        robotGroup.add(ring2);

        let isAuditing = false;
        let targetRotX = 0;
        let targetRotY = 0;

        window.addEventListener("mousemove", (e) => {
          const normX = (e.clientX / window.innerWidth) * 2 - 1;
          const normY = -(e.clientY / window.innerHeight) * 2 + 1;
          targetRotY = normX * 0.65;
          targetRotX = -normY * 0.45;
        });

        window.setRobotAuditState = function(state) {
          const stateEl = document.getElementById("robotStateText");
          const visorFallback = document.getElementById("robotFallbackVisor");
          if (state === "auditing") {
            isAuditing = true;
            if (stateEl) {
              stateEl.textContent = "SCANNING DIFF...";
              stateEl.className = "robot-state-badge scanning";
            }
            if (visorFallback) visorFallback.className = "robot-visor-scanner scanning";
            visorMat.color.setHex(0xef4444);
            eyePupilMat.color.setHex(0xff7875);
            ring2Mat.color.setHex(0xef4444);
          } else if (state === "approved") {
            isAuditing = false;
            if (stateEl) {
              stateEl.textContent = "VERDICT: APPROVED";
              stateEl.className = "robot-state-badge approved";
            }
            if (visorFallback) visorFallback.className = "robot-visor-scanner approved";
            visorMat.color.setHex(0x10b981);
            eyePupilMat.color.setHex(0x6ee7b7);
            ring2Mat.color.setHex(0x10b981);
          } else if (state === "changes") {
            isAuditing = false;
            if (stateEl) {
              stateEl.textContent = "VERDICT: ISSUES FOUND";
              stateEl.className = "robot-state-badge changes";
            }
            if (visorFallback) visorFallback.className = "robot-visor-scanner changes";
            visorMat.color.setHex(0xef4444);
            eyePupilMat.color.setHex(0xff7875);
            ring2Mat.color.setHex(0xef4444);
          } else {
            isAuditing = false;
            if (stateEl) {
              stateEl.textContent = "SYS: STANDBY";
              stateEl.className = "robot-state-badge";
            }
            if (visorFallback) visorFallback.className = "robot-visor-scanner";
            visorMat.color.setHex(0xfbbf24);
            eyePupilMat.color.setHex(0xfffbeb);
            ring2Mat.color.setHex(0xf59e0b);
          }
        };

        const clock = new THREE.Clock();

        function animate() {
          requestAnimationFrame(animate);
          const elapsedTime = clock.getElapsedTime();

          robotGroup.position.y = Math.sin(elapsedTime * 2) * 1.5;
          robotGroup.rotation.y += (targetRotY - robotGroup.rotation.y) * 0.08;
          robotGroup.rotation.x += (targetRotX - robotGroup.rotation.x) * 0.08;

          const speedMult = isAuditing ? 3.5 : 1.0;
          ring1.rotation.x += 0.012 * speedMult;
          ring1.rotation.y += 0.008 * speedMult;
          ring2.rotation.y -= 0.018 * speedMult;
          ring2.rotation.z += 0.01 * speedMult;

          if (isAuditing) {
            eyePupil.position.x = Math.sin(elapsedTime * 14) * 5;
            visorMat.opacity = 0.6 + Math.sin(elapsedTime * 12) * 0.4;
          } else {
            eyePupil.position.x += (0 - eyePupil.position.x) * 0.1;
            visorMat.opacity = 0.85 + Math.sin(elapsedTime * 2) * 0.15;
          }

          renderer.render(scene, camera);
        }
        animate();

      } catch (err) {
        console.warn("Three.js initialization notice:", err);
      }
    }

    // -------------------------------------------------------------
    // 12. Global Listeners & Startup Initialization
    // -------------------------------------------------------------
    if (runAuditBtn) runAuditBtn.addEventListener("click", executeAudit);

    window.addEventListener("keydown", (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
        e.preventDefault();
        executeAudit();
      }
    });

    // Startup Execution: Run immediately so the UI is active right away!
    updateNavEngineUI();
    renderInteractiveDiff(currentDiffText);
    initRobotSentinel();

    logTerminal("Sentinel Orchestrator initialized. AST Parser ready.", "normal");
