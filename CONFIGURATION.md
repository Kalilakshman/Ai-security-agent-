# Configuration & Environment Variables Reference

The **AI Security Orchestrator CLI** uses strongly typed configuration schemas (`core/config.py`) powered by **Pydantic v2** and **PyYAML**.

---

## ⚙️ Configuration Files & Priority

Settings are loaded in the following precedence order:
1. CLI flags (`--profile`, `--concurrency`, `--retries`, `--provider`, `--model`)
2. Environment Variables (`SECURITY_AI_*`, `OPENROUTER_API_KEY`, `OPENAI_API_KEY`)
3. `config/config.yaml` or `config.yaml` file in root directory

---

## 🌐 Environment Variables

| Variable | Description | Default |
| :--- | :--- | :--- |
| `SECURITY_AI_LLM__PROVIDER` | Active LLM provider (`openrouter`, `openai`, `ollama`) | `openrouter` |
| `SECURITY_AI_LLM__MODEL` | Active model identifier | `nvidia/nemotron-3-ultra-550b-a55b:free` |
| `SECURITY_AI_LLM__API_ENDPOINT` | Base URL for LLM API | `https://openrouter.ai/api/v1` |
| `OPENROUTER_API_KEY` | OpenRouter API Key | `""` |
| `OPENAI_API_KEY` | OpenAI API Key | `""` |
| `OLLAMA_HOST` / `OLLAMA_BASE_URL` | Ollama service endpoint | `http://localhost:11434` |
| `ZAP_API_URL` | OWASP ZAP REST API URL | `http://localhost:8080` |
| `BURP_API_URL` | Burp Suite REST API URL | `http://localhost:1337` |
| `MSF_RPC_URL` | Metasploit MSF RPC API URL | `http://127.0.0.1:55553` |

---

## 📄 Full `config/config.yaml` Schema

```yaml
policy:
  allowed_targets: ["127.0.0.1", "localhost", "192.168.*", "10.*", "*.local"]
  denied_targets: ["*.gov", "*.mil", "169.254.169.254"]
  tool_allowlist: ["nmap", "whatweb", "nikto", "gobuster", "nuclei", "owasp_zap", "burp_suite", "tshark", "metasploit"]
  tool_denylist: []
  allowed_profiles: ["fast", "standard", "deep"]
  max_execution_time_seconds: 3600.0
  require_explicit_auth: true
  allow_destructive_tools: false
  audit_log_file: "policy_audit.log"

llm:
  provider: "openrouter"
  model: "nvidia/nemotron-3-ultra-550b-a55b:free"
  api_endpoint: "https://openrouter.ai/api/v1"
  api_key: "sk-or-v1-your-key-here"
  temperature: 0.7
  max_tokens: 2048
  timeout_seconds: 45.0

executor:
  default_timeout_seconds: 60.0
  max_timeout_seconds: 600.0

database:
  db_url: "sqlite:///security_orchestrator.db"
  echo: false

reports:
  output_dir: "reports_output"
  default_formats: ["md", "html", "pdf"]

timeouts:
  nmap: { fast: 120, standard: 600, deep: 1800 }
  whatweb: { fast: 60, standard: 300, deep: 900 }
  nikto: { fast: 180, standard: 900, deep: 2400 }
  gobuster: { fast: 180, standard: 1200, deep: 3600 }
  nuclei: { fast: 300, standard: 1800, deep: 7200 }
```
