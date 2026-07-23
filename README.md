# Building Secure AI Agents: Defense-First Development

## Half-day workshop (3 hours) &mdash; Revision 1.0

These instructions will guide you through configuring a GitHub Codespaces
environment that you can use to run the workshop labs.

This workshop is for **agent builders**. Across five labs you take one
deliberately vulnerable AI support agent and harden it, layer by layer:
guardrails and canary tokens, least-privilege tool controls, a scoped MCP
server, RAG poisoning defenses, and observability. The final lab
(observability) is designed to also work as post-class homework if time runs
short.

### Prerequisites

Experience building AI agents (via the AI Accelerator, an agents workshop, or
equivalent), comfort with Python, and a basic understanding of agent
architectures (ReAct, tool calling, MCP). No prior security background is
assumed &mdash; every term is defined as it comes up.

<br><br>

**1. Change your codespace's default timeout from 30 minutes to longer.**
When logged in to GitHub, go to https://github.com/settings/codespaces and
scroll down to the *Default idle timeout* section. Adjust the value as desired.

<br><br>

**2. Start a new codespace from this repository.**
Use the green **Code** button on the repo, choose the **Codespaces** tab, and
create a new codespace. This will run for several minutes while it builds. While
it runs, do step 3.

<br><br>

**3. Get a free Groq API key** (enables the more powerful models and the real
Llama Guard 4 safety classifier used in Lab 1).

a. In a browser, go to https://console.groq.com and create an account.
b. Click **API Keys** (top right), then **Create API Key**.
c. Fill in the info, submit, and **copy the key** (you can't view it again later).

The labs still run without a key &mdash; they fall back to the local Ollama model
&mdash; but a Groq key makes them faster and unlocks Llama Guard.

<br><br>

**4. Ensure the codespace is done setting up.**
After the initial build, a script sets up the Python environment, installs the
dependencies and Ollama, and downloads the `llama3.2:3b` model. This takes
several more minutes. The codespace is ready when you see a normal prompt in the
terminal.

<br><br>

**5. Set your Groq key in the codespace.**
In the codespace **TERMINAL**, run the command below, paste your key when
prompted, and hit *Enter*:

```
source scripts/setup-key.sh
```

You should see that `AGENT_PROVIDER` and `GROQ_API_KEY` are set.

<br><br>

**6. Run the warm-up script for faster first responses.**

```
python scripts/warmup_ollama.py
```

<br><br>

**7. Open `labs.md`** and follow along. You can open it in the codespace
(right-click > *Open Preview*) or in a separate browser tab.

**Now you are ready for the labs!**

<br><br>

### The five labs

| Lab | Focus | Directory |
|---|---|---|
| 1 | Prompt-injection defense: guardrails, PII redaction, canary tokens | `guardrails/` |
| 2 | Securing agent tool calls: least privilege, approval gates, budgets | `agents/` |
| 3 | Hardening MCP servers: JWT auth + per-tool scopes | `mcp/` |
| 4 | RAG pipeline hardening: source allowlists, injection detection, output scanning | `rag/` |
| 5 | Auditing & observability: OpenTelemetry spans + anomaly detection *(homework-capable)* | `observability/` |

<br><br>

### Reopening a timed-out codespace

1. Go to https://github.com/codespaces
2. Find the codespace, right-click, and select *Open in browser*
3. Repeat steps 5 & 6 above to set the Groq key and re-run the warm-up.

<br><br>

## Troubleshooting

- **A lab reports it cannot reach Ollama** &mdash; the server isn't running. Run `bash scripts/startup_ollama.sh --skip-pull` from the repo root, then retry. Check `/tmp/ollama.log` if it persists.
- **The first model call is slow (~30-60s)** &mdash; run `python scripts/warmup_ollama.py` once, then retry. Later calls in the same session are fast.
- **Groq returns 429 (rate limit)** &mdash; you've exceeded the free tier. Wait a few seconds and retry, or `export LLM_BACKEND=ollama` to switch to the local model. Each person should use their own key.
- **Groq returns 401 / invalid key** &mdash; `GROQ_API_KEY` is missing or wrong. Re-copy it from console.groq.com, or unset it to fall back to Ollama.
- **A `python` command "hangs"** &mdash; the RAG and MCP labs use interactive prompts or run servers. Follow the lab's stop instruction (`quit` or `Ctrl+C`).
- **`Address already in use` in Lab 3** &mdash; a previous server is still running. Stop it with `Ctrl+C`, or `kill $(lsof -t -i:8000)`.
- **`ModuleNotFoundError`** &mdash; run `pip install -r requirements.txt` from the repo root (inside the `py_env` virtualenv).
- **Skeleton file errors before merging** &mdash; skeletons are completed via the `code -d` diff-merge step first. Each lab tells you when to merge.

## License and attribution

For educational use only by the attendees of our workshops.

&copy; 2026 Tech Skills Transformations and Brent C. Laster. All rights reserved.
