# ARCHITECTURE AUDIT: AI SECURITY ORCHESTRATOR CLI

**Auditor Role**: Principal AI Architect & Senior Python Engineer  
**Repository**: Security Orchestrator CLI (`security-orchestrator`)  
**Date**: August 8, 2026  
**Status**: Initial Architecture & Technical Debt Audit  

---

## 1. Current Architecture

The AI Security Orchestrator CLI is built as a modular, decoupled Python 3.12+ application following Clean Architecture, Dependency Inversion (DIP), and Interface Segregation (ISP) principles.

```
                         ┌──────────────────────────────────────────┐
                         │          Typer & Rich CLI UI             │
                         │             (app/cli.py)                 │
                         └────────────────────┬─────────────────────┘
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    ▼                         ▼                         ▼
         ┌────────────────────┐    ┌────────────────────┐    ┌────────────────────┐
         │     AppConfig      │    │     AIPlanner      │    │   WorkflowEngine   │
         │  (core/config.py)  │    │ (core/planner.py)  │    │ (core/workflow.py) │
         └──────────┬─────────┘    └──────────┬─────────┘    └──────────┬─────────┘
                    │                         │                         │
                    │                         ▼                         │
                    │              ┌────────────────────┐               │
                    │              │  OpenRouterClient  │               │
                    │              │   (core/llm.py)    │               │
                    │              └────────────────────┘               │
                    │                                                   │
                    └─────────────────────────┬─────────────────────────┘
                                              │
                                              ▼
                                   ┌────────────────────┐
                                   │   PluginRegistry   │
                                   │ (core/registry.py) │
                                   └──────────┬─────────┘
                                              │
                                              ▼
                                   ┌────────────────────┐
                                   │   BasePlugin Tools │
                                   │ (plugins/*.py)     │
                                   └──────────┬─────────┘
                                              │
                                              ▼
                                   ┌────────────────────┐
                                   │    SafeExecutor    │
                                   │ (core/executor.py) │
                                   └──────────┬─────────┘
                                              │
                                              ▼
                                 ┌────────────────────────┐
                                 │ Subprocess OS Sandboxing│
                                 │  (No shell=True)       │
                                 └────────────────────────┘
```

### Component Breakdown
1. **CLI Layer (`app/cli.py`, `app/main.py`)**: Built with Typer and Rich. Handles terminal interaction, Cyberpunk visual formatting, interactive permission prompts, diagnostic sub-system audits (`doctor`), and command routing.
2. **Configuration Subsystem (`core/config.py`)**: Strongly typed settings management using Pydantic v2 and `pydantic-settings`. Loads from `config/config.yaml` with environment variable overrides (`SECURITY_AI_*`). Defines timeouts per plugin profile (`fast`, `standard`, `deep`).
3. **Execution Sandbox (`core/executor.py`)**: Subprocess wrapper implementing `IExecutor`. Uses `subprocess.Popen` / `asyncio.create_subprocess_exec` explicitly without `shell=True` to eliminate shell injection vulnerabilities. Sanitizes environment variables via a safelist (`PATH`, `SYSTEMROOT`, `TEMP`, `TMP`, `HOME`, `USER`, `LANG`). Tracks precision timing in milliseconds and enforces hard execution timeouts.
4. **Plugin Architecture (`plugins/`, `core/registry.py`)**: Plugin abstraction (`BasePlugin`) enforcing `StandardPluginOutput` schema. `PluginRegistry` provides dynamic auto-discovery of tool plugins (`nmap`, `whatweb`, `nikto`, `gobuster`, `nuclei`).
5. **AI Planning & Analysis (`core/planner.py`, `core/analyzer.py`, `core/llm.py`, `core/llm_openrouter.py`)**: Connects to OpenRouter API (defaults to `nvidia/nemotron-3-ultra-550b-a55b:free` with `google/gemini-2.0-flash-exp:free` fallback). Formulates structured JSON assessment plans and synthesizes analysis reports with strict evidence-grounding guardrails separating observed facts from AI inferences.
6. **Workflow Engine (`core/workflow.py`)**: Target format validation, mandatory authorization check enforcement, sequential step execution, and result aggregation into `UnifiedScanResult`.
7. **Persistence Layer (`memory/database.py`, `memory/models.py`)**: SQLAlchemy 2.0 ORM (`ScanRecord`) backed by SQLite (`security_orchestrator.db`). Stores scan parameters, execution durations, findings summaries, and raw JSON outputs.
8. **Multi-Format Reporting (`reports/`)**: Generates GitHub Flavored Markdown (`markdown.py`), self-contained modern HTML (`html.py`), and ReportLab PDF documents (`pdf.py`).

---

## 2. Existing Capabilities

- **CLI Commands**:
  - `security-ai doctor`: Diagnostics check for Python 3.12+, YAML config engine, Subprocess Sandbox, and OpenRouter API connectivity.
  - `security-ai config`: Displays active configuration and profile timeout settings with masked API keys.
  - `security-ai plugins`: Tool matrix listing discovered plugins, system binary presence on `$PATH`, and operational states.
  - `security-ai scan <target> [-p profile] [-y]`: Full automated scan execution with explicit authorization guardrails, real-time Rich spinner updates, SQLite persistence, and JSON artifact generation.
  - `security-ai plan <target> [-p profile] [-e]`: AI strategic plan generation via OpenRouter with option to execute immediately.
  - `security-ai history [-n limit]`: Tabular display of historical scan runs from SQLite database.
  - `security-ai report <file.json> [--md] [--html] [--pdf]`: Multi-format report generation from normalized scan JSON artifacts.
- **Security Tools Integrated**: Wrappers for `nmap`, `whatweb`, `nikto`, `gobuster`, and `nuclei`.
- **Profiles**: `fast`, `standard`, and `deep` assessment timeout profiles per tool.
- **Fail-Safe Fallbacks**: Deterministic fallback plan formulation when LLM APIs are unreachable or return malformed JSON. Partial tool output preservation on timeout/failure.

---

## 3. Technical Debt

1. **Dual LLM Provider Implementation**:
   - `core/llm.py` (`OpenRouterClient`) and `core/llm_openrouter.py` (`OpenRouterLLMProvider`) both communicate with OpenRouter API using different interfaces and HTTP client instantiation patterns (`httpx.Client` vs `httpx.AsyncClient`).
2. **Broken Legacy Plugin Manager**:
   - `plugins/manager.py` contains structural flaws: `discover_plugins()` (line 24) and `list_plugins()` (line 60) omit `self` in method signatures, causing runtime errors if called. `PluginManager` uses `IPlugin` while concrete plugins inherit `BasePlugin`. The active system relies on `core/registry.py` instead.
3. **Outdated CLI Unit Tests**:
   - `tests/test_cli.py` contains `test_cli_scan_placeholder` expecting `scan` to be a placeholder command, whereas `app/cli.py` has already implemented a full `scan` command.
4. **Hardcoded Linux Wordlist Path in Gobuster Plugin**:
   - `plugins/gobuster.py` defaults to `/usr/share/wordlists/dirb/common.txt`, which is non-existent on Windows systems unless overridden by options.
5. **Redundant Config File Discovers**:
   - Configuration loading (`load_config()`) is invoked redundantly across plugins, CLI callbacks, and workflow steps without caching or sharing singletons effectively.
6. **Lack of Database Migration Management**:
   - `memory/database.py` calls `Base.metadata.create_all()` directly; schema changes in `models.py` will not automatically migrate existing SQLite DB tables.

---

## 4. Extension Points

1. **Tool Plugins (`plugins/`)**: Drop a new `.py` module extending `BasePlugin` with `build_command()` and `parse()`. Auto-discovered automatically by `PluginRegistry`.
2. **LLM Provider Backends (`core/interfaces.py`)**: Implement `ILLMProvider` for local LLMs (Ollama, vLLM) or alternative cloud API providers (Anthropic, OpenAI, LocalAI).
3. **Report Generators (`reports/`)**: Implement new generators (e.g. SARIF, CycloneDX, Executive Dashboard HTML) taking `AnalysisReport` and `raw_data`.
4. **Multi-Step Playbooks (`app/cli.py`)**: Extend the `orchestrate` command to load YAML playbooks specifying tool chains, thresholds, and conditional branching.
5. **Artifact Triage (`app/cli.py`)**: Extend the `analyze` command to accept arbitrary log files/pcap/xml for offline AI vulnerability analysis.

---

## 5. Components That Should Remain Unchanged

- `core/executor.py` (`SafeExecutor`): Process sandboxing, `shell=False` execution, time tracking, and environment sanitization are robust and meet strict security requirements.
- `plugins/base.py` (`BasePlugin` & `StandardPluginOutput`): Clean, unified JSON contract across all tools.
- `core/interfaces.py` (`IExecutor`, `ExecutionResult`, `ILLMProvider` core definitions).
- `memory/models.py` (`ScanRecord` SQLAlchemy 2.0 ORM structure).

---

## 6. Components Requiring Modification

- `core/llm.py` & `core/llm_openrouter.py`: Refactor and consolidate into a single unified OpenRouter client implementing `ILLMProvider` with synchronous and asynchronous support.
- `plugins/manager.py`: Fix missing `self` parameters, align with `PluginRegistry` or deprecate cleanly to avoid developer confusion.
- `plugins/gobuster.py`: Make default wordlists OS-aware or fall back gracefully when wordlists are absent on Windows/macOS.
- `app/cli.py`: Wire up placeholder commands (`orchestrate`, `analyze`) as new prompts deliver playbook and artifact triage features.
- `tests/test_cli.py`: Update outdated test assertions to reflect current fully implemented commands.

---

## 7. Backward Compatibility Risks

- **API Signature Changes**: Modifying `BasePlugin.execute()` signature or `StandardPluginOutput` schema fields will break existing plugin execution and report generation.
- **Config Key Renaming**: Altering `AppConfig` field names or environment variable prefix (`SECURITY_AI_*`) will break existing user `config.yaml` files.
- **Database Schema Alterations**: Modifying `ScanRecord` columns without an Alembic migration script will corrupt or invalidate existing SQLite `.db` instances.

---

## 8. Recommended Upgrade Sequence

To implement future features cleanly without breaking existing functionality, follow this strictly ordered multi-phase roadmap:

1. **Refactoring & Technical Debt Cleanup**:
   - Consolidate LLM clients (`core/llm.py` / `core/llm_openrouter.py`).
   - Fix `plugins/manager.py` signatures and update `tests/test_cli.py`.
2. **Enhanced Tool Integration & OS Compatibility**:
   - Make plugin wordlist handling OS-agnostic (Windows/Linux/macOS).
   - Add output parsing error handling improvements.
3. **Advanced Playbook Orchestration Engine**:
   - Implement YAML playbook parsing and execution engine for `security-ai orchestrate`.
4. **Deep AI Analysis & Triage Engine**:
   - Implement offline log/artifact parsing and triage for `security-ai analyze`.
5. **Interactive Cyberpunk UI & Real-Time Monitoring**:
   - Add live process streaming and dashboard views to CLI UI.
