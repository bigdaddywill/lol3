import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

from openpyxl import Workbook

from pipeline.production import (
    BidRecord,
    Contractor,
    _load_rows_from_xlsx,
    bid_is_open,
    dedupe_bids,
    generate_messages,
    load_contractors,
    make_bid_id,
    extract_indot_letting_datetime,
    parse_indot_notice_text,
    score_contract_match,
    validate_outreach,
    valid_email,
    valid_phone,
)


class ProductionTests(unittest.TestCase):
    def test_realistic_xlsx_loader_and_duplicate_removal(self):
        with __import__("tempfile").TemporaryDirectory() as td:
            path = Path(td) / "contractors.xlsx"
            wb = Workbook()
            ws = wb.active
            ws.title = "On Leads Magnet"
            ws.append([
                "business_name", "first_name", "last_name", "email_address",
                "business_phone", "cell_phone", "city", "state", "zip_code",
                "category", "source_sheet", "leads_magnet_url"
            ])
            ws.append(["Percrete", "Lucas", "Perez", "lp@example.com", "", "2602392608",
                       "Indianapolis", "IN", "46241", "Concrete & Masonry", "TEST", "https://example.com/p"])
            ws.append(["Percrete", "Lucas", "Perez", "lp@example.com", "", "2602392608",
                       "Indianapolis", "IN", "46241", "Concrete & Masonry", "TEST", "https://example.com/p"])
            wb.save(path)
            wb.close()

            contractors, audit = load_contractors(path)

        self.assertEqual(len(contractors), 1)
        self.assertEqual(audit["duplicates_removed"], 1)
        self.assertEqual(audit["rows_loaded"], 1)
        self.assertEqual(contractors[0].phone, "2602392608")

    def test_email_phone_validation(self):
        self.assertTrue(valid_email("lp@example.com"))
        self.assertFalse(valid_email("not-an-email"))
        self.assertTrue(valid_phone("2602392608"))
        self.assertFalse(valid_phone("12345"))

    def test_state_gate_blocks_wrong_state(self):
        bid = BidRecord(
            bid_id="b1", source_type="test", source_url="https://example.com/bid",
            source_domain="example.com", project_name="Indiana Concrete Sidewalk",
            scope="concrete sidewalk replacement", location="Indianapolis, IN", state="IN",
            deadline="October 1, 2099", deadline_iso="2099-10-01T10:00:00+00:00",
        )
        contractor = Contractor(
            contractor_id="c1", business_name="Wrong State Concrete",
            email="x@example.com", city="Columbus", state="OH", category="Concrete & Masonry",
        )
        result = score_contract_match(contractor, bid)
        self.assertFalse(result["eligible"])
        self.assertIn("state mismatch", result["reasons"])

    def test_same_state_trade_match_is_open_and_sendable(self):
        bid = BidRecord(
            bid_id="b1", source_type="test", source_url="https://example.com/bid",
            source_domain="example.com", project_name="Indiana Concrete Sidewalk",
            scope="concrete sidewalk replacement", location="Indianapolis, IN", state="IN",
            deadline="October 1, 2099", deadline_iso="2099-10-01T10:00:00+00:00",
        )
        contractor = Contractor(
            contractor_id="c1", business_name="Percrete", first_name="Lucas",
            email="lp@example.com", city="Indianapolis", state="IN",
            zip_code="46241", category="Concrete & Masonry",
        )
        result = score_contract_match(contractor, bid)
        self.assertTrue(result["eligible"])
        self.assertEqual(result["open_status"], "open")
        validation = validate_outreach(bid, contractor, result)
        self.assertTrue(validation["ready_for_email"])
        messages = generate_messages(bid, contractor, result)
        self.assertIn("Percrete", messages["email_body"])
        self.assertIn("October 1, 2099", messages["email_body"])
        self.assertLessEqual(len(messages["follow_up_sms"]), 480)

    def test_closed_bid_never_becomes_email_ready(self):
        bid = BidRecord(
            bid_id="b1", source_type="test", source_url="https://example.com/bid",
            source_domain="example.com", project_name="Closed Concrete Job",
            scope="concrete slab", location="Indianapolis, IN", state="IN",
            deadline="January 1, 2020", deadline_iso="2020-01-01T10:00:00+00:00",
        )
        contractor = Contractor(
            contractor_id="c1", business_name="Percrete", email="lp@example.com",
            city="Indianapolis", state="IN", category="Concrete & Masonry",
        )
        status, _ = bid_is_open(bid, datetime(2026, 9, 19, tzinfo=timezone.utc))
        self.assertEqual(status, "closed")
        result = score_contract_match(contractor, bid)
        self.assertFalse(result["eligible"])

    def test_unknown_deadline_requires_review(self):
        bid = BidRecord(
            bid_id="b1", source_type="test", source_url="https://example.com/bid",
            source_domain="example.com", project_name="Unknown Deadline Job",
            scope="concrete slab", location="Indianapolis, IN", state="IN",
        )
        contractor = Contractor(
            contractor_id="c1", business_name="Percrete", email="lp@example.com",
            city="Indianapolis", state="IN", category="Concrete & Masonry",
        )
        result = score_contract_match(contractor, bid)
        self.assertTrue(result["eligible"])
        validation = validate_outreach(bid, contractor, result)
        self.assertFalse(validation["ready_for_email"])
        self.assertIn("bid_not_verified_open", validation["errors"])

    def test_dedup_uses_stable_bid_id(self):
        a = BidRecord(
            bid_id="", source_type="test", source_url="https://example.com/a",
            source_domain="example.com", project_name="Same Job", state="IN",
            solicitation="R-123", location="Indianapolis, IN", scope="concrete"
        )
        b = BidRecord(
            bid_id="", source_type="test", source_url="https://example.com/a",
            source_domain="example.com", project_name="Same Job", state="IN",
            solicitation="R-123", location="Indianapolis, IN", scope="concrete plus details"
        )
        self.assertEqual(make_bid_id(a), make_bid_id(b))
        self.assertEqual(len(dedupe_bids([a, b])), 1)

    def test_indot_letting_datetime_survives_pdf_line_breaks(self):
        fixture = """NOTICE TO HIGHWAY CONTRACTORS
Letting Date & Time:
October 7, 2026
at 10:00 AM
"""
        deadline, deadline_iso = extract_indot_letting_datetime(fixture)
        self.assertEqual(deadline, "October 7, 2026 10:00 AM")
        self.assertEqual(deadline_iso, "2026-10-07T10:00+00:00")

    def test_indot_notice_parser(self):
        fixture = """NOTICE TO HIGHWAY CONTRACTORS
Letting Date & Time: October 7, 2026 at 10:00 AM
130
R -43748-A SMALL STRUCTURE REPLACEMENT
Call Seymour District
Contract
Project Control No. Federal/State No. Location
2100771 2100771 SMALL STRUCTURE REPLACEMENT CV I64-031-102.15 CULVERT
HARRISON COUNTY - ON I-64 OVER UNNAMED TRIBUTARY, 3.38
MILES WEST OF SR 135
November 13, 2027 0.00
C(B) E(E)
Completion Date DBE Goal:
Qualifications:"""
        bids = parse_indot_notice_text(fixture, "https://www.in.gov/example.pdf", "2026-09-19T00:00:00+00:00")
        self.assertEqual(len(bids), 1)
        self.assertEqual(bids[0].solicitation, "R-43748-A")
        self.assertIn("SMALL STRUCTURE REPLACEMENT", bids[0].project_name)
        self.assertEqual(bids[0].state, "IN")

if __name__ == "__main__":
    unittest.main()
