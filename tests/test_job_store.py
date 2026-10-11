"""Run: python3 -m unittest /workspace/grok-tools/tests/test_job_store.py -v
Works on a temp COPY of the real ledger; never writes to the real DB or Trello."""
import json, os, shutil, sqlite3, subprocess, sys, tempfile, unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import job_store as js  # noqa: E402

REAL_DB = HERE / "data" / "grok-tools.db"
S3 = "https://careers.strategicstaff.com/jobs/senior-ai-platform-engineer-248217/"


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.db = Path(self.tmp) / "copy.db"
        if REAL_DB.exists():
            src = sqlite3.connect(str(REAL_DB))
            dst = sqlite3.connect(str(self.db))
            src.backup(dst); src.close(); dst.close()
        self.conn = js.connect(self.db)

    def tearDown(self):
        self.conn.close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_tracking_variant_caught(self):
        variant = "http://WWW.careers.strategicstaff.com/jobs/senior-ai-platform-engineer-248217?utm_source=linkedin&utm_medium=social&ref=jobboard&gclid=abc#apply"
        kind, row = js.find_seen(self.conn, {"url": variant, "title": "x", "company": "y"})
        self.assertEqual(kind, "url")
        self.assertEqual(row["status"], "potential")
        self.assertEqual(js.normalize_url(variant), js.normalize_url(S3))

    def test_meaningful_params_kept(self):
        self.assertNotEqual(js.normalize_url("https://workato.com/careers?gh_jid=1"),
                            js.normalize_url("https://workato.com/careers?gh_jid=2"))

    def test_repost_dropped_then_allowed(self):
        item = {"title": "Senior AI Platform Engineer - 99812", "company": "Strategic Staffing Solutions, Inc.",
                "url": "https://www.dice.com/job-detail/some-other-board-id"}
        kept, dropped = js.filter_new(self.conn, [item])
        self.assertEqual((len(kept), dropped[0]["reason"]), (0, "repost"))
        kept, dropped = js.filter_new(self.conn, [item], allow_reposts=True)
        self.assertEqual(len(kept), 1)
        self.assertIn("Strategic Staffing", kept[0]["repostOf"])

    def test_known_items_all_dropped_new_kept(self):
        known = js.load_dig_items(Path("/workspace/tmp/dig-stl.out"))
        new = {"title": "AI Automation Engineer", "company": "Brand New Co", "url": "https://jobs.example.com/123?utm_source=x"}
        dupe_in_batch = dict(new, url="https://jobs.example.com/123/?ref=y")
        kept, dropped = js.filter_new(self.conn, known + [new, dupe_in_batch])
        self.assertEqual([k["company"] for k in kept], ["Brand New Co"])
        self.assertEqual(len(dropped), len(known) + 1)
        self.assertEqual(dropped[-1]["reason"], "duplicate-in-batch")

    def test_dead_seed_card_by_tracking_variant(self):
        kind, row = js.find_seen(self.conn, {"url": "https://koantek.zohorecruit.com/jobs/Careers/793183000001298001/Sr-AI-Engineer-Data-Scientist?source=LinkedIn&utm_campaign=z"})
        self.assertEqual((kind, row["status"]), ("url", "dead"))

    def test_status_never_downgraded_by_dig(self):
        js.upsert(self.conn, {"url": S3, "title": "Senior AI Platform Engineer"}, source="dig", status="seen")
        self.assertEqual(js.find_seen(self.conn, {"url": S3})[1]["status"], "potential")

    def test_non_job_schema_not_job_shaped(self):
        self.assertFalse(js.is_job_shaped(["title", "date", "venue", "url", "notes"]))
        self.assertFalse(js.is_job_shaped(["summary", "start", "end", "location", "url"]))
        self.assertTrue(js.is_job_shaped(["title", "company", "location", "pay", "postedDate", "url"]))
        self.assertTrue(js.is_job_shaped(["title", "pay", "url"]))

    def test_prompt_pairs_capped(self):
        pairs = js.seen_pairs_for_prompt(self.conn, limit=5, max_chars=300)
        self.assertLessEqual(len(pairs), 5)
        self.assertLessEqual(sum(len(p) + 2 for p in pairs), 300)

    def test_dig_replay_end_to_end(self):
        """dig.py path without an agent: --items-file replay against the temp DB copy."""
        items = js.load_dig_items(Path("/workspace/tmp/dig-stl.out"))
        items.append({"title": "AI Platform Engineer", "company": "OnePay",
                      "url": "https://jobs.ashbyhq.com/oneapp/a85bb5aa-9683-4d67-84e5-5d3e4bacda59?utm_source=indeed"})
        items.append({"title": "Agentic Workflow Engineer", "company": "Test Replay LLC",
                      "url": "https://boards.example.org/jobs/42", "pay": None})
        f = Path(self.tmp) / "replay.json"
        f.write_text(json.dumps({"items": items}))
        env = dict(os.environ, GROK_TOOLS_DB=str(self.db))
        proc = subprocess.run(
            [sys.executable, str(HERE / "dig.py"), "--schema-file", "/workspace/tmp/stl-ai-jobs.schema.json",
             "--items-file", str(f), "--prompt", "replay test", "--out", str(Path(self.tmp) / "doc.md")],
            capture_output=True, text=True, env=env, timeout=60)
        body = json.loads(proc.stdout.strip().splitlines()[-1])
        self.assertTrue(body["ok"], body)
        self.assertEqual([i["company"] for i in body["items"]], ["Test Replay LLC"])
        self.assertEqual(body["dedupe"]["received"], 8)
        self.assertEqual(body["dedupe"]["recorded"], 1)
        self.assertEqual(js.find_seen(self.conn, {"url": "https://boards.example.org/jobs/42/"})[0], "url")
        # --no-dedupe returns everything untouched
        proc = subprocess.run(
            [sys.executable, str(HERE / "dig.py"), "--schema-file", "/workspace/tmp/stl-ai-jobs.schema.json",
             "--items-file", str(f), "--prompt", "replay test", "--no-dedupe", "--out", str(Path(self.tmp) / "doc2.md")],
            capture_output=True, text=True, env=env, timeout=60)
        body = json.loads(proc.stdout.strip().splitlines()[-1])
        self.assertEqual(len(body["items"]), 8)
        self.assertNotIn("dedupe", body)


if __name__ == "__main__":
    unittest.main(verbosity=2)
