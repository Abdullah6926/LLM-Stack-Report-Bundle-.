# Runnable lab: The Modern LLM Stack

Python **3.11+**. The offline examples and the calculators use only the standard library. `mcp` and `openai` are optional live integrations, pinned in `requirements.txt`. The build runtime had no DNS/network access, so package install and live API/Ollama checks are **not run** here. The examples have a default offline stub path; `--live` deliberately opts into external calls.

## Set up and test

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows: .venv\Scripts\activate
python -m pip install -r code/requirements.txt
python -m unittest discover -s tests -v
python -m pip freeze > code/requirements-frozen.txt
```

The requirements pin the direct SDKs. After a successful fresh install, the final `pip freeze` creates the environment-specific full dependency lock. For a no-network test, skip installation: run the scripts below and `python -m unittest discover -s tests -v`.

## Offline-safe demos

```bash
python code/cloud_stream.py
python code/tool_loop.py
python code/structured_output.py
python code/ollama_rest.py
python code/ollama_openai_compat.py
python code/mcp_raw_stdio.py --demo
python code/hybrid_router.py
python code/rag_hybrid.py
python code/agent_loop.py
python code/mcp_description_pin.py
python code/trace_jsonl.py
```

Offline output is explicitly marked `[stub]` or described as a fixture. The RAG dense scores are toy inputs, not model embeddings. `mcp_raw_stdio.py` prints every request/response in demo mode and implements only a tiny protocol subset; use the official SDK for real interoperability.

## Optional live integrations (not run during this build)

- `OPENAI_API_KEY=... OPENAI_MODEL=... python code/cloud_stream.py --live`
- `OPENAI_API_KEY=... OPENAI_MODEL=... python code/tool_loop.py --live`
- `OPENAI_API_KEY=... OPENAI_MODEL=... python code/structured_output.py --live`
- Start Ollama locally, pull a compatible model, then `python code/ollama_rest.py --live` or `python code/ollama_openai_compat.py --live`.
- Start `python code/mcp_server_sdk.py` using stdio from an MCP host. For HTTP client smoke-testing, edit the final line to `mcp.run(transport="streamable-http")`, start it, then run `python code/mcp_sdk_client.py`. Do not run stdio and HTTP servers on the same transport simultaneously.

## Files

- `cloud_stream.py`: official OpenAI SDK Responses streaming pattern.
- `tool_loop.py`: bounded allowlisted function-call loop.
- `structured_output.py`: JSON Schema structured output.
- `ollama_rest.py`: native `/api/chat` NDJSON stream parser.
- `ollama_openai_compat.py`: official OpenAI client pointed at Ollama's `/v1` compatibility endpoint.
- `Modelfile`: example with a commented `ADAPTER` line.
- `mcp_server_sdk.py`, `mcp_sdk_client.py`: official MCP Python SDK v2; two tools, one resource and one prompt.
- `mcp_raw_stdio.py`: small line-delimited JSON-RPC fixture that prints all messages.
- `hybrid_router.py`: sensitive/local preference, cloud fallback and a per-request budget cap.
- `rag_hybrid.py`: lexical rank, toy dense rank, reciprocal rank fusion and recall@k.
- `agent_loop.py`: under 50 lines, step budget and tool allowlist.
- `mcp_description_pin.py`: harmless canary + SHA-256 description pin.
- `trace_jsonl.py`: latency/token/cost fields to JSONL.

Review official docs before production use; model names, API schemas, spec revisions, SDK surfaces, prices, and Ollama defaults can change.
