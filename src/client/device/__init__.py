"""Everything that touches the trainee’s machine.

executor
    Single entry: ``handle(op, args) -> DeviceResult``. Applies allowlists and
    may require ``local_confirm`` before destructive ops.
fileops / localops / launcher / probe / indexer / capture / vault / winnative
    Concrete implementations (find files, open apps, screenshots, Windows
    Task Scheduler toasts, …).
"""
