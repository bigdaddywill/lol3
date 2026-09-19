from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from pipeline import Bid, Contractor, Match, SearchResult, extract_bid, generate_email, generate_sms, load_contractors, rank_matches, search_bing, source_field

def make_xlsx(path: Path):
    workbook = '''<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="On Leads Magnet" sheetId="1" r:id="rId1"/></sheets></workbook>'''
    rels = '''<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>'''
    sheet = '''<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>Company Name</t></is></c><c r="B1" t="inlineStr"><is><t>Email</t></is></c><c r="C1" t="inlineStr"><is><t>City</t></is></c><c r="D1" t="inlineStr"><is><t>State</t></is></c><c r="E1" t="inlineStr"><is><t>Trade</t></is></c></row><row r="2"><c r="A2" t="inlineStr"><is><t>Acme Tree Care</t></is></c><c r="B2" t="inlineStr"><is><t>ops@acme.example</t></is></c><c r="C2" t="inlineStr"><is><t>Raleigh</t></is></c><c r="D2" t="inlineStr"><is><t>NC</t></is></c><c r="E2" t="inlineStr"><is><t>Tree Trimming</t></is></c></row></sheetData></worksheet>'''
    with ZipFile(path, "w", ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>')
        z.writestr("xl/workbook.xml", workbook)
        z.writestr("xl/_rels/workbook.xml.rels", rels)
        z.writestr("xl/worksheets/sheet1.xml", sheet)

def test_workbook_load(tmp_path):
    p=tmp_path/"c.xlsx"
    make_xlsx(p)
    rows,audit=load_contractors(p)
    assert len(rows)==1 and rows[0].trade=="Tree Trimming" and audit["rows_loaded"]==1

def test_bid_extraction():
    r=SearchResult("Test","https://example.org/bid")
    b=extract_bid(r,"Walmart Exterior Tree Pruning","Scope of work: Prune limbs, remove deadwood and haul debris. Project Location: Raleigh, NC. Bid Due: December 1, 2026. Contact: Jane Doe jane@example.org 919-555-1212. Bid # ABC-123")
    assert b.scope and b.scope.source_url==r.url and b.location.value=="Raleigh, NC" and b.due_date.value=="December 1, 2026" and b.contact_email.value=="jane@example.org"

def test_match_and_outreach():
    c=Contractor(sheet="x",company="Acme Tree Care",contact="John",email="john@example.com",city="Raleigh",state="NC",trade="Tree Trimming")
    b=Bid(title="Invitation to Bid - Walmart Exterior Tree Pruning",source_url="https://example.org/bid",source_domain="example.org",scope=source_field("Prune limbs and haul debris.","https://example.org/bid"),location=source_field("Raleigh, NC","https://example.org/bid"),due_date=source_field("December 1, 2026","https://example.org/bid"))
    m=rank_matches(c,[b],minimum_score=1)[0]
    subject,email=generate_email(m)
    sms=generate_sms(m)
    assert m.score>=60 and "https://example.org/bid" in email and "John" in sms and len(sms)<=480

def test_no_hallucinated_contact():
    c=Contractor(sheet="x",company="Acme",city="Raleigh",state="NC",trade="Tree")
    b=Bid(title="Bid Without Contact",source_url="https://example.org/x",source_domain="example.org")
    m=Match(contractor=c,bid=b,score=0,reasons=[])
    _,email=generate_email(m)
    assert "Not stated in the source" in email


def test_bing_result_parser(monkeypatch):
    class Resp:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def read(self, n):
            return b'<html><li class="b_algo"><h2><a href="https://example.org/bid">Invitation to Bid - Roof Repair</a></h2></li></html>'
        def geturl(self):
            return "https://www.bing.com/search"
        def getcode(self):
            return 200
        def getheaders(self):
            return []
        @property
        def headers(self):
            return type("H", (), {"get_content_charset": lambda self: "utf-8"})()
    monkeypatch.setattr("pipeline.urlopen", lambda *args, **kwargs: Resp())
    results = search_bing("roofing bid")
    assert results and results[0].title == "Invitation to Bid - Roof Repair"
    assert results[0].url == "https://example.org/bid"
