# 🤖 AI Security Orchestrator CLI (`security-ai`)

Production-grade, modular, DevSecOps-ready AI Security Orchestrator CLI built with **Python 3.12**, **Typer**, **Rich**, **Pydantic v2**, **PyYAML**, and **SQLAlchemy 2.x**.

> [!IMPORTANT]
> **Authorization & Ethical Scope**  
> This software is strictly intended for authorized penetration tests, internal security assessments, corporate environments with written permission, CTF environments, and isolated personal lab environments. Never assess unauthorized target systems.

---

## 🏛️ System Architecture

```
                                ┌───────────────────────────────────┐
                                │            Typer CLI              │
                                │           (app/cli.py)            │
                                └─────────────────┬─────────────────┘
                                                  │
                 ┌────────────────────────────────┼────────────────────────────────┐
                 ▼                                ▼                                ▼
    ┌───────────────────────────┐   ┌───────────────────────────┐   ┌───────────────────────────┐
    │        AI Planner         │   │   Dynamic Plugin Registry │   │     OpenRouter Client     │
    │     (core/planner.py)     │   │     (core/registry.py)    │   │       (core/llm.py)       │
    └────────────┬──────────────┘   └─────────────┬─────────────┘   └─────────────┬─────────────┘
                 │                                │                               │
                 └────────────────────────────────┼───────────────────────────────┘
                                                  │
                                                  ▼
                                ┌───────────────────────────────────┐
                                │          Workflow Engine          │
                                │        (core/workflow.py)         │
                                └─────────────────┬─────────────────┘
                                                  │ (Routes Tool Executions via SafeExecutor)
                     ┌────────────────────────────┼────────────────────────────┐
                     ▼                            ▼                            ▼
        ┌──────────────────────────┐ ┌──────────────────────────┐ ┌──────────────────────────┐
        │       nmap Plugin        │ │      whatweb Plugin      │ │       nikto Plugin       │
        │    (plugins/nmap.py)     │ │   (plugins/whatweb.py)   │ │    (plugins/nikto.py)    │
        └────────────┬─────────────┘ └────────────┬─────────────┘ └────────────┬─────────────┘
                     │                            │                            │
                     └────────────────────────────┼────────────────────────────┘
                                                  │ (Collects Standard JSON Outputs)
                                                  ▼
                                ┌───────────────────────────────────┐
                                │       AI Results Analyzer         │
                                │        (core/analyzer.py)         │
                                └─────────────────┬─────────────────┘
                                                  │ (Facts vs Inferences Separation)
                     ┌────────────────────────────┼────────────────────────────┐
                     ▼                            ▼                            ▼
        ┌──────────────────────────┐ ┌──────────────────────────┐ ┌──────────────────────────┐
        │     Markdown Reporter    │ │       HTML Reporter      │ │       PDF Reporter       │
        │   (reports/markdown.py)  │ │     (reports/html.py)    │ │     (reports/pdf.py)     │
        └──────────────────────────┘ └──────────────────────────┘ └──────────────────────────┘
```

---

## 📦 Installation Guide

### Option 1: Kali Linux / Ubuntu / Debian Installation
```bash
# 1. Update system package index & install required scanner binaries
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git nmap whatweb nikto gobuster nuclei

# 2. Clone repository & navigate to directory
git clone https://github.com/Kalilakshman/Ai-security-agent-.git
cd Ai-security-agent-

# 3. Create & activate Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 4. Install package in editable mode
pip install -e .[dev]

# 5. Export OpenRouter API key
export OPENROUTER_API_KEY="your-openrouter-api-key-here"

# 6. Verify installation
security-ai doctor
```

### Option 2: Windows / Generic Native Installation (Python 3.12)
```bash
# Clone or navigate to codebase
cd security-orchestrator

# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Install in editable mode
pip install -e .[dev]
```

### Option 3: Docker Container Setup
```bash
# Build multi-stage Docker image
make docker-build

# Run CLI doctor diagnostic inside container
docker run --rm security-ai-orchestrator doctor
```

---

## 🔑 OpenRouter API Setup Guide

Set your OpenRouter API key as an environment variable:
```bash
# Windows PowerShell
$env:OPENROUTER_API_KEY="sk-or-v1-your-key-here"

# Linux / macOS
export OPENROUTER_API_KEY="sk-or-v1-your-key-here"
```
Or edit `config/config.yaml`:
```yaml
openrouter:
  api_key: "sk-or-v1-your-key-here"
  default_model: "meta-llama/llama-3.3-70b-instruct:free"
```

---

## 💻 CLI Commands & Usage Examples

### 1. Environment & API Diagnostics (`doctor`)
```bash
security-ai doctor
```

### 2. View System Tool & Plugin Status (`plugins`)
```bash
security-ai plugins
```

### 3. Display Configuration (`config`)
```bash
security-ai config
```

### 4. AI-Driven Assessment Planning (`plan`)
Formulate an AI assessment plan for a target:
```bash
security-ai plan scanme.nmap.org
```
To prompt for authorization and execute workflow immediately:
```bash
security-ai plan scanme.nmap.org --execute
```

### 5. Generate Multi-Format Reports (`report`)
Analyze normalized scan JSON results and generate Markdown, HTML, and PDF reports:
```bash
security-ai report scan_results.json --md --html --pdf -o my_reports/
```

### 6. View Historical Assessments (`history`)
```bash
security-ai history --limit 10
```

---

## 🧩 Plugin Development Guide

To create a new tool wrapper plugin, create a single `.py` file inside `plugins/` (e.g. `plugins/mytool.py`):

```python
from typing import Dict, List, Any, Optional
from plugins.base import BasePlugin

class MyToolPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "mytool"

    @property
    def description(self) -> str:
        return "My custom security tool plugin."

    def build_command(self, target: str, options: Optional[Dict[str, Any]] = None) -> List[str]:
        return ["mytool", "--target", target]

    def parse(self, stdout: str, stderr: str) -> List[Dict[str, Any]]:
        return [{"raw": stdout.strip()}]
```
No core code or planner changes required — `PluginRegistry` discovers and registers it automatically!

---

## 🛠️ Developer & Makefile Commands

```bash
make install    # Install dependencies
make test       # Run pytest test suite
make lint       # Run ruff and mypy linters
make format     # Format code using ruff
make clean      # Clean python build artifacts
```
