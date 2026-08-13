#!/usr/bin/env python3
"""Build one Kindle-friendly EPUB per Org tutorial.

The builder deliberately keeps tutorials reflowable. Local images referenced by
Org file links are embedded by Pandoc, while a deterministic 1600x2560 JPEG
cover is generated for every tutorial.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
TUTORIALS = ROOT / "tutorials"
BOOK_DIR = ROOT / "book"
IMAGE_EXTENSIONS = {".bmp", ".gif", ".jpeg", ".jpg", ".png", ".svg", ".webp"}
ORG_META = re.compile(r"^#\+([A-Za-z0-9_-]+):\s*(.*?)\s*$", re.IGNORECASE)
ORG_FILE_LINK = re.compile(r"\[\[file:([^\]\[]+?)(?:\]\[[^\]]*)?\]\]", re.IGNORECASE)
SLUG_BAD = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class Tutorial:
    source: Path
    title: str
    author: str
    language: str
    slug: str
    images: tuple[Path, ...]


def fail(message: str) -> "NoReturn":
    raise SystemExit(message)


def require_program(name: str) -> None:
    if shutil.which(name) is None:
        fail(f"required program not found: {name}")


def parse_metadata(path: Path) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("* "):
            break
        match = ORG_META.match(line)
        if match:
            metadata[match.group(1).lower()] = match.group(2).strip()
    return metadata


def slugify(value: str) -> str:
    slug = SLUG_BAD.sub("-", value.lower()).strip("-")
    return slug or "tutorial"


def resolve_image(source: Path, raw_target: str) -> Path | None:
    target = raw_target.split("::", 1)[0].strip()
    suffix = Path(target).suffix.lower()
    if suffix not in IMAGE_EXTENSIONS:
        return None

    candidate = Path(target)
    if candidate.is_absolute():
        fail(f"{source}: image path must be repository-relative, got {target!r}")

    candidates = [source.parent / candidate, ROOT / candidate]
    for path in candidates:
        if path.is_file():
            return path.resolve()

    fail(f"{source}: referenced image does not exist: {target}")


def source_images(source: Path) -> tuple[Path, ...]:
    text = source.read_text(encoding="utf-8")
    found: list[Path] = []
    for raw_target in ORG_FILE_LINK.findall(text):
        image = resolve_image(source, raw_target)
        if image is not None and image not in found:
            found.append(image)
    return tuple(found)


def load_tutorial(path: Path) -> Tutorial:
    metadata = parse_metadata(path)
    title = metadata.get("title") or path.stem.replace("-", " ").title()
    author = metadata.get("author") or "lost-rob0t"
    language = metadata.get("language") or "en-US"
    return Tutorial(
        source=path,
        title=title,
        author=author,
        language=language,
        slug=slugify(path.stem),
        images=source_images(path),
    )


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size=size)


def text_width(draw: ImageDraw.ImageDraw, text: str, selected_font: ImageFont.ImageFont) -> int:
    left, _, right, _ = draw.textbbox((0, 0), text, font=selected_font)
    return right - left


def wrap_words(
    draw: ImageDraw.ImageDraw,
    text: str,
    selected_font: ImageFont.ImageFont,
    max_width: int,
) -> list[str]:
    words = text.split()
    if not words:
        return [""]

    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if text_width(draw, candidate, selected_font) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def fit_title(
    draw: ImageDraw.ImageDraw,
    title: str,
    max_width: int,
    max_height: int,
) -> tuple[ImageFont.FreeTypeFont, list[str], int]:
    bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    for size in range(128, 55, -4):
        selected = font(bold, size)
        lines = wrap_words(draw, title, selected, max_width)
        line_height = int(size * 1.22)
        if len(lines) * line_height <= max_height:
            return selected, lines, line_height
    selected = font(bold, 52)
    return selected, wrap_words(draw, title, selected, max_width), 64


def cover_palette(slug: str) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    palettes = [
        ((20, 24, 35), (92, 180, 255)),
        ((26, 22, 31), (201, 120, 255)),
        ((18, 29, 29), (93, 214, 180)),
        ((31, 24, 19), (255, 169, 82)),
    ]
    index = int(hashlib.sha256(slug.encode()).hexdigest()[:8], 16) % len(palettes)
    return palettes[index]


def draw_network(
    draw: ImageDraw.ImageDraw,
    slug: str,
    accent: tuple[int, int, int],
) -> None:
    seed = int(hashlib.sha256(slug.encode()).hexdigest()[:16], 16)
    rng = random.Random(seed)
    nodes = [(rng.randint(80, 1520), rng.randint(120, 2380)) for _ in range(34)]
    line_color = tuple(max(0, c - 60) for c in accent)

    for index, point in enumerate(nodes):
        for other in nodes[index + 1 : index + 4]:
            draw.line((point, other), fill=line_color, width=3)

    for x, y in nodes:
        radius = rng.randint(6, 15)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=accent)


def make_cover(tutorial: Tutorial, destination: Path) -> None:
    width, height = 1600, 2560
    background, accent = cover_palette(tutorial.slug)
    image = Image.new("RGB", (width, height), background)
    draw = ImageDraw.Draw(image)
    draw_network(draw, tutorial.slug, accent)

    # A solid reading panel keeps title contrast high in color and grayscale.
    panel = (90, 330, 1510, 2040)
    draw.rounded_rectangle(panel, radius=36, fill=(245, 245, 242))
    draw.rectangle((90, 330, 118, 2040), fill=accent)

    title_font, lines, line_height = fit_title(draw, tutorial.title, 1230, 980)
    small = font("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 48)
    medium = font("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 54)

    y = 520
    for line in lines:
        draw.text((190, y), line, font=title_font, fill=(20, 22, 27))
        y += line_height

    draw.text((190, 1780), "A GPT Org-roam Tutorial", font=medium, fill=(40, 43, 49))
    draw.text((190, 1870), tutorial.author, font=small, fill=(70, 72, 78))
    draw.text((130, 2290), "PROLOG  •  ACTORS  •  SYSTEMS", font=small, fill=(238, 238, 238))

    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination, "JPEG", quality=94, optimize=True, progressive=True)


def pandoc_command(tutorial: Tutorial, cover: Path, output: Path) -> list[str]:
    resource_paths = [
        str(ROOT),
        str(tutorial.source.parent),
        str(ROOT / "images"),
        str(TUTORIALS / "images"),
    ]
    return [
        "pandoc",
        str(tutorial.source),
        "--from=org",
        "--to=epub3",
        "--standalone",
        "--toc",
        "--toc-depth=3",
        "--epub-chapter-level=1",
        "--no-highlight",
        f"--css={BOOK_DIR / 'kindle.css'}",
        f"--lua-filter={BOOK_DIR / 'kindle.lua'}",
        f"--epub-cover-image={cover}",
        f"--resource-path={os.pathsep.join(resource_paths)}",
        f"--metadata=title:{tutorial.title}",
        f"--metadata=author:{tutorial.author}",
        f"--metadata=lang:{tutorial.language}",
        f"--metadata=identifier:urn:gpt-org-roam:{tutorial.slug}",
        f"--output={output}",
    ]


def verify_epub(path: Path) -> None:
    if path.stat().st_size < 1024:
        fail(f"generated EPUB is suspiciously small: {path}")

    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if not names or names[0] != "mimetype":
            fail(f"{path}: EPUB mimetype entry is not first")
        if archive.read("mimetype") != b"application/epub+zip":
            fail(f"{path}: invalid EPUB mimetype")
        if "META-INF/container.xml" not in names:
            fail(f"{path}: missing META-INF/container.xml")
        if not any("cover" in name.lower() for name in names):
            fail(f"{path}: generated cover was not embedded")
        if not any(name.lower().endswith((".xhtml", ".html")) for name in names):
            fail(f"{path}: no XHTML/HTML content found")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def discover_tutorials(selected: Iterable[str]) -> list[Path]:
    requested = list(selected)
    if requested:
        paths = []
        for item in requested:
            path = Path(item)
            if not path.is_absolute():
                path = ROOT / path
            if not path.is_file():
                fail(f"tutorial not found: {item}")
            paths.append(path.resolve())
        return sorted(paths)

    paths = sorted(TUTORIALS.glob("*.org"))
    if not paths:
        fail(f"no tutorials found under {TUTORIALS}")
    return paths


def build(tutorial: Tutorial, output_dir: Path) -> dict[str, object]:
    covers = output_dir / "covers"
    cover = covers / f"{tutorial.slug}.jpg"
    epub = output_dir / f"{tutorial.slug}.epub"

    make_cover(tutorial, cover)
    subprocess.run(pandoc_command(tutorial, cover, epub), cwd=ROOT, check=True)
    verify_epub(epub)

    record: dict[str, object] = {
        "slug": tutorial.slug,
        "title": tutorial.title,
        "author": tutorial.author,
        "language": tutorial.language,
        "source": str(tutorial.source.relative_to(ROOT)),
        "source_images": [str(path.relative_to(ROOT)) for path in tutorial.images],
        "source_image_count": len(tutorial.images),
        "cover": str(cover.relative_to(output_dir)),
        "epub": epub.name,
        "bytes": epub.stat().st_size,
        "sha256": sha256(epub),
    }
    print(f"built {epub.relative_to(ROOT)} ({record['bytes']} bytes)")
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="dist", help="output directory relative to repo root")
    parser.add_argument(
        "--tutorial",
        action="append",
        default=[],
        help="build only this tutorial path; repeat for more than one",
    )
    args = parser.parse_args()

    require_program("pandoc")
    output_dir = Path(args.output)
    if not output_dir.is_absolute():
        output_dir = ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    tutorials = [load_tutorial(path) for path in discover_tutorials(args.tutorial)]
    slugs = [tutorial.slug for tutorial in tutorials]
    if len(slugs) != len(set(slugs)):
        fail("tutorial filenames collapse to duplicate EPUB slugs")

    records = [build(tutorial, output_dir) for tutorial in tutorials]
    manifest = {
        "format": "gpt-org-roam-tutorial-epubs/v1",
        "count": len(records),
        "books": records,
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"built {len(records)} tutorial EPUB(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
