# Tests

| Folder | Scope |
|--------|-------|
| `server/` | Unit tests for parser, commands, KB, LLM layer, storage, policy |
| `client/` | Device executor, shell, STT, vault, agent |
| `integration/` | End-to-end over Channels + Admin API sync to PCs |
| `tools/` | Helpers for the suites |

## Running Tests

**Bash / CMD:**
```bash
pytest
```

Async tests use `pytest-asyncio` (mode=auto). To run specific test suites:

**Bash / CMD:**
```bash
pytest tests/server/
pytest tests/client/
pytest tests/integration/
```
