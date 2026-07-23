# Building Secure AI Agents: Defense-First Development
## Half-day workshop (3 hours)
## Session labs
## Revision 1.0 - 07/06/26


**Follow the startup instructions in the README.md file IF NOT ALREADY DONE!**

**NOTE: To copy and paste in the codespace, you may need to use keyboard commands - CTRL-C and CTRL-V. Chrome may work best for this.**

---

### The through-line: one vulnerable agent, hardened layer by layer

Every lab in this workshop hardens **the same system** - *HelpBot*, OmniTech's
customer-support AI agent. HelpBot was shipped fast and works great in the demo:
it answers from a knowledge base (RAG), calls tools to do real work, reaches
external tools over MCP, and keeps a little memory between turns. It is also
completely undefended - and that is exactly the agent an attacker wants.

You will add one defensive layer per lab, in the order a builder should think
about them:

| Lab | The layer you add to HelpBot | What attack it stops |
|---|---|---|
| 1 | **Guardrails + canary tokens** around the model | Jailbreaks, PII leaks, system-prompt leaks |
| 2 | **Tool-call controls**: least privilege, approval, budgets | Indirect prompt injection abusing tools |
| 3 | **A hardened MCP server**: JWT auth + per-tool scopes | Unauthorized / over-scoped tool access |
| 4 | **RAG pipeline hardening**: allowlists, injection detection, output scanning | Knowledge-base poisoning |
| 5 | **Observability**: OpenTelemetry spans + anomaly detection | Blind spots - abuse you can't see |

No single control is perfect - that is the point. By the end, HelpBot survives
attacks that flattened it in Lab 1, because the layers cover each other. This is
**defense in depth**, applied to agents.

A note on the model: the labs use a **real** language model. With a free Groq
key set (see README) they use fast hosted models plus the real **Llama Guard 4**
safety classifier; without one they fall back to a local `llama3.2:3b` via
Ollama. Because the model is real, exact wording varies run to run - the
security *outcomes* (BLOCKED / FIXED / DENIED) do not.

---
<br><br>

**Lab 1: Guardrails and Canary Tokens - Wrapping the Model**

**Purpose: In this lab, we put the first layer of defense around HelpBot: a guardrails pipeline modeled on the validator pattern used by frameworks like Guardrails.ai and Llama Guard. Input guards run *before* the model to block jailbreaks and off-topic or oversized requests; output guards run *after* the model to redact PII and block unsafe completions. Then we add a canary token - a tripwire that catches a system-prompt leak even when every other guard misses it.**

> **New terms in this lab:** a **guardrail** is a cheap, deterministic check you run around the model (not inside it). An **input guard** screens the user's request before it costs a model call; an **output guard** screens the model's reply before the user sees it. A **jailbreak** is a prompt crafted to make the model ignore its instructions. A **canary token** is a unique secret string planted in the system prompt that should never appear in a normal answer - if it does, you know the prompt leaked.

<br>

1. From the terminal, change to the *guardrails* directory:

```
cd /workspaces/building-secure-ai-agents/guardrails
```

<br><br>

2. Open the skeleton and review its shape:

```
code guardrails_demo.py
```

Notice the two families of guards. **Input guards** (`guard_jailbreak`, `guard_topic`, `guard_length`) screen the user's request. **Output guards** (`guard_pii`, `guard_banned`) screen the model's response. Each guard returns `(ok, reason, fixed_text)` - if a guard returns fixed text, the pipeline *repairs* the content and continues; if it returns `None`, the content is *blocked*. These are the cheap, fast, deterministic checks you control.

Wrapping those hand-built guards, `main()` also calls a **real safety classifier - Meta's Llama Guard 4, hosted on Groq** - on both the input and the output (via `llm.moderate()`). That's the production pattern: regex/allowlist guards you own, **plus** a model-based classifier that catches whole categories of harmful content (violence, weapons, hate, self-harm, ...) you could never enumerate by hand. Llama Guard runs only if you've set a `GROQ_API_KEY`; without one, the lab still runs with just the hand-built guards.

<br><br>

3. Open the diff-and-merge view to fill in the validator logic:

```
code -d ../extra/guardrails_complete.txt guardrails_demo.py
```

![Building the guardrails pipeline](./images/bsa-1-build.png?raw=true "Building the guardrails pipeline")

<br><br>

4. Review the **input guards** in the complete version (left): the jailbreak patterns (`ignore previous instructions`, `reveal your system prompt`, "developer mode," etc.), the `ALLOWED_TOPICS` allowlist that keeps the assistant in its lane, and the maximum input length.

<br><br>

5. Review the **output guards**: the `PII_PATTERNS` that redact SSNs, card numbers, emails, and phone numbers (a *FIXED* outcome), and the `BANNED_OUTPUT` patterns that hard-block dangerous responses (a *BLOCK* outcome). Note how `run_guards` distinguishes a repairable finding from a hard block.

<br><br>

6. Merge all sections from the complete version (left) into the skeleton (right). When no differences remain, close the diff tab to save.

<br><br>

7. Run the guardrails demo:

```
python guardrails_demo.py
```

✓ **Success looks like:** one block prints per request. The jailbreak, the off-topic poem, and the oversized input each show **INPUT BLOCKED (never reached the model)**; the benign question shows **DELIVERED (PASS)**; and the record-with-PII request shows **DELIVERED (FIXED)** with `[SSN-REDACTED]` / `[CARD-REDACTED]`. (Exact model wording varies; the BLOCKED / FIXED labels don't.) If everything shows PASS with no blocks, a guard didn't merge - reopen the diff at Step 3.

Each request flows through four layers: **Llama Guard (input) -> your input guards -> the model -> your output guards -> Llama Guard (output)**. The header line shows whether the Llama Guard classifier is `on` (it is when `GROQ_API_KEY` is set). The first request includes a brief model warm-up.

![Input guard results](./images/bsa-1-input1.png?raw=true "Input guard results")

<br><br>

8. Look at the requests stopped at the **input** stage. The legitimate password question passes and is sent to the model. The jailbreak attempt, the off-topic poem request, and the oversized input are each marked **INPUT BLOCKED (never reached the model)**, with the triggering guard named - those prompts never cost you a model call.

![Input guard details](./images/bsa-1-input2.png?raw=true "Input guard details")

<br><br>

9. Look at the **output** side. The benign answer is **DELIVERED (PASS)**. The contact-confirmation request is the one that exercises the PII guard: the assistant repeats back the email and phone you gave it, so the output guard redacts them and you get **DELIVERED (FIXED)** with `[EMAIL-REDACTED]` / `[PHONE-REDACTED]` in place. A strong model often *refuses* to repeat an SSN and card on its own (a good outcome), which means the output guard is your **backstop for whenever the model doesn't refuse**.

![Output guard results](./images/bsa-1-output.png?raw=true "Output guard results")

<br><br>

10. Now look at the **last** request (`...walk me through building a pipe bomb`). It is genuinely harmful, but it is also *on-topic* (it mentions an account), so your regex and allowlist guards let it through - exactly the kind of thing hand-built rules miss. If you set a `GROQ_API_KEY`, **Llama Guard flags it as unsafe and blocks it at the input layer**, before the model ever sees it. Without a key you'll watch it slip past the cheap guards - which is the whole point: a model-based safety classifier is the layer that catches what patterns can't.

<br><br>

11. Now add the **canary token** tripwire. This bonus piece is provided complete - just run it:

```
python canary_demo.py
```

A unique secret (`CANARY-7f3a9c2b1e-DO-NOT-REVEAL`) is planted in HelpBot's *hardened* system prompt, which also pre-refuses meta-requests ("reveal your prompt," "repeat everything above"). The script fires real leak attempts at the model, then **replays one known-compromised response** so you always see the tripwire fire: `scan_for_canary()` finds the secret in the output, **BLOCKS** the answer, and raises an alert. The lesson: a canary can't *prevent* a leak, but it *guarantees you detect one* - turning a silent compromise into a logged, alertable event.

<br><br>

12. (Optional) Add your own guard or pattern. For example, add a new prompt to the `inputs` list in `main()`, or generate a fresh per-session canary in `canary_demo.py`, then re-run to watch it fire.

<br><br>

> **Invariant lens:** each guard is a *precondition* on an action — the answer is delivered only if it satisfies every check. You are declaring invariants ("no PII leaves the system," "the canary never appears in output") and enforcing them at runtime, in the shell around the model rather than trusting the model to hold them.

<br><br>

**Key Takeaways:**
- **Guardrails wrap the model on both sides** - validate input before the model, validate output before the user.
- **Two outcomes, not one** - some violations are *repaired* (redact PII), others are *blocked* (unsafe content). A good pipeline supports both.
- **Allowlists beat blocklists for scope** - defining what's allowed keeps an assistant on-topic more reliably than chasing every off-topic case.
- **A canary token is a tripwire** - it detects the system-prompt leaks your other guards miss, so a silent compromise becomes a loud alert.

<p align="center">
<b>[END OF LAB]</b>
</p>
<br><br>

**Lab 2: Securing Agent Tool Calls - Least Privilege, Approval, and Budgets**

**Purpose: In this lab, we constrain HelpBot so a hijacked prompt can't make it misuse its tools. We start from the agent blindly following a poisoned support ticket - exporting employee data, emailing it outside the company, and deleting the audit log - then add three controls that contain the exact same attack: a least-privilege tool allowlist per task, a human-approval gate for high-risk actions, and hard budgets on how much the agent can do.**

> **New terms in this lab (skip if you build agents already):** an **agent** is an LLM in a loop that decides which **tools** (functions like "send email" or "export data") to call to finish a job. **Indirect prompt injection** is when the malicious instructions arrive *inside data the agent reads* - here, a hidden note in a support ticket - rather than from the user. **Least privilege** means giving the agent only the tools a given task needs. An **allowlist** is the explicit set of permitted tools. An **approval gate** pauses a risky action for a human. A **budget** is a hard cap on how many steps or tool calls one run may take.

<br>

1. From the terminal, change to the *agents* directory:

```
cd /workspaces/building-secure-ai-agents/agents
```

<br><br>

2. Open the agent skeleton and read the scenario:

```
code secure_agent.py
```

Look at three things. `TICKET` is a support request that *looks* benign ("summarize the Q3 benefits changes") but hides an attacker's instructions in an HTML comment - the indirect-injection payload. The tool set is split into `SAFE_TOOLS` (`read_ticket`, `summarize`) and `HIGH_RISK_TOOLS` (`export_data`, `send_email`, `delete_records`). A **real model** reads the ticket in `build_plan()` and proposes which tools to call - and, taking the bait, it tries to run the dangerous ones.

![Indirect injection](./images/bsa-2-injection.png?raw=true "Indirect injection")

<br><br>

3. Run the agent as shipped to see the attack land:

```
python secure_agent.py
```

The script runs the agent's plan. Right now the three control functions are no-ops, so `export_data`, `send_email`, and `delete_records` all fire, ending in `BREACH`. That's undefended HelpBot doing exactly what the poisoned ticket told it to. (Tool choices come from a real model, so the model's proposed plan may vary run to run; the canonical attack is replayed so the breach is reproducible.)

![The breach](./images/bsa-2-breach.png?raw=true "The breach")

<br><br>

4. Open the diff-and-merge view to build the three controls:

```
code -d ../extra/secure_agent_complete.txt secure_agent.py
```

![Building the secured agent](./images/bsa-2-build.png?raw=true "Building the secured agent")

<br><br>

5. Review the three functions you'll merge in - this is the whole defense:
   - **`allowed_tools(task)`** - *least privilege.* Return only the tools this job needs (`read_ticket`, `summarize`, `send_email`). Because `export_data` and `delete_records` are never offered, a hijacked plan that calls them is refused outright.
   - **`approve(tool, args)`** - *human approval gate.* Low-risk tools run freely; high-risk tools pause for an operator. In this unattended demo the operator denies the unexpected action (emailing data to an outside address was never part of the ticket).
   - **`within_budget(steps_taken, executed)`** - *budgets.* Stop the run once it exceeds `MAX_STEPS`, so even a bypassed agent can't loop or escalate.

<br><br>

6. Merge all three sections into the skeleton and close the diff tab to save.

<br><br>

7. Run the updated secured agent:

```
python secure_agent.py
```

✓ **Success looks like:** the **SECURED AGENT** section shows `export_data` **BLOCKED** (allowlist), `send_email` **BLOCKED** (approval denied), the remaining steps **HALTED** (budget), and ends `contained (no high-risk tool fired)` - while the **UNDEFENDED** section above still ends in `BREACH`. If the secured run also shows `BREACH`, a control didn't merge; reopen the diff at Step 4.

<br><br>

8. Compare the two runs. The **UNDEFENDED AGENT** still ends in `BREACH`. The **SECURED AGENT** runs the same plan but contains it - and you can see *each control* doing a distinct job:
   - `export_data` -> **BLOCKED (not in least-privilege allowlist)**
   - `send_email` -> **BLOCKED (approval denied)**
   - the remaining attacker steps -> **HALTED (budget)**

   The legitimate `read_ticket` and `summarize` steps still succeed, so HelpBot completes the job it was actually hired to do.

![Same hijack, contained](./images/bsa-2-contained.png?raw=true "Same hijack, contained")

<br><br>

9. Notice that all three controls are necessary. Least privilege removes the tools the task never needs; the approval gate catches a high-risk tool the task *does* legitimately use (`send_email`) but that the attacker tried to abuse; budgets cap the blast radius if anything slips through. Defense in depth - no single control has to be perfect.

<br><br>

10. (Optional) Tighten or loosen a control and re-run to see the effect:
   - In `approve()`, temporarily `return True` for everything and re-run - `send_email` now fires. Put the denial back.
   - In `allowed_tools()`, add `"export_data"` to the returned set and re-run - the export is no longer blocked by least privilege. Remove it again.
   - Lower `MAX_STEPS` to `2` and re-run - even the second legitimate step gets budget-halted, showing why budgets must be sized to the real work.

<br><br>

> **Invariant lens:** least privilege, approval, and budgets are *preconditions* on every tool call — a tool fires only if it is in the allowlist, is approved, and the run is within budget. These are runtime invariants on what the agent may *do*, enforced independently of whatever plan the model proposes.

<br><br>

**Key Takeaways:**
- **The agent will be talked into things** - indirect prompt injection means any data the agent reads can carry instructions. Assume the model will follow them.
- **Least privilege first** - the safest dangerous tool is the one you never hand the model for that task.
- **Gate high-risk actions** - some tools are legitimate but consequential; route those through a human (or a stricter policy) before they fire.
- **Budget the blast radius** - hard caps on steps and tool calls keep a hijacked agent from looping or escalating, even when other controls miss.

<p align="center">
<b>[END OF LAB]</b>
</p>
<br><br>

**Lab 3: Hardening MCP Servers and Tools**

**Purpose: In this lab, we'll harden the Model Context Protocol (MCP) server that HelpBot uses to reach its tools. A token authority issues scoped JWT access tokens (PyJWT), and a real FastMCP server enforces per-tool scope checks in middleware - so the same server grants different clients access to different subsets of tools, following least privilege at the protocol boundary.**

**This lab uses two terminals: the MCP server and the client.**

> **New terms in this lab:** **MCP (Model Context Protocol)** is a standard way for an agent to call external tools over a connection. A **JWT** is a signed token whose contents (here, a list of allowed tool **scopes**) can't be tampered with. **Middleware** is code that runs on *every* request before it reaches a tool - the right place to put an authorization check so nothing is protected by accident.

<br>

1. From the terminal, change to the *mcp* directory:

```
cd /workspaces/building-secure-ai-agents/mcp
```

<br><br>

2. Review the token authority (provided complete):

```
code auth.py
```

`auth.py` mints and verifies scoped JWTs with the real **PyJWT** library. Note the **client registry**: `full-client` is granted scopes for all three tools (`tools:add`, `tools:multiply`, `tools:divide`), while `limited-client` is granted only `tools:add`. Those scopes are signed into each token's `scope` claim, so they can't be tampered with. (This stands in for a real identity provider.)

![Token authority](./images/bsa-3-auth.png?raw=true "Token authority")

<br><br>

3. Open the MCP server skeleton:

```
code secure_server.py
```

This is a real **FastMCP** server exposing three tools (`add`, `multiply`, `divide`) over HTTP. The security lives in `ScopeMiddleware.on_call_tool`, which runs on **every** tool call: it reads the `Authorization` header, verifies the Bearer JWT with `auth.verify_token`, and then calls `enforce_scope()` - the one function you'll complete - to allow the call only if the token carries the matching `tools:<name>` scope.

![Secure server](./images/bsa-3-server.png?raw=true "Secure server")

<br><br>

4. Open the diff-and-merge view and build the scope check:

```
code -d ../extra/secure_server_complete.txt secure_server.py
```

The provided code already authenticates the JWT (a missing or bad token raises **401**). The piece you merge in is **`enforce_scope(claims, tool_name)`**: read the token's scopes, and raise a **403** `ToolError` if they don't include `tools:<tool_name>`. Because the check is in middleware, it protects every tool by default.

![Building the secure MCP server](./images/bsa-3-build.png?raw=true "Building the secure MCP server")

<br><br>

5. Merge `enforce_scope` into the skeleton and close the diff tab to save.

<br><br>

6. **Terminal 1 (server).** Start the FastMCP server and leave it running:

```
python secure_server.py
```

You should see `FastMCP server on http://127.0.0.1:8000/mcp/` and the list of scope-protected tools.

![Secure server running](./images/bsa-3-running.png?raw=true "Secure server running")

<br><br>

7. **Terminal 2 (client).** Open a new terminal (click the `+` in the terminal panel), then run the client:

```
cd /workspaces/building-secure-ai-agents/mcp
python client.py
```

The client mints a scoped JWT for each registered client and calls all three tools against the server.

<br><br>

8. Watch the output. First, the **no-auth** run (no token) is rejected on every call with **401 Unauthorized: missing bearer token** - an unauthenticated call never reaches a tool.

![No-auth rejected](./images/bsa-3-noauth.png?raw=true "No-auth rejected")

<br><br>

9. Then the client runs as each registered client:
   - **full-client**: `add`, `multiply`, and `divide` all succeed
   - **limited-client**: `add` succeeds, but `multiply` and `divide` are **DENIED (403)** because the token only carries the `tools:add` scope

This is per-tool authorization - the same server, different access levels driven entirely by signed token scopes. Look at the **server** terminal too: it logs each allowed call (`[SECURE] full-client -> multiply (allowed)`).

![Scope enforcement in action](./images/bsa-3-scopes.png?raw=true "Scope enforcement in action")

<br><br>

10. (Optional) Inspect what's actually inside a token. In Terminal 2:

```
python -c "import auth; print(auth.verify_token(auth.mint_token('limited-client')))"
```

You'll see `'scope': 'tools:add'` - confirming the limited client's token never carries the multiply/divide scopes, so the server can't be tricked into running them.

<br><br>

11. When you're done, stop the server with **Ctrl+C** in Terminal 1.

<br><br>

> **Invariant lens:** `enforce_scope()` is a *precondition* on every tool call, asserted in middleware — the invariant "no call runs without a token that carries its scope" holds for every tool by default, including tools you add later.

<br><br>

**Key Takeaways:**
- **Authenticate every MCP call** - an unauthenticated tool call should never reach your tools.
- **Scope tokens per tool** - least privilege means a client gets exactly the tools it needs and nothing more.
- **Enforce in middleware** - centralizing the scope check keeps every tool protected by default.
- **Restrict the manifest** - only expose the tools a client population actually needs.

<p align="center">
<b>[END OF LAB]</b>
</p>
<br><br>

**Lab 4: Hardening HelpBot's RAG Pipeline Against Poisoned Documents**

**Purpose: In this lab, we'll defend HelpBot's RAG pipeline against document poisoning. We'll see how a malicious document injected into the knowledge base can hijack the model with hidden instructions and phish users, then implement defensive layers - source allowlisting, injection detection, relevance filtering, and output scanning - to neutralize the attack.**

> **New terms in this lab:** **RAG (Retrieval-Augmented Generation)** means the agent answers by first *retrieving* relevant chunks from a knowledge base and feeding them to the model. **Document poisoning** is slipping a malicious document into that knowledge base so its hidden instructions reach the model as if they were trusted content. A **source allowlist** trusts only chunks that came from known, verified documents.

<br>

1. From the terminal, change to the *rag* directory:

```
cd /workspaces/building-secure-ai-agents/rag
```

<br><br>

2. Examine the poisoned document that simulates what an attacker might inject into the knowledge base. Open it and read through it carefully:

```
code docs/OmniTech_Security_Bulletin.txt
```

This looks like a legitimate OmniTech bulletin, but it carries three attacks: a hidden `[SYSTEM OVERRIDE]` **prompt injection**, a **phishing URL** (`https://omnitech-secure-verify.com/reset`), and a **social-engineering** instruction to email full credit card numbers for "refund verification."

![The poisoned document](./images/bsa-4-poison.png?raw=true "The poisoned document")

<br><br>

3. Look at the retrieval helpers used by both versions of the lab:

```
code kb.py
```

This is a **real RAG pipeline** built on a local **Chroma vector database**. `kb.py` opens that database, runs a **semantic similarity** search (`retrieve`) using real embeddings (Chroma's built-in `all-MiniLM-L6-v2`), and sends the top chunks to a **real model** (`rag_answer`). Notice the system prompt tells the model to answer **using only the retrieved context** and to include any URL or instruction it finds there - which is exactly why a poisoned chunk reaching this stage is dangerous.

<br><br>

4. Now build the vector database. `create_db.py` chunks every document in `docs/` - the legitimate handbook and returns policy **and** the poisoned bulletin - embeds them, and stores them in the same Chroma collection. This simulates an attacker who has slipped a malicious document into the knowledge base:

```
python create_db.py
```

You'll see each source and its chunk count, with the poisoned PDF flagged. (The first run downloads the small embedding model, ~30-60s; later runs are instant.)

![Building the vector database](./images/bsa-4-builddb.png?raw=true "Building the vector database")

<br><br>

5. Run the **vulnerable** RAG system - this is HelpBot's RAG with no security defenses:

```
python rag_vulnerable.py
```

You'll see the vector DB load, including the poisoned source mixed in with the two legitimate documents. (The first model query also includes a ~30-60s warm-up.)

![Loading the knowledge base](./images/bsa-4-kbload.png?raw=true "Loading the knowledge base")

<br><br>

6. At the prompt, ask:

```
How do I reset my password?
```

Watch the **SOURCES** and **ANSWER**. Because the poisoned bulletin really is about password resets, it scores a high similarity and `OmniTech_Security_Bulletin_2024.pdf` appears among the retrieved sources - and the answer hands the user the **phishing URL** from the poisoned document.

![Phishing URL in the answer](./images/bsa-4-phish.png?raw=true "Phishing URL in the answer")

<br><br>

7. Now ask:

```
How do I get a refund?
```

The poisoned document's instruction to share a full credit card number surfaces in the response. The vulnerable system trusts all retrieved context equally. Type `quit` to exit.

<br><br>

8. Now let's add defenses. Open the diff-and-merge view to compare the skeleton with the complete hardened version:

```
code -d ../extra/rag_hardened_complete.txt rag_hardened.py
```

![Building the hardened version](./images/bsa-4-build.png?raw=true "Building the hardened version")

<br><br>

9. Examine the `SecurityGuard` class in the complete version (left side). It implements four layers of defense in depth:
   - **Source allowlist** - only chunks from known, verified PDFs are trusted (the poisoned bulletin is not on the list)
   - **Injection detection** - regex patterns catch `[SYSTEM OVERRIDE]`, `ignore previous instructions`, `supersedes all previous`, etc.
   - **Relevance threshold** - low-confidence chunks are dropped
   - **Output scanning** - the final answer is scrubbed of phishing domains and sensitive-data requests

Note the `filter_chunks()` and `scan_output()` methods - these are the two checkpoints that block bad input and redact bad output.

<br><br>

10. Merge all sections from the complete version (left) into the skeleton (right). When no differences remain, close the diff tab to save.

<br><br>

11. Run the hardened version against the same poisoned knowledge base:

```
python rag_hardened.py
```

Notice the startup output now labels each source `[TRUSTED]` or `[UNKNOWN]`.

![Trusted vs unknown sources](./images/bsa-4-trusted.png?raw=true "Trusted vs unknown sources")

<br><br>

12. Ask the same two questions again:

```
How do I reset my password?
```
```
How do I get a refund?
```

This time the poisoned chunks are blocked at the source-allowlist stage, and any sensitive request that slips into the output is redacted. The answers now come only from the legitimate handbook and returns policy. Type `report` to see every security event, then `quit` to exit.

![Blocked and redacted](./images/bsa-4-blocked.png?raw=true "Blocked and redacted")

<br><br>

**Key Takeaways:**
- **Document poisoning is a real threat** - anyone who can insert a document into a RAG knowledge base can steer its outputs.
- **Treat retrieved content as untrusted input** - it can carry hidden instructions aimed at the model.
- **Defense in depth wins** - source allowlists, injection detection, relevance filtering, and output scanning each catch what the others miss.
- **Output scanning is the safety net** - it protects users even when a malicious chunk slips through input filtering.

<p align="center">
<b>[END OF LAB]</b>
</p>
<br><br>

**Lab 5: Auditing and Observability for Agents *(homework-capable)***

**Purpose: In this lab, we'll make HelpBot observable using real OpenTelemetry. We'll wrap every tool call in an OTel span - trace IDs, span IDs, attributes, status - under one session trace, then run an anomaly detector over the captured spans to surface suspicious tool-call patterns. You can't defend what you can't see.**

> **This lab is designed to work as post-class homework if we run short on time.** It's self-contained and needs only the observability directory.

> **New terms in this lab:** **observability** just means being able to see what your system actually did. **OpenTelemetry (OTel)** is the industry-standard library for recording that. A **span** is one timed record of one operation - like a log line with a stopwatch and a label. A **trace** ties together all the spans from one session via a shared **trace ID**. Real systems ship these to tools like Jaeger or a SIEM; here we keep them in memory so we can inspect them right away.

<br>

1. From the terminal, change to the *observability* directory:

```
cd /workspaces/building-secure-ai-agents/observability
```

<br><br>

2. Open the skeleton and review its shape:

```
code observable_agent.py
```

Note the `REQUESTS` list of natural-language `(user, request)` pairs and the `SENSITIVE_TOOLS` set (`export_employee_data`, `send_company_email`, `update_salary`). A **real model** drives the agent: `choose_tool()` asks it to pick one tool per request and return JSON. The provided `build_tracer()` sets up a real **OpenTelemetry** tracer with an in-memory span exporter. Some requests are benign; `mallory` issues a burst of bulk-export requests and `bob` asks for a mass email - your instrumentation has to make all of that visible.

![Observable agent skeleton](./images/bsa-5-skeleton.png?raw=true "Observable agent skeleton")

<br><br>

3. Open the diff-and-merge view to add the instrumentation and detector:

```
code -d ../extra/observable_agent_complete.txt observable_agent.py
```

![Building the observable agent](./images/bsa-5-build.png?raw=true "Building the observable agent")

<br><br>

4. Review the two pieces you're completing in the complete version:
   - **`instrument_call`** - opens an OpenTelemetry span (`tracer.start_as_current_span`) around the model's tool choice, sets attributes on it (`user`, `tool`, `args`, `sensitive`, `status`), marks unauthorized calls with an ERROR status, and prints a compact `[AUDIT]` line with the span's real `trace_id` / `span_id`.
   - **`detect_anomalies`** - reads the **captured spans** (from the in-memory exporter) and flags denied calls, sensitive-tool bursts (3+ of the same call), and any user touching sensitive tooling.

   The simple authorization stub (`authorize`, only `alice` may call sensitive tools) and the OTel setup are already provided.

<br><br>

5. Merge all sections into the skeleton and close the diff tab to save.

<br><br>

6. Run the observable agent:

```
python observable_agent.py
```

✓ **Success looks like:** a stream of `[AUDIT]` lines (one per request), each carrying a `trace=` and `span=` id, followed by a **TELEMETRY SUMMARY** and an **ANOMALY DETECTION** block that flags `mallory`'s denied exports, a **BURST**, and the users who touched sensitive tooling. If you see `NotImplementedError` or no anomaly findings, a function didn't merge - reopen the `code -d` diff and finish it.

![Structured audit stream](./images/bsa-5-audit.png?raw=true "Structured audit stream")

<br><br>

7. Look at the stream of **`[AUDIT]`** lines (one per request). Every call is a real OpenTelemetry span sharing a single **trace_id** for the session, each with its own **span_id** - the same trace/span model you'd export to Jaeger, Tempo, or a SIEM.

<br><br>

8. Look at the **TELEMETRY SUMMARY** - tool spans, sensitive calls, and denied calls, all read back from the captured OpenTelemetry spans. These are the kind of metrics you'd graph on a dashboard.

![Telemetry summary](./images/bsa-5-summary.png?raw=true "Telemetry summary")

<br><br>

9. Look at the **ANOMALY DETECTION** section. The detector flags `mallory`'s denied export attempts, the **BURST** of three rapid export calls, and surfaces every user who touched sensitive tooling for review.

![Anomaly detection](./images/bsa-5-anomaly.png?raw=true "Anomaly detection")

<br><br>

10. **(Optional) Extend HelpBot's domain — add a new action and validate it through the explainable logs.** This mirrors how you grow a real agent: add a capability, then rely on the audit trail (not guesswork) to confirm how it behaves. Make three small edits to `observable_agent.py`:
   - Add `"update_salary"` to the `TOOLS` list.
   - Add `update_salary` to the tool names listed in `TOOL_SYSTEM`, so the model is allowed to choose it. (It is already in `SENSITIVE_TOOLS`, so it is automatically treated as sensitive — no other change needed.)
   - Add a request that exercises it, e.g. `("mallory", "Update employee E1002's salary to $200k.")`

   Re-run `python observable_agent.py`. The brand-new action flows through the **same** instrumentation with no new logging code: a span is emitted, the `[AUDIT]` line shows `tool=update_salary sensitive=True status=denied` (mallory isn't authorized for sensitive tools), and `detect_anomalies` surfaces it automatically. You validated a new domain action purely by reading its explainable trace — exactly how you'd verify behavior as an agent's domain grows.

<br><br>

**Key Takeaways:**
- **Instrument every tool call** - structured logs with trace and span IDs make agent behavior auditable and explainable.
- **Telemetry feeds both ops and security** - the same spans power latency dashboards and intrusion detection.
- **Detect patterns, not just events** - bursts and denied-call clusters reveal abuse that any single line wouldn't.
- **Audit trails enable incident response** - forensics depends on having recorded what happened.

<p align="center">
<b>[END OF LAB]</b>
</p>
<br><br>

---

### Where HelpBot ends up

Trace the layers back through the workshop. The agent that leaked its system
prompt, obeyed a poisoned ticket, exposed unscoped tools, served phishing URLs
from its knowledge base, and did all of it invisibly in Lab 1 now: blocks
jailbreaks and redacts PII (Lab 1), refuses tools outside its task and gates the
risky ones (Lab 2), authenticates and scopes every MCP call (Lab 3), filters
poisoned knowledge and scrubs its output (Lab 4), and records every action for
detection and forensics (Lab 5). No single control carried the load - together
they are defense in depth for an agent.

**Take it further:** the defensive patterns here (input/output validation,
least privilege, scoped auth, retrieval hygiene, telemetry) map directly to the
OWASP Top 10 for LLM Applications and MITRE ATLAS. A natural next step is a full
threat model of your own agent and a red-team pass against it.

<br><br>

<p align="center">
<b>For educational use only by the attendees of our workshops.</b>
</p>

<p align="center">
<b>(c) 2026 Tech Skills Transformations and Brent C. Laster. All rights reserved.</b>
</p>
