# Tutorial EPUB pipeline

Every top-level `tutorials/*.org` file is a separate reflowable EPUB book.

## Local build

On Ubuntu:

```sh
sudo apt-get install pandoc epubcheck python3-pil fonts-dejavu-core
python3 scripts/build_epubs.py --output dist
for epub in dist/*.epub; do epubcheck "$epub"; done
```

Build only one tutorial:

```sh
python3 scripts/build_epubs.py \
  --tutorial tutorials/prolog-rlm-from-zero.org \
  --output dist
```

Outputs include:

- one `.epub` per tutorial;
- one generated `1600x2560` JPEG cover per tutorial under `dist/covers/`;
- `dist/manifest.json` with source/image/checksum metadata;
- `dist/SHA256SUMS` in CI.

## Images

Use repository-relative Org file links:

```org
[[file:../images/runtime-architecture.png]]
```

or an image next to a tutorial:

```org
[[file:images/context-flow.svg]]
```

The build fails when a referenced local image is missing or uses an absolute path. Pandoc embeds valid local images into that tutorial's EPUB. The Kindle stylesheet scales block images to the reader viewport.

The generated cover guarantees every book has at least one image even when the tutorial itself has no figures yet.

## Code blocks

Ordinary Org source blocks are preserved as text, not screenshots. The EPUB stylesheet wraps long lines and uses a smaller monospace size so code remains readable on narrow E Ink screens.

Prefer code like this:

```org
#+begin_src prolog
rlm_completion(Query, Context, Options, Outcome).
#+end_src
```

Do not turn code samples into images unless the visual layout itself is what the tutorial is teaching.

## Org-roam links

A standalone EPUB cannot resolve `id:` links to nodes that are not packaged into that book. The Pandoc filter therefore renders the link label as ordinary text instead of leaving a broken `id:` URI. HTTP(S) links remain links.

## CI/CD behavior

The `Kindle EPUBs` workflow:

1. builds every tutorial on pull requests and pushes to `main`;
2. runs `epubcheck` on every generated EPUB;
3. uploads the complete `kindle-epubs` Actions artifact;
4. on a `books-v*` tag, publishes the validated EPUBs, covers, manifest, and checksums as GitHub Release assets.

Example release tag:

```sh
git tag books-v2026.08.13
git push origin books-v2026.08.13
```

EPUBCheck validates the EPUB package. Before external Kindle publication, also inspect the result in Amazon Kindle Previewer because device-specific rendering is a separate QA step.
