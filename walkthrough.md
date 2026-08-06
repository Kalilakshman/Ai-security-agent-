# Assessment Profiles & Long-Running Timeout Improvements — AI Security Orchestrator CLI (`security-ai`)

The **AI Security Orchestrator CLI** (`security-ai`) has been upgraded with configurable assessment profiles (`fast`, `standard`, `deep`), tool-specific timeout resolution, partial results preservation upon process termination, and live UI terminal timeout displays.

---

## ⏱️ Timeout & Assessment Profile Enhancements

### 1. Default Timeout Values & Assessment Profiles
Supported assessment profiles:
- **Fast (`-p fast`)**: Accelerated scans for quick discovery.
- **Standard (`-p standard`)**: Balanced depth and execution time (Default).
- **Deep (`-p deep`)**: Comprehensive long-running security assessments with extended timeouts.

| Tool Plugin | Fast Profile | Standard Profile | Deep Profile |
| :--- | :--- | :--- | :--- |
| **`nmap`** | 120s (2m) | 600s (10m) | 1800s (30m) |
| **`whatweb`** | 60s (1m) | 300s (5m) | 900s (15m) |
| **`nikto`** | 180s (3m) | 900s (15m) | 2400s (40m) |
| **`gobuster`** | 180s (3m) | 1200s (20m) | 3600s (60m) |
| **`nuclei`** | 300s (5m) | 1800s (30m) | 7200s (120m) |

### 2. Configurable via `config/config.yaml`
Timeouts can be customized per tool and profile in `config/config.yaml`:
```yaml
timeouts:
  nmap:
    fast: 120
    standard: 600
    deep: 1800
  whatweb:
    fast: 60
    standard: 300
    deep: 900
  nikto:
    fast: 180
    standard: 900
    deep: 2400
  gobuster:
    fast: 180
    standard: 1200
    deep: 3600
  nuclei:
    fast: 300
    standard: 1800
    deep: 7200
```

### 3. Graceful Timeout Termination & Partial Findings Preservation
When a tool plugin exceeds its profile timeout limit:
- **Isolated Process Termination**: Only the timed-out plugin process is killed (`process.kill()`).
- **Structured Timeout Logging**: Logs warning with exact timeout duration.
- **Partial Results Preserved**: Whatever `stdout` and `stderr` streams were captured prior to termination are passed to `plugin.parse()`, preserving partial findings.
- **Workflow Continuation**: The workflow continues executing remaining tools in the queue without interrupting the assessment.

### 4. Terminal UI Live Timeout Display
During scan execution, the active timeout and profile are displayed in the status spinner:
```text
Running step 1/2: nmap (Timeout: 1800s | Profile: DEEP)...
```

---

## 💻 Usage Commands

### Run Scan with Deep Assessment Profile
```bash
security-ai scan example.com --profile deep
```

### Formulate Plan with Fast Assessment Profile
```bash
security-ai plan example.com --profile fast --execute
```
