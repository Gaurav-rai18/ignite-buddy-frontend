"""Central server package.

Owns authentication, routing, deterministic commands, chat/RAG, jobs,
per-user data, and the Admin REST API. Must never import ``client``.

Subpackages
-----------
auth
    Passwords, JWT, legacy static tokens.
api
    DRF ViewSets and ``/auth/login``.
realtime
    Channels WebSocket consumer, presence, notifier, admin HTML.
domain
    Session, policy, router, orchestrator (no HTTP/WS imports).
commands
    Deterministic command engine + skills.
chat / chat.rag
    Prose answers and pluggable retrievers.
features
    Activity, screen help, personal docs.
knowledge
    Knowledge-base ingest / query (Chroma).
llm
    Model gateway client.
data
    Central DB + per-user stores.
jobs
    Background timers, reminders, summaries.
web
    Thin Django/Channels settings + ASGI.
util
    Server-only helpers.
"""
