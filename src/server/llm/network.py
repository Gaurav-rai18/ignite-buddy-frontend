"""Network settings for reaching the org Ollama server: auth header, proxy (Zscaler), TLS trust, timeouts.

Everything ends up as plain httpx keyword arguments, which ChatOllama / OllamaEmbeddings / ollama.Client
forward to httpx via `client_kwargs`.
"""
import ssl
from urllib.parse import urlparse

import httpx

from server import config


def _tls_context():
    """Return an ssl.SSLContext when custom trust is configured, else None (httpx default = certifi + SSL_CERT_FILE).

    Zscaler re-signs HTTPS traffic with its own root CA. Python does not trust that CA by default, so you get
    CERTIFICATE_VERIFY_FAILED. Two fixes (pick one):
      OLLAMA_USE_SYSTEM_CERTS=1       trust the OS certificate store (where IT already installed the Zscaler root)
      OLLAMA_CA_BUNDLE=C:\\path\\zscaler_root.pem   trust this PEM file in addition to the normal CAs
    """
    if not config.LLM_USE_SYSTEM_CERTS and not config.LLM_CA_BUNDLE:
        return None
    if config.LLM_USE_SYSTEM_CERTS:
        try:
            import truststore
        except ImportError as e:
            raise RuntimeError("OLLAMA_USE_SYSTEM_CERTS=1 needs the 'truststore' package: pip install truststore") from e
        ctx = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    else:
        import certifi
        ctx = ssl.create_default_context(cafile=certifi.where())
    if config.LLM_CA_BUNDLE:
        ctx.load_verify_locations(cafile=config.LLM_CA_BUNDLE)   # raises FileNotFoundError if the path is wrong
    return ctx


def auth_headers() -> dict:
    if not config.LLM_API_KEY:
        return {}
    # DEV ONLY: a key on the trainee machine is readable by the trainee. Production should send the user's
    # login token (short-lived) instead of a shared model API key.
    if config.LLM_AUTH_HEADER.lower() == "authorization":
        return {"Authorization": f"Bearer {config.LLM_API_KEY}"}
    return {config.LLM_AUTH_HEADER: config.LLM_API_KEY}


def httpx_kwargs() -> dict:
    """Keyword arguments for the underlying httpx client."""
    kw: dict = {
        "timeout": httpx.Timeout(config.LLM_TIMEOUT, connect=config.LLM_CONNECT_TIMEOUT),
        "headers": auth_headers(),
    }
    # ---- TLS ----
    if urlparse(config.LLM_BASE_URL).scheme == "https":
        if not config.LLM_VERIFY_SSL:
            kw["verify"] = False                      # DEV ONLY: accepts any certificate
        else:
            ctx = _tls_context()
            if ctx is not None:
                kw["verify"] = ctx
    # ---- proxy ----
    p = config.LLM_PROXY.strip()
    if p.lower() in ("none", "direct", "off"):
        kw["trust_env"] = False                       # ignore HTTP(S)_PROXY / system proxy: connect directly
    elif p and p.lower() not in ("env", "system"):
        kw["proxy"] = p                               # explicit proxy, e.g. http://proxy.example.com:8080
    # else: default httpx behaviour = HTTP_PROXY / HTTPS_PROXY / NO_PROXY env vars (and the Windows system proxy)
    return kw


def describe() -> dict:
    """Human-readable view of the effective settings (never includes the API key)."""
    p = config.LLM_PROXY.strip()
    if config.LLM_USE_SYSTEM_CERTS:
        tls = "OS certificate store"
    elif config.LLM_CA_BUNDLE:
        tls = f"default CAs + {config.LLM_CA_BUNDLE}"
    else:
        tls = "default CAs (certifi / SSL_CERT_FILE)"
    if not config.LLM_VERIFY_SSL:
        tls = "VERIFICATION DISABLED (dev only)"
    return {
        "base_url": config.LLM_BASE_URL,
        "auth": f"{config.LLM_AUTH_HEADER} header set" if config.LLM_API_KEY else "none",
        "tls_trust": tls if urlparse(config.LLM_BASE_URL).scheme == "https" else "n/a (http)",
        "proxy": "direct (proxy ignored)" if p.lower() in ("none", "direct", "off")
                 else (p if p and p.lower() not in ("env", "system") else "from environment / system settings"),
        "timeout_s": f"read {config.LLM_TIMEOUT}, connect {config.LLM_CONNECT_TIMEOUT}",
    }
