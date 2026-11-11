"""Readable errors. The UI shows str(exception) to the trainee, so make it actionable (Zscaler/proxy aware)."""
import ssl

import httpx


class LLMError(RuntimeError):
    """The model server could not be used. The message says why and what to check."""


def _chain(exc: BaseException):
    seen = set()
    while exc is not None and id(exc) not in seen:
        seen.add(id(exc))
        yield exc
        exc = exc.__cause__ or exc.__context__


def explain(exc: Exception) -> Exception:
    """Return an LLMError for known network failures, else the original exception unchanged."""
    if isinstance(exc, LLMError):
        return exc
    chain = list(_chain(exc))
    text = " ".join(str(e) for e in chain)

    if any(isinstance(e, ssl.SSLCertVerificationError) for e in chain) or "CERTIFICATE_VERIFY_FAILED" in text:
        return LLMError("TLS certificate not trusted. Zscaler re-signs HTTPS traffic with its own root CA. "
                        "Set OLLAMA_USE_SYSTEM_CERTS=1 (pip install truststore) or OLLAMA_CA_BUNDLE=<path to the "
                        "Zscaler root .pem>. Run `python -m server.llm.diagnose` for details.")
    if any(isinstance(e, httpx.ProxyError) for e in chain) or "407" in text and "Proxy" in text:
        return LLMError("The proxy refused the request (authentication or policy). Check OLLAMA_PROXY, or set "
                        "OLLAMA_PROXY=none if the Ollama server is on the internal network. "
                        "Run `python -m server.llm.diagnose`.")
    if any(isinstance(e, (httpx.ConnectTimeout, httpx.ConnectError)) for e in chain) or isinstance(exc, ConnectionError):
        return LLMError("Cannot reach the model server. Check OLLAMA_BASE_URL (host, port, path), that you are on the "
                        "company network/VPN with Zscaler connected, and the proxy settings. "
                        "Run `python -m server.llm.diagnose`.")
    if any(isinstance(e, httpx.ReadTimeout) for e in chain):
        return LLMError("The model server took too long to answer (the first call loads the model). "
                        "Retry, or raise OLLAMA_TIMEOUT.")
    status = getattr(exc, "status_code", None)
    if status is None:
        for e in chain:
            if isinstance(e, httpx.HTTPStatusError):
                status = e.response.status_code
    if status == 401:
        return LLMError("The model server rejected the credentials (401). Check OLLAMA_API_KEY / OLLAMA_AUTH_HEADER.")
    if status == 404:
        return LLMError(f"Model or endpoint not found (404): {exc}. Check the model tag and the URL path in OLLAMA_BASE_URL.")
    if status == 403 and "zscaler" in text.lower():
        return LLMError("Zscaler blocked the request (403). Ask IT to allow the Ollama server URL.")
    return exc
