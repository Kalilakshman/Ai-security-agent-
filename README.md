# 🤖 AI Security Orchestrator CLI (`security-ai`)

[![DevSecOps CI/CD](https://github.com/Kalilakshman/Ai-security-agent-/actions/workflows/ci.yml/badge.svg)](https://github.com/Kalilakshman/Ai-security-agent-/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An enterprise-grade, modular, DevSecOps-ready **AI Security Orchestrator CLI** built with **Python 3.12**, **Typer**, **Rich**, **Pydantic v2**, **PyYAML**, and **SQLAlchemy 2.x**.

`security-ai` automates cybersecurity assessment workflows by pairing an **AI Strategic Planner** with an **un-bypassable Security Policy Engine**, an **extensible Security-Tool Adapter Layer** (Nmap, OWASP ZAP, Metasploit, Wireshark/tshark, Nikto, WhatWeb, Gobuster, Nuclei), and a **Model Context Protocol (MCP) Gateway**.

> [!IMPORTANT]
> **Authorization & Ethical Scope**  
> This software is strictly intended for authorized penetration tests, internal security assessments, corporate environments with explicit written permission, CTF environments, and isolated personal lab environments. Never assess unauthorized target systems.

---

## 📖 Beginner's Guide: What is `security-ai` and How Does It Work?

If you are a new user, `security-ai` works like an **intelligent DevSecOps Lead**:

```
                       ┌──────────────────────────────────────────────┐
                       │  1. USER INPUT & AUTHORIZATION ACKNOWLEDGEMENT│
                       │   Target Domain / IP + Scope Confirmation    │
                       └──────────────────────┬───────────────────────┘
                                              │
                                              ▼
                       ┌──────────────────────────────────────────────┐
                       │  2. UN-BYPASSABLE SECURITY POLICY ENGINE     │
                       │   Checks scope rules, allowed/denied targets │
                       └──────────────────────┬───────────────────────┘
                                              │
                                              ▼
                       ┌──────────────────────────────────────────────┐
                       │  3. AI STRATEGIC PLANNER & TOOL DISCOVERY    │
                       │   Discovers active tools, classifies target, │
                       │   generates DAG workflow (No hallucination)  │
                       └──────────────────────┬───────────────────────┘
                                              │
                                              ▼
                       ┌──────────────────────────────────────────────┐
                       │  4. RESILIENT EXECUTION ENGINE               │
                       │   Runs tools independently, handles retries, │
                       │   saves atomic checkpoints, isolation        │
                       └──────────────────────┬───────────────────────┘
                                              │
                                              ▼
                       ┌──────────────────────────────────────────────┐
                       │  5. EVIDENCE NORMALIZATION & AI ANALYSIS     │
                       │   Converts raw outputs to JSON schema,       │
                       │   separates Observed Facts from Inferences   │
                       └──────────────────────┬───────────────────────┘
                                              │
                                              ▼
                       ┌──────────────────────────────────────────────┐
                       │  6. MULTI-FORMAT REPORT GENERATION           │
                       │   Generates Markdown, HTML (SVG charts), PDF  │
                       └──────────────────────────────────────────────┘
```

---

## ⚡ Quickstart & Installation (Step-by-Step for Kali Linux & Ubuntu)

### Step 1: Clone Repository & Create Virtual Environment
```bash
# 1. Clone repository
git clone https://github.com/Kalilakshman/Ai-security-agent-.git
cd Ai-security-agent-

# 2. Create Python 3.12 virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install orchestrator package in editable mode
pip install --upgrade pip
pip install -e .[dev]
```

### Step 2: Set Your AI Provider Key
```bash
# Export OpenRouter API Key (Recommended free tier provider)
export OPENROUTER_API_KEY="sk-or-v1-your-key-here"

# (Optional) Export OpenAI or Ollama environment variables
export OPENAI_API_KEY="sk-proj-your-key-here"
export OLLAMA_HOST="http://localhost:11434"
```

### Step 3: Run System Diagnostic Doctor
```bash
security-ai doctor
```

---

## 🛠️ Security Tool & Background Daemon Setup Guide

To get full scanning capabilities across all security tools, install or start the following daemons on Kali Linux:

### 1. Install Scanner Binaries
```bash
sudo apt update && sudo apt install -y nmap whatweb nikto gobuster nuclei tshark
```

### 2. Start Background Tool Daemons (Optional for ZAP & Metasploit)
```bash
# Start OWASP ZAP REST API Daemon in background
zaproxy -daemon -port 8080 -config api.disablekey=true &
export ZAP_API_URL="http://localhost:8080"

# Start Metasploit RPC Daemon in background
msfrpcd -U msf -P msfpassword -S -a 127.0.0.1 -p 55553 &
export MSF_RPC_URL="http://127.0.0.1:55553"
```

### 3. Verify Health Matrix of All 12+ Tools
```bash
security-ai tools health
```

---

## 💻 Beginner CLI Command Reference & Examples

### 1. Automated Security Assessment (`security-ai scan`)
Run an automated security scan against an authorized target. Unrelated tool failures or timeouts will **not** stop the scan, and partial results are preserved.

```bash
# Standard automated scan against target domain
security-ai scan scanme.nmap.org -y

# Deep assessment scan with 4 parallel worker threads
security-ai scan https://www.spkcazk.com/ --profile deep --concurrency 4 -y

# Resume an interrupted scan from saved atomic checkpoint
security-ai scan https://www.spkcazk.com/ --resume latest -y
```

---

### 2. View AI Assessment Plan (`security-ai plan`)
Formulate a structured AI security plan showing tool selection reasons and step dependencies without running tool binaries.

```bash
security-ai plan https://www.spkcazk.com/ --profile deep
```

---

### 3. Interactive Operations Dashboard (`security-ai dashboard`)
Launch a professional cybersecurity operations dashboard displaying system health, live progress, active tool status, timeline, and risk metrics.

```bash
security-ai dashboard --target scanme.nmap.org --profile deep
```

---

### 4. LLM Provider Hub (`security-ai llm`)
Switch or test LLM backends (OpenRouter, OpenAI-compatible endpoints, Ollama local models).

```bash
# List supported LLM providers and operational health
security-ai llm providers

# Discover models available for active provider
security-ai llm models

# Test LLM connection and measure API response latency
security-ai llm test

# Switch active provider and model
security-ai llm select --provider openrouter --model nvidia/nemotron-3-ultra-550b-a55b:free
security-ai llm select --provider openai --model gpt-4o
security-ai llm select --provider ollama --model llama3
```

---

### 5. Security Tools Matrix (`security-ai tools`)
Discover tool capability metadata, installation status, and operational health across **Tool Adapters**, **Native Plugins**, and **MCP Tools**.

```bash
# Display matrix of all registered tools, source, and version
security-ai tools list

# Real-time health diagnostics across all 12+ integrated tools
security-ai tools health

# Display capability discovery and options schema for a specific tool
security-ai tools info nmap
security-ai tools info owasp_zap
security-ai tools info metasploit
```

---

### 6. Model Context Protocol Subsystem (`security-ai mcp`)
Manage external Model Context Protocol (MCP) servers communicating over stdio or HTTP/SSE JSON-RPC 2.0.

```bash
# List registered MCP servers
security-ai mcp servers

# List exposed MCP tools
security-ai mcp tools

# Register a custom MCP server
security-ai mcp register --id custom_mcp --name "Custom Security MCP" --transport http --url "http://localhost:8000/mcp"
```

---

### 7. Multi-Format Report Generation (`security-ai report`)
Analyze normalized scan JSON results and generate Markdown, dark-mode HTML (with embedded SVG charts), and PDF reports.

```bash
security-ai report scan_scanme.nmap.org.json --md --html --pdf -o reports_output/
```

---

### 8. View Assessment History (`security-ai history`)
View past scan assessments, target scopes, profiles, execution durations, and findings saved in the SQLite database.

```bash
security-ai history --limit 10
```

---

## ⏱️ Assessment Profiles & Timeout Controls

| Security Tool | Fast Profile (`-p fast`) | Standard Profile (`-p standard`) | Deep Profile (`-p deep`) |
| :--- | :--- | :--- | :--- |
| **`nmap`** | 120s (2m) | 600s (10m) | 1800s (30m) |
| **`whatweb`** | 60s (1m) | 300s (5m) | 900s (15m) |
| **`nikto`** | 180s (3m) | 900s (15m) | 2400s (40m) |
| **`gobuster`** | 180s (3m) | 1200s (20m) | 3600s (60m) |
| **`nuclei`** | 300s (5m) | 1800s (30m) | 7200s (120m) |
| **`owasp_zap`** | 180s (3m) | 1200s (20m) | 3600s (60m) |
| **`metasploit`** | 120s (2m) | 600s (10m) | 1800s (30m) |

---

## ❓ Frequently Asked Questions & Troubleshooting

#### Q: OpenRouter API error: `Illegal header value ...`
- **Solution**: Make sure there are no trailing spaces or newlines when exporting your API key:
  `export OPENROUTER_API_KEY="sk-or-v1-your-key-without-spaces"`

#### Q: How do I resolve `Address already in use` error when starting `msfrpcd`?
- **Solution**: Metasploit RPC is already running in the background! Export the MSF RPC URL directly:
  `export MSF_RPC_URL="http://127.0.0.1:55553"`

#### Q: Will a tool failure or timeout stop the scan?
- **No**. Tools run independently. If one tool (e.g. `nuclei`) times out or encounters a network issue, the orchestrator preserves partial evidence, continues running remaining tools, and generates factual remediation advice in the final report.

---

## 📚 Complete Technical Documentation

- [ARCHITECTURE.md](file:///c:/Users/kalilakshman/project/security-orchestrator/ARCHITECTURE.md) — Enterprise System Architecture & Subsystem Specification
- [SECURITY_MODEL.md](file:///c:/Users/kalilakshman/project/security-orchestrator/SECURITY_MODEL.md) — Security Policy Engine, Scope Validation & Guardrails
- [MCP_GUIDE.md](file:///c:/Users/kalilakshman/project/security-orchestrator/MCP_GUIDE.md) — Model Context Protocol (MCP) Integration Specification
- [LLM_GUIDE.md](file:///c:/Users/kalilakshman/project/security-orchestrator/LLM_GUIDE.md) — Provider-Independent LLM Architecture Guide
- [CONFIGURATION.md](file:///c:/Users/kalilakshman/project/security-orchestrator/CONFIGURATION.md) — Configuration Reference & Environment Variables
- [CLI_REFERENCE.md](file:///c:/Users/kalilakshman/project/security-orchestrator/CLI_REFERENCE.md) — Complete Typer CLI Command Reference
- [PLUGIN_DEVELOPMENT.md](file:///c:/Users/kalilakshman/project/security-orchestrator/PLUGIN_DEVELOPMENT.md) — Tool Adapter & BasePlugin Extension Guide

---

## 🛠️ Developer & Makefile Commands

```bash
make install      # Install dependencies
make test         # Run full pytest test suite (9 test modules)
make lint         # Run ruff and mypy linters
make format       # Format code using ruff
make clean        # Clean python build artifacts
make docker-build # Build multi-stage Docker container image
```
