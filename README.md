# 🤖 AI Security Orchestrator CLI (`security-ai`)

Production-grade, modular, DevSecOps-ready **AI Security Orchestrator CLI** built with **Python 3.12**, **Typer**, **Rich**, **Pydantic v2**, **PyYAML**, and **SQLAlchemy 2.x**.

> [!IMPORTANT]
> **Authorization & Ethical Scope**  
> This software is strictly intended for authorized penetration tests, internal security assessments, corporate environments with explicit written permission, CTF environments, and isolated personal lab environments. Never assess unauthorized target systems.

---

## 🛠️ Complete Tool Setup & Execution Guide for Kali Linux

### 1. External Daemon Setup (ZAP, Metasploit, Burp, Tshark)

Run security assessment daemons in the background on Kali Linux before scanning:

```bash
# 1. OWASP ZAP REST API Daemon
zaproxy -daemon -port 8080 -config api.disablekey=true &
export ZAP_API_URL="http://localhost:8080"

# 2. Metasploit Framework RPC Daemon
msfrpcd -U msf -P msfpassword -S -a 127.0.0.1 -p 55553 &
export MSF_RPC_URL="http://127.0.0.1:55553"

# 3. Wireshark / Tshark CLI Packet Capture
sudo apt update && sudo apt install -y tshark nmap whatweb nikto gobuster nuclei

# 4. Verify Health of All Integrated Security Tools
security-ai tools health
```

---

## 🔌 Model Context Protocol (MCP) Subsystem (`security-ai mcp`)

```bash
# 1. List registered MCP servers
security-ai mcp servers

# 2. List exposed MCP tools
security-ai mcp tools

# 3. Register a custom MCP server
security-ai mcp register -i custom_mcp -n "Custom Security MCP" -t http -u "http://localhost:8000/mcp"
```

---

## 🏛️ System Architecture

```
                               ┌───────────────────────────────────┐
                               │     Professional Terminal UI      │
                               │      (app/ui.py & app/cli.py)     │
                               └─────────────────┬─────────────────┘
                                                 │
                ┌────────────────────────────────┼────────────────────────────────┐
                ▼                                ▼                                ▼
   ┌───────────────────────────┐   ┌───────────────────────────┐   ┌───────────────────────────┐
   │    Provider-Independent   │   │  Security Policy Engine   │   │  MCP Gateway & Server Hub │
   │   LLM Provider Architecture│  │     (core/policy.py)      │   │    (core/mcp/gateway.py)  │
   └────────────┬──────────────┘   └─────────────┬─────────────┘   └─────────────┬─────────────┘
                │                                │                               │
                └────────────────────────────────┼───────────────────────────────┘
                                                 │
                                                 ▼
                               ┌───────────────────────────────────┐
                               │    Upgraded AI Strategic Planner  │
                               │        (core/planner.py)          │
                               └─────────────────┬─────────────────┘
                                                 │
                                                 ▼
                               ┌───────────────────────────────────┐
                               │    Resilient Execution Engine     │
                               │        (core/workflow.py)         │
                               └─────────────────┬─────────────────┘
                                                 │ (Routes Tool Executions & Enforces Retries/Timeouts)
                     ┌───────────────────────────┼───────────────────────────┐
                     ▼                           ▼                           ▼
        ┌─────────────────────────┐ ┌─────────────────────────┐ ┌─────────────────────────┐
        │   Nmap / ZAP Adapters   │ │   Burp / Tshark Adapters│ │    Metasploit Adapter   │
        │  (core/adapters/nmap)   │ │  (core/adapters/tshark) │ │ (core/adapters/metasp)  │
        └────────────┬────────────┘ └────────────┬────────────┘ └────────────┬────────────┘
                     │                           │                           │
                     └───────────────────────────┼───────────────────────────┘
                                                 │ (Normalizes JSON Evidence & Artifacts)
                                                 ▼
                               ┌───────────────────────────────────┐
                               │   Evidence & Results Analyzer     │
                               │        (core/analyzer.py)         │
                               └─────────────────┬─────────────────┘
                                                 │ (Observed Facts vs. AI Inferences Separation)
                     ┌───────────────────────────┼───────────────────────────┐
                     ▼                           ▼                           ▼
        ┌─────────────────────────┐ ┌─────────────────────────┐ ┌─────────────────────────┐
        │    Markdown Reporter    │ │      HTML Reporter      │ │      PDF Reporter       │
        │  (reports/markdown.py)  │ │    (reports/html.py)    │ │    (reports/pdf.py)     │
        └─────────────────────────┘ └─────────────────────────┘ └─────────────────────────┘
```

---

## 📦 Quickstart & Installation

```bash
# Clone repository
git clone https://github.com/Kalilakshman/Ai-security-agent-.git
cd Ai-security-agent-

# Create virtual environment (Python 3.12)
python3 -m venv .venv
source .venv/bin/activate

# Install package in editable mode with development dependencies
pip install -e .[dev]

# Set API key for OpenRouter / OpenAI / Ollama
export OPENROUTER_API_KEY="your-openrouter-api-key-here"

# Run doctor diagnostic
security-ai doctor
```

---

## 💻 Primary Commands

### 1. Security Scan (`security-ai scan`)
```bash
security-ai scan example.com --profile deep --concurrency 4 --retries 1 -y
```

### 2. Strategic AI Plan (`security-ai plan`)
```bash
security-ai plan example.com --profile deep
```

### 3. Interactive Operations Dashboard (`security-ai dashboard`)
```bash
security-ai dashboard --target example.com --profile deep
```

### 4. LLM Provider Hub (`security-ai llm`)
```bash
security-ai llm providers
security-ai llm models
security-ai llm select --provider openai --model gpt-4o
security-ai llm test
```

### 5. Security Tools Matrix (`security-ai tools`)
```bash
security-ai tools list
security-ai tools info nmap
security-ai tools health
```

### 6. Multi-Format Report Generation (`security-ai report`)
```bash
security-ai report scan_example_com.json --md --html --pdf -o reports_output
```

---

## 📚 Complete Documentation Guides

- [ARCHITECTURE.md](file:///c:/Users/kalilakshman/project/security-orchestrator/ARCHITECTURE.md) — Enterprise System Architecture & Component Interactions
- [SECURITY_MODEL.md](file:///c:/Users/kalilakshman/project/security-orchestrator/SECURITY_MODEL.md) — Security Policy Engine, Scope Validation & Guardrails
- [MCP_GUIDE.md](file:///c:/Users/kalilakshman/project/security-orchestrator/MCP_GUIDE.md) — Model Context Protocol (MCP) Integration Specification
- [LLM_GUIDE.md](file:///c:/Users/kalilakshman/project/security-orchestrator/LLM_GUIDE.md) — Provider-Independent LLM Architecture Guide
- [CONFIGURATION.md](file:///c:/Users/kalilakshman/project/security-orchestrator/CONFIGURATION.md) — Configuration Reference & Environment Variables
- [CLI_REFERENCE.md](file:///c:/Users/kalilakshman/project/security-orchestrator/CLI_REFERENCE.md) — Typer CLI Command Reference
- [PLUGIN_DEVELOPMENT.md](file:///c:/Users/kalilakshman/project/security-orchestrator/PLUGIN_DEVELOPMENT.md) — Tool Adapter & BasePlugin Extension Guide

---

## 🛠️ Testing & Quality Controls

```bash
# Run complete unit test suite
pytest tests/ -v

# Run linting and type checks
ruff check .
mypy app/ core/ plugins/ memory/ reports/
```
