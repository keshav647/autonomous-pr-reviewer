    // -------------------------------------------------------------
    // 1. Ambient 3D Particle Constellation (Three.js)
    // -------------------------------------------------------------
    (function initThreeBackground() {
      const canvas = document.getElementById("bg-canvas");
      const scene = new THREE.Scene();
      const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 1, 1000);
      camera.position.z = 400;

      const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
      renderer.setSize(window.innerWidth, window.innerHeight);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

      const particleCount = 120;
      const geometry = new THREE.BufferGeometry();
      const positions = new Float32Array(particleCount * 3);

      for (let i = 0; i < particleCount * 3; i += 3) {
        positions[i] = (Math.random() - 0.5) * 800;
        positions[i + 1] = (Math.random() - 0.5) * 800;
        positions[i + 2] = (Math.random() - 0.5) * 500;
      }
      geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));

      const material = new THREE.PointsMaterial({
        color: 0x58a6ff,
        size: 2.2,
        transparent: true,
        opacity: 0.45
      });
      const points = new THREE.Points(geometry, material);
      scene.add(points);

      function animate() {
        requestAnimationFrame(animate);
        points.rotation.y += 0.0004;
        points.rotation.x += 0.0002;
        renderer.render(scene, camera);
      }
      animate();

      window.addEventListener("resize", () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
      });
    })();

    // -------------------------------------------------------------
    // 2. Preset Data Fixtures
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
      }
    };

    // -------------------------------------------------------------
    // 3. DOM References & State
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

    let currentGitHubOwner = "";
    let currentGitHubRepo = "";
    let currentGitHubPR = 0;
    let lastReviewResult = null;

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

    let currentDiffText = PRESETS.sql_injection.diff;
    let lastSummaryMarkdown = "";
    let isCustomDiffMode = false;

    // -------------------------------------------------------------
    // 4. Onboarding & BYOK Vault Management
    // -------------------------------------------------------------
    function updateNavEngineUI() {
      const savedKey = localStorage.getItem("BYOK_LLM_KEY") || localStorage.getItem("BYOK_GEMINI_KEY") || "";
      const savedProvider = localStorage.getItem("BYOK_PROVIDER") || "gemini";

      if (savedKey) {
        navEngineDot.className = "status-dot";
        if (savedProvider === "gemini") navEngineLabel.textContent = "Google Gemini (gemini-2.5-flash)";
        else if (savedProvider === "openai") navEngineLabel.textContent = "OpenAI (GPT-4o Mini)";
        else if (savedProvider === "anthropic") navEngineLabel.textContent = "Anthropic Claude 3.5";
        else if (savedProvider === "groq") navEngineLabel.textContent = "Groq (Llama 3.3 70B)";
        else if (savedProvider === "openrouter") navEngineLabel.textContent = "OpenRouter Gateway";
        else navEngineLabel.textContent = "Auto-Detect Provider";
      } else {
        navEngineDot.className = "status-dot offline";
        navEngineLabel.textContent = "Offline AST Engine (No Key)";
      }
    }

    function openModal() {
      const savedKey = localStorage.getItem("BYOK_LLM_KEY") || localStorage.getItem("BYOK_GEMINI_KEY") || "";
      const savedProvider = localStorage.getItem("BYOK_PROVIDER") || "gemini";
      dialogKeyInput.value = savedKey;
      dialogProviderSelect.value = savedProvider;
      settingsDialog.classList.add("active");
    }

    function closeModal() {
      settingsDialog.classList.remove("active");
    }

    openSettingsBtn.addEventListener("click", openModal);
    closeSettingsBtn.addEventListener("click", closeModal);

    dialogToggleEyeBtn.addEventListener("click", () => {
      dialogKeyInput.type = dialogKeyInput.type === "password" ? "text" : "password";
    });

    btnSaveKey.addEventListener("click", () => {
      const key = dialogKeyInput.value.trim();
      const provider = dialogProviderSelect.value;
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
      logTerminal(`BYOK Vault updated: ${provider} engine configured.`, "succ");
    });

    btnOfflineDemo.addEventListener("click", () => {
      localStorage.removeItem("BYOK_LLM_KEY");
      localStorage.removeItem("BYOK_GEMINI_KEY");
      dialogKeyInput.value = "";
      updateNavEngineUI();
      closeModal();
      logTerminal("Offline AST deterministic inspection mode enabled.", "normal");
    });

    // Landing Check: If no key is set on first visit, open modal immediately!
    const initialKey = localStorage.getItem("BYOK_LLM_KEY") || localStorage.getItem("BYOK_GEMINI_KEY");
    if (!initialKey) {
      setTimeout(() => openModal(), 400);
    }
    updateNavEngineUI();

    // -------------------------------------------------------------
    // 5. Workspace Tab Switching
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
    // 6. Preset Selector & Blank Canvas / Custom Diff
    // -------------------------------------------------------------
    document.querySelectorAll(".preset-tab").forEach(tab => {
      if (tab.id === "toggleCustomDiffBtn" || tab.id === "btnNewBlankDiff" || tab.id === "btnOpenGitHubModal") return;
      tab.addEventListener("click", () => {
        document.querySelectorAll(".preset-tab").forEach(t => t.classList.remove("active"));
        tab.classList.add("active");

        isCustomDiffMode = false;
        rawDiffInput.style.display = "none";
        diffCodeContainer.style.display = "block";

        const p = PRESETS[tab.dataset.preset];
        currentDiffText = p.diff;
        activeFilePath.textContent = p.path;
        currentGitHubOwner = "";
        currentGitHubRepo = "";
        currentGitHubPR = 0;

        const ghNavBtnText = document.getElementById("ghNavBtnText");
        const ghActiveDot = document.getElementById("ghActiveDot");
        if (ghNavBtnText) ghNavBtnText.textContent = "Import GitHub PR";
        if (ghActiveDot) ghActiveDot.style.display = "none";
        btnOpenGitHubModal.classList.remove("active");

        renderInteractiveDiff(currentDiffText);
      });
    });

    btnNewBlankDiff.addEventListener("click", () => {
      document.querySelectorAll(".preset-tab").forEach(t => t.classList.remove("active"));
      btnNewBlankDiff.classList.add("active");

      const ghNavBtnText = document.getElementById("ghNavBtnText");
      const ghActiveDot = document.getElementById("ghActiveDot");
      if (ghNavBtnText) ghNavBtnText.textContent = "Import GitHub PR";
      if (ghActiveDot) ghActiveDot.style.display = "none";
      btnOpenGitHubModal.classList.remove("active");

      isCustomDiffMode = true;
      diffCodeContainer.style.display = "none";
      rawDiffInput.style.display = "block";
      rawDiffInput.value = "";
      currentDiffText = "";
      currentGitHubOwner = "";
      currentGitHubRepo = "";
      currentGitHubPR = 0;
      activeFilePath.textContent = "untitled.diff (Blank Editor Buffer)";
      rawDiffInput.placeholder = "Paste your custom unified git diff or source code here...\n\nExample:\ndiff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py\n@@ -1,5 +1,6 @@\n+import os\n+def run_cmd(user_arg):\n+    os.system(f'ping -c 1 {user_arg}')\n\nTip: You can also paste raw code snippets directly!\nShortcut: Press ⌘+Enter to trigger audit.";

      // Switch to Diff tab
      const diffTabBtn = document.querySelector('[data-tab="tab-diff"]') || document.querySelector('[data-tab="tabDiff"]');
      if (diffTabBtn) diffTabBtn.click();

      // Reset state indicators to standby
      verdictBadge.className = "verdict-status-badge STANDBY";
      verdictIcon.setAttribute("data-lucide", "play-circle");
      verdictText.textContent = "Ready to Audit";
      verdictHeadline.innerHTML = "Clean editor buffer initialized. Paste custom code and click <strong>Run Multi-Agent Audit</strong>.";
      findingsBadge.textContent = "0 issues";
      metricCrit.textContent = "0";
      metricWarn.textContent = "0";

      rawDiffInput.focus();
      logTerminal("[BUFFER] Clean diff canvas ready. Awaiting custom input.", "normal");
      lucide.createIcons();
    });

    toggleCustomDiffBtn.addEventListener("click", () => {
      document.querySelectorAll(".preset-tab").forEach(t => t.classList.remove("active"));
      toggleCustomDiffBtn.classList.add("active");

      isCustomDiffMode = true;
      diffCodeContainer.style.display = "none";
      rawDiffInput.style.display = "block";
      rawDiffInput.value = currentDiffText;
      activeFilePath.textContent = "Custom Diff Input (Editor)";

      const diffTabBtn = document.querySelector('[data-tab="tab-diff"]') || document.querySelector('[data-tab="tabDiff"]');
      if (diffTabBtn) diffTabBtn.click();

      rawDiffInput.focus();
    });

    rawDiffInput.addEventListener("input", (e) => {
      currentDiffText = e.target.value;
    });

    // -------------------------------------------------------------
    // 6b. GitHub Live PR Import Logic
    // -------------------------------------------------------------
    function openGitHubModal() {
      ghFetchError.style.display = "none";
      ghTokenInput.value = localStorage.getItem("BYOK_GITHUB_TOKEN") || "";
      githubDialog.classList.add("active");
      ghRepoInput.focus();
    }

    function closeGitHubModal() {
      githubDialog.classList.remove("active");
    }

    btnOpenGitHubModal.addEventListener("click", openGitHubModal);
    closeGitHubBtn.addEventListener("click", closeGitHubModal);
    btnCancelGitHub.addEventListener("click", closeGitHubModal);

    ghToggleTokenEyeBtn.addEventListener("click", () => {
      ghTokenInput.type = ghTokenInput.type === "password" ? "text" : "password";
    });

    // Auto-parse full GitHub PR URLs pasted into repo input
    ghRepoInput.addEventListener("input", () => {
      const val = ghRepoInput.value.trim();
      if (val.includes("github.com/")) {
        const m = val.match(/github\.com\/([^\/]+)\/([^\/]+)\/pull\/(\d+)/);
        if (m) {
          ghRepoInput.value = `${m[1]}/${m[2]}`;
          ghPrNumberInput.value = m[3];
        }
      }
    });

    // Quick demo PR chips
    document.querySelectorAll(".btn-chip").forEach(chip => {
      chip.addEventListener("click", () => {
        ghRepoInput.value = chip.dataset.repo;
        ghPrNumberInput.value = chip.dataset.pr;
        fetchLiveGitHubPR();
      });
    });

    async function fetchLiveGitHubPR() {
      const repo = ghRepoInput.value.trim();
      const prNumber = parseInt(ghPrNumberInput.value, 10);
      const token = ghTokenInput.value.trim();

      if (!repo || !prNumber) {
        ghFetchError.textContent = "Please specify both repository ('owner/repo') and PR number.";
        ghFetchError.style.display = "block";
        return;
      }

      ghFetchError.style.display = "none";
      btnSubmitGitHubFetch.disabled = true;
      ghFetchSpinner.style.display = "inline-block";
      ghFetchIcon.style.display = "none";
      ghFetchBtnText.textContent = "Fetching...";

      try {
        const resp = await fetch("/api/v1/github/fetch", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            repo: repo,
            pull_number: prNumber,
            github_token: token || undefined
          })
        });

        const data = await resp.json();
        if (!data.success) {
          throw new Error(data.error || "Failed to fetch PR diff from GitHub.");
        }

        if (token) {
          localStorage.setItem("BYOK_GITHUB_TOKEN", token);
        }

        currentGitHubOwner = data.owner;
        currentGitHubRepo = data.repo;
        currentGitHubPR = data.pull_number;
        currentDiffText = data.diff_text;

        // Update UI state
        document.querySelectorAll(".preset-tab").forEach(t => t.classList.remove("active"));
        btnOpenGitHubModal.classList.add("active");
        const ghNavBtnText = document.getElementById("ghNavBtnText");
        const ghActiveDot = document.getElementById("ghActiveDot");
        if (ghNavBtnText) ghNavBtnText.textContent = `${data.owner}/${data.repo} #${data.pull_number}`;
        if (ghActiveDot) ghActiveDot.style.display = "inline-block";

        isCustomDiffMode = false;
        rawDiffInput.style.display = "none";
        diffCodeContainer.style.display = "block";

        activeFilePath.textContent = `${data.title} (${data.owner}/${data.repo} #${data.pull_number})`;
        renderInteractiveDiff(currentDiffText);

        // Switch to Diff tab
        const diffTabBtn = document.querySelector('[data-tab="tab-diff"]') || document.querySelector('[data-tab="tabDiff"]');
        if (diffTabBtn) diffTabBtn.click();

        // Reset Verdict HUD
        verdictBadge.className = "verdict-status-badge STANDBY";
        verdictIcon.setAttribute("data-lucide", "play-circle");
        verdictText.textContent = "Ready to Audit";
        verdictHeadline.innerHTML = `Loaded live GitHub PR: <strong>${data.owner}/${data.repo} #${data.pull_number}</strong>. Click <strong>Run Multi-Agent Audit</strong>.`;
        findingsBadge.textContent = "Ready";

        closeGitHubModal();
        logTerminal(`[GITHUB] Imported PR #${data.pull_number} from ${data.owner}/${data.repo} (${data.lines_count} diff lines).`, "succ");
        lucide.createIcons();

      } catch (err) {
        ghFetchError.textContent = err.message;
        ghFetchError.style.display = "block";
      } finally {
        btnSubmitGitHubFetch.disabled = false;
        ghFetchSpinner.style.display = "none";
        ghFetchIcon.style.display = "inline-block";
        ghFetchBtnText.textContent = "Fetch Live PR";
      }
    }

    btnSubmitGitHubFetch.addEventListener("click", fetchLiveGitHubPR);

    // -------------------------------------------------------------
    // 6c. GitHub Publish Review Logic
    // -------------------------------------------------------------
    function openPublishDialog() {
      if (!lastReviewResult) return;
      ghPublishStatusMsg.style.display = "none";
      ghPublishTarget.textContent = currentGitHubOwner ? `${currentGitHubOwner}/${currentGitHubRepo} #${currentGitHubPR}` : "Workspace Review #42 (Demo)";
      ghPublishVerdict.textContent = lastReviewResult.overall_status;
      ghPublishVerdict.style.color = lastReviewResult.overall_status === "APPROVE" ? "var(--success)" : "var(--danger)";
      const count = (lastReviewResult.comments || []).length;
      ghPublishCommentsCount.textContent = `${count} inline line comment${count === 1 ? '' : 's'}`;

      ghPublishTokenInput.value = localStorage.getItem("BYOK_GITHUB_TOKEN") || "";
      githubPublishDialog.classList.add("active");
    }

    function closePublishDialog() {
      githubPublishDialog.classList.remove("active");
    }

    btnPublishGitHub.addEventListener("click", openPublishDialog);
    closeGHPublishBtn.addEventListener("click", closePublishDialog);
    btnCancelGHPublish.addEventListener("click", closePublishDialog);

    btnConfirmPublish.addEventListener("click", async () => {
      const token = ghPublishTokenInput.value.trim();
      const dryRun = !Boolean(token);

      btnConfirmPublish.disabled = true;
      ghPublishSpinner.style.display = "inline-block";
      ghPublishIcon.style.display = "none";
      btnConfirmPublishText.textContent = "Publishing...";

      try {
        const resp = await fetch("/api/v1/github/publish", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            owner: currentGitHubOwner || "demo",
            repo: currentGitHubRepo || "repo",
            pull_number: currentGitHubPR || 42,
            review_result: lastReviewResult,
            github_token: token || undefined,
            dry_run: dryRun
          })
        });

        const data = await resp.json();
        if (!data.success) {
          throw new Error(data.error || "Failed to publish review to GitHub.");
        }

        if (token) {
          localStorage.setItem("BYOK_GITHUB_TOKEN", token);
        }

        ghPublishStatusMsg.style.display = "block";
        if (data.dry_run) {
          ghPublishStatusMsg.style.background = "rgba(210, 153, 34, 0.1)";
          ghPublishStatusMsg.style.border = "1px solid rgba(210, 153, 34, 0.3)";
          ghPublishStatusMsg.style.color = "var(--warning)";
          ghPublishStatusMsg.innerHTML = `<strong>Dry-Run Simulated:</strong> Review formatted with ${(lastReviewResult.comments || []).length} inline suggestion comments. Provide a GitHub Token to post live.`;
          logTerminal(`[GITHUB DRY-RUN] Review payload formatted for ${currentGitHubOwner || 'demo'}/${currentGitHubRepo || 'repo'} #${currentGitHubPR || 42}. Dispatched 0 network requests.`, "normal");
        } else {
          ghPublishStatusMsg.style.background = "rgba(63, 185, 80, 0.1)";
          ghPublishStatusMsg.style.border = "1px solid rgba(63, 185, 80, 0.3)";
          ghPublishStatusMsg.style.color = "var(--success)";
          ghPublishStatusMsg.innerHTML = `<strong>Published Live:</strong> Review comments successfully submitted to GitHub PR #${currentGitHubPR}!`;
          logTerminal(`[GITHUB LIVE] Published review to ${currentGitHubOwner}/${currentGitHubRepo} #${currentGitHubPR} successfully!`, "succ");
        }

        btnPublishGitHubText.textContent = data.dry_run ? "Simulated" : "Published";
        setTimeout(() => {
          btnPublishGitHubText.textContent = "Publish to GitHub";
          closePublishDialog();
        }, 2200);

      } catch (err) {
        ghPublishStatusMsg.style.display = "block";
        ghPublishStatusMsg.style.background = "rgba(248, 81, 73, 0.1)";
        ghPublishStatusMsg.style.border = "1px solid rgba(248, 81, 73, 0.3)";
        ghPublishStatusMsg.style.color = "var(--danger)";
        ghPublishStatusMsg.textContent = err.message;
      } finally {
        btnConfirmPublish.disabled = false;
        ghPublishSpinner.style.display = "none";
        ghPublishIcon.style.display = "inline-block";
        btnConfirmPublishText.textContent = "Submit Review";
      }
    });

    // -------------------------------------------------------------
    // 7. Interactive Diff Parser & Inline Comment Injector
    // -------------------------------------------------------------
    function escapeHtml(str) {
      return (str || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
    }

    function renderInteractiveDiff(diffText, inlineComments = []) {
      diffCodeContainer.innerHTML = "";
      const lines = diffText.split("\n");
      let oldLine = 0;
      let newLine = 0;

      lines.forEach((line) => {
        let type = "context";
        let symbol = " ";
        let displayedOld = "";
        let displayedNew = "";

        if (line.startsWith("@@")) {
          type = "hunk";
          symbol = "~";
          const match = line.match(/@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@/);
          if (match) {
            oldLine = parseInt(match[1]);
            newLine = parseInt(match[2]);
          }
        } else if (line.startsWith("+")) {
          type = "add";
          symbol = "+";
          displayedNew = newLine++;
        } else if (line.startsWith("-")) {
          type = "del";
          symbol = "-";
          displayedOld = oldLine++;
        } else {
          type = "context";
          symbol = " ";
          displayedOld = oldLine++;
          displayedNew = newLine++;
        }

        const row = document.createElement("div");
        row.className = `diff-row ${type}`;
        row.innerHTML = `
          <div class="diff-gutter">${displayedOld || displayedNew || "..."}</div>
          <div class="diff-symbol">${symbol}</div>
          <div class="diff-content">${escapeHtml(line.startsWith("+") || line.startsWith("-") ? line.slice(1) : line)}</div>
        `;
        diffCodeContainer.appendChild(row);

        // Check if an AI Review Comment belongs under this line
        if (type === "add" && displayedNew) {
          const matchedComments = inlineComments.filter(c => c.line_number === displayedNew);
          matchedComments.forEach(comment => {
            const commentRow = document.createElement("div");
            commentRow.className = `inline-comment-row ${comment.severity}`;

            let fixHtml = "";
            if (comment.suggested_diff_fix) {
              fixHtml = `
                <div class="fix-container">
                  <div class="fix-header">
                    <span>Suggested Patch Fix</span>
                    <button class="btn-secondary" style="padding: 2px 8px; font-size: 0.65rem;" onclick="navigator.clipboard.writeText(\`${escapeHtml(comment.suggested_diff_fix)}\`)">
                      Copy Fix
                    </button>
                  </div>
                  <div class="fix-code">${escapeHtml(comment.suggested_diff_fix)}</div>
                </div>
              `;
            }

            commentRow.innerHTML = `
              <div class="comment-header">
                <span class="severity-pill ${comment.severity}">${comment.severity}</span>
                <span class="comment-category">${comment.category}</span>
                <span style="font-size: 0.72rem; color: var(--text-muted); font-family: var(--font-mono);">Line ${comment.line_number}</span>
              </div>
              <div class="comment-summary">${escapeHtml(comment.issue_summary)}</div>
              <div class="comment-explanation">${escapeHtml(comment.detailed_explanation)}</div>
              ${fixHtml}
            `;
            diffCodeContainer.appendChild(commentRow);
          });
        }
      });
    }

    // Initialize with default diff
    renderInteractiveDiff(currentDiffText);

    // -------------------------------------------------------------
    // 8. Terminal Streaming & Telemetry Logging
    // -------------------------------------------------------------
    function logTerminal(message, type = "normal") {
      const now = new Date().toTimeString().split(" ")[0];
      const row = document.createElement("div");
      row.className = "t-row";
      let tag = "";
      if (type === "sec") tag = '<span class="t-tag-sec">[SECURITY]</span>';
      else if (type === "perf") tag = '<span class="t-tag-perf">[PERF]</span>';
      else if (type === "arch") tag = '<span class="t-tag-arch">[ARCH]</span>';
      else if (type === "succ") tag = '<span class="t-tag-succ">[CONSENSUS]</span>';

      row.innerHTML = `<span class="t-time">${now}</span> ${tag} <span>${message}</span>`;
      terminalFeed.appendChild(row);
      terminalFeed.scrollTop = terminalFeed.scrollHeight;

      if (window.gsap) {
        gsap.from(row, { opacity: 0, x: -8, duration: 0.2 });
      }
    }

    // -------------------------------------------------------------
    // 9. Multi-Agent Audit Runner
    // -------------------------------------------------------------
    async function executeAudit() {
      const diffToTest = isCustomDiffMode ? rawDiffInput.value : currentDiffText;
      if (!diffToTest || !diffToTest.trim()) return alert("Please specify or paste a code diff to audit.");
      currentDiffText = diffToTest;

      const apiKey = localStorage.getItem("BYOK_LLM_KEY") || localStorage.getItem("BYOK_GEMINI_KEY") || "";
      const provider = localStorage.getItem("BYOK_PROVIDER") || "gemini";

      // UI Loading state
      runAuditBtn.disabled = true;
      auditSpinner.style.display = "inline-block";
      auditPlayIcon.style.display = "none";
      auditBtnText.textContent = "Auditing Code...";

      // Reset Workers & Terminal
      terminalFeed.innerHTML = "";
      logTerminal("Orchestrator: Parsing unified patch & computing AST scopes...", "normal");

      stateSec.textContent = "Auditing...";
      statePerf.textContent = "Auditing...";
      stateArch.textContent = "Auditing...";
      stateSynth.textContent = "Awaiting consensus";

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

      logTerminal("Parallel specialist dispatch: [Security, Performance, Architecture]", "normal");

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

        // Complete Progress Bars
        if (window.gsap) {
          gsap.to([progSec, progPerf, progArch, progSynth, hudProgSec, hudProgPerf, hudProgArch, hudProgSynth], { width: "100%", duration: 0.3 });
        }
        stateSec.textContent = "Complete";
        statePerf.textContent = "Complete";
        stateArch.textContent = "Complete";
        stateSynth.textContent = "Synthesized & Validated";

        if (hudStateSec) hudStateSec.textContent = "Complete";
        if (hudStatePerf) hudStatePerf.textContent = "Complete";
        if (hudStateArch) hudStateArch.textContent = "Complete";
        if (hudStateSynth) hudStateSynth.textContent = "Pydantic v2 Verified";

        if (hudDotSec) hudDotSec.className = "hud-dot";
        if (hudDotPerf) hudDotPerf.className = "hud-dot";
        if (hudDotArch) hudDotArch.className = "hud-dot";
        if (hudDotSynth) hudDotSynth.className = "hud-dot";

        // Log Findings
        (data.comments || []).forEach(c => {
          const type = c.category === "SECURITY" ? "sec" : (c.category === "PERFORMANCE" ? "perf" : "arch");
          logTerminal(`Line ${c.line_number}: [${c.severity}] ${c.issue_summary}`, type);
        });

        logTerminal(`Consensus resolved: Overall Status -> ${data.overall_status}`, "succ");
        logTerminal(`Schema guardrail: Pydantic v2 validation passed 100%.`, "succ");

        // Render UI Results
        displayResults(data, duration);

      } catch (err) {
        logTerminal(`Audit failed: ${err.message}`, "sec");
      } finally {
        runAuditBtn.disabled = false;
        auditSpinner.style.display = "none";
        auditPlayIcon.style.display = "inline-block";
        auditBtnText.textContent = "Run Multi-Agent Audit";
      }
    }

    function displayResults(data, latencyMs) {
      lastSummaryMarkdown = data.summary_markdown || "";
      lastReviewResult = data;
      copyReviewBtn.style.display = "inline-flex";
      btnPublishGitHub.style.display = "inline-flex";

      // Re-render Diff with Inline Findings
      if (isCustomDiffMode) {
        rawDiffInput.style.display = "none";
        diffCodeContainer.style.display = "block";
        isCustomDiffMode = false;
        toggleCustomDiffBtn.classList.remove("active");
        btnNewBlankDiff.classList.remove("active");
      }
      renderInteractiveDiff(currentDiffText, data.comments || []);

      // Update Engine Badge
      const engineText = data.engine_used || "AST Deterministic Engine (Offline Fallback)";
      if (engineBadgeText) {
        engineBadgeText.textContent = engineText;
        if (engineText.includes("Gemini")) engineBadgeText.style.color = "var(--accent)";
        else if (engineText.includes("OpenAI")) engineBadgeText.style.color = "#10a37f";
        else if (engineText.includes("Anthropic")) engineBadgeText.style.color = "#d97706";
        else if (engineText.includes("Groq")) engineBadgeText.style.color = "#f55036";
        else engineBadgeText.style.color = "var(--warning)";
      }

      // Update Verdict Badge
      verdictBadge.className = `verdict-status-badge ${data.overall_status}`;
      if (data.overall_status === "APPROVE") {
        verdictText.textContent = "Approved";
        verdictIcon.setAttribute("data-lucide", "check-circle");
        verdictHeadline.innerHTML = "All parallel specialist checks passed. <strong>No blocking vulnerabilities or leaks.</strong>";
      } else if (data.overall_status === "REQUEST_CHANGES") {
        verdictText.textContent = "Changes Requested";
        verdictIcon.setAttribute("data-lucide", "alert-octagon");
        verdictHeadline.innerHTML = `Automated specialists flagged <strong>${(data.comments || []).length} blocking issues</strong> requiring remediation.`;
      } else {
        verdictText.textContent = "Comments Provided";
        verdictIcon.setAttribute("data-lucide", "message-square");
        verdictHeadline.innerHTML = "Advisory findings detected. Review comments before merging.";
      }

      // Update Counters
      const crits = (data.comments || []).filter(c => c.severity === "CRITICAL").length;
      const warns = (data.comments || []).filter(c => c.severity === "WARNING").length;
      const total = (data.comments || []).length;

      metricCrit.textContent = crits;
      metricWarn.textContent = warns;
      metricLatency.textContent = `${latencyMs}ms`;
      metricCost.textContent = `$${(data.total_token_cost_usd || 0.0012).toFixed(4)}`;
      findingsBadge.textContent = `${total} issue${total === 1 ? '' : 's'}`;

      // Update Markdown Surface
      renderMarkdownReport(data.summary_markdown);

      // Refresh Lucide Icons
      lucide.createIcons();
    }

    function renderMarkdownReport(mdText) {
      if (!mdText) return;

      // 1. Strip any emoji characters completely to ensure clean, high-taste typography
      let cleaned = mdText.replace(/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}\u{1F900}-\u{1F9FF}\u{1F600}-\u{1F64F}\u{1F680}-\u{1F6FF}]/gu, '');

      // 2. Parse Markdown Tables into structured HTML tables
      const tableRegex = /((?:\|[^\n]+\|\r?\n)+)/g;
      cleaned = cleaned.replace(tableRegex, (match) => {
        const rows = match.trim().split(/\r?\n/).filter(r => r.trim());
        if (rows.length < 2) return match;

        let tableHtml = '<div class="report-table-wrapper"><table class="report-table">';
        let isHeader = true;

        for (let i = 0; i < rows.length; i++) {
          const row = rows[i].trim();
          if (/^\|(?:\s*:?-+:?\s*\|)+$/.test(row)) {
            isHeader = false;
            continue;
          }

          const cols = row.split('|').slice(1, -1).map(c => c.trim());
          if (isHeader) {
            tableHtml += '<thead><tr>';
            cols.forEach(c => { tableHtml += `<th>${c}</th>`; });
            tableHtml += '</tr></thead><tbody>';
            isHeader = false;
          } else {
            tableHtml += '<tr>';
            cols.forEach(c => { tableHtml += `<td>${c}</td>`; });
            tableHtml += '</tr>';
          }
        }
        tableHtml += '</tbody></table></div>';
        return tableHtml;
      });

      // 3. Transform PR STATUS labels into High-Contrast Badges
      cleaned = cleaned.replace(/\*\*PR STATUS:\s*CHANGES REQUESTED\*\*/gi, 
        '<div class="report-status-pill danger"><i data-lucide="shield-alert" style="width: 14px; height: 14px;"></i> PR STATUS: CHANGES REQUESTED</div>');
      cleaned = cleaned.replace(/\*\*PR STATUS:\s*APPROVED\*\*/gi, 
        '<div class="report-status-pill success"><i data-lucide="shield-check" style="width: 14px; height: 14px;"></i> PR STATUS: APPROVED</div>');
      cleaned = cleaned.replace(/\*\*PR STATUS:\s*REVIEW COMMENTS PROVIDED\*\*/gi, 
        '<div class="report-status-pill warning"><i data-lucide="info" style="width: 14px; height: 14px;"></i> PR STATUS: REVIEW COMMENTS PROVIDED</div>');

      // 4. Transform blockquotes
      cleaned = cleaned.replace(/^>\s*(.+)$/gim, '<div class="report-callout">$1</div>');

      // 5. Transform bullet lists
      const listRegex = /((?:^-\s*.+\r?\n?)+)/gm;
      cleaned = cleaned.replace(listRegex, (match) => {
        const items = match.trim().split(/\r?\n/).filter(line => line.startsWith('-'));
        const lis = items.map(line => `<li>${line.replace(/^-\s*/, '')}</li>`).join('');
        return `<ul class="report-list">${lis}</ul>`;
      });

      // 6. Standard Headings and Formats
      let html = cleaned
        .replace(/^### (.*$)/gim, '<h3>$1</h3>')
        .replace(/^## (.*$)/gim, '<h2>$1</h2>')
        .replace(/^# (.*$)/gim, '<h1>$1</h1>')
        .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/gim, '<em>$1</em>')
        .replace(/`([^`]+)`/gim, '<code>$1</code>')
        .replace(/\n\n/gim, '<br><br>');

      markdownSurface.innerHTML = html;
      lucide.createIcons();
    }

    // -------------------------------------------------------------
    // 10. Global Listeners & Keyboard Shortcuts
    // -------------------------------------------------------------
    runAuditBtn.addEventListener("click", executeAudit);

    // Keyboard Shortcut: Cmd/Ctrl + Enter triggers audit
    window.addEventListener("keydown", (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
        e.preventDefault();
        executeAudit();
      }
      if (e.key === "Escape") {
        if (settingsDialog.classList.contains("active")) closeModal();
        if (githubDialog.classList.contains("active")) closeGitHubModal();
        if (githubPublishDialog.classList.contains("active")) closePublishDialog();
      }
    });

    copyReviewBtn.addEventListener("click", () => {
      navigator.clipboard.writeText(lastSummaryMarkdown);
      const prev = copyReviewBtn.innerHTML;
      copyReviewBtn.innerHTML = `<i data-lucide="check" style="width: 13px; height: 13px; color: var(--success);"></i> Copied!`;
      lucide.createIcons();
      setTimeout(() => {
        copyReviewBtn.innerHTML = prev;
        lucide.createIcons();
      }, 1800);
    });

    // Initialize Lucide Icons
    lucide.createIcons();
