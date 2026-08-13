# GPT Org-roam

Personal technical learning graph and tutorial repository maintained as Org-roam documents.

## Repository layout

- `tutorials/` — long-form technical tutorials intended to be read from zero knowledge through practical use.
- `projects/` — project-level notes and entry points.
- `architecture/` — architecture and implementation-model notes.
- `concepts/` — focused conceptual references.
- `index.org` — top-level Org-roam navigation index.

## Contribution and merge policy

Changes should be made on a feature branch and submitted through a pull request.

**Merge automatically only when all required CI/CD checks are green.**

A missing, skipped, cancelled, pending, or failing required check is **not** green and must not be treated as approval to merge. If a repository change requires a new validation rule, add that validation to CI/CD rather than relying on a manual convention.

Documentation changes should preserve valid Org syntax, Org-roam IDs and links, and the navigability of `index.org`.
