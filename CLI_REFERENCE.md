# CLI Command Reference — AI Security Orchestrator CLI (`security-ai`)

Complete command-line interface reference for `security-ai`.

---

## 📌 Table of Contents
1. [Core Operations Commands](#1-core-operations-commands)
2. [LLM Neural Hub Management (`security-ai llm`)](#2-llm-neural-hub-management-security-ai-llm)
3. [Security Tool Adapter Management (`security-ai tools`)](#3-security-tool-adapter-management-security-ai-tools)
4. [Reporting & History Commands](#4-reporting--history-commands)
5. [System Diagnostics & Configuration](#5-system-diagnostics--configuration)
6. [Assessment Profiles & Timeouts](#6-assessment-profiles--timeouts)
7. [DevSecOps Makefile Commands](#7-devsecops-makefile-commands)

---

## 1. Core Operations Commands

### 🚀 `security-ai scan`
Run an automated, resilient security assessment workflow against an authorized target.

```bash
# Standard assessment scan
security-ai scan scanme.nmap.org

# Deep assessment scan with 4 parallel threads and 1 retry attempt
security-ai scan scanme.nmap.org --profile deep --concurrency 4 --retries 1 -y

# Resume an interrupted assessment scan from latest checkpoint
security-ai scan scanme.nmap.org --resume latest -y
```

| Option | Flag | Type | Description |
| :--- | :--- | :--- | :--- |
| **Profile** | `-p, --profile` | Text | `fast`, `standard`, `deep`, or `custom` (Default: `standard`) |
| **Concurrency** | `-c, --concurrency` | Int | Maximum worker threads for DAG execution (Default: `3`) |
| **Retries** | `-r, --retries` | Int | Retry attempts for transient step failures (Default: `0`) |
| **Resume** | `--resume` | Text | Assessment ID or `latest` to resume from checkpoint |
| **Auto-Approve** | `-y, --yes` | Flag | Automatically confirm target authorization |

---

### 🧠 `security-ai plan`
Formulate an AI strategic security assessment plan without executing tool commands.

```bash
# View AI assessment plan for a web application
security-ai plan http://example.com --profile deep

# Formulate plan and prompt for authorization to execute immediately
security-ai plan 192.168.1.1 --profile fast --execute
```

| Option | Flag | Type | Description |
| :--- | :--- | :--- | :--- |
| **Profile** | `-p, --profile` | Text | `fast`, `standard`, `deep`, or `custom` (Default: `standard`) |
| **Execute Now** | `-e, --execute` | Flag | Prompt for authorization and execute workflow immediately |

---

### 🖥️ `security-ai dashboard`
Render the live interactive cybersecurity operations terminal dashboard.

```bash
security-ai dashboard --target scanme.nmap.org --profile deep
```

---

## 2. LLM Neural Hub Management (`security-ai llm`)

Manage provider-independent LLM backends (OpenRouter, OpenAI-compatible APIs, Ollama local models).

```bash
# 1. List registered LLM providers and operational health
security-ai llm providers

# 2. List available models for active provider
security-ai llm models

# 3. Test LLM provider connectivity and measure latency
security-ai llm test

# 4. Switch active LLM provider and default model
security-ai llm select --provider openai --model gpt-4o
security-ai llm select --provider openrouter --model nvidia/nemotron-3-ultra-550b-a55b:free
security-ai llm select --provider ollama --model llama3
```

---

## 3. Security Tool Adapter Management (`security-ai tools`)

Manage security tool adapters (Nmap, OWASP ZAP, Burp Suite, Wireshark/tshark, Metasploit RPC).

```bash
# 1. Matrix of registered tools, installation status, and version
security-ai tools list

# 2. Detailed capability discovery and supported parameters schema
security-ai tools info nmap
security-ai tools info owasp_zap

# 3. Real-time operational health checks across all tool adapters
security-ai tools health
```

---

## 4. Reporting & History Commands

### 📄 `security-ai report`
Analyze normalized scan JSON results and generate Markdown, HTML (with SVG charts), and PDF reports.

```bash
# Generate Markdown, HTML, and PDF reports in reports_output/ directory
security-ai report scan_scanme.nmap.org.json --md --html --pdf -o reports_output/
```

---

### 📜 `security-ai history`
View historical scan records, targets, execution durations, and findings count from the SQLite database.

```bash
security-ai history --limit 10
```

---

## 5. System Diagnostics & Configuration

```bash
# Run environment, binary dependency, and API diagnostics
security-ai doctor

# Display registered dynamic security plugins
security-ai plugins

# Display active configuration settings and per-tool profile timeouts
security-ai config
```

---

## 6. Assessment Profiles & Timeouts

| Tool Plugin | Fast Profile (`-p fast`) | Standard Profile (`-p standard`) | Deep Profile (`-p deep`) |
| :--- | :--- | :--- | :--- |
| **`nmap`** | 120s (2m) | 600s (10m) | 1800s (30m) |
| **`whatweb`** | 60s (1m) | 300s (5m) | 900s (15m) |
| **`nikto`** | 180s (3m) | 900s (15m) | 2400s (40m) |
| **`gobuster`** | 180s (3m) | 1200s (20m) | 3600s (60m) |
| **`nuclei`** | 300s (5m) | 1800s (30m) | 7200s (120m) |

---

## 7. DevSecOps Makefile Commands

```bash
make install    # Install dependencies
make test       # Run pytest test suite
make lint       # Run ruff and mypy linters
make format     # Format code using ruff
make clean      # Clean python build artifacts
make docker-build # Build multi-stage Docker container image
```
