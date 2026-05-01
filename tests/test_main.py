from __future__ import annotations

import csv
import importlib
import sys
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CODE_DIR = PROJECT_ROOT / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

main = importlib.import_module("main")
retrieval = importlib.import_module("retrieval")


class MainPipelineTests(TestCase):
    def test_process_tickets_normalizes_missing_fields(self) -> None:
        with tempfile.TemporaryDirectory(dir=PROJECT_ROOT) as temp_dir:
            temp_path = Path(temp_dir)
            input_path = temp_path / "support_tickets.csv"
            output_path = temp_path / "output.csv"
            log_path = temp_path / "log.txt"

            with input_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=["Issue", "Subject", "Company"])
                writer.writeheader()
                writer.writerow({"Issue": "Need help", "Subject": "", "Company": ""})

            fake_docs = {"hackerrank": [], "claude": [], "visa": [], "all": ["fallback doc"]}

            with (
                patch.object(main, "INPUT_PATH", input_path),
                patch.object(main, "OUTPUT_PATH", output_path),
                patch.object(main, "LOG_PATH", log_path),
                patch.object(main, "load_documents", return_value=fake_docs),
                patch.object(main, "classify_request_type", return_value="product_issue"),
                patch.object(main, "classify_product_area", return_value="general_support"),
                patch.object(main, "decision_engine", return_value=(False, "benign", 25)),
                patch.object(main, "retrieve_docs", return_value=[]),
                patch.object(main, "generate_response", return_value="stub response"),
            ):
                rows = main.process_tickets(fake_docs)

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["issue"], "Need help")
            self.assertEqual(rows[0]["subject"], "")
            self.assertEqual(rows[0]["company"], "")
            self.assertEqual(rows[0]["status"], "replied")
            self.assertEqual(rows[0]["response"], "stub response")
            self.assertTrue(rows[0]["security_flag"] in {"true", "false"})

    def test_normalize_field_handles_nan_like_values(self) -> None:
        self.assertEqual(main._normalize_field(None), "")
        self.assertEqual(main._normalize_field(float("nan")), "")
        self.assertEqual(main._normalize_field("  value  "), "value")

    def test_retrieve_docs_uses_company_bucket_for_display_name(self) -> None:
        domain_docs = {
            "hackerrank": ["Hackerrank billing document"],
            "claude": ["Claude account guide"],
            "visa": ["Visa fraud guide"],
            "all": ["Global fallback doc"],
        }

        docs = retrieval.retrieve_docs("Claude account guide", domain_docs, "Claude")

        self.assertEqual(docs, ["claude account guide"[:600]])


if __name__ == "__main__":
    import unittest

    unittest.main()
