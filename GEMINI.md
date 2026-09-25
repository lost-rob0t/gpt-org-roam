# Gemini adapter for GPT Org-roam

Read and obey `AGENTS.md`.

For notebook work:

- Org is canonical; generated `_exports/gemini/` files are read-only projections.
- Raw provider transcripts belong in gitignored `private/` by default.
- Treat raw LLM conversations as provenance/evidence, not automatically verified facts.
- When `starintel-auto-research` is present, preserve its research approval and lifecycle semantics.
- When `starintel-server` is present, read its live `schema/starintel-schema.lock.json`; the lock beats stale prose.
- Never copy credential-like files into notebook sources.
- Distinguish code executed in Gemini Notebook from code merely read from repository source packs.

Build the local source set with:

```bash
python3 tools/llm_roam.py build-gemini
python3 tools/llm_roam.py verify-gemini
```
