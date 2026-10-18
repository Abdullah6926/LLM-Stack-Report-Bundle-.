# The Modern LLM Stack — compact report source

This repository builds a 24-page A4 PDF and DOCX field guide from one Markdown source. It covers cloud LLM APIs, local inference/Ollama, serving and quantization, RAG, MCP (spec revision **2026-07-28**), agent loops, architecture, costs, security, and operations.

## Build the documents

Python 3.11+ is required. The build uses WeasyPrint, Pillow, python-docx, and lxml, pinned in `requirements-build.txt`. Install the system fonts **EB Garamond**, **Inter**, and **DejaVu Sans Mono** for the intended layout.

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows: .venv\Scripts\activate
python -m pip install -r requirements-build.txt
python build.py
```

`build.py` reads `content/report.md`, draws the technical diagrams in `images/figures/`, and writes `report.pdf`, `report.docx`, and `content/rendered.html`. It does not need network access to rebuild.

## Real-photo fallback

The build runtime could not download external stock imagery. The current documents therefore use explicitly labeled flat-color placeholders; no AI-generated or uncredited photos are included. The 18 stable slots are mapped in `images/slots/manifest.csv`. Put a verified, non-AI, adequately sized asset at `images/slots/<slot_id>.jpg` (or `.jpeg`, `.png`, `.webp`), update its manifest alt text/caption to match the chosen image, record the actual author, source URL and license in both the manifest and `credits.csv`, then run `python build.py`. A real asset automatically replaces that placeholder in both PDF and DOCX.

## Offline lab and tests

```bash
python -m unittest discover -s tests -v
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

The calculators are standard-library scripts under `calc/`. Offline runners were executed and their trimmed stdout is in `code/verification_outputs.txt`; the toy dense RAG scores are explicitly not real embeddings. The optional official OpenAI/MCP SDK examples are pinned under `code/requirements.txt`, but package installation and live provider/Ollama/GPU calls were **not run** because the build runtime had no external DNS, no API key, no Ollama daemon, and no accessible GPU. After installing the optional SDK requirements in a networked fresh environment, freeze the full resolved environment with `python -m pip freeze > code/requirements-frozen.txt`.
