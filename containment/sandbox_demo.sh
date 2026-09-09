#!/usr/bin/env bash
# Containment demo (provided complete) - the fourth leg the labs do not build.
#
# Runs the SAME hijacked-agent code twice:
#   1. unconfined       - it reads the data, steals the key, and phones home
#   2. inside a sandbox - the environment refuses all three
#
# The sandbox is three ordinary Linux features - no Docker, no root:
#   unshare -n   private network namespace                     -> no egress
#   unshare -m   private mount namespace + empty tmpfs over the
#                data directory                                -> filesystem scope
#   env -i       empty environment                             -> credentials out of reach
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo
echo "=== 1. UNCONFINED - the agent's own code is the only thing in its way ==="
DEMO_API_KEY=gsk_live_abc123 python3 "$HERE/exfil_attempt.py"

echo
read -rp $'\033[2m--- press Enter to run the exact same code inside a sandbox ---\033[0m '
echo
echo "=== 2. SANDBOXED - same code, contained by the environment ==="

if ! unshare -rmn true 2>/dev/null; then
    echo "  (this machine does not allow unprivileged namespaces - skipping."
    echo "   The same three controls are what a Docker/gVisor sandbox gives you.)"
    exit 0
fi

env -i PATH=/usr/local/bin:/usr/bin:/bin SANDBOXED=1 HERE="$HERE" \
    unshare -rmn sh -c 'mount -t tmpfs none "$HERE/company_data" && exec python3 "$HERE/exfil_attempt.py"'

echo
echo "Nothing inside the agent changed. The environment around it did."
