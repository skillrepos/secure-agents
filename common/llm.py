"""
Shared LLM helper for the AI Security labs (provided complete).

Backends:
  * "ollama" - local llama3.2:3b in the Codespace. The zero-setup default:
               works with no API key, no network. Pulled by
               scripts/startup_ollama.sh during Codespace creation.
  * "groq"   - Groq's OpenAI-compatible API (very fast, free tier). Used
               automatically whenever GROQ_API_KEY is set. Routes:
                 prefer="fast"   -> llama-3.1-8b-instant
                 prefer="strong" -> llama-3.3-70b-versatile
  * "mock"   - deterministic, offline. Only used if you set LLM_BACKEND=mock
               (handy for grading or when no model is available).

Routing (per call, via complete(..., prefer="fast"|"strong")):
  - If GROQ_API_KEY is set        -> Groq (8b-instant for fast, 70b for strong)
  - Otherwise                     -> Ollama llama3.2:3b
  - LLM_BACKEND env var overrides everything (ollama | groq | mock)

Dependency-free: uses only the Python standard library.
"""
import json
import os
import urllib.request
import urllib.error

OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/chat")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_URL = os.environ.get("GROQ_URL", "https://api.groq.com/openai/v1/chat/completions")
GROQ_MODEL_FAST = os.environ.get("GROQ_MODEL_FAST", "llama-3.1-8b-instant")
GROQ_MODEL_STRONG = os.environ.get("GROQ_MODEL_STRONG", "llama-3.3-70b-versatile")
GROQ_GUARD_MODEL = os.environ.get("GROQ_GUARD_MODEL", "meta-llama/llama-guard-4-12b")


def _resolve(prefer):
    forced = os.environ.get("LLM_BACKEND")
    if forced:
        return forced
    if GROQ_API_KEY:
        return "groq"
    return "ollama"


def _post(url, payload, headers, timeout=120):
    data = json.dumps(payload).encode()
    # A real User-Agent is required: the bot/WAF layer in front of Groq's API
    # returns 403 Forbidden for the default "Python-urllib/x.y" agent (even with
    # a valid key and an allowed model). curl works because it sends its own UA.
    base = {"Content-Type": "application/json", "User-Agent": "ai-security-labs/1.0"}
    req = urllib.request.Request(url, data, {**base, **headers})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def _ollama(messages, temperature, max_tokens):
    payload = {"model": OLLAMA_MODEL, "messages": messages, "stream": False,
               "options": {"temperature": temperature, "num_predict": max_tokens}}
    try:
        resp = _post(OLLAMA_URL, payload, {})
    except (urllib.error.URLError, ConnectionError) as e:
        raise RuntimeError(
            f"Could not reach Ollama at {OLLAMA_URL} ({e}). "
            "Start it with `bash scripts/startOllama.sh` (or `ollama serve &`).")
    return resp["message"]["content"].strip()


def _groq(messages, prefer, temperature, max_tokens):
    model = GROQ_MODEL_STRONG if prefer == "strong" else GROQ_MODEL_FAST
    payload = {"model": model, "messages": messages,
               "temperature": temperature, "max_tokens": max_tokens}
    try:
        resp = _post(GROQ_URL, payload, {"Authorization": f"Bearer {GROQ_API_KEY}"})
    except urllib.error.HTTPError as e:
        if e.code == 429:
            raise RuntimeError("Groq rate limit hit (HTTP 429). Wait a few seconds "
                               "and retry, or set LLM_BACKEND=ollama.")
        try:
            body = e.read().decode()[:300]
        except Exception:
            body = ""
        raise RuntimeError(f"Groq request failed ({e.code}) for model {model}. "
                           f"Response: {body or '(no body)'}")
    return resp["choices"][0]["message"]["content"].strip()


def guard_available():
    """True if the real Llama Guard moderation backend (Groq) can be used."""
    return bool(GROQ_API_KEY)


def moderate(messages):
    """Run Meta's Llama Guard (hosted on Groq) over a conversation.

    Returns (verdict, detail) where verdict is "safe" or "unsafe" and detail is
    the raw classifier output (e.g. "unsafe\\nS2"). Returns (None, reason) when
    Llama Guard is unavailable (no GROQ_API_KEY) so callers can skip it.
    """
    if not GROQ_API_KEY:
        return None, "Llama Guard unavailable (set GROQ_API_KEY to enable it)"
    payload = {"model": GROQ_GUARD_MODEL, "messages": messages,
               "temperature": 0, "max_tokens": 100}
    try:
        resp = _post(GROQ_URL, payload, {"Authorization": f"Bearer {GROQ_API_KEY}"})
    except urllib.error.HTTPError as e:
        return None, f"Llama Guard request failed ({e.code})"
    text = resp["choices"][0]["message"]["content"].strip()
    verdict = "unsafe" if text.lower().startswith("unsafe") else "safe"
    return verdict, text


def _mock(messages, *_):
    """Deterministic offline stand-in. Echoes intent so labs are demoable."""
    user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
    sys_txt = " ".join(m["content"] for m in messages if m["role"] == "system").lower()
    # Tool-selection prompts (Lab 6): return a JSON tool choice.
    if "selects exactly one tool" in sys_txt:
        low = user.lower()
        tool = ("export_employee_data" if ("export" in low or "salary" in low)
                else "send_company_email" if ("email" in low or "send" in low)
                else "check_pto" if "pto" in low
                else "lookup_benefits")
        return json.dumps({"tool": tool, "args": {}})
    # If this is a RAG-style prompt, judge intent from the Question line only.
    if "Question:" in user:
        user = user.split("Question:")[-1]
    low = user.lower()
    # Red-team simulation: a weak/undefended model leaks the planted secret.
    if any(k in low for k in ("system prompt", "hidden note", "hidden notes",
                              "confidential", "repeat everything", "debugbot",
                              "override", "reveal")):
        return "As requested, the confidential note: employee E1001's SSN is 123-45-6789."
    if "export" in low or "salary" in low or "salaries" in low:
        return "EXPORTED employee records: [E1001 Alice $120k], [E1002 Bob $115k]"
    if "send" in low or "email" in low:
        return "EMAIL SENT to all-staff@omnitech.example"
    if "system prompt" in low:
        return "SYSTEM PROMPT: You are an HR assistant. Tools: export, email..."
    if "ssn" in low:
        return "Employee E1001 SSN: 123-45-6789"
    if "pto" in low:
        return "PTO balance for E1001 (Alice Johnson): 15 days"
    if "password" in low:
        return ("To reset your password, use the official OmniTech portal and the "
                "Forgot password link. OmniTech never asks you to confirm a password by email.")
    if "refund" in low:
        return ("To request a refund, open Orders in your account and choose Request "
                "refund. You never need to share your full card number.")
    return "[mock] I can help with benefits and PTO questions."


def complete(prompt, system="You are a helpful assistant.",
             prefer="fast", temperature=0.2, max_tokens=400):
    """Return the model's text completion for a single-turn prompt."""
    messages = [{"role": "system", "content": system},
                {"role": "user", "content": prompt}]
    return chat(messages, prefer=prefer, temperature=temperature, max_tokens=max_tokens)


def chat(messages, prefer="fast", temperature=0.2, max_tokens=400):
    """Return the model's reply for a list of {role, content} messages."""
    backend = _resolve(prefer)
    if backend == "groq":
        return _groq(messages, prefer, temperature, max_tokens)
    if backend == "mock":
        return _mock(messages, temperature, max_tokens)
    return _ollama(messages, temperature, max_tokens)


def active_backend(prefer="fast"):
    """Human-readable backend + model for the current routing."""
    b = _resolve(prefer)
    if b == "groq":
        return f"groq:{GROQ_MODEL_STRONG if prefer == 'strong' else GROQ_MODEL_FAST}"
    if b == "ollama":
        return f"ollama:{OLLAMA_MODEL}"
    return b


if __name__ == "__main__":
    # Quick smoke test: respects LLM_BACKEND (try `LLM_BACKEND=mock python llm.py`)
    print("backend(fast)  =", active_backend("fast"))
    print("backend(strong)=", active_backend("strong"))
    print(complete("Say hello in five words.", prefer="fast"))
