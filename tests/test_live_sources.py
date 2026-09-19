import unittest

from pipeline.live_sources import parse_sab_bids


class LiveSourceParserTests(unittest.TestCase):
    def test_armory_board_row_parser(self):
        fixture = """
        <table>
          <tr>
            <th>Project Number</th><th>Project Title/Description</th><th>Pre-bid</th>
            <th>Bid Date and Time</th><th>SAB Project Manager</th><th>Viewer Information</th>
            <th>Date Entered</th><th>Last Modified</th>
          </tr>
          <tr>
            <td>MDI-CAIN-26-B-013</td>
            <td>
              <a href="https://www.in.gov/apps/sab/bidsystem/sab_bviewer">MUSCATATUCK URBAN TRAINING CENTER BLDG 5114 MAINTENANCE &amp; REPAIR</a>
              Prequalification Required
            </td>
            <td>8/26/2026 9:00 AM</td>
            <td>9/16/2026 11:00 AM</td>
            <td>Freeman Capps<br>freeman.d.capps.ctr@army.mil<br>460-701-7048</td>
            <td>Bidder Information</td>
            <td>8/19/2026</td>
            <td>8/19/2026</td>
          </tr>
        </table>
        """
        bids = parse_sab_bids(fixture)
        self.assertEqual(len(bids), 1)
        self.assertEqual(bids[0]["solicitation"], "MDI-CAIN-26-B-013")
        self.assertIn("MUSCATATUCK", bids[0]["project_name"])
        self.assertEqual(bids[0]["state"], "IN")
        self.assertEqual(bids[0]["requirements"], "Prequalification Required")
        self.assertEqual(bids[0]["poc_email"], "freeman.d.capps.ctr@army.mil")
        self.assertEqual(bids[0]["deadline_iso"], "2026-09-16T11:00")


if __name__ == "__main__":
    unittest.main()
