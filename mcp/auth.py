"""
Lab 5 - Token authority + client registry (provided complete).

Mints and verifies scoped JWT access tokens with PyJWT. Each client is
registered with the exact per-tool scopes it is allowed. This stands in for a
real OAuth/identity provider; in production you'd use asymmetric keys and a
hardened issuer.
"""
import jwt   # PyJWT

# HMAC signing secret (demo only). >= 32 bytes to satisfy PyJWT for HS256.
SECRET = "omnitech-workshop-demo-signing-secret-change-me"
ALGO = "HS256"

# Client registry: which per-tool scopes each client is granted.
CLIENTS = {
    "full-client":    ["tools:add", "tools:multiply", "tools:divide"],
    "limited-client": ["tools:add"],
}


def mint_token(client_id):
    """Issue a signed JWT whose 'scope' claim lists the client's tool scopes."""
    if client_id not in CLIENTS:
        raise ValueError(f"unknown client {client_id}")
    payload = {"sub": client_id, "scope": " ".join(CLIENTS[client_id])}
    return jwt.encode(payload, SECRET, algorithm=ALGO)


def verify_token(token):
    """Verify the signature and return the claims (raises on tampering/expiry)."""
    return jwt.decode(token, SECRET, algorithms=[ALGO])
