"""
The three things a hijacked agent actually tries to do (provided complete).

Lab 2's tools only PRINT what they would do - safe for a classroom, but it
also means a sandbox would have nothing to stop. This script does the real
thing: it reads real company data, reads a real credential out of the
environment, and opens a real network connection. Run it twice - once
normally, once inside the sandbox - and watch the same code get stopped by
the environment instead of by its own code.
"""
import os
import socket
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))
from labkit import blue, green, red

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "company_data", "employees.csv")


def attempt(label, fn):
    """Run one exfiltration step. GREEN = it got through. RED = the OS stopped it."""
    try:
        green(f"  {label:<30} -> REACHED: {fn()}")
    except Exception as e:
        red(f"  {label:<30} -> BLOCKED: {type(e).__name__}")


def read_company_data():
    return open(DATA).read().strip().splitlines()[1][:38] + " ..."


def read_credential():
    key = os.environ["DEMO_API_KEY"]           # KeyError once the env is stripped
    return f"DEMO_API_KEY={key[:8]}..."


def phone_home():
    s = socket.create_connection(("1.1.1.1", 80), timeout=4)
    s.close()
    return "opened a socket to the outside world"


blue(f"  ({'sandboxed' if os.environ.get('SANDBOXED') else 'unconfined'} run)")
attempt("1. export employee data", read_company_data)
attempt("2. steal the API credential", read_credential)
attempt("3. email it out (exfiltrate)", phone_home)
