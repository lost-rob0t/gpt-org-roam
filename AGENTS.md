# GPT Org-roam contribution contract

This repository is a general technical Org-roam knowledge graph with tutorials. It is not the authoritative StarIntel research graph.

## Scope

- Put reusable technical concepts, architectures, research notes, workflows, and tutorials here.
- StarIntel-specific research, approvals, and design authority belong in the dedicated StarIntel research repository.
- Existing StarLang/StarIntel learning material may remain here as project/tutorial material; do not silently turn it into authority for StarIntel design.

## Canonical format

- Org is canonical for knowledge documents.
- Every Org node must have one stable UUID-backed `:ID:` and a `#+title:`.
- Link durable knowledge with `[[id:UUID][Title]]`, not absolute filesystem paths.
- Preserve IDs when renaming or moving a node.
- `index.org` is the top-level navigation node and must remain usable.
- Do not generate large numbers of empty or placeholder notes.

## Knowledge model

Prefer a graph over a document dump:

- `concepts/` — reusable ideas, definitions, models, invariants, and distinctions.
- `research/` — source-grounded investigations, evidence, disagreements, open questions, and synthesis.
- `architecture/` — compositions of concepts into systems and execution models.
- `tutorials/` — long-form teaching paths from zero knowledge to practical use.
- `projects/` — concrete project entry points and project-specific facts.

Tutorials are first-class. They should reuse concept and architecture nodes instead of redefining the same theory in isolation.

## Research rules

- Ground factual technical claims in primary sources when available.
- Record source URLs, versions, commits, dates, or paper identifiers when they materially affect the claim.
- Distinguish observed facts from proposals, synthesis, hypotheses, and future work.
- Do not fabricate citations, benchmarks, test results, implementation status, or source verification.
- If a source cannot establish a claim, weaken the claim or mark it unresolved.

## Tutorial rules

- Teach from prerequisites through a working mental model to practical use.
- Reuse existing project, concept, research, and architecture nodes with Org-roam ID links.
- Create support nodes only when they add durable knowledge.
- Keep examples reproducible and label pseudocode or illustrative output as such.
- Never claim code was executed, tests passed, or an API exists unless verified.

## Specifications and verification

For autonomous-agent material, distinguish a plan from a specification:

- A plan is an editable strategy for doing work.
- A specification defines acceptance conditions.
- Once an acceptance specification is frozen for a run, workers must not mutate it in place.
- Legitimate requirement changes create a new version with explicit provenance/supersession.
- Verification evidence should be produced independently of the worker's self-report when practical.

## Change workflow

- Work on a feature branch.
- Inspect existing nodes before creating duplicates.
- Update backlinks and `index.org` when adding durable top-level material.
- Run repository validation before merge.
- Merge only when every required CI/CD check is green. Missing, skipped, cancelled, pending, or failing is not green.
- If a rule matters repeatedly, prefer enforcing it in CI over relying on memory.
