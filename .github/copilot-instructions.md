# Copilot / AI Assistant Instructions

GitHub Copilot and other inline AI assistants are **intentionally disabled** in
this workshop environment (see `.devcontainer/devcontainer.json`). The labs are
hands-on: you learn the defensive patterns by building them yourself in the
diff-and-merge steps, not by autocompleting them.

If you want an AI assistant to *explain* a file (not write it), use this prompt
template in chat:

> Explain this app / file for me, structured as:
> 1. **What it does** - one sentence.
> 2. **High-level flow** - the main steps in order.
> 3. **Key building blocks** - the important functions/classes and each one's job.
> 4. **Data flow** - what data moves where (user input -> guards -> model -> output).
> 5. **Where the security lives** - the specific lines that enforce a control.
> 6. **Safe experiments** - small changes I can make to see behavior change.
> 7. **Debug checklist** - what to check first if it doesn't run.

Keep the focus on understanding *why* each control exists and *what attack it
stops* - that is the point of the workshop.
