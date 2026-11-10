"""Regression and API tests for Contract Version Comparison."""

import time
import unittest
from io import BytesIO

from docx import Document
from fastapi.testclient import TestClient

from contract_compare import compare_contracts, risk_level, split_clauses
from main import app

client = TestClient(app)


def make_docx(text: str) -> bytes:
    document = Document()
    for line in text.splitlines():
        if line.strip():
            document.add_paragraph(line)
    output = BytesIO()
    document.save(output)
    return output.getvalue()


class CompareLogicTests(unittest.TestCase):
    def test_identical_versions_have_no_changes(self):
        result = compare_contracts("1. PAYMENT. Pay within 30 days.", "1. PAYMENT. Pay within 30 days.")
        self.assertEqual(result["verdict"], "No changes")
        self.assertEqual(result["summary"]["unchanged"], 1)

    def test_whitespace_and_line_break_changes_are_ignored(self):
        result = compare_contracts("1. PAYMENT.\nPay within 30 days.", "1. payment. Pay   within 30 days.")
        self.assertEqual(result["summary"]["modified"], 0)
        self.assertEqual(result["summary"]["unchanged"], 1)

    def test_payment_period_change_is_detected_as_riskier(self):
        result = compare_contracts("1. PAYMENT. Pay within 30 days.", "1. PAYMENT. Pay within 90 days.")
        change = result["changes"][0]
        self.assertEqual(change["status"], "modified")
        self.assertIn({"before": "30 days", "after": "90 days"}, change["key_terms"])
        self.assertEqual(result["verdict"], "Riskier")

    def test_new_non_compete_is_high_risk(self):
        result = compare_contracts("1. SERVICES. Provide design services.",
                                   "1. SERVICES. Provide design services.\n2. NON-COMPETE. Contractor agrees to a non-compete.")
        added = next(c for c in result["changes"] if c["status"] == "added")
        self.assertEqual(added["after_risk"], "High")

    def test_deleting_liability_cap_increases_risk(self):
        # Compare against a remaining clause because an empty version is rejected.
        result = compare_contracts("1. LIABILITY. Liability shall not exceed $10,000.\n2. TERM. This agreement lasts one year.",
                                   "1. TERM. This agreement lasts one year.")
        removed = next(c for c in result["changes"] if c["status"] == "removed")
        self.assertEqual(removed["risk_change"], "Protection removed")
        self.assertEqual(result["verdict"], "Riskier")

    def test_reordered_clause_is_reported_as_moved(self):
        result = compare_contracts("1. SERVICES. Design a website.\n2. PAYMENT. Pay $500.",
                                   "1. PAYMENT. Pay $500.\n2. SERVICES. Design a website.")
        self.assertEqual(result["summary"]["moved"], 1)
        self.assertEqual(result["summary"]["modified"], 0)

    def test_added_clause_at_top_keeps_existing_clauses_unchanged(self):
        result = compare_contracts("1. SERVICES. Design a website.\n2. PAYMENT. Pay $500.",
                                   "1. NEW. Add a non-compete.\n2. SERVICES. Design a website.\n3. PAYMENT. Pay $500.")
        self.assertEqual(result["summary"]["added"], 1)
        self.assertEqual(result["summary"]["unchanged"], 2)
        self.assertEqual(result["summary"]["modified"], 0)

    def test_risk_levels_include_high_medium_low_and_none(self):
        self.assertEqual(risk_level("A non-compete applies for two years."), "High")
        self.assertEqual(risk_level("Payment is due within 90 days."), "Medium")
        self.assertEqual(risk_level("The parties will use reasonable efforts."), "Low")
        self.assertIsNone(risk_level("This contract is governed by New York law."))

    def test_numbered_sample_splits_into_preamble_and_clauses(self):
        sample = "AGREEMENT\n\nThis agreement is between A and B.\n\n1. TERM. One year.\n2. PAYMENT. $100."
        self.assertEqual(len(split_clauses(sample)), 4)

    def test_unmodified_version_without_numbered_headings(self):
        result = compare_contracts("Payment is due within 30 days.\n\nThe term is one year.",
                                   "Payment is due within 30 days.\n\nThe term is one year.")
        self.assertEqual(result["summary"]["unchanged"], 2)

    def test_same_heading_with_rewritten_clause_is_modified(self):
        result = compare_contracts("1. PAYMENT. Pay on receipt.", "1. PAYMENT. Pay within 90 days after acceptance.")
        self.assertEqual(result["summary"]["modified"], 1)
        self.assertEqual(result["summary"]["added"], 0)
        self.assertEqual(result["summary"]["removed"], 0)

    def test_long_contract_comparison_is_fast(self):
        before = "\n".join(f"{i}. SECTION. Standard unchanged clause number {i}." for i in range(1, 121))
        after = before.replace("clause number 73", "amended clause number 73")
        start = time.perf_counter()
        result = compare_contracts(before, after)
        elapsed = time.perf_counter() - start
        self.assertEqual(result["summary"]["modified"], 1)
        self.assertLess(elapsed, 5)

    def test_word_diff_and_disclaimer_are_in_response(self):
        result = compare_contracts("1. PAYMENT. Pay 30 days.", "1. PAYMENT. Pay 90 days.")
        self.assertTrue(any(part["kind"] in {"removed", "added"} for part in result["changes"][0]["word_diff"]))
        self.assertIn("not legal advice", result["disclaimer"].lower())

    def test_russian_text_changes_are_detected_without_risk_classification(self):
        result = compare_contracts("1. ОПЛАТА. Оплата в течение 30 дней.",
                                   "1. ОПЛАТА. Оплата в течение 90 дней.")
        self.assertEqual(result["summary"]["modified"], 1)
        self.assertIsNone(result["changes"][0]["after_risk"])

    def test_removing_automatic_renewal_reduces_risk(self):
        result = compare_contracts("1. RENEWAL. This agreement automatically renews each year.",
                                   "1. RENEWAL. This agreement renews only by written agreement.")
        self.assertEqual(result["verdict"], "Safer")
        self.assertLess(result["risk_delta"], 0)

    def test_multiple_similar_payment_clauses_keep_their_headings(self):
        before = ("1. FIRST PAYMENT. Pay $100 on signing.\n"
                  "2. SECOND PAYMENT. Pay 40% at the milestone.\n"
                  "3. FINAL PAYMENT. Pay 30% at acceptance.")
        after = ("1. FIRST PAYMENT. Pay $100 on signing.\n"
                 "2. SECOND PAYMENT. Pay 50% at the milestone.\n"
                 "3. FINAL PAYMENT. Pay 20% at acceptance.")
        result = compare_contracts(before, after)
        modified = [c for c in result["changes"] if c["status"] == "modified"]
        self.assertEqual(len(modified), 2)
        terms = [[(t["before"], t["after"]) for t in c["key_terms"]] for c in modified]
        self.assertIn([("40%", "50%")], terms)
        self.assertIn([("30%", "20%")], terms)

    def test_each_change_has_required_fields(self):
        result = compare_contracts("1. PAYMENT. Pay in 30 days.", "1. PAYMENT. Pay in 90 days.")
        required = {"status", "before_text", "after_text", "before_risk", "after_risk",
                    "risk_change", "risk_delta", "key_terms", "word_diff"}
        self.assertTrue(all(required.issubset(change) for change in result["changes"]))

    def test_percentages_are_extracted_as_key_terms(self):
        result = compare_contracts("1. PAYMENT. Pay 40% at signing.", "1. PAYMENT. Pay 50% at signing.")
        self.assertIn({"before": "40%", "after": "50%"}, result["changes"][0]["key_terms"])

    def test_empty_file_upload_fields_are_rejected(self):
        response = client.post("/api/compare/files")
        self.assertEqual(response.status_code, 422)

    def test_html_like_clause_content_is_returned_as_plain_data(self):
        response = client.post("/api/compare", json={
            "v1": "1. CLAUSE. <script>alert('old')</script> term.",
            "v2": "1. CLAUSE. <script>alert('new')</script> term.",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("<script>", response.json()["changes"][0]["after_text"])


class CompareApiTests(unittest.TestCase):
    def test_post_compare_returns_summary_changes_and_disclaimer(self):
        response = client.post("/api/compare", json={"v1": "1. PAYMENT. 30 days.", "v2": "1. PAYMENT. 90 days."})
        self.assertEqual(response.status_code, 200)
        self.assertTrue({"summary", "changes", "disclaimer"}.issubset(response.json()))

    def test_empty_version_returns_422(self):
        response = client.post("/api/compare", json={"v1": "", "v2": "1. TERM. One year."})
        self.assertEqual(response.status_code, 422)

    def test_version_over_limit_returns_413(self):
        response = client.post("/api/compare", json={"v1": "x" * 200_001, "v2": "valid text"})
        self.assertEqual(response.status_code, 413)

    def test_two_docx_files_can_be_compared(self):
        older = make_docx("1. PAYMENT. The client must pay the approved invoice within 30 days after receiving the final deliverable.")
        newer = make_docx("1. PAYMENT. The client must pay the approved invoice within 90 days after receiving the final deliverable.")
        response = client.post("/api/compare/files", files={
            "v1": ("old.docx", older, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
            "v2": ("new.docx", newer, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["verdict"], "Riskier")

    def test_unsupported_file_returns_415(self):
        response = client.post("/api/compare/files", files={
            "v1": ("old.exe", b"old", "application/octet-stream"),
            "v2": ("new.txt", b"This is a sufficiently long legal clause for extraction.", "text/plain"),
        })
        self.assertEqual(response.status_code, 415)

    def test_file_over_10mb_returns_413(self):
        response = client.post("/api/compare/files", files={
            "v1": ("old.txt", b"x" * (10 * 1024 * 1024 + 1), "text/plain"),
            "v2": ("new.txt", b"This is a sufficiently long legal clause for extraction.", "text/plain"),
        })
        self.assertEqual(response.status_code, 413)


if __name__ == "__main__":
    unittest.main()
