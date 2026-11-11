"""Background sensors on the client.

activity
    Periodic sampler of foreground app / title (masked where required).
    Results are sent to the server for sessionisation and “how long did I…”
    questions; the server never sees keystrokes or full screenshots here.
"""
