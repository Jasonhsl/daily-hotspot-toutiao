import base64
import copy
import json
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from zipfile import ZipFile

from build_article import build
from publish_ledger import connect, reserve, mark
from prepare_toutiao_pack import sanitize_title


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.image = self.root / "image.png"
        self.image.write_bytes(base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aB1sAAAAASUVORK5CYII="))
        self.article = {
            "run_date": "2026-09-05", "title": "Concrete reader question",
            "lead": "A concrete opening.", "sections": [
                {"heading": "Evidence", "paragraphs": ["A supported judgment."], "image": "sample.png"}],
            "image_sources": [{"source": str(self.image), "filename": "sample.png"}]
        }
        self.db = connect(self.root / "ledger.sqlite3")

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def test_docx_embeds_image_without_duplicate_title_and_keeps_reviews_pending(self):
        paths = build(self.article, self.root / "output")
        with ZipFile(paths["docx"]) as z:
            xml = z.read("word/document.xml").decode()
            self.assertNotIn(self.article["title"], xml)
            self.assertIn("A concrete opening.", xml)
            self.assertEqual(1, len([n for n in z.namelist() if n.startswith("word/media/")]))
        audit = json.loads(Path(paths["audit"]).read_text(encoding="utf-8"))
        self.assertEqual("pending", audit["render_check"]["status"])
        self.assertTrue(all(v["status"] == "pending" for v in audit["quality_checks"].values()))
        with self.assertRaises(FileExistsError):
            build(self.article, self.root / "output")

    def test_duplicate_date_and_retitle_cannot_reserve_again(self):
        self.assertTrue(reserve(self.db, "account", self.article)["created"])
        changed = copy.deepcopy(self.article)
        changed["title"] = "A different title"
        changed["run_date"] = "2026-09-06"
        self.assertFalse(reserve(self.db, "account", changed)["created"])
        changed["run_date"] = self.article["run_date"]
        changed["lead"] = "Different body."
        self.assertFalse(reserve(self.db, "account", changed)["created"])

    def test_ambiguous_submission_cannot_blindly_retry(self):
        ident = reserve(self.db, "account", self.article)["id"]
        mark(self.db, "account", ident, "preview_verified", "Preview checked", "123")
        mark(self.db, "account", ident, "submitting", "About to click once")
        with self.assertRaises(ValueError):
            mark(self.db, "account", ident, "submitting", "Blind retry")
        mark(self.db, "account", ident, "unknown", "Response timed out")
        with self.assertRaises(ValueError):
            mark(self.db, "account", ident, "preview_verified", "No evidence")
        mark(self.db, "account", ident, "submitted_review", "Same ID under review")
        with self.assertRaises(ValueError):
            mark(self.db, "account", ident, "submitting", "Duplicate final click")

    def test_only_one_concurrent_worker_can_submit(self):
        ident = reserve(self.db, "account", self.article)["id"]
        mark(self.db, "account", ident, "preview_verified", "Checked", "123")
        def attempt(_):
            db = connect(self.root / "ledger.sqlite3")
            try:
                mark(db, "account", ident, "submitting", "Claim final click")
                return True
            except ValueError:
                return False
            finally:
                db.close()
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(1, sum(pool.map(attempt, range(2))))

    def test_missing_image_and_invalid_title_stop_build(self):
        invalid = copy.deepcopy(self.article)
        invalid["title"] = "x" * 31
        with self.assertRaises(ValueError):
            build(invalid, self.root / "bad-title")
        invalid = copy.deepcopy(self.article)
        invalid["image_sources"][0]["source"] = str(self.root / "missing.png")
        with self.assertRaises(ValueError):
            build(invalid, self.root / "bad-image")
        self.assertFalse((self.root / "bad-image").exists())

    def test_flagged_title_keeps_original_meaning(self):
        title = "\u4ea7\u54c1\u7ffb\u8f66\u4e86\uff1f"
        self.assertEqual(title, sanitize_title("  " + title + "  "))

    def test_explicit_extra_preserves_daily_limit_and_fingerprint_check(self):
        reserve(self.db, "account", self.article)
        extra = copy.deepcopy(self.article)
        extra["lead"] = "A distinct extra article."
        with self.assertRaises(ValueError):
            reserve(self.db, "account", extra, "manual-extra-1")
        self.assertTrue(reserve(self.db, "account", extra, "manual-extra-1", "Publish one extra")["created"])
        self.assertFalse(reserve(self.db, "account", extra, "manual-extra-2", "Extra")["created"])
        extra["lead"] = "Another different body."
        self.assertFalse(reserve(self.db, "account", extra)["created"])

    def test_legacy_database_preserves_ids_and_statuses(self):
        path = self.root / "legacy.sqlite3"
        old = sqlite3.connect(path)
        old.execute("""CREATE TABLE posts (
            id INTEGER PRIMARY KEY, account TEXT NOT NULL, run_date TEXT NOT NULL,
            fingerprint TEXT NOT NULL, title TEXT NOT NULL, status TEXT NOT NULL,
            platform_id TEXT, evidence TEXT NOT NULL, updated_at TEXT NOT NULL,
            UNIQUE(account,run_date), UNIQUE(account,fingerprint))""")
        old.execute("INSERT INTO posts VALUES (1,'account','2026-09-05','digest','title','published','123','observed','now')")
        old.commit()
        old.close()
        migrated = connect(path)
        try:
            row = migrated.execute("SELECT * FROM posts").fetchone()
            self.assertEqual((1, "published", "123", "daily"),
                             (row["id"], row["status"], row["platform_id"], row["edition"]))
        finally:
            migrated.close()


if __name__ == "__main__":
    unittest.main()
