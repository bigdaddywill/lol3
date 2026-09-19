from __future__ import annotations

import argparse
import html
import json
import re
import urllib.request
from email import policy
from email.parser import BytesParser
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


CATEGORY_ALIASES = {
    "concrete & masonry": {"concrete", "masonry"},
    "additions and remodels": {"general construction", "renovation", "building", "foundation"},
    "carpenters": {"building", "renovation", "general construction"},
    "flooring": {"flooring", "slab"},
}

SCOPE_KEYWORDS = {
    "slab": {"slab", "foundation", "on-grade", "on grade", "footing"},
    "flatwork": {"sidewalk", "walkway", "trail", "curb", "flatwork", "pccp", "pavement", "patching"},
    "structural": {"reinforced concrete", "box culvert", "3-sided", "structure"},
    "paving": {"paving", "pavement", "overlay", "patching"},
    "building": {"building", "facility", "renovation", "school", "maintenance and repair", "general trades"},
}

CONCRETE_TERMS = (
    "concrete", "pccp", "sidewalk", "slab", "foundation", "curb",
    "reinforced", "box culvert", "3-sided", "paving", "patching", "overlay",
)


def normalize(value: Any) -> str:
    text = "" if value is None else str(value)
    text = html.unescape(text).replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip().lower()


def normalize_state(value: Any) -> str:
    return normalize(value).upper()


def normalize_row(raw: dict[str, Any]) -> dict[str, Any]:
    row_number = raw.get("sheet_row") or raw.get("txt sheet_row") or raw.get("row")
    return {
        "sheet_row": str(row_number or "").strip(),
        "business_name": str(raw.get("business_name") or "").strip(),
        "first_name": str(raw.get("first_name") or "").strip(),
        "last_name": str(raw.get("last_name") or "").strip(),
        "email_address": str(raw.get("email_address") or "").strip(),
        "business_phone": str(raw.get("business_phone") or "").strip(),
        "cell_phone": str(raw.get("cell_phone") or "").strip(),
        "city": str(raw.get("city") or "").strip(),
        "state": str(raw.get("state") or "").strip(),
        "zip_code": str(raw.get("zip_code") or "").strip(),
        "category": str(raw.get("category") or "").strip(),
        "source_sheet": str(raw.get("source_sheet") or "").strip(),
        "leads_magnet_url": str(raw.get("leads_magnet_url") or "").strip(),
        "leads_magnet_title": str(raw.get("leads_magnet_title") or "").strip(),
        "listing_slug": str(raw.get("listing_slug") or "").strip(),
        "match_reason": str(raw.get("match_reason") or "").strip(),
        "sponsored": str(raw.get("sponsored") or "").strip(),
        "claimed": str(raw.get("claimed") or "").strip(),
        "angi_url": str(raw.get("angi_url") or "").strip(),
    }


def read_contractors_tsv(path: str | Path) -> list[dict[str, Any]]:
    text = Path(path).read_text(encoding="utf-8-sig")
    lines = [line.rstrip("\r") for line in text.replace("\r\n", "\n").split("\n") if line.strip()]
    if not lines:
        return []
    headers = lines[0].split("\t")
    while headers and not headers[-1].strip():
        headers.pop()
    result = []
    for line in lines[1:]:
        cells = line.split("\t")
        if len(cells) < len(headers):
            cells.extend([""] * (len(headers) - len(cells)))
        raw = {headers[i].strip(): cells[i] if i < len(cells) else "" for i in range(len(headers))}
        if raw.get("txt sheet_row") and not raw.get("sheet_row"):
            raw["sheet_row"] = raw["txt sheet_row"]
        row = normalize_row(raw)
        if row["business_name"]:
            result.append(row)
    return result


class _CardParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.card_start_depth: int | None = None
        self.cards: list[str] = []
        self.current: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "div" and any(k == "style" and "border:1px solid #d0d5dd" in (v or "") for k, v in attrs):
            self.card_start_depth = self.depth
            self.current = []
        if self.current is not None:
            rendered = " ".join(f'{k}="{v or ""}"' for k, v in attrs)
            self.current.append(f"<{tag}{(' ' + rendered) if rendered else ''}>")
        self.depth += 1

    def handle_endtag(self, tag: str) -> None:
        self.depth = max(0, self.depth - 1)
        if self.current is not None:
            self.current.append(f"</{tag}>")
            if tag == "div" and self.card_start_depth == self.depth:
                self.cards.append("".join(self.current))
                self.current = None
                self.card_start_depth = None

    def handle_data(self, data: str) -> None:
        if self.current is not None:
            self.current.append(html.escape(data))


def _clean_tag_text(value: str) -> str:
    text = html.unescape(re.sub(r"<[^>]+>", " ", value)).replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def parse_reference_html(html_text: str, default_state: str = "") -> list[dict[str, Any]]:
    parser = _CardParser()
    parser.feed(html_text)
    bids: list[dict[str, Any]] = []

    for card in parser.cards:
        title_match = re.search(
            r'<h2[^>]*>\s*<a\s+href="([^"]+)"[^>]*>\s*(.*?)\s*</a>',
            card,
            re.I | re.S,
        )
        if not title_match:
            continue

        title = _clean_tag_text(title_match.group(2))
        source_url = html.unescape(title_match.group(1))
        score_match = re.search(r"score\s+(\d+)", _clean_tag_text(card), re.I)
        scope_match = re.search(r"<h2[\s\S]*?</h2>\s*<p[^>]*>(.*?)</p>", card, re.I)
        why_match = re.search(r"Why this matched:\s*(.*?)</p>", card, re.I | re.S)

        fields: dict[str, str] = {}
        for label, value in re.findall(
            r"<tr>\s*<td[^>]*><b>([^<]+)</b></td>\s*<td[^>]*>(.*?)</td>\s*</tr>",
            card,
            re.I | re.S,
        ):
            fields[normalize(label)] = _clean_tag_text(value)

        poc_match = re.search(r"<b>POC</b></td>\s*<td>(.*?)</td>", card, re.I | re.S)
        poc_text = _clean_tag_text(poc_match.group(1)) if poc_match else ""
        poc_parts = [p.strip() for p in re.split(r"[·•]", poc_text) if p.strip()]

        bid = {
            "project_name": title,
            "source_url": source_url,
            "score_source": int(score_match.group(1)) if score_match else None,
            "scope": _clean_tag_text(scope_match.group(1)) if scope_match else "",
            "agency": fields.get("agency", ""),
            "solicitation": fields.get("solicitation", ""),
            "posted": fields.get("posted", ""),
            "deadline": fields.get("deadline", ""),
            "naics": fields.get("naics", ""),
            "requirements": fields.get("set-aside", ""),
            "location": fields.get("place", ""),
            "poc_raw": poc_text,
            "poc_name": poc_parts[0] if poc_parts else "",
            "poc_email": next((p for p in poc_parts if "@" in p), ""),
            "poc_phone": next((p for p in poc_parts if re.search(r"\d", p) and "@" not in p), ""),
            "why_matched_source": _clean_tag_text(why_match.group(1)) if why_match else "",
        }
        bid["bid_text"] = normalize(" ".join([
            bid["project_name"], bid["scope"], bid["agency"], bid["requirements"], bid["location"]
        ]))
        bid["state"] = infer_state(bid["location"]) or normalize_state(default_state)
        bids.append(bid)

    return bids


def infer_state(location: str) -> str:
    match = re.search(
        r"\b(IN|Indiana|OH|MI|IL|KY|PA|NY|MA|DE|MD|TX|CA|FL|GA|NC|SC|TN|AL|CO|NV|WI|MN)\b",
        location,
        re.I,
    )
    if not match:
        return ""
    aliases = {
        "indiana": "IN",
        "ohio": "OH",
        "michigan": "MI",
        "illinois": "IL",
        "kentucky": "KY",
    }
    return aliases.get(match.group(1).lower(), match.group(1).upper())


def extract_eml(path: str | Path) -> tuple[str, str]:
    raw = Path(path).read_bytes()
    msg = BytesParser(policy=policy.default).parsebytes(raw)
    subject = str(msg.get("Subject") or "")
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                return part.get_content(), subject
    if msg.get_content_type() == "text/html":
        return msg.get_content(), subject
    raise ValueError("No HTML MIME part found in EML")


def extract_eml_html(path: str | Path) -> str:
    return extract_eml(path)[0]


def scrape_url(url: str, timeout: int = 20) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        content_type = response.headers.get("Content-Type", "")
        if "html" not in content_type.lower():
            raise ValueError(f"Expected HTML, got {content_type!r}")
        return response.read().decode("utf-8", errors="replace")


def scope_tokens(text: str) -> set[str]:
    normalized = normalize(text)
    return {
        bucket for bucket, phrases in SCOPE_KEYWORDS.items()
        if any(phrase in normalized for phrase in phrases)
    }


def contractor_trade_tokens(contractor: dict[str, Any]) -> set[str]:
    category = normalize(contractor.get("category"))
    tokens = set(CATEGORY_ALIASES.get(category, set()))
    if "concrete" in category or "masonry" in category:
        tokens.add("concrete")
    return tokens


def score_match(bid: dict[str, Any], contractor: dict[str, Any]) -> dict[str, Any]:
    bid_text = normalize(bid.get("bid_text") or " ".join([
        bid.get("project_name", ""), bid.get("scope", ""), bid.get("location", "")
    ]))
    category = normalize(contractor.get("category"))
    bid_state = normalize_state(bid.get("state") or infer_state(bid.get("location", "")))
    contractor_state = normalize_state(contractor.get("state"))

    reasons: list[str] = []
    evidence: list[str] = []
    trade_score = 0

    if "concrete" in contractor_trade_tokens(contractor):
        if any(term in bid_text for term in CONCRETE_TERMS):
            trade_score = 55
            reasons.append("Concrete & Masonry category directly aligns with concrete-related bid scope.")
            evidence.append(f"contractor.category={contractor['category']}")
        else:
            trade_score = 25
            reasons.append("Concrete & Masonry category is relevant, but concrete scope evidence is weak.")
    elif any(term in bid_text for term in ("building", "renovation", "general trades")) and category in {
        "additions and remodels", "carpenters"
    }:
        trade_score = 28
        reasons.append(
            f"{contractor['category']} can cover general building/remodel scope, but concrete specialization is not documented."
        )

    state_score = 0
    if bid_state and contractor_state and bid_state == contractor_state:
        state_score = 25
        reasons.append(f"State match: bid={bid_state}, contractor={contractor_state}; distance/service area is not verified.")
        evidence.append(f"contractor.state={contractor['state']}")

    scope_score = 0
    buckets = scope_tokens(bid_text)
    if "slab" in buckets and "concrete" in contractor_trade_tokens(contractor):
        scope_score = 10
        reasons.append("Slab/foundation language supports concrete trade fit.")
    elif "flatwork" in buckets and "concrete" in contractor_trade_tokens(contractor):
        scope_score = 10
        reasons.append("Sidewalk/pavement/flatwork language supports concrete trade fit.")
    elif "structural" in buckets and "concrete" in contractor_trade_tokens(contractor):
        scope_score = 10
        reasons.append("Structural concrete language supports concrete trade fit.")
    elif "paving" in buckets and "concrete" in contractor_trade_tokens(contractor):
        scope_score = 8
        reasons.append("Paving/patching language supports concrete trade fit.")

    contact_score = 5 if contractor.get("email_address") else 0
    if contact_score:
        reasons.append("Email contact is present for outreach.")
        evidence.append("contractor.email_address=present")

    total = min(100, trade_score + state_score + scope_score + contact_score)
    confidence = "high" if total >= 85 and "concrete" in contractor_trade_tokens(contractor) else (
        "medium" if total >= 60 else "low"
    )

    missing = []
    if bid.get("requirements"):
        missing.append("Bid qualification requirements are present in source but contractor qualification is not documented.")
    if not contractor.get("city"):
        missing.append("Contractor city is missing.")
    if not contractor.get("email_address"):
        missing.append("Contractor email is missing.")

    return {
        "contractor_id": contractor.get("sheet_row") or contractor.get("listing_slug") or contractor.get("business_name"),
        "business_name": contractor.get("business_name", ""),
        "score": total,
        "confidence": confidence,
        "score_breakdown": {
            "trade_fit": trade_score,
            "state_fit": state_score,
            "scope_fit": scope_score,
            "contact_readiness": contact_score,
        },
        "reasons": reasons,
        "evidence": evidence,
        "unverified": missing,
    }


def match_contractors(
    bid: dict[str, Any],
    contractors: list[dict[str, Any]],
    limit: int = 10,
    strict_state: bool = True,
) -> list[dict[str, Any]]:
    bid_state = normalize_state(bid.get("state") or infer_state(bid.get("location", "")))

    eligible = []
    for contractor in contractors:
        contractor_state = normalize_state(contractor.get("state"))
        if strict_state and bid_state and contractor_state and contractor_state != bid_state:
            continue
        eligible.append(contractor)

    scored = [score_match(bid, c) for c in eligible]
    scored.sort(key=lambda x: (-x["score"], x["business_name"].lower()))
    return [m for m in scored if m["score"] >= 55][:limit]


def generate_outreach(
    bid: dict[str, Any], contractor: dict[str, Any], match: dict[str, Any]
) -> dict[str, str]:
    first_name = contractor.get("first_name") or "there"
    company = contractor.get("business_name") or "your company"
    project = bid.get("project_name") or "the project"
    location = bid.get("location") or bid.get("state") or "the project area"
    deadline = bid.get("deadline") or "the listed deadline"
    scope = bid.get("scope") or "the available scope"
    source_url = bid.get("source_url") or ""

    invitation = (
        f"Bid invitation — {project}\n\n"
        f"Hi {first_name},\n\n"
        f"Company: {company}\n"
        f"We have a potential fit for your {contractor.get('category') or 'contracting'} company: "
        f"{project} in {location}.\n\n"
        f"Scope: {scope}\n"
        f"Bid deadline: {deadline}\n"
        f"Listing: {source_url}\n\n"
        "Reply with whether you want the plans/specs and bid package, plus the best contact for this opportunity."
    )

    email_subject = f"Bid opportunity: {project} — {location}"
    email_body = (
        f"Hi {first_name},\n\n"
        f"Company: {company}\n\n"
        f"I’m reaching out about {project} in {location}. Based on your listed "
        f"{contractor.get('category') or 'contracting'} services and location, this looks potentially relevant.\n\n"
        f"Scope: {scope}\n"
        f"Bid deadline: {deadline}\n\n"
        f"If you want to review it, reply and I’ll send the bid package / next steps. Source: {source_url}\n\n"
        "Note: qualification or licensing requirements shown by the bid source have not been independently verified for your company."
    )

    sms = (
        f"Hi {first_name}, this is a bid opportunity for {project} in {location}, due {deadline}. "
        f"Your {contractor.get('category') or 'contracting'} listing matched the scope. Want the bid package? — Phantom/LOL3"
    )

    return {
        "bid_invitation": invitation,
        "email_subject": email_subject,
        "email_body": email_body,
        "follow_up_sms": sms,
    }


def run_pipeline(contractor_path: str, source_path: str, output_path: str) -> dict[str, Any]:
    contractors = read_contractors_tsv(contractor_path)
    html_text, subject = extract_eml(source_path)
    default_state = infer_state(subject)
    bids = parse_reference_html(html_text, default_state=default_state)

    results = []
    for bid in bids:
        matches = match_contractors(bid, contractors)
        enriched = []
        for match in matches:
            contractor = next(
                c for c in contractors
                if (c.get("sheet_row") or c.get("listing_slug") or c.get("business_name")) == match["contractor_id"]
            )
            enriched.append({
                "contractor": contractor,
                "match": match,
                "outreach": generate_outreach(bid, contractor, match),
            })
        results.append({"bid": bid, "matches": enriched})

    output = {
        "pipeline_version": "0.1",
        "source": str(source_path),
        "contractor_source": str(contractor_path),
        "bid_count": len(bids),
        "contractor_count": len(contractors),
        "results": results,
    }
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="LOL3 evidence-first bid matching + outreach pipeline")
    parser.add_argument("--contractors", default="hi")
    parser.add_argument(
        "--source",
        default="[Concrete _ Indiana] 8 open bids last 14 days — nearest deadline Aug 25, 2026.eml",
    )
    parser.add_argument("--output", default="artifacts/bid_pipeline.json")
    args = parser.parse_args()

    output = run_pipeline(args.contractors, args.source, args.output)
    matched = sum(1 for r in output["results"] if r["matches"])
    print(f"bids={output['bid_count']} contractors={output['contractor_count']} bids_with_matches={matched}")
    for item in output["results"]:
        names = ", ".join(m["contractor"]["business_name"] for m in item["matches"])
        print(f"[BID] {item['bid']['project_name']} -> {names or 'NO MATCH'}")


if __name__ == "__main__":
    main()
