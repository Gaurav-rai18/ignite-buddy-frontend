"""Accumulates the steps of a plan while the parser walks the clauses of one sentence."""


class Builder:
    def __init__(self):
        self.steps: list[dict] = []
        self.last_folder: int | None = None       # id of the latest step whose output `path` is a folder

    def add(self, tool: str, **args) -> int:
        sid = len(self.steps) + 1
        self.steps.append({"id": sid, "tool": tool,
                           "args": {k: str(v) for k, v in args.items() if v is not None}})
        return sid

    @staticmethod
    def ref(step_id: int, key: str = "path") -> str:
        return f"${step_id}.{key}"

    def mark(self):
        return len(self.steps), self.last_folder

    def rewind(self, mark):
        del self.steps[mark[0]:]
        self.last_folder = mark[1]
