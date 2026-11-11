"""Screen capture on the client (the user previews it before anything is sent)."""
import base64
import io

from client import config


def encode(img) -> bytes:
    """PIL image -> downscaled JPEG bytes (keeps the payload small)."""
    img = img.convert("RGB")
    big = max(img.size)
    if big > config.SCREEN_MAX_DIM:
        scale = config.SCREEN_MAX_DIM / big
        img = img.resize((int(img.width * scale), int(img.height * scale)))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=80)
    return buf.getvalue()


def grab_primary() -> bytes:
    import mss
    from PIL import Image
    with mss.mss() as sct:
        shot = sct.grab(sct.monitors[1])
        return encode(Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX"))


def capture_payload() -> dict:
    from .probe import active_window
    app, title = active_window()
    return {"image_b64": base64.b64encode(grab_primary()).decode(), "app": app or "", "title": title or ""}
