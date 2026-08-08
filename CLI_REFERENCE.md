# CLI Command Reference — AI Security Orchestrator CLI (`security-ai`)

Complete command-line interface reference for `security-ai`.

---

## 🚀 Core Commands

### `security-ai scan TARGET [OPTIONS]`
Run automated resilient security scanning workflow against an authorized target.

**Options**:
- `-p, --profile [fast|standard|deep|custom]`: Assessment profile depth (Default: `standard`).
- `-c, --concurrency INTEGER`: Worker threads for parallel DAG execution (Default: `3`).
- `-r, --retries INTEGER`: Retry attempts for transient step failures (Default: `0`).
- `--resume TEXT`: Assessment ID or `latest` to resume from saved checkpoint.
- `-y, --yes`: Automatically confirm target authorization.

---

### `security-ai plan TARGET [OPTIONS]`
Formulate an AI-driven security assessment plan.

**Options**:
- `-p, --profile [fast|standard|deep|custom]`: Assessment profile depth (Default: `standard`).
- `-e, --execute`: Confirm authorization and execute plan immediately.

---

### `security-ai dashboard [OPTIONS]`
Render interactive terminal operations dashboard.

**Options**:
- `-t, --target TEXT`: Target scope to display (Default: `127.0.0.1`).
- `-p, --profile TEXT`: Assessment profile (Default: `deep`).

---

### `security-ai llm [SUBCOMMAND]`
Manage provider-independent LLM subsystem.

**Subcommands**:
- `providers`: List supported LLM providers and operational health states.
- `models`: List available models for active/specified provider (`--provider`).
- `test`: Run completion latency test and health check.
- `select`: Interactively or via flags (`--provider`, `--model`) switch active backend.

---

### `security-ai tools [SUBCOMMAND]`
Manage security tool adapters.

**Subcommands**:
- `list`: Display matrix of registered tools, installation status, and version.
- `info TOOL_NAME`: Display detailed capabilities and configuration options.
- `health`: Run real-time health checks across all tool adapters.

---

### `security-ai report FILE_PATH [OPTIONS]`
Generate multi-format reports from scan JSON data.

**Options**:
- `--md / --no-md`: Generate Markdown report (.md) (Default: `True`).
- `--html / --no-html`: Generate HTML report (.html) (Default: `False`).
- `--pdf / --no-pdf`: Generate PDF report (.pdf) (Default: `False`).
- `-o, --out-dir TEXT`: Output directory path (Default: `reports_output`).

---

### `security-ai doctor`
Run system environment, binary dependency, and API diagnostics.

---

### `security-ai plugins`
List dynamic security plugins.

---

### `security-ai config`
Display active configuration settings and timeout profiles.

---

### `security-ai history [OPTIONS]`
Display historical scan records from database.

**Options**:
- `-n, --limit INTEGER`: Maximum records to display (Default: `10`).
