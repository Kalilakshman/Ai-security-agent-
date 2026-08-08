# System Architecture — AI Security Orchestrator CLI (`security-ai`)

The **AI Security Orchestrator CLI** is designed as a modular, decoupled, enterprise-grade security automation platform built using **Python 3.12**.

---

## 🏛️ Subsystem Overview

```
User / Typer CLI (app/cli.py) & Rich UI Terminal Dashboard (app/ui.py)
                       │
                       ▼
            Security Policy Engine (core/policy.py)
   (Target Scope Validation | Tool Allowlists | Audit Logging)
                       │
                       ▼
          Upgraded AI Strategic Planner (core/planner.py)
   (Target Classification | Healthy Tool Discovery | DAG Plan)
                       │
                       ▼
         Provider-Independent LLM Hub (core/llm/)
   (OpenRouter | OpenAI-Compatible | Ollama Local Models)
                       │
                       ▼
         Resilient Execution Engine (core/workflow.py)
   (Fault Isolation | Timeouts | Retries | Checkpoints | DAG Tiers)
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
   MCP Gateway Layer       Extensible Tool Adapters
(core/mcp/gateway.py)      (core/adapters/)
 (stdio / HTTP RPC)     (Nmap, ZAP, Burp, Tshark, MSF)
          │                         │
          └────────────┬────────────┘
                       │
                       ▼
       Evidence & Results Analyzer (core/analyzer.py)
   (Observed Facts vs. AI Analytical Inferences Separation)
                       │
                       ▼
     Multi-Format Reporting Pipeline (reports/)
         (Markdown | HTML | PDF Output)
                       │
                       ▼
     SQLite Persistence & Audit Database (memory/database.py)
```

---

## 🔬 Core Components & Responsibilities

1. **Typer CLI (`app/cli.py`) & Rich Terminal Dashboard (`app/ui.py`)**:
   - Provides non-breaking Typer commands (`doctor`, `plugins`, `config`, `llm`, `tools`, `scan`, `plan`, `history`, `report`, `dashboard`).
   - Renders a professional dark-mode terminal operations UI.

2. **Provider-Independent LLM Architecture (`core/llm/`)**:
   - Abstract base class `LLMProvider`.
   - Implementations for OpenRouter (`OpenRouterLLMProvider`), OpenAI-compatible endpoints (`OpenAICompatibleProvider`), and Ollama local models (`OllamaLLMProvider`).

3. **Security Policy Engine (`core/policy.py`)**:
   - Gatekeeper evaluating all execution requests against explicit authorization confirmation, target scope rules, tool allowlists/denylists, profile depth rules, and timeout constraints.

4. **Model Context Protocol (MCP) Integration Layer (`core/mcp/`)**:
   - `MCPGateway`, `MCPServerRegistry`, `MCPClient`, and `MCPPolicyEngine`. Connects to external MCP servers over stdio and HTTP/SSE JSON-RPC 2.0.

5. **Extensible Security-Tool Adapter Subsystem (`core/adapters/`)**:
   - Adapters for Nmap, OWASP ZAP, Burp Suite, Wireshark/tshark, and Metasploit RPC. `AdapterPluginBridge` automatically registers all adapters into `PluginRegistry` without modifying core workflow code.

6. **Resilient Execution Engine (`core/workflow.py`)**:
   - Step isolation, independent per-tool timeouts, retries, partial result preservation, atomic disk checkpointing (`core/checkpoint.py`), and parallel DAG scheduling (`core/scheduler.py`).

7. **Evidence Analyzer & Reporter Pipeline (`core/analyzer.py`, `reports/`)**:
   - Formats tool output into standard `NormalizedToolResult` and `EvidenceModel` schemas.
   - Enforces strict factual separation between `OBSERVED FACTS` and `AI INFERENCES`.
   - Generates Markdown (`.md`), responsive HTML (`.html` with SVG charts), and PDF (`.pdf`) reports.

8. **Database Persistence Layer (`memory/database.py`)**:
   - SQLAlchemy 2.x SQLite database storing assessment records, target scopes, profiles, LLM models, MCP servers, tool executions, retries, evidence counts, and policy audit entries.
