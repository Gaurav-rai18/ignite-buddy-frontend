"""The window is a transparent rectangle; only the rectangles the page reports (avatar, bubble, answer...) may catch the mouse.
Pure geometry so it is testable without a display."""


def normalize_rects(rects, width: int, height: int, pad: int = 4, limit: int = 40) -> list[tuple[int, int, int, int]]:
    """Validate what the page sent (it is untrusted input), pad it a little, clip it to the window. -> [(x, y, w, h)]"""
    out = []
    if not isinstance(rects, (list, tuple)):
        return out
    for r in list(rects)[:limit]:
        try:
            x, y, w, h = (int(v) for v in r)
        except (TypeError, ValueError):
            continue
        if w <= 0 or h <= 0:
            continue
        x0, y0, x1, y1 = max(0, x - pad), max(0, y - pad), min(width, x + w + pad), min(height, y + h + pad)
        if x1 > x0 and y1 > y0:
            out.append((x0, y0, x1 - x0, y1 - y0))
    return out
