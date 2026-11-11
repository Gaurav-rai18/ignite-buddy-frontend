"""The tool registry = the ALLOWLIST. A plan can only contain tools registered here, with exactly these args.
There is deliberately NO generic run_command(any_string) tool."""
from .model import DEVICE, SERVER, Tool

REGISTRY: dict[str, Tool] = {}


def tool(name, level, doc, args, describe=None, preview=None, capability=None):
    """Register a SERVER-side tool: fn(session, **args) -> {"msg": str, ...}."""
    def deco(fn):
        REGISTRY[name] = Tool(name, level, doc, args, fn, SERVER, describe, preview, capability)
        return fn
    return deco


def device_tool(name, level, doc, args, capability=None):
    """Register the schema of a tool that runs ON THE CLIENT (see client/device/)."""
    REGISTRY[name] = Tool(name, level, doc, args, None, DEVICE, capability=capability)
