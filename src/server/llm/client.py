"""Cached ChatOllama / OllamaEmbeddings / raw client factories. One place that knows the URL and network kwargs."""
from functools import lru_cache
from typing import TYPE_CHECKING

import ollama

from server import config
from .network import httpx_kwargs

if TYPE_CHECKING:
    from langchain_ollama import ChatOllama, OllamaEmbeddings


@lru_cache(maxsize=32)
def chat_model(model: str, temperature: float, num_ctx: int, json_mode: bool = False):
    """Instantiate and cache a ChatOllama instance for text generation or conversational turns.

    Uses lazy importing so that deterministic command handling and modules importing the LLM package
    do not fail if langchain_ollama is not installed or initialized.
    """
    from langchain_ollama import ChatOllama

    kw = dict(
        model=model,
        base_url=config.LLM_BASE_URL,
        temperature=temperature,
        num_ctx=num_ctx,
        client_kwargs=httpx_kwargs(),
    )
    if json_mode:
        kw["format"] = "json"          # planner needs strict JSON
    else:
        kw["reasoning"] = False        # thinking off for speed (was think=False)
    return ChatOllama(**kw)


@lru_cache(maxsize=4)
def embedding_model(model: str):
    """Instantiate and cache an OllamaEmbeddings instance for vector encoding.

    Uses lazy importing to decouple package loading from optional embedding dependencies.
    """
    from langchain_ollama import OllamaEmbeddings

    return OllamaEmbeddings(model=model, base_url=config.LLM_BASE_URL, client_kwargs=httpx_kwargs())


@lru_cache(maxsize=1)
def raw_client() -> ollama.Client:
    """Only for server-info calls LangChain does not expose (model capabilities)."""
    return ollama.Client(host=config.LLM_BASE_URL, **httpx_kwargs())
