# GPT Org-roam

General technical knowledge graph and tutorial repository maintained as Org-roam documents.

The repository is **concept-first, not tutorial-only**. Reusable concepts and source-grounded research form the backbone; architectures compose those concepts; tutorials provide long-form learning paths through the graph; projects anchor the ideas in concrete systems.

StarIntel-specific research, approvals, and design authority belong in the dedicated StarIntel research repository. Existing StarLang/StarIntel material may remain here as project and tutorial material, but it is not the authority for StarIntel design.

## Repository layout

- `concepts/` — focused reusable concepts, distinctions, invariants, and models.
- `research/` — source-grounded research, evidence, synthesis, hypotheses, and open questions.
- `architecture/` — system-level compositions and implementation models.
- `tutorials/` — first-class long-form technical tutorials intended to be read from zero knowledge through practical use.
- `projects/` — concrete project notes and entry points.
- `index.org` — top-level Org-roam navigation index.
- `AGENTS.md` — contribution, research, linking, verification, and merge contract.

## Graph model

Prefer durable Org-roam links over duplicated prose. A tutorial can explain a concept in context, but reusable theory should live in a concept/research node and be linked by stable Org ID.

The initial general agent-systems backbone covers:

- frozen acceptance specifications;
- proof-carrying execution;
- symbolic verification with Prolog;
- symbolic agent memory;
- RLM-driven exploration;
- mutation testing as adversarial evidence;
- spec-carrying agent loops.

## Personal LLM memory and Gemini Notebook

This repository also has a local-first LLM journal/export path. Raw provider history is **not** committed by default: ChatGPT conversations import into the gitignored `private/` tree, where they can still participate in the local Org-roam graph.

```bash
python3 tools/llm_roam.py import-chatgpt ~/Downloads/conversations.json
```

Build a Gemini Notebook source set with:

```bash
python3 tools/llm_roam.py build-gemini
python3 tools/llm_roam.py verify-gemini
```

`build-gemini` automatically includes sibling `starintel-auto-research` and `starintel-server` checkouts when present. You can pin exact local checkouts instead:

```bash
python3 tools/llm_roam.py build-gemini \
  --repo auto-research=../starintel-auto-research \
  --repo starintel-server=../starintel-server
```

The generated `_exports/gemini/` directory contains uploadable Markdown source packs, `CODE-INDEX.csv`, notebook instructions, and a hash manifest. StarIntel material is a read-only projection: Auto-Research remains the research/design authority, and StarIntel Server plus its schema lock remain runtime/schema authority.

See the Org-roam architecture node **LLM Org-roam with Gemini Notebook Code Execution** for the full model.

## Contribution and merge policy

Changes should be made on a feature branch and submitted through a pull request.

**Merge automatically only when all required CI/CD checks are green.**

A missing, skipped, cancelled, pending, or failing required check is **not** green and must not be treated as approval to merge. If a repository change requires a new validation rule, add that validation to CI/CD rather than relying on a manual convention.

Documentation changes must preserve valid Org syntax, stable Org-roam IDs and links, source grounding where claims require it, and the navigability of `index.org`. See `AGENTS.md` for the full contract.
