---
name: tutorial-authoring
description: Create and update source-verified Org-roam tutorials in gpt-org-roam without inventing project behavior or breaking the learning graph.
---

# Tutorial Authoring

Use this skill whenever creating, expanding, correcting, renaming, or re-verifying a tutorial in `tutorials/`.

## Core contract

A tutorial in this repository is not generic prose. It is a technical learning artifact grounded in the source project's current code and intended to take a reader from zero knowledge to practical use.

Before writing:

1. Inspect the source project's current default branch.
2. Inspect open pull requests and issues that materially affect the tutorial topic.
3. Distinguish behavior that exists on the default branch from behavior that exists only in a branch, PR, design, ADR, or research note.
4. Prefer executable code, real symbols, real paths, and real commands from the repository over invented examples.
5. Record the verification point in the tutorial metadata when the source project supports it.

Never describe planned behavior as already merged.

## Filename contract

Tutorials use:

```text
NN-<project>-<slug>.org
```

The first or canonical tutorial for a project uses `00`.

Example:

```text
tutorials/00-starlang-from-zero.org
```

Use lowercase kebab-case for the project and slug. New tutorials must not use unnumbered filenames.

If an existing tutorial is renamed, preserve its Org-roam `:ID:` so graph links remain stable.

## Org-roam contract

Every tutorial must:

- contain a stable Org-roam `:ID:` property;
- contain a `#+title:`;
- use useful `#+filetags:`;
- link related project, architecture, and concept nodes by Org-roam ID when available;
- keep `index.org` navigable;
- avoid duplicate IDs;
- keep all referenced Org-roam IDs resolvable.

When updating an existing tutorial, preserve its ID unless the document is intentionally being replaced by a distinct node.

## Verification metadata

When practical, include metadata like:

```org
#+property: repo https://github.com/<owner>/<repo>
#+property: source_ref main
#+property: verified_against <commit-sha>
#+property: verified_on YYYY-MM-DD
```

Update `verified_against` only after checking the source at that revision.

## Teaching contract

Assume the reader knows nothing about the project unless the tutorial explicitly says otherwise.

Prefer this progression:

1. Goal and what the reader will be able to do.
2. Current-state warning when the project is actively migrating.
3. Minimal terminology and syntax needed to start.
4. Reproducible installation/development environment.
5. Smallest runnable example.
6. Explanation of the execution/data flow.
7. Increasingly realistic examples.
8. Debugging and failure modes.
9. Advanced architecture and extension points.
10. Practical projects or exercises that integrate the concepts.

Define a term before relying on it. Show concrete input and output where possible.

## Current versus planned behavior

Use explicit language for unstable projects:

- **current/default-branch behavior** — verified in merged code;
- **open-PR behavior** — implemented or proposed in an unmerged PR;
- **design/research direction** — documented intent without authoritative merged implementation.

Do not collapse these categories.

## Code examples

Code examples should be copied from, reduced from, or mechanically consistent with the real project APIs.

For every nontrivial example, verify at least one of:

- the referenced symbol exists;
- the referenced command exists;
- the referenced file or package exists;
- the syntax is accepted by the project's parser/compiler/runtime;
- the example mirrors a project test or fixture.

If an example is pseudocode, label it as pseudocode.

## Update workflow

When updating a tutorial:

1. Read the existing tutorial completely enough to preserve its teaching flow and IDs.
2. Re-check the source project and relevant open PRs/issues.
3. Correct stale statements before adding new material.
4. Preserve working examples unless the source changed.
5. Add new material where it naturally fits instead of appending disconnected addenda.
6. Update verification metadata.
7. Update `index.org` only if titles, IDs, or navigation need to change.
8. Run repository validation.

## Validation gate

A tutorial change is not complete until repository CI passes.

CI should reject at least:

- invalid UTF-8 Org files;
- empty Org documents;
- duplicate Org-roam IDs;
- unresolved Org-roam ID links;
- tutorial files missing `#+title:`;
- tutorial filenames that violate `NN-<project>-<slug>.org`.

Do not merge a tutorial change with missing, pending, skipped, cancelled, or failing required checks.
