import tempfile
import unittest
from pathlib import Path

from pipeline.bid_pipeline import (
    generate_outreach,
    match_contractors,
    parse_reference_html,
    read_contractors_tsv,
    score_match,
)


FIXTURE_TSV = """txt sheet_row\tbusiness_name\tfirst_name\tlast_name\temail_address\tbusiness_phone\tcell_phone\tcity\tstate\tzip_code\tcategory\tsource_sheet\tleads_magnet_url\tleads_magnet_title\tlisting_slug\tmatch_reason\tsponsored\tclaimed\tangi_url
166\tGustavo Bustamante\tGustavo\tBustamante\tgustavo@example.com\t\t7205795996\tDenver\tCO\t80247\tConcrete & Masonry\tTEST\thttps://example.com/gustavo\tGustavo Bustamante\tgustavo-bustamante\tlive-url\t\thttps://example.com/gustavo
179\tPercrete\tLucas\tPerez\tlp@example.com\t\t2602392608\tIndianapolis\tIN\t46241\tConcrete & Masonry\tTEST\thttps://example.com/percrete\tPercrete\tpercrete\tlive-url\t\thttps://example.com/percrete
202\tJLAM CONSTRUCTION\tJose\tAlberto Munoz\tjlam@example.com\t\t6264126736\tPigeon Forge\tTN\t37863\tCarpenters\tTEST\thttps://example.com/jlam\tJLAM CONSTRUCTION\tjlam-construction\tlive-url\t\thttps://example.com/jlam
"""


class PipelineTests(unittest.TestCase):
    def test_tsv_parser_tolerates_header_quirk(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "hi"
            p.write_text(FIXTURE_TSV, encoding="utf-8")
            rows = read_contractors_tsv(p)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["sheet_row"], "166")
        self.assertEqual(rows[1]["category"], "Concrete & Masonry")

    def test_reference_html_parser_extracts_bid_fields(self):
        html = """
        <html><body>
        <div style="border:1px solid #d0d5dd;border-radius:8px;">
          <div>Invitation for Bids · score 17</div>
          <h2><a href="https://example.com/bid">Camp Atterbury Covered Training Area Facility</a></h2>
          <p>Commercial building slab and foundations.</p>
          <table>
            <tr><td><b>Agency</b></td><td>Indiana Army National Guard</td></tr>
            <tr><td><b>Deadline</b></td><td>Sep 09, 2026</td></tr>
            <tr><td><b>Place</b></td><td>Edinburgh, IN 46124</td></tr>
            <tr><td><b>Set-aside</b></td><td>IDOA Certificate of Qualification 1542.04 required</td></tr>
            <tr><td><b>POC</b></td><td>Elysia Justice · contracting@example.com · (317) 552-1674</td></tr>
          </table>
          <p>Why this matched: commercial building slab / foundation</p>
        </div>
        </body></html>
        """
        bids = parse_reference_html(html)
        self.assertEqual(len(bids), 1)
        self.assertEqual(bids[0]["project_name"], "Camp Atterbury Covered Training Area Facility")
        self.assertEqual(bids[0]["deadline"], "Sep 09, 2026")
        self.assertEqual(bids[0]["poc_email"], "contracting@example.com")
        self.assertEqual(bids[0]["score_source"], 17)

    def test_indiana_concrete_beats_wrong_state_carpenter(self):
        bid = {
            "project_name": "Camp Atterbury Covered Training Area Facility",
            "scope": "commercial building slab and foundations",
            "location": "Camp Atterbury, Edinburgh, IN 46124",
            "state": "IN",
        }
        contractors = [
            {
                "sheet_row": "179",
                "business_name": "Percrete",
                "first_name": "Lucas",
                "email_address": "lp@example.com",
                "city": "Indianapolis",
                "state": "IN",
                "category": "Concrete & Masonry",
            },
            {
                "sheet_row": "202",
                "business_name": "JLAM CONSTRUCTION",
                "first_name": "Jose",
                "email_address": "jlam@example.com",
                "city": "Pigeon Forge",
                "state": "TN",
                "category": "Carpenters",
            },
        ]
        matches = match_contractors(bid, contractors)
        self.assertEqual(matches[0]["business_name"], "Percrete")
        self.assertGreater(matches[0]["score"], score_match(bid, contractors[1])["score"])
        self.assertEqual(matches[0]["confidence"], "high")

    def test_non_concrete_out_of_state_is_not_selected(self):
        bid = {
            "project_name": "Concrete Sidewalk Replacement",
            "scope": "sidewalk and PCCP work",
            "location": "Columbus, IN",
            "state": "IN",
        }
        contractor = {
            "sheet_row": "202",
            "business_name": "JLAM CONSTRUCTION",
            "first_name": "Jose",
            "email_address": "jlam@example.com",
            "city": "Pigeon Forge",
            "state": "TN",
            "category": "Carpenters",
        }
        self.assertEqual(match_contractors(bid, [contractor]), [])

    def test_outreach_discloses_unverified_requirements(self):
        bid = {
            "project_name": "Camp Atterbury Covered Training Area Facility",
            "scope": "commercial building slab and foundations",
            "location": "Camp Atterbury, Edinburgh, IN 46124",
            "deadline": "Sep 09, 2026",
            "source_url": "https://example.com/bid",
            "state": "IN",
            "requirements": "IDOA Certificate of Qualification 1542.04 required",
        }
        contractor = {
            "sheet_row": "179",
            "business_name": "Percrete",
            "first_name": "Lucas",
            "email_address": "lp@example.com",
            "city": "Indianapolis",
            "state": "IN",
            "category": "Concrete & Masonry",
        }
        match = score_match(bid, contractor)
        out = generate_outreach(bid, contractor, match)
        joined = "\n".join(out.values())
        self.assertIn("Percrete", joined)
        self.assertIn("Camp Atterbury Covered Training Area Facility", joined)
        self.assertIn("Sep 09, 2026", joined)
        self.assertIn("not been independently verified", joined)
        self.assertNotIn("licensed", joined.lower())


if __name__ == "__main__":
    unittest.main()
