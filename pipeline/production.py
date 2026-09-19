from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Iterable

try:
    from openpyxl import load_workbook
except ImportError:  # pragma: no cover
    load_workbook = None

from .bid_pipeline import (
    CATEGORY_ALIASES,
    CONCRETE_TERMS,
    SCOPE_KEYWORDS,
    infer_state,
    normalize,
    normalize_state,
    scope_tokens,
)
from .live_sources import parse_sab_bids


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36"
)

STATE_BID_NETWORKS = {
    "NY": "https://www.newyorkbids.net/",
    "MA": "https://www.massbids.net/",
    "CA": "https://www.californiabids.com/",
    "OH": "https://www.ohiobids.com/",
    "TX": "https://www.texasbids.net/",
    "FL": "https://www.floridabids.net/",
}

SAB_URL = "https://www.in.gov/apps/sab/bidsystem/sab_bviewer"
INDOT_INDEX_URL = "https://www.in.gov/indot/doing-business-with-indot/home/contracts/"
PUBLIC_PURCHASE_INDIANA = "https://www.publicpurchase.com/gems/indianapolis%2Cin/buyer/public/home"

EMAIL_RE = re.compile(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", re.I)
PHONE_RE = re.compile(r"\d{10,15}")

TRADE_GROUPS = {
    "concrete": {"concrete", "masonry", "pccp", "slab", "foundation", "sidewalk", "curb", "culvert"},
    "roofing": {"roof", "roofing", "gutter", "gutters", "reroof", "downspout"},
    "painting": {"paint", "painting", "coating"},
    "flooring": {"floor", "flooring", "tile", "stone", "granite", "marble", "carpet", "vinyl"},
    "landscaping": {"landscape", "landscaping", "grounds", "tree", "arbor", "mowing", "mulch", "pruning"},
    "plumbing": {"plumbing", "plumber", "pipe", "piping", "drain"},
    "electrical": {"electrical", "electric", "lighting", "low voltage"},
    "general": {"general", "construction", "remodel", "renovation", "addition", "building", "carpentry"},
    "hvac": {"hvac", "mechanical", "heating", "cooling", "air conditioning"},
}


@dataclass
class Contractor:
    contractor_id: str
    business_name: str
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    business_phone: str = ""
    cell_phone: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    category: str = ""
    source_sheet: str = ""
    listing_url: str = ""

    @property
    def phone(self) -> str:
        return self.business_phone or self.cell_phone

    def to_dict(self) -> dict[str, Any]:
        return {
            "contractor_id": self.contractor_id,
            "business_name": self.business_name,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "business_phone": self.business_phone,
            "cell_phone": self.cell_phone,
            "phone": self.phone,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "category": self.category,
            "source_sheet": self.source_sheet,
            "listing_url": self.listing_url,
        }


@dataclass
class BidRecord:
    bid_id: str
    source_type: str
    source_url: str
    source_domain: str
    project_name: str
    agency: str = ""
    solicitation: str = ""
    scope: str = ""
    location: str = ""
    state: str = ""
    deadline: str = ""
    deadline_iso: str = ""
    posted: str = ""
    requirements: str = ""
    poc_name: str = ""
    poc_email: str = ""
    poc_phone: str = ""
    source_as_of: str = ""
    raw_excerpt: str = ""

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


def _cell(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in {"none", "nan", "nat"}:
        return ""
    return text


def _header_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", _cell(value).lower()).strip()


HEADER_ALIASES = {
    "business_name": ["business_name", "business name", "company", "company name", "contractor", "contractor name"],
    "first_name": ["first_name", "first name"],
    "last_name": ["last_name", "last name"],
    "email": ["email_address", "email", "email address", "e-mail"],
    "business_phone": ["business_phone", "business phone", "phone", "phone number"],
    "cell_phone": ["cell_phone", "cell phone", "mobile"],
    "city": ["city", "town"],
    "state": ["state", "state code", "province", "st"],
    "zip_code": ["zip_code", "zip code", "zip", "postal code"],
    "category": ["category", "trade", "specialty", "services", "service", "work type"],
    "source_sheet": ["source_sheet", "source sheet"],
    "listing_url": ["leads_magnet_url", "website", "url", "company website"],
    "sheet_row": ["sheet_row", "sheet row", "row"],
}


def _pick_header(headers: list[str], aliases: list[str]) -> str:
    keyed = {_header_key(h): h for h in headers if h}
    for alias in aliases:
        hit = keyed.get(_header_key(alias))
        if hit:
            return hit
    for header in headers:
        h = _header_key(header)
        if any(_header_key(alias) in h for alias in aliases):
            return header
    return ""


def _load_rows_from_xlsx(path: str | Path) -> tuple[list[dict[str, str]], dict[str, Any]]:
    if load_workbook is None:
        raise RuntimeError("openpyxl is required for XLSX contractor ingestion")
    wb = load_workbook(path, read_only=True, data_only=True)
    rows: list[dict[str, str]] = []
    audit = {
        "source": str(path),
        "sheets": [],
        "target_sheet": "On Leads Magnet",
        "rows_seen": 0,
        "rows_loaded": 0,
        "blank_rows": 0,
        "duplicates_removed": 0,
        "recovered_business_name_rows": 0,
        "unidentifiable_rows": 0,
        "header_mapping": {},
    }
    seen: set[tuple[str, str, str]] = set()
    try:
        target = next((ws for ws in wb.worksheets if _header_key(ws.title) == _header_key("On Leads Magnet")), None)
        for ws in wb.worksheets:
            audit["sheets"].append({"name": ws.title, "max_row": ws.max_row, "max_column": ws.max_column})
        if target is None:
            raise ValueError("Workbook does not contain an 'On Leads Magnet' sheet")
        iterator = target.iter_rows(values_only=True)
        first = next(iterator, None)
        headers = [_cell(v) for v in (first or [])]
        mapping = {field: _pick_header(headers, aliases) for field, aliases in HEADER_ALIASES.items()}
        audit["header_mapping"][target.title] = mapping
        for raw_values in iterator:
            values = [_cell(v) for v in raw_values]
            audit["rows_seen"] += 1
            if not any(values):
                audit["blank_rows"] += 1
                continue
            raw = {headers[i]: values[i] if i < len(values) else "" for i in range(len(headers)) if headers[i]}
            normalized = {
                field: raw.get(column, "") if column else ""
                for field, column in mapping.items()
            }
            if not normalized["business_name"]:
                fallback_name = " ".join(
                    x for x in (normalized.get("first_name", ""), normalized.get("last_name", ""))
                    if x
                ).strip()
                fallback_name = fallback_name or normalized.get("email", "").strip()
                fallback_name = fallback_name or normalized.get("business_phone", "").strip()
                fallback_name = fallback_name or normalized.get("cell_phone", "").strip()
                if not fallback_name:
                    audit["unidentifiable_rows"] += 1
                    continue
                normalized["business_name"] = fallback_name
                audit["recovered_business_name_rows"] += 1
            business_key = normalize(normalized["business_name"])
            email_key = normalize(normalized["email"])
            phone_key = re.sub(r"\D", "", normalized["business_phone"])
            fingerprint = (business_key, email_key, phone_key) if (email_key or phone_key) else None
            if fingerprint and fingerprint in seen:
                audit["duplicates_removed"] += 1
                continue
            if fingerprint:
                seen.add(fingerprint)
            rows.append(normalized)
        audit["rows_loaded"] = len(rows)
    finally:
        wb.close()
    return rows, audit


def _load_rows_from_tsv(path: str | Path) -> tuple[list[dict[str, str]], dict[str, Any]]:
    text = Path(path).read_text(encoding="utf-8-sig")
    lines = [line for line in text.replace("\r\n", "\n").split("\n") if line.strip()]
    if not lines:
        return [], {"source": str(path), "rows_loaded": 0, "rows_seen": 0, "duplicates_removed": 0}
    headers = lines[0].split("\t")
    while headers and not headers[-1].strip():
        headers.pop()
    rows: list[dict[str, str]] = []
    audit = {
        "source": str(path),
        "rows_seen": 0,
        "rows_loaded": 0,
        "blank_rows": 0,
        "duplicates_removed": 0,
        "recovered_business_name_rows": 0,
        "header_mapping": {},
    }
    seen: set[tuple[str, str, str]] = set()
    for line in lines[1:]:
        audit["rows_seen"] += 1
        cells = line.split("\t")
        cells += [""] * max(0, len(headers) - len(cells))
        raw = {headers[i].strip(): cells[i].strip() for i in range(len(headers))}
        normalized = {
            field: raw.get(_pick_header(headers, aliases), "")
            for field, aliases in HEADER_ALIASES.items()
        }
        if raw.get("txt sheet_row") and not normalized.get("sheet_row"):
            normalized["sheet_row"] = raw["txt sheet_row"]
        if not normalized["business_name"]:
            fallback_name = " ".join(
                x for x in (normalized.get("first_name", ""), normalized.get("last_name", ""))
                if x
            ).strip()
            fallback_name = fallback_name or normalized.get("email", "").strip()
            fallback_name = fallback_name or normalized.get("business_phone", "").strip()
            fallback_name = fallback_name or normalized.get("cell_phone", "").strip()
            if not fallback_name:
                audit["unidentifiable_rows"] += 1
                audit["blank_rows"] += 1
                continue
            normalized["business_name"] = fallback_name
            audit["recovered_business_name_rows"] += 1
        business_key = normalize(normalized["business_name"])
        email_key = normalize(normalized["email"])
        phone_key = re.sub(r"\D", "", normalized["business_phone"])
        fingerprint = (business_key, email_key, phone_key) if (email_key or phone_key) else None
        if fingerprint and fingerprint in seen:
            audit["duplicates_removed"] += 1
            continue
        if fingerprint:
            seen.add(fingerprint)
        rows.append(normalized)
    audit["rows_loaded"] = len(rows)
    return rows, audit


def load_contractors(path: str | Path) -> tuple[list[Contractor], dict[str, Any]]:
    suffix = Path(path).suffix.lower()
    rows, audit = _load_rows_from_xlsx(path) if suffix == ".xlsx" else _load_rows_from_tsv(path)
    contractors: list[Contractor] = []
    for row in rows:
        cid = row.get("sheet_row") or hashlib.sha1(
            f'{row.get("business_name","")}|{row.get("email","")}|{row.get("zip_code","")}'.encode()
        ).hexdigest()[:12]
        contractors.append(
            Contractor(
                contractor_id=cid,
                business_name=row.get("business_name", "").strip(),
                first_name=row.get("first_name", "").strip(),
                last_name=row.get("last_name", "").strip(),
                email=row.get("email", "").strip(),
                business_phone=row.get("business_phone", "").strip(),
                cell_phone=row.get("cell_phone", "").strip(),
                city=row.get("city", "").strip(),
                state=normalize_state(row.get("state", "")),
                zip_code=row.get("zip_code", "").strip(),
                category=row.get("category", "").strip(),
                source_sheet=row.get("source_sheet", "").strip(),
                listing_url=row.get("listing_url", "").strip(),
            )
        )
    audit["rows_with_email"] = sum(bool(c.email) for c in contractors)
    audit["rows_with_business_phone"] = sum(bool(c.business_phone) for c in contractors)
    audit["rows_with_any_phone"] = sum(bool(c.phone) for c in contractors)
    audit["rows_with_phone"] = audit["rows_with_any_phone"]
    audit["rows_with_location"] = sum(bool(c.city and c.state) for c in contractors)
    audit["rows_with_trade"] = sum(bool(c.category) for c in contractors)
    return contractors, audit


def fetch_text(url: str, timeout: int = 20, max_bytes: int = 5_000_000) -> tuple[int, str, str]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        body = response.read(max_bytes)
        content_type = response.headers.get("Content-Type", "")
        charset = response.headers.get_content_charset() or "utf-8"
        return getattr(response, "status", 200), content_type, body.decode(charset, errors="replace")


def _state_network_links(html_text: str, base_url: str) -> list[tuple[str, str]]:
    from html.parser import HTMLParser

    class Parser(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.open = False
            self.href = ""
            self.parts: list[str] = []
            self.links: list[tuple[str, str]] = []

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            if tag.lower() == "a":
                attrs_dict = dict(attrs)
                self.open = True
                self.href = attrs_dict.get("href") or ""
                self.parts = []

        def handle_data(self, data: str) -> None:
            if self.open:
                self.parts.append(data)

        def handle_endtag(self, tag: str) -> None:
            if tag.lower() == "a" and self.open:
                text = normalize(" ".join(self.parts))
                if text and self.href:
                    self.links.append((text, urllib.parse.urljoin(base_url, self.href)))
                self.open = False

    p = Parser()
    p.feed(html_text)
    return p.links


def _is_network_detail(url: str) -> bool:
    path = urllib.parse.urlparse(url).path.lower()
    return "/bid_opportunities/" in path and not any(
        bad in path for bad in ("/page/", "bid-result", "bid-results", "/register")
    )


def _parse_state_network_bid(url: str, title: str, html_text: str, state: str) -> BidRecord:
    text = normalize(re.sub(r"<[^>]+>", " ", html_text))
    scope = ""
    for label in ("scope", "scope of work", "project description"):
        m = re.search(rf"{re.escape(label)}\s*[:\-]\s*(.+?)(?:login to view|contact us|bids in {state.lower()}|$)", text, re.I)
        if m:
            scope = m.group(1).strip(" .")
            break

    date_tokens = re.findall(
        r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+\d{2,4}\b",
        text,
        re.I,
    )
    source_date = date_tokens[0] if date_tokens else ""
    deadline = ""
    deadline_m = re.search(
        r"(?:bid due|bid date|due date|closing date|close date|deadline|submission deadline)\s*[:\-]?\s*"
        r"((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+\d{2,4}(?:\s+\d{1,2}:\d{2}\s*(?:AM|PM))?)",
        text,
        re.I,
    )
    deadline = deadline_m.group(1).strip() if deadline_m else ""
    location = ""
    location_m = re.search(r"(?:location|project location|job site|place)\s*[:\-]\s*([^.;]{4,160})", text, re.I)
    if location_m:
        location = location_m.group(1).strip()
    poc_email = ""
    email_m = re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", text, re.I)
    if email_m:
        poc_email = email_m.group(0)
    poc_phone = ""
    phone_m = re.search(r"(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}", text)
    if phone_m:
        poc_phone = phone_m.group(0)

    solicitation = ""
    match = re.search(r"/(\d{7,})[-/]", urllib.parse.urlparse(url).path)
    if match:
        solicitation = match.group(1)

    return BidRecord(
        bid_id="",
        source_type="state_bid_network",
        source_url=url,
        source_domain=urllib.parse.urlparse(url).netloc.lower(),
        project_name=re.sub(r"^\s*Bid on\s+", "", title, flags=re.I).strip(),
        agency=f"{state} Bid Network",
        solicitation=solicitation,
        scope=scope,
        location=location,
        state=state,
        deadline=deadline,
        posted=source_date,
        poc_email=poc_email,
        poc_phone=poc_phone,
        source_as_of=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        raw_excerpt=text[:2000],
    )



def search_bing_rss(query: str, max_results: int = 8) -> list[tuple[str, str]]:
    url = "https://www.bing.com/search?format=rss&q=" + urllib.parse.quote_plus(query)
    try:
        _, _, xml = fetch_text(url)
    except Exception:
        return []
    results: list[tuple[str, str]] = []
    for item in re.findall(r"<item>(.*?)</item>", xml, re.I | re.S):
        title_m = re.search(r"<title>(.*?)</title>", item, re.I | re.S)
        link_m = re.search(r"<link>(.*?)</link>", item, re.I | re.S)
        if not title_m or not link_m:
            continue
        title = html.unescape(re.sub(r"<[^>]+>", " ", title_m.group(1))).strip()
        link = html.unescape(link_m.group(1)).strip()
        if title and link.startswith(("http://", "https://")):
            results.append((title, link))
        if len(results) >= max_results:
            break
    return results


def _generic_bid_record(state: str, title: str, url: str, html_text: str) -> BidRecord | None:
    domain = urllib.parse.urlparse(url).netloc.lower()
    if not (domain.endswith(".gov") or domain.endswith(".us") or any(domain.endswith(urllib.parse.urlparse(v).netloc) for v in STATE_BID_NETWORKS.values())):
        return None

    text = normalize(re.sub(r"<[^>]+>", " ", html_text))
    low = text.lower()
    blocked_markers = ("bid results", "bid result", "award notice", "contract awarded", "closed solicitation")
    if any(marker in low for marker in blocked_markers):
        return None

    bid_language = (
        "invitation to bid" in low
        or "request for bid" in low
        or "request for proposal" in low
        or "request for quotation" in low
        or re.search(r"\b(?:rfp|rfq|ifb|solicitation|bid opportunity|procurement)\b", low)
    )
    if not bid_language:
        return None

    due = ""
    due_m = re.search(
        r"(?:bid due|bid date|due date|deadline|submission deadline|closing date)\s*[:\-]?\s*"
        r"((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
        r"\s+\d{1,2},?\s+\d{2,4}(?:\s+\d{1,2}:\d{2}\s*(?:AM|PM))?)",
        text,
        re.I,
    )
    if due_m:
        due = due_m.group(1).strip()

    scope = ""
    scope_m = re.search(
        r"(?:scope of work|scope|project description|work includes)\s*[:\-]\s*(.{30,1000}?)(?:\s+(?:login|contact|attachments|bids in )|$)",
        text,
        re.I,
    )
    if scope_m:
        scope = scope_m.group(1).strip(" .")
    if not scope:
        scope = title

    location = ""
    location_m = re.search(
        r"(?:project location|job site|site address|location|place)\s*[:\-]\s*(.{4,180}?)(?:\s+(?:bid due|bid date|deadline|scope|contact)\b|$)",
        text,
        re.I,
    )
    if location_m:
        location = location_m.group(1).strip(" .")

    email = ""
    email_m = re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", text, re.I)
    if email_m:
        email = email_m.group(0)

    phone = ""
    phone_m = re.search(r"(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}", text)
    if phone_m:
        phone = phone_m.group(0)

    bid = BidRecord(
        bid_id="",
        source_type="web_fallback",
        source_url=url,
        source_domain=domain,
        project_name=title,
        agency="",
        scope=scope,
        location=location,
        state=state,
        deadline=due,
        poc_email=email,
        poc_phone=phone,
        source_as_of=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        raw_excerpt=text[:2000],
    )
    bid.bid_id = make_bid_id(bid)
    return bid


def scrape_web_fallback(state: str, trade: str, max_results: int = 5) -> tuple[list[BidRecord], dict[str, Any]]:
    health = {"source": f"web_fallback:{state}", "status": "unknown", "count": 0, "error": ""}
    queries = [
        f'site:.gov "{trade}" "{state}" "invitation to bid"',
        f'site:.gov "{trade}" "{state}" RFP OR IFB OR solicitation',
        f'"{trade}" "{state}" "bid opportunity"',
    ]
    seen: set[str] = set()
    bids: list[BidRecord] = []
    try:
        for query in queries:
            for title, url in search_bing_rss(query, max_results=max_results * 2):
                if url in seen:
                    continue
                seen.add(url)
                try:
                    _, _, page = fetch_text(url)
                except Exception:
                    continue
                bid = _generic_bid_record(state, title, url, page)
                if not bid:
                    continue
                bids.append(bid)
                if len(bids) >= max_results:
                    health["count"] = len(bids)
                    health["status"] = "ok"
                    return bids, health
        health["count"] = len(bids)
        health["status"] = "ok" if bids else "empty"
        return bids, health
    except Exception as exc:
        health["status"] = "error"
        health["error"] = repr(exc)
        return [], health


def scrape_state_network(state: str, trade: str, max_results: int = 8) -> tuple[list[BidRecord], dict[str, Any]]:
    state = normalize_state(state)
    base = STATE_BID_NETWORKS.get(state)
    health = {"source": f"state_bid_network:{state}", "status": "unknown", "count": 0, "error": ""}
    if not base:
        health["status"] = "unsupported"
        return [], health

    try:
        status, content_type, root = fetch_text(base)
    except Exception as exc:
        health["status"] = "error"
        health["error"] = repr(exc)
        return [], health

    if status >= 400:
        health["status"] = "error"
        health["error"] = f"http_status={status}"
        return [], health

    pages_to_scan = [(base, root)]
    today = datetime.now(timezone.utc).date()
    for days_back in range(0, 15):
        day = today - timedelta(days=days_back)
        pages_to_scan.append((
            urllib.parse.urljoin(base, f"bid_opportunities/{day:%Y/%m/%d}/"),
            "",
        ))
    links: list[tuple[str, str]] = []
    for page_url, page_html in pages_to_scan:
        if not page_html:
            try:
                _, _, page_html = fetch_text(page_url)
            except Exception:
                continue
        links.extend(_state_network_links(page_html, page_url))

    terms = trade_terms(trade)
    candidates = []
    seen_urls: set[str] = set()
    for title, url in links:
        if url in seen_urls or not _is_network_detail(url):
            continue
        seen_urls.add(url)
        low = f"{title} {url}".lower()
        hit_count = sum(1 for term in terms if term in low)
        generic = any(term in low for term in (
            "construction", "renovation", "remodel", "roof", "gutter", "painting",
            "floor", "tile", "building", "sidewalk", "concrete", "paving", "maintenance",
        ))
        if hit_count or generic:
            candidates.append((hit_count, title, url))
    candidates.sort(key=lambda x: (-x[0], x[1]))
    bids: list[BidRecord] = []

    for _, title, url in candidates[: max_results * 2]:
        try:
            _, _, page = fetch_text(url)
            bid = _parse_state_network_bid(url, title, page, state)
            if not bid.scope:
                continue
            bid.bid_id = make_bid_id(bid)
            bids.append(bid)
            if len(bids) >= max_results:
                break
        except Exception:
            continue

    health["count"] = len(bids)
    health["status"] = "ok" if bids else "empty"
    return bids, health


def parse_indot_notice_text(text: str, source_url: str, as_of: str) -> list[BidRecord]:
    flat = re.sub(r"\s+\n", "\n", text.replace("\r", ""))
    blocks = re.split(r"(?m)(?=^\s*[A-Z]\s*-\s*[A-Z0-9-]+\s+)", flat)
    bids: list[BidRecord] = []
    for block in blocks:
        head = re.search(r"(?m)^\s*([A-Z]\s*-\s*[A-Z0-9-]+)\s+(.+?)(?:\n|$)", block)
        if not head:
            continue

        solicitation = re.sub(r"\s+", "", head.group(1))
        title = head.group(2).strip()

        locations = re.findall(
            r"(?m)^\s*([A-Z][A-Z /-]+ COUNTY)\s+-\s+ON\s+(.+)$",
            block,
        )
        location = "; ".join(
            f"{county.title()} - {road.strip()}" for county, road in locations
        ) or "Indiana"

        qualifications = ""
        qual_m = re.search(
            r"(?m)^\s*([A-Z](?:\([A-Z]\))?(?:\s+[A-Z](?:\([A-Z]\))?)*)\s*$",
            block,
        )
        if qual_m:
            qualifications = qual_m.group(1).strip()

        scope = f"{title}. {block[:900].strip()}"
        bid = BidRecord(
            bid_id="",
            source_type="indot_ntc_pdf",
            source_url=source_url,
            source_domain="in.gov",
            project_name=title,
            agency="Indiana Department of Transportation",
            solicitation=solicitation,
            scope=scope,
            location=location,
            state="IN",
            source_as_of=as_of,
            raw_excerpt=block[:1600],
        )
        bid.bid_id = make_bid_id(bid)
        bids.append(bid)
    return bids

def scrape_indot_current() -> tuple[list[BidRecord], dict[str, Any]]:
    health = {"source": "indot_current_regular_letting", "status": "unknown", "count": 0, "error": ""}
    try:
        status, _, index_html = fetch_text(INDOT_INDEX_URL)
        if status >= 400:
            raise RuntimeError(f"http_status={status}")

        from html.parser import HTMLParser
        class _Links(HTMLParser):
            def __init__(self) -> None:
                super().__init__()
                self.in_a = False
                self.href = ""
                self.parts: list[str] = []
                self.items: list[tuple[str, str]] = []
            def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
                if tag.lower() == "a":
                    a = dict(attrs)
                    self.in_a = True
                    self.href = a.get("href") or ""
                    self.parts = []
            def handle_data(self, data: str) -> None:
                if self.in_a:
                    self.parts.append(data)
            def handle_endtag(self, tag: str) -> None:
                if tag.lower() == "a" and self.in_a:
                    text = " ".join(" ".join(self.parts).split())
                    if text and self.href:
                        self.items.append((text, urllib.parse.urljoin(INDOT_INDEX_URL, self.href)))
                    self.in_a = False

        p = _Links()
        p.feed(index_html)
        now = datetime.now(timezone.utc)
        candidates: list[tuple[datetime, str]] = []
        month_map = {m.lower(): i for i, m in enumerate(
            ("January", "February", "March", "April", "May", "June",
             "July", "August", "September", "October", "November", "December"), 1
        )}
        for text, url in p.items:
            if "regular letting" not in text.lower():
                continue
            m = re.search(
                r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s*"
                r"(January|February|March|April|May|June|July|August|September|October|November|December)"
                r"\s+(\d{1,2}),\s+(\d{4})",
                text,
                re.I,
            )
            if not m:
                m = re.search(
                    r"(January|February|March|April|May|June|July|August|September|October|November|December)"
                    r"\s+(\d{1,2}),\s+(\d{4})",
                    text,
                    re.I,
                )
            if not m:
                continue
            dt = datetime(int(m.group(3)), month_map[m.group(1).lower()], int(m.group(2)), 10, 0, tzinfo=timezone.utc)
            if dt >= now - timedelta(hours=6):
                candidates.append((dt, url))
        if not candidates:
            fallback_url = "https://www.in.gov/indot/doing-business-with-indot/home/contracts/letting-archives2/wednesday-october-7-2026-regular-letting/"
            candidates.append((now, fallback_url))
        _, letting_url = sorted(candidates)[0]

        _, _, letting_html = fetch_text(letting_url)
        pdf_m = re.search(r'href=["\']([^"\']+2026\d{4}-REG-NTC_[^"\']*\.pdf)["\']', letting_html, re.I)
        if not pdf_m:
            pdf_m = re.search(r'href=["\']([^"\']+REG-NTC_[^"\']*\.pdf)["\']', letting_html, re.I)
        if not pdf_m:
            raise RuntimeError("Notice to Contractors PDF link not found")
        pdf_url = urllib.parse.urljoin(letting_url, html.unescape(pdf_m.group(1)))

        from pypdf import PdfReader
        req = urllib.request.Request(pdf_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=30) as response:
            data = response.read(20_000_000)
        import io
        reader = PdfReader(io.BytesIO(data))
        text = "\n".join((pg.extract_text() or "") for pg in reader.pages)

        letting_match = re.search(
            r"Letting Date & Time:\s*([A-Za-z]+\s+\d{1,2},\s+\d{4})\s+at\s+(\d{1,2}:\d{2}\s*[AP]M)",
            text,
            re.I,
        )
        deadline = ""
        deadline_iso = ""
        if letting_match:
            deadline = f"{letting_match.group(1)} {letting_match.group(2)}"
            from datetime import datetime as _dt
            local = _dt.strptime(deadline, "%B %d, %Y %I:%M %p").replace(tzinfo=timezone.utc)
            deadline_iso = local.isoformat(timespec="minutes")

        bids = parse_indot_notice_text(
            text,
            source_url=pdf_url,
            as_of=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )
        for bid in bids:
            if deadline:
                bid.deadline = deadline
            if deadline_iso:
                bid.deadline_iso = deadline_iso
            bid.source_url = pdf_url

        health["count"] = len(bids)
        health["status"] = "ok" if bids else "empty"
        health["letting_url"] = letting_url
        health["notice_pdf"] = pdf_url
        return bids, health
    except Exception as exc:
        health["status"] = "error"
        health["error"] = repr(exc)
        return [], health

def scrape_sab_current() -> tuple[list[BidRecord], dict[str, Any]]:
    health = {"source": "indiana_armory_board", "status": "unknown", "count": 0, "error": ""}
    try:
        status, _, raw = fetch_text(SAB_URL)
        if status >= 400:
            raise RuntimeError(f"http_status={status}")
        bids_raw = parse_sab_bids(raw, source_url=SAB_URL)
        bids: list[BidRecord] = []
        for raw_bid in bids_raw:
            bid = BidRecord(
                bid_id="",
                source_type=raw_bid.get("source_type", "indiana_armory_board"),
                source_url=raw_bid.get("source_url", SAB_URL),
                source_domain="in.gov",
                project_name=raw_bid.get("project_name", ""),
                agency=raw_bid.get("agency", ""),
                solicitation=raw_bid.get("solicitation", ""),
                scope=raw_bid.get("scope", ""),
                location=raw_bid.get("location", "Indiana"),
                state="IN",
                deadline=raw_bid.get("deadline", ""),
                deadline_iso=raw_bid.get("deadline_iso", ""),
                posted=raw_bid.get("posted", ""),
                requirements=raw_bid.get("requirements", ""),
                poc_name=raw_bid.get("poc_name", ""),
                poc_email=raw_bid.get("poc_email", ""),
                poc_phone=raw_bid.get("poc_phone", ""),
                source_as_of=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                raw_excerpt=raw_bid.get("bid_text", ""),
            )
            bid.bid_id = make_bid_id(bid)
            bids.append(bid)
        health["count"] = len(bids)
        health["status"] = "ok" if bids else "empty"
        if not bids and "No Bids Posted at This Time" not in normalize(raw):
            health["status"] = "invalid_empty"
        return bids, health
    except Exception as exc:
        health["status"] = "error"
        health["error"] = repr(exc)
        return [], health


def source_health_public_purchase() -> dict[str, Any]:
    health = {"source": "public_purchase_indianapolis", "status": "unknown", "count": 0, "error": ""}
    try:
        status, _, body = fetch_text(PUBLIC_PURCHASE_INDIANA)
        normalized = normalize(body)
        health["status"] = (
            "auth_required"
            if "please log in to view the open bids" in normalized
            else ("ok" if status < 400 else "error")
        )
        health["http_status"] = status
        return health
    except Exception as exc:
        health["status"] = "error"
        health["error"] = repr(exc)
        return health


def trade_terms(category: str) -> set[str]:
    base = set(re.findall(r"[a-z0-9]+", normalize(category)))
    result = set(base)
    for terms in TRADE_GROUPS.values():
        if result & terms:
            result |= terms
    return result


def contractor_trade_terms(category: str) -> set[str]:
    category_norm = normalize(category)
    result = set(re.findall(r"[a-z0-9]+", category_norm))
    for label, terms in TRADE_GROUPS.items():
        if any(term in category_norm for term in terms) or category_norm == label:
            result |= terms
    return result


def bid_text(bid: BidRecord) -> str:
    return normalize(" ".join([
        bid.project_name, bid.scope, bid.location, bid.agency, bid.requirements,
    ]))


def bid_is_open(bid: BidRecord, as_of: datetime) -> tuple[str, str]:
    if not bid.deadline_iso and not bid.deadline:
        return "unknown", "No deadline supplied by source."
    if bid.deadline_iso:
        try:
            due = datetime.fromisoformat(bid.deadline_iso)
            if due.tzinfo is None:
                due = due.replace(tzinfo=timezone.utc)
            return ("open", "Deadline is in the future.") if due > as_of else ("closed", "Deadline has passed.")
        except ValueError:
            pass
    for fmt in (
        "%B %d, %Y %I:%M %p",
        "%B %d, %Y",
        "%b %d, %Y",
        "%m/%d/%Y %I:%M %p",
        "%m/%d/%Y",
    ):
        try:
            due = datetime.strptime(bid.deadline.strip(), fmt).replace(tzinfo=as_of.tzinfo)
            return ("open", "Deadline is in the future.") if due > as_of else ("closed", "Deadline has passed.")
        except ValueError:
            continue
    return "unknown", "Deadline could not be normalized."


def make_bid_id(bid: BidRecord) -> str:
    basis = "|".join([
        normalize(bid.source_domain),
        normalize(bid.solicitation),
        normalize(bid.project_name),
        normalize(bid.location),
    ])
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:20]


def dedupe_bids(bids: Iterable[BidRecord]) -> list[BidRecord]:
    buckets: dict[str, BidRecord] = {}
    for bid in bids:
        bid.bid_id = bid.bid_id or make_bid_id(bid)
        key = bid.bid_id
        existing = buckets.get(key)
        if not existing:
            buckets[key] = bid
            continue
        # Prefer the record with more factual fields and a direct source URL.
        old_fill = sum(bool(v) for v in existing.to_dict().values())
        new_fill = sum(bool(v) for v in bid.to_dict().values())
        if new_fill > old_fill:
            buckets[key] = bid
    return sorted(buckets.values(), key=lambda x: (normalize(x.state), x.deadline_iso or "9999", x.project_name.lower()))


def _trade_overlap(contractor: Contractor, bid: BidRecord) -> tuple[int, list[str]]:
    cterms = contractor_trade_terms(contractor.category)
    btext = bid_text(bid)
    hits = sorted(term for term in cterms if len(term) >= 3 and term in btext)
    return min(50, len(hits) * 8), hits[:8]


def score_contract_match(contractor: Contractor, bid: BidRecord) -> dict[str, Any]:
    reasons: list[str] = []
    evidence: list[str] = []
    state = normalize_state(bid.state or infer_state(bid.location))
    cstate = normalize_state(contractor.state)

    if state and cstate and state != cstate:
        return {
            "eligible": False,
            "score": 0,
            "confidence": "blocked",
            "reasons": ["state mismatch"],
            "evidence": [f"bid.state={state}", f"contractor.state={cstate}"],
            "breakdown": {},
        }

    score = 0
    breakdown = {"state": 0, "zip": 0, "city": 0, "trade": 0, "scope": 0, "contact": 0, "open_status": 0}

    if state and cstate and state == cstate:
        breakdown["state"] = 25
        score += 25
        reasons.append("Exact state match.")
        evidence.append(f"state={state}")

    location_norm = normalize(bid.location)
    city_norm = normalize(contractor.city)
    if city_norm and city_norm in location_norm:
        breakdown["city"] = 15
        score += 15
        reasons.append("Contractor city appears in the bid location.")
        evidence.append(f"city={contractor.city}")

    if contractor.zip_code and contractor.zip_code in bid.location:
        breakdown["zip"] = 20
        score += 20
        reasons.append("Exact contractor ZIP appears in the bid location.")
        evidence.append(f"zip={contractor.zip_code}")

    trade_score, hits = _trade_overlap(contractor, bid)
    if not hits:
        return {
            "eligible": False,
            "score": 0,
            "confidence": "blocked",
            "reasons": ["No documented trade/scope overlap."],
            "evidence": [],
            "breakdown": breakdown,
        }
    breakdown["trade"] = trade_score
    score += trade_score
    reasons.append("Trade overlap: " + ", ".join(hits))
    evidence.append("trade_overlap=" + ",".join(hits))

    buckets = scope_tokens(bid_text(bid))
    cterms = contractor_trade_terms(contractor.category)
    scope_score = 0
    if "concrete" in cterms and "structural" in buckets:
        scope_score = 10
        reasons.append("Structural-concrete scope aligns with Concrete & Masonry.")
    elif "concrete" in cterms and ("flatwork" in buckets or "paving" in buckets):
        scope_score = 10
        reasons.append("Flatwork/paving scope aligns with Concrete & Masonry.")
    elif "roofing" in cterms and "roof" in bid_text(bid):
        scope_score = 10
        reasons.append("Roofing scope aligns with Roofing & Gutters.")
    elif "painting" in cterms and "paint" in bid_text(bid):
        scope_score = 10
        reasons.append("Painting scope aligns with Painting.")
    breakdown["scope"] = scope_score
    score += scope_score

    if contractor.email and valid_email(contractor.email):
        breakdown["contact"] = 5
        score += 5
        reasons.append("Valid email is available for outreach.")
        evidence.append("email=valid")
    elif contractor.phone and valid_phone(contractor.phone):
        breakdown["contact"] = 2
        score += 2
        reasons.append("Valid phone is available for SMS outreach.")
        evidence.append("phone=valid")

    open_status, status_reason = bid_is_open(bid, datetime.now(timezone.utc))
    if open_status == "open":
        breakdown["open_status"] = 10
        score += 10
        reasons.append("Source deadline is still open at evaluation time.")
    elif open_status == "closed":
        return {
            "eligible": False,
            "score": 0,
            "confidence": "blocked",
            "reasons": ["Bid is closed.", status_reason],
            "evidence": [],
            "breakdown": breakdown,
        }
    else:
        reasons.append("Bid freshness/deadline is not fully verified.")
    
    confidence = "high" if score >= 80 and open_status == "open" else (
        "medium" if score >= 60 else "low"
    )

    return {
        "eligible": True,
        "score": min(score, 100),
        "confidence": confidence,
        "reasons": reasons,
        "evidence": evidence,
        "breakdown": breakdown,
        "open_status": open_status,
    }


def valid_email(value: str) -> bool:
    return bool(EMAIL_RE.fullmatch((value or "").strip()))


def valid_phone(value: str) -> bool:
    return bool(PHONE_RE.search(re.sub(r"\D", "", value or "")))


def validate_outreach(bid: BidRecord, contractor: Contractor, match: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not bid.source_url:
        errors.append("source_url_missing")
    if not bid.project_name:
        errors.append("project_name_missing")
    if match.get("open_status") != "open":
        errors.append("bid_not_verified_open")
    if not contractor.email:
        warnings.append("email_missing")
    elif not valid_email(contractor.email):
        errors.append("email_invalid")
    if contractor.phone and not valid_phone(contractor.phone):
        warnings.append("phone_invalid")
    if bid.requirements:
        warnings.append("contractor_qualification_not_verified")
    return {
        "ready_for_email": not errors and valid_email(contractor.email),
        "ready_for_sms": not errors and valid_phone(contractor.phone),
        "errors": errors,
        "warnings": warnings,
    }


def generate_messages(bid: BidRecord, contractor: Contractor, match: dict[str, Any]) -> dict[str, str]:
    first_name = contractor.first_name or contractor.business_name or "there"
    location = bid.location or bid.state or "the project area"
    deadline = bid.deadline or "the listed deadline"
    scope = bid.scope or "the available scope"
    subject = f"Bid opportunity: {bid.project_name} — {location}"
    body = (
        f"Hi {first_name},\n\n"
        f"Company: {contractor.business_name}\n\n"
        f"I’m reaching out about {bid.project_name} in {location}. "
        f"Your listed {contractor.category or 'contracting'} services match documented bid scope, "
        "so I wanted to put the opportunity in front of you.\n\n"
        f"Scope: {scope}\n"
        f"Bid deadline: {deadline}\n"
        f"Source: {bid.source_url}\n\n"
        "Reply if you want the plans/specs and bid package or the appropriate contact for this opportunity.\n\n"
        "Note: bid-side qualification requirements have not been independently verified for your company."
    )
    invitation = (
        f"INVITATION TO BID\n\n"
        f"Project: {bid.project_name}\n"
        f"Location: {location}\n"
        f"Scope: {scope}\n"
        f"Bid deadline: {deadline}\n"
        f"Source: {bid.source_url}\n\n"
        "Action requested: confirm whether you want the bid package and identify the person who will review it."
    )
    sms = (
        f"Hi {first_name}, bid opportunity: {bid.project_name} in {location}, due {deadline}. "
        "I can send the bid package. Reply YES and I’ll send it."
    )[:480]
    return {"email_subject": subject, "email_body": body, "bid_invitation": invitation, "follow_up_sms": sms}


def load_tracking(path: str | Path) -> dict[str, dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return {}
    state: dict[str, dict[str, Any]] = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        state[row["key"]] = row
    return state


def append_tracking(path: str | Path, rows: Iterable[dict[str, Any]]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def pair_key(bid: BidRecord, contractor: Contractor) -> str:
    return f"{bid.bid_id}:{contractor.contractor_id}"


def run_production(
    contractor_path: str | Path,
    output_dir: str | Path,
    states: set[str] | None = None,
    limit_contractors: int | None = None,
    max_bids_per_source: int = 8,
    tracking_path: str | Path | None = None,
    include_reference_eml: str | Path | None = None,
) -> dict[str, Any]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    contractors, contractor_audit = load_contractors(contractor_path)
    if states:
        contractors = [c for c in contractors if normalize_state(c.state) in {normalize_state(s) for s in states}]
    if limit_contractors:
        contractors = contractors[:limit_contractors]

    bids: list[BidRecord] = []
    health: list[dict[str, Any]] = []
    state_list = sorted({c.state for c in contractors if c.state})

    # Indiana direct sources.
    if "IN" in state_list:
        current, h = scrape_sab_current()
        bids.extend(current)
        health.append(h)
        health.append(source_health_public_purchase())
        current, h = scrape_indot_current()
        bids.extend(current)
        health.append(h)

    # Public state bid networks with known public opportunity indexes.
    seen_states = set()
    for state in state_list:
        if state in seen_states or state == "IN":
            continue
        seen_states.add(state)
        category = next((c.category for c in contractors if c.state == state and c.category), "construction")
        current, h = scrape_state_network(state, category, max_results=max_bids_per_source)
        bids.extend(current)
        health.append(h)
        if state not in STATE_BID_NETWORKS or not current:
            fallback, fallback_health = scrape_web_fallback(state, category, max_results=max_bids_per_source)
            bids.extend(fallback)
            health.append(fallback_health)

    if include_reference_eml:
        from .bid_pipeline import extract_eml, parse_reference_html
        html_text, subject = extract_eml(include_reference_eml)
        default_state = infer_state(subject)
        for raw in parse_reference_html(html_text, default_state=default_state):
            bid = BidRecord(
                bid_id="",
                source_type="reference_eml",
                source_url=raw.get("source_url", ""),
                source_domain=urllib.parse.urlparse(raw.get("source_url", "")).netloc.lower(),
                project_name=raw.get("project_name", ""),
                agency=raw.get("agency", ""),
                solicitation=raw.get("solicitation", ""),
                scope=raw.get("scope", ""),
                location=raw.get("location", ""),
                state=raw.get("state", ""),
                deadline=raw.get("deadline", ""),
                posted=raw.get("posted", ""),
                requirements=raw.get("requirements", ""),
                poc_name=raw.get("poc_name", ""),
                poc_email=raw.get("poc_email", ""),
                poc_phone=raw.get("poc_phone", ""),
                source_as_of=subject,
                raw_excerpt=raw.get("bid_text", ""),
            )
            bid.bid_id = make_bid_id(bid)
            bids.append(bid)
        health.append({"source": "reference_eml", "status": "fixture", "count": len(bids)})

    bids = dedupe_bids(bids)
    prior = load_tracking(tracking_path) if tracking_path else {}
    output_records: list[dict[str, Any]] = []
    tracking_rows: list[dict[str, Any]] = []

    for bid in bids:
        for contractor in contractors:
            match = score_contract_match(contractor, bid)
            if not match["eligible"]:
                continue
            validation = validate_outreach(bid, contractor, match)
            key = pair_key(bid, contractor)
            prior_row = prior.get(key)
            duplicate = bool(prior_row and prior_row.get("message_hash"))
            messages = generate_messages(bid, contractor, match) if not duplicate else {}
            message_hash = ""
            if messages:
                message_hash = hashlib.sha256(
                    (messages["email_subject"] + "\n" + messages["email_body"] + "\n" + messages["follow_up_sms"]).encode()
                ).hexdigest()
            record = {
                "key": key,
                "bid": bid.to_dict(),
                "contractor": contractor.to_dict(),
                "match": match,
                "validation": validation,
                "duplicate_from_tracking": duplicate,
                "messages": messages,
                "message_hash": message_hash,
                "send_gate": "HUMAN_REVIEW_REQUIRED",
            }
            output_records.append(record)
            tracking_rows.append({
                "key": key,
                "bid_id": bid.bid_id,
                "contractor_id": contractor.contractor_id,
                "status": "ready_email" if validation["ready_for_email"] and not duplicate else "needs_review",
                "message_hash": message_hash,
                "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            })

    Path(out / "contractor_audit.json").write_text(
        json.dumps(contractor_audit, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    Path(out / "source_health.json").write_text(
        json.dumps(health, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    Path(out / "bids.json").write_text(
        json.dumps([b.to_dict() for b in bids], indent=2, ensure_ascii=False), encoding="utf-8"
    )
    Path(out / "outreach_queue.json").write_text(
        json.dumps(output_records, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    Path(out / "manifest.json").write_text(
        json.dumps({
            "contractors_evaluated": len(contractors),
            "bids_deduped": len(bids),
            "outreach_records": len(output_records),
            "email_ready": sum(1 for r in output_records if r["validation"]["ready_for_email"]),
            "sms_ready": sum(1 for r in output_records if r["validation"]["ready_for_sms"]),
            "duplicates_blocked": sum(1 for r in output_records if r["duplicate_from_tracking"]),
            "sources": health,
        }, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    if tracking_path:
        append_tracking(tracking_path, tracking_rows)

    return {
        "contractor_audit": contractor_audit,
        "sources": health,
        "bids": bids,
        "records": output_records,
    }


def main() -> None:
    p = argparse.ArgumentParser(prog="lol3-production")
    p.add_argument("--contractors", required=True)
    p.add_argument("--output", default="artifacts/production")
    p.add_argument("--states", default="")
    p.add_argument("--limit-contractors", type=int, default=25)
    p.add_argument("--max-bids-per-source", type=int, default=8)
    p.add_argument("--tracking", default="")
    p.add_argument("--reference-eml", default="")
    args = p.parse_args()
    result = run_production(
        contractor_path=args.contractors,
        output_dir=args.output,
        states={x.strip().upper() for x in args.states.split(",") if x.strip()} or None,
        limit_contractors=args.limit_contractors or None,
        max_bids_per_source=args.max_bids_per_source,
        tracking_path=args.tracking or None,
        include_reference_eml=args.reference_eml or None,
    )
    print(json.dumps({
        "contractors_loaded": result["contractor_audit"].get("rows_loaded", 0),
        "contractors_seen": result["contractor_audit"].get("rows_seen", 0),
        "bids": len(result["bids"]),
        "records": len(result["records"]),
        "sources": result["sources"],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
