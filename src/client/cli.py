"""Headless client (`trainee-cli`): same protocol and same device executor as the desktop app, plain terminal I/O.
Useful for testing against a server and on machines without a display."""
import sys
import threading

from client.device.executor import DeviceExecutor
from client.net import Net


def main():
    """Terminal client loop for testing and headless interaction with the assistant server.

    Connects to the assistant WebSocket server, sets up the local device action executor,
    and forwards console input and incoming streaming responses. Handles connection
    lifecycle events including failures and server disconnections.
    """
    net = Net()
    executor = DeviceExecutor(confirm=lambda title, preview: input(f"\n[confirm] {title}\n{preview}\nApprove? [y/N] ").strip().lower() == "y")
    threading.Thread(target=executor.index.refresh, daemon=True).start()
    net.start()
    print("Connecting... type a message, or 'quit'.")
    while True:
        m = net.inbox.get()
        t = m.get("type")
        if t == "_connected":
            break
        if t == "_disconnected":
            print(f"Could not connect: {m.get('code', 'disconnected')}")
            net.stop()
            return
        if t == "_error":
            print(f"Connection error: {m.get('error', 'unknown error')}")
            net.stop()
            return
    while True:
        try:
            text = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if text in ("quit", "exit"):
            break
        if not text:
            continue
        net.send({"type": "text", "text": text})
        while True:
            m = net.inbox.get()
            t = m.get("type")
            if t == "token":
                print(m["text"], end="", flush=True)
            elif t == "message_end":
                print()
            elif t in ("say", "notification"):
                print(f"  {m['text']}")
            elif t == "device_call":
                res = executor.handle(m["op"], m["args"])
                net.send({"type": "device_result", "id": m["id"], **res.to_wire()})
            elif t == "confirm_request":
                ok = input(f"\n[confirm] {m['title']}\n{m.get('preview', '')}\nApprove? [y/N] ").strip().lower() == "y"
                net.send({"type": "confirm_response", "id": m["id"], "approved": ok})
            elif t == "choose_request":
                for i, o in enumerate(m["options"], 1):
                    print(f"  {i}. {o}")
                pick = input("choose number (blank = cancel)> ").strip()
                choice = m["options"][int(pick) - 1] if pick.isdigit() and 0 < int(pick) <= len(m["options"]) else None
                net.send({"type": "choose_response", "id": m["id"], "choice": choice})
            elif t == "capture_request":
                net.send({"type": "capture_response", "id": m["id"], "image_b64": None})   # screenshots: desktop app only
            elif t == "_disconnected":
                print("Disconnected." + (" Authentication failed." if m.get("code") == 4401 else ""))
                return
            elif t == "state" and m["state"] == "idle":
                break
    net.stop()


if __name__ == "__main__":
    main()
