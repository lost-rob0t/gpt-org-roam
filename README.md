# GPT Org-roam

Personal technical learning graph and tutorial repository maintained as Org-roam documents.

## Repository layout

- `tutorials/` — long-form technical tutorials intended to be read from zero knowledge through practical use.
- `projects/` — project-level notes and entry points.
- `architecture/` — architecture and implementation-model notes.
- `concepts/` — focused conceptual references.
- `skills/` — repository-local authoring and maintenance skills for agents working on this knowledge base.
- `index.org` — top-level Org-roam navigation index.

## Tutorial filename convention

Tutorials use an ordered, project-qualified filename:

```text
NN-<project>-<slug>.org
```

The canonical or first tutorial for a project starts at `00`, so the standard example is:

```text
tutorials/00-<project>-<slug>.org
```

For StarLang, the current tutorial is:

```text
tutorials/00-starlang-from-zero.org
```

Rules:

- `NN` is a two-digit tutorial order beginning at `00`.
- `<project>` and `<slug>` use lowercase kebab-case.
- Do not add unnumbered tutorial filenames.
- Preserve the document's Org-roam `:ID:` when renaming or substantially updating an existing tutorial.
- Keep `index.org` linked by Org-roam ID rather than by filename so renames remain stable.

## Agent skills

Before creating or updating tutorials, read `skills/tutorial-authoring/SKILL.md`. Repository-local skills define the source-verification, naming, Org-roam, and tutorial-quality contract agents should follow.

## Contribution and merge policy

Changes should be made on a feature branch and submitted through a pull request.

**Merge automatically only when all required CI/CD checks are green.**

A missing, skipped, cancelled, pending, or failing required check is **not** green and must not be treated as approval to merge. If a repository change requires a new validation rule, add that validation to CI/CD rather than relying on a manual convention.

Documentation changes should preserve valid Org syntax, Org-roam IDs and links, and the navigability of `index.org`.
