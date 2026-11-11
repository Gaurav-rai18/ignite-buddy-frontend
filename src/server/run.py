"""`ignite-server`: start the Ignite Buddy unified server (Daphne)."""
import os
import sys

from server import config


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.ignite_server.settings")
    from daphne.cli import CommandLineInterface
    if config.HOST in ("127.0.0.1", "localhost", "::1"):
        print(f"[server] WARNING: listening on {config.HOST} only. "
              "For other computers or VDI clients, start with ASSISTANT_HOST=0.0.0.0.", flush=True)
    CommandLineInterface().run(["-b", config.HOST, "-p", str(config.PORT),
                                "server.ignite_server.asgi:application"] + sys.argv[1:])


if __name__ == "__main__":
    main()
