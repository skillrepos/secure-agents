"""
Shared output helpers for the workshop labs (provided complete).

One place for the colour scheme and the "press Enter" pacing every lab uses:

    BLUE   the request / prompt / what is being asked
    GREEN  it passed, ran, or was delivered
    RED    it was blocked, denied, or failed

Colours switch themselves off when output is piped to a file, so redirecting
a run still produces clean plain text.
"""
import sys

_TTY = sys.stdout.isatty()
BLUE, GREEN, RED, DIM, RESET = (
    ("\033[94m", "\033[92m", "\033[91m", "\033[2m", "\033[0m") if _TTY else ("",) * 5
)


def say(color, text):
    """Print one line in a colour."""
    print(f"{color}{text}{RESET}")


def blue(text):  say(BLUE, text)
def green(text): say(GREEN, text)
def red(text):   say(RED, text)


def pause(what="the next section"):
    """Wait for Enter so each section can be read before the next one."""
    try:
        input(f"{DIM}--- press Enter for {what} ---{RESET}")
    except EOFError:
        pass
    print()
