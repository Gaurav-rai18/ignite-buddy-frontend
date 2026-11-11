"""Convert internal conversation message dictionaries ({"role","content","images"?}) into LangChain message types."""
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from langchain_core.messages import BaseMessage


def to_langchain(messages: list[dict]) -> list[Any]:
    """Convert a sequence of message dicts into LangChain message classes.

    Imports langchain_core dynamically at call time to prevent importing heavy AI dependencies
    during server startup or pure command parsing. Supports system, assistant, text human,
    and multi-modal image blocks.
    """
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

    out = []
    for m in messages:
        role, content, images = m["role"], m.get("content", ""), m.get("images")
        if role == "system":
            out.append(SystemMessage(content=content))
        elif role == "assistant":
            out.append(AIMessage(content=content))
        elif images:
            blocks = [{"type": "text", "text": content}]
            blocks += [{"type": "image_url", "image_url": f"data:image/jpeg;base64,{b64}"} for b64 in images]
            out.append(HumanMessage(content=blocks))
        else:
            out.append(HumanMessage(content=content))
    return out
