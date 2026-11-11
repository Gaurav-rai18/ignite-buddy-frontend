"""Choose one item by fuzzy query; raise Ambiguous when unclear so the executor asks the user."""
from rapidfuzz import fuzz

from server.util.text import norm
from .model import Ambiguous, ToolError


def pick(items, query, text_of, label_of, finish):
    if not items:
        raise ToolError("There is nothing to choose from.")
    q = norm(query or "")
    if len(items) == 1 and not q:
        return finish(items[0])
    scored = sorted(((fuzz.WRatio(q, norm(text_of(i))) if q else 0, idx) for idx, i in enumerate(items)),
                    reverse=True)
    best = scored[0][0]
    close = [s for s in scored if s[0] >= best - 5]
    if q and best >= 75 and len(close) == 1:
        return finish(items[scored[0][1]])
    top = [items[idx] for _, idx in scored[:5]]
    labels = [label_of(i) for i in top]
    lookup = dict(zip(labels, top))
    raise Ambiguous("Which one did you mean?", labels, finish=lambda choice: finish(lookup[choice]))
