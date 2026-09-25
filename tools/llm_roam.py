#!/usr/bin/env python3
"""Personal LLM Org-roam journal and Gemini Notebook source packer."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import uuid
from pathlib import Path

NAMESPACE = uuid.UUID("f143239f-3dbb-4a0d-957f-cf5580327cd6")
TEXT = {
    ".asd", ".c", ".cl", ".css", ".el", ".go", ".h", ".html", ".java", ".js",
    ".json", ".jsonl", ".kt", ".lisp", ".md", ".nim", ".nix", ".org", ".pl",
    ".prolog", ".py", ".rs", ".scm", ".sh", ".sql", ".toml", ".ts", ".tsx",
    ".txt", ".xml", ".yaml", ".yml",
}
SKIP_DIRS = {".git", ".direnv", ".venv", "__pycache__", "_exports", "_site", "build", "dist", "node_modules", "target", "vendor"}
SECRET = re.compile(r"(^|/)(\.env($|[.])|credentials?($|[._-])|secrets?($|[._-])|tokens?($|[._-]))|\.(key|pem|p12|pfx|jks|keystore)$", re.I)
WORDS = re.compile(r"\S+")


def stable_uuid(kind: str, identity: str) -> str:
    return str(uuid.uuid5(NAMESPACE, f"{kind}:{identity}"))


def _text(value: object) -> str:
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _message_text(message: dict) -> str:
    content = message.get("content") or {}
    parts = content.get("parts")
    if isinstance(parts, list):
        return "\n".join(filter(None, (_text(part) for part in parts)))
    if isinstance(content.get("text"), str):
        return content["text"]
    return _text(content) if content else ""


def _messages(conversation: dict) -> list[tuple[str, dict]]:
    result = []
    for node_id, node in (conversation.get("mapping") or {}).items():
        if isinstance(node, dict) and isinstance(node.get("message"), dict):
            result.append((str(node_id), node["message"]))
    result.sort(key=lambda item: (float(item[1].get("create_time") or 0), item[0]))
    return result


def _slug(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-._").lower()
    return value[:80] or "untitled"


def _render_chat(conversation: dict) -> tuple[str, str]:
    conversation_id = str(conversation.get("id") or stable_uuid("chatgpt-fallback", json.dumps(conversation, sort_keys=True)))
    node_id = stable_uuid("chatgpt-conversation", conversation_id)
    title = str(conversation.get("title") or "Untitled ChatGPT conversation").replace("\x00", "\uFFFD")
    lines = [
        ":PROPERTIES:", f":ID:       {node_id}", f":CHATGPT_CONVERSATION_ID: {conversation_id}", ":END:",
        f"#+title: {title}", "#+filetags: :llm:chatgpt:conversation:", "#+provider: chatgpt",
    ]
    if conversation.get("create_time") is not None:
        lines.append(f"#+created_unix: {conversation['create_time']}")
    if conversation.get("update_time") is not None:
        lines.append(f"#+updated_unix: {conversation['update_time']}")
    lines.append("")
    for i, (message_id, message) in enumerate(_messages(conversation), 1):
        role = str((message.get("author") or {}).get("role") or "unknown")
        lines += [
            f"* {i:04d} {role}", ":PROPERTIES:", f":LLM_MESSAGE_ID: {message_id}",
            f":LLM_MESSAGE_UUID: {stable_uuid('chatgpt-message', message_id)}", f":ROLE: {role}",
        ]
        if message.get("create_time") is not None:
            lines.append(f":CREATED_UNIX: {message['create_time']}")
        lines += [":END:", "", _message_text(message).replace("\x00", "\uFFFD").rstrip(), ""]
    return node_id, "\n".join(lines).rstrip() + "\n"


def import_chatgpt(export_path: Path, output_dir: Path) -> list[Path]:
    payload = json.loads(export_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise SystemExit("ChatGPT export must be a conversations.json-style JSON array")
    output_dir.mkdir(parents=True, exist_ok=True)
    rows, written, names = [], [], set()
    for conversation in payload:
        if not isinstance(conversation, dict):
            continue
        node_id, rendered = _render_chat(conversation)
        conv_id = str(conversation.get("id") or node_id)
        title = str(conversation.get("title") or "Untitled ChatGPT conversation")
        base = f"{_slug(title)}-{_slug(conv_id)[:16]}"
        filename = f"{base}.org"
        n = 2
        while filename in names:
            filename, n = f"{base}-{n}.org", n + 1
        names.add(filename)
        path = output_dir / filename
        path.write_text(rendered, encoding="utf-8")
        rows.append((node_id, title))
        written.append(path)
    index_id = stable_uuid("chatgpt-index", "chatgpt")
    index = [":PROPERTIES:", f":ID:       {index_id}", ":END:", "#+title: ChatGPT Conversation Archive", "#+filetags: :llm:chatgpt:index:", "", "* Conversations"]
    index += [f"- [[id:{node_id}][{title.replace(chr(0), chr(0xFFFD))}]]" for node_id, title in rows]
    index_path = output_dir / "index.org"
    index_path.write_text("\n".join(index) + "\n", encoding="utf-8")
    written.append(index_path)
    return written


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _language(path: Path) -> str:
    return {
        ".cl": "lisp", ".lisp": "lisp", ".el": "emacs-lisp", ".pl": "prolog", ".prolog": "prolog",
        ".py": "python", ".kt": "kotlin", ".java": "java", ".js": "javascript", ".ts": "typescript",
        ".org": "org", ".md": "markdown", ".json": "json", ".sh": "bash", ".nix": "nix", ".nim": "nim",
    }.get(path.suffix.lower(), "text")


def _source_files(collection: str, root: Path):
    root = root.resolve()
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts) or SECRET.search(rel.as_posix()):
            continue
        if path.suffix.lower() not in TEXT:
            continue
        data = path.read_bytes()
        if b"\x00" in data[:8192]:
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            continue
        yield collection, rel, path, text


def _repo_args(root: Path, repos: list[tuple[str, Path]] | None) -> list[tuple[str, Path]]:
    if repos:
        return repos
    parent = root.resolve().parent
    return [
        (name, path) for name, path in [
            ("auto-research", parent / "starintel-auto-research"),
            ("starintel-server", parent / "starintel-server"),
        ] if path.is_dir()
    ]


def _schema_lock(repos: list[tuple[str, Path]]) -> dict | None:
    for name, root in repos:
        if name != "starintel-server":
            continue
        path = root / "schema" / "starintel-schema.lock.json"
        if not path.is_file():
            raise SystemExit(f"StarIntel Server source is missing schema lock: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        for key in ("release_version", "schema_version", "canonical_commit"):
            if not data.get(key):
                raise SystemExit(f"StarIntel schema lock missing {key}: {path}")
        return {
            "path": str(path), "release_version": data["release_version"],
            "schema_version": data["schema_version"], "canonical_repository": data.get("canonical_repository"),
            "canonical_commit": data["canonical_commit"],
        }
    return None


def _block(collection: str, rel: Path, path: Path, text: str) -> tuple[dict, str]:
    digest = hashlib.sha256(text.encode()).hexdigest()
    fence = "`" * max(3, 1 + max((len(m.group()) for m in re.finditer(r"`+", text)), default=0))
    record = {
        "source_id": f"{collection}:{rel.as_posix()}", "collection": collection, "path": rel.as_posix(),
        "sha256": digest, "language": _language(path), "words": len(WORDS.findall(text)),
        "bytes": len(text.encode()),
    }
    body = (
        f"\n# Source: {record['source_id']}\n\n- collection: `{collection}`\n- path: `{rel.as_posix()}`\n"
        f"- sha256: `{digest}`\n- language: `{record['language']}`\n\n"
        f"{fence}{record['language']}\n{text.rstrip()}\n{fence}\n"
    )
    return record, body


def build_gemini(repo_root: Path, output_dir: Path, repositories: list[tuple[str, Path]], max_words: int, max_bytes: int) -> dict:
    repo_root, output_dir = repo_root.resolve(), output_dir.resolve()
    repositories = _repo_args(repo_root, repositories)
    lock = _schema_lock(repositories)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    manifest = {
        "format": "llm-org-roam.gemini-notebook.v1", "canonical_org_root": str(repo_root),
        "repositories": [{"name": n, "path": str(p.resolve())} for n, p in repositories],
        "starintel_schema_lock": lock, "packs": [],
    }
    rows, pack_no = [], 1
    for collection, root in [("personal-org-roam", repo_root), *repositories]:
        current_rows, chunks, words, size = [], [], 0, 0
        def flush():
            nonlocal current_rows, chunks, words, size, pack_no
            if not chunks:
                return
            filename = f"{pack_no:03d}-{_slug(collection)}.md"
            content = f"# Gemini Notebook source pack {pack_no}: {collection}\n\nGenerated read-only projection.\n" + "".join(chunks)
            path = output_dir / filename
            path.write_text(content, encoding="utf-8")
            manifest["packs"].append({"file": filename, "collection": collection, "sha256": _sha(path), "source_count": len(current_rows), "words": len(WORDS.findall(content)), "bytes": len(content.encode())})
            rows.extend([{**row, "pack": filename} for row in current_rows])
            current_rows, chunks, words, size, pack_no = [], [], 0, 0, pack_no + 1
        for _, rel, path, text in _source_files(collection, root):
            row, body = _block(collection, rel, path, text)
            bw, bb = len(WORDS.findall(body)), len(body.encode())
            if bw > max_words or bb > max_bytes:
                raise SystemExit(f"source exceeds one Gemini pack limit: {row['source_id']}")
            if chunks and (words + bw > max_words or size + bb > max_bytes):
                flush()
            current_rows.append(row); chunks.append(body); words += bw; size += bb
        flush()

    instructions = output_dir / "NOTEBOOK-INSTRUCTIONS.md"
    release = ""
    if lock:
        release = f"\nStarIntel Server was packed from release `{lock['release_version']}` over schema `{lock['schema_version']}`. The included lock beats stale prose.\n"
    instructions.write_text(
        "# LLM Org-roam / Gemini Notebook instructions\n\n"
        "This notebook is a read-only projection of the personal Org-roam graph and selected repositories.\n\n"
        "1. Org is canonical for personal durable knowledge.\n"
        "2. Raw LLM conversation nodes are evidence/history, not automatically verified truth.\n"
        "3. `starintel-auto-research` remains authoritative for StarIntel research/design approval.\n"
        "4. `starintel-server` remains authoritative for runtime behavior and its live schema lock.\n"
        "5. Notebook execution proves only the notebook environment; never invent CI/production status.\n"
        "6. Preserve source path and SHA-256 when citing or reconstructing packed code.\n"
        "7. Credential-like files are intentionally excluded.\n" + release,
        encoding="utf-8",
    )
    manifest["instructions"] = {"file": instructions.name, "sha256": _sha(instructions)}

    index = output_dir / "CODE-INDEX.csv"
    fields = ["source_id", "collection", "path", "sha256", "language", "words", "bytes", "pack"]
    with index.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    manifest["code_index"] = {"file": index.name, "sha256": _sha(index)}

    (output_dir / "MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def verify_gemini(output_dir: Path) -> None:
    manifest = json.loads((output_dir / "MANIFEST.json").read_text(encoding="utf-8"))
    for item in [manifest["instructions"], manifest["code_index"], *manifest["packs"]]:
        path = output_dir / item["file"]
        if not path.is_file():
            raise SystemExit(f"missing generated source: {path}")
        if _sha(path) != item["sha256"]:
            raise SystemExit(f"hash mismatch: {path}")
    print(f"verified {len(manifest['packs'])} Gemini source packs")


def parse_repo(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("--repo requires NAME=PATH")
    name, raw = value.split("=", 1)
    path = Path(raw).expanduser().resolve()
    if not path.is_dir():
        raise argparse.ArgumentTypeError(f"repository path does not exist: {path}")
    return _slug(name), path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    chat = sub.add_parser("import-chatgpt")
    chat.add_argument("export")
    chat.add_argument("--output", default="private/llm/chatgpt")

    build = sub.add_parser("build-gemini")
    build.add_argument("--root", default=".")
    build.add_argument("--output", default="_exports/gemini")
    build.add_argument("--repo", action="append", type=parse_repo, default=[])
    build.add_argument("--max-words", type=int, default=250_000)
    build.add_argument("--max-bytes", type=int, default=50 * 1024 * 1024)

    verify = sub.add_parser("verify-gemini")
    verify.add_argument("--output", default="_exports/gemini")

    args = parser.parse_args(argv)
    if args.command == "import-chatgpt":
        written = import_chatgpt(Path(args.export), Path(args.output))
        print(f"imported {len(written) - 1} conversations into {args.output}")
    elif args.command == "build-gemini":
        manifest = build_gemini(Path(args.root), Path(args.output), list(args.repo), args.max_words, args.max_bytes)
        print(f"built {len(manifest['packs'])} Gemini source packs")
    else:
        verify_gemini(Path(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
