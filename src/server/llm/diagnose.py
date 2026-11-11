"""Connectivity check:  python -m server.llm.diagnose
Uses exactly the same URL / proxy / TLS / auth settings as the app, so a pass here means the app can connect."""
import sys

import httpx

from server import config
from . import network
from .errors import explain


def main() -> int:
    print("Effective LLM settings:")
    for k, v in network.describe().items():
        print(f"  {k:10} {v}")
    url = config.LLM_BASE_URL.rstrip("/") + "/api/tags"
    print(f"\nGET {url}")
    try:
        with httpx.Client(**network.httpx_kwargs()) as c:
            r = c.get(url)
    except Exception as e:
        print(f"  FAILED: {type(e).__name__}: {e}\n  -> {explain(e)}")
        return 1
    print(f"  HTTP {r.status_code}")
    if r.status_code != 200:
        body = r.text[:200].replace("\n", " ")
        hint = "Zscaler block page? Ask IT to allow this URL." if "zscaler" in r.text.lower() else ""
        print(f"  body: {body}\n  {hint}")
        return 1
    try:
        names = {m.get("name") or m.get("model") for m in r.json().get("models", [])}
    except ValueError:
        print("  Response was not JSON (wrong path, or a proxy/login page answered). Check OLLAMA_BASE_URL.")
        return 1
    print(f"  server lists {len(names)} model(s)")
    rc = 0
    for label, tag in (("FAST_MODEL", config.FAST_MODEL), ("CHAT_MODEL", config.CHAT_MODEL), ("EMBED_MODEL", config.EMBED_MODEL)):
        ok = tag in names or f"{tag}:latest" in names
        print(f"  {label:11} {tag:24} {'OK' if ok else 'NOT FOUND on server'}")
        rc |= 0 if ok else 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
