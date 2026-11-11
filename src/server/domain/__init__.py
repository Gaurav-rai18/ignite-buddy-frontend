"""Request lifecycle after a WebSocket message has been accepted.

Flow (see also ``docs/ARCHITECTURE.md``)::

    realtime.consumer
        → domain.orchestrator.process(session, text)
            → domain.router.route(text)     # command | chat | activity | …
            → tools / chat / features
            → stream tokens / device_calls back through the consumer

Modules: session, policy, router, orchestrator.
"""
