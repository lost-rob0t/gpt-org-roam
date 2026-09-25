from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "llm_roam.py"
SPEC = importlib.util.spec_from_file_location("llm_roam", MODULE_PATH)
llm_roam = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = llm_roam
SPEC.loader.exec_module(llm_roam)


class LlmRoamTests(unittest.TestCase):
    def test_chatgpt_import_is_deterministic_and_complete(self) -> None:
        conversation = {
            "id": "conversation-1",
            "title": "Example",
            "create_time": 1,
            "mapping": {
                "a": {
                    "message": {
                        "author": {"role": "user"},
                        "create_time": 1,
                        "content": {"parts": ["hello"]},
                    }
                },
                "b": {
                    "message": {
                        "author": {"role": "assistant"},
                        "create_time": 2,
                        "content": {"parts": ["world"]},
                    }
                },
            },
        }
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            export = root / "conversations.json"
            export.write_text(json.dumps([conversation]), encoding="utf-8")
            output = root / "private" / "llm" / "chatgpt"
            paths = llm_roam.import_chatgpt(export, output)
            self.assertEqual(2, len(paths))
            body = next(path for path in paths if path.name != "index.org").read_text(encoding="utf-8")
            self.assertIn("hello", body)
            self.assertIn("world", body)
            self.assertIn(
                llm_roam.stable_uuid("chatgpt-conversation", "conversation-1"),
                body,
            )

    def test_gemini_pack_excludes_secret_files_and_records_starintel_lock(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "gpt-org-roam"
            root.mkdir()
            (root / "index.org").write_text(
                ":PROPERTIES:\n:ID: test\n:END:\n#+title: Test\n",
                encoding="utf-8",
            )
            private = root / "private" / "llm"
            private.mkdir(parents=True)
            (private / "history.org").write_text(
                ":PROPERTIES:\n:ID: chat\n:END:\n#+title: Private chat\n",
                encoding="utf-8",
            )

            auto = Path(temp) / "starintel-auto-research"
            auto.mkdir()
            (auto / "README.md").write_text("research", encoding="utf-8")
            (auto / ".env").write_text("TOKEN=do-not-export", encoding="utf-8")

            server = Path(temp) / "starintel-server"
            (server / "schema").mkdir(parents=True)
            (server / "schema" / "starintel-schema.lock.json").write_text(
                json.dumps(
                    {
                        "release_version": "0.9.1",
                        "schema_version": "0.9.0",
                        "canonical_repository": "example/schema",
                        "canonical_commit": "abc123",
                    }
                ),
                encoding="utf-8",
            )
            (server / "source.lisp").write_text("(print :ok)\n", encoding="utf-8")

            output = Path(temp) / "out"
            manifest = llm_roam.build_gemini(
                root,
                output,
                [("auto-research", auto), ("starintel-server", server)],
                max_words=10_000,
                max_bytes=2_000_000,
            )
            self.assertEqual("0.9.1", manifest["starintel_schema_lock"]["release_version"])
            combined = "\n".join(
                (output / pack["file"]).read_text(encoding="utf-8")
                for pack in manifest["packs"]
            )
            self.assertIn("Private chat", combined)
            self.assertIn("(print :ok)", combined)
            self.assertNotIn("do-not-export", combined)
            llm_roam.verify_gemini(output)

    def test_verify_detects_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "root"
            root.mkdir()
            (root / "index.org").write_text(
                ":PROPERTIES:\n:ID: test\n:END:\n#+title: Test\n",
                encoding="utf-8",
            )
            output = Path(temp) / "out"
            manifest = llm_roam.build_gemini(
                root,
                output,
                [],
                max_words=10_000,
                max_bytes=2_000_000,
            )
            pack = output / manifest["packs"][0]["file"]
            pack.write_text(pack.read_text(encoding="utf-8") + "\nchanged\n", encoding="utf-8")
            with self.assertRaises(SystemExit):
                llm_roam.verify_gemini(output)


if __name__ == "__main__":
    unittest.main()
