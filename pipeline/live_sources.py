from __future__ import annotations

import html
import re
from datetime import datetime
from typing import Any

from .bid_pipeline import scrape_url


SAB_BID_URL = "https://www.in.gov/apps/sab/bidsystem/sab_bviewer"


def _clean(value: str) -> str:
    value = html.unescape(re.sub(r"<[^>]+>", " ", value))
    return re.sub(r"\s+", " ", value).strip()


def _first_link(cell: str) -> tuple[str, str]:
    match = re.search(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', cell, re.I | re.S)
    if not match:
        return _clean(cell), ""
    return _clean(match.group(2)), html.unescape(match.group(1))


def _extract_email(value: str) -> str:
    match = re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", value)
    return match.group(0) if match else ""


def _extract_phone(value: str) -> str:
    match = re.search(r"(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}", value)
    return match.group(0) if match else ""


def _parse_deadline(value: str) -> tuple[str, str]:
    cleaned = _clean(value)
    for fmt in ("%m/%d/%Y %I:%M %p", "%m/%d/%Y %H:%M"):
        try:
            dt = datetime.strptime(cleaned, fmt)
            return dt.isoformat(timespec="minutes"), cleaned
        except ValueError:
            continue
    return "", cleaned


def parse_sab_bids(html_text: str, source_url: str = SAB_BID_URL) -> list[dict[str, Any]]:
    bids: list[dict[str, Any]] = []

    for row_html in re.findall(r"<tr\b[^>]*>(.*?)</tr>", html_text, re.I | re.S):
        cells = re.findall(r"<t[dh]\b[^>]*>(.*?)</t[dh]>", row_html, re.I | re.S)
        if len(cells) < 5:
            continue

        number = _clean(cells[0])
        if not re.match(r"^[A-Z0-9-]{6,}$", number):
            continue

        title, href = _first_link(cells[1])
        full_title = _clean(cells[1])
        requirement = "Prequalification Required" if "prequalification required" in full_title.lower() else ""

        deadline_iso, deadline_raw = _parse_deadline(cells[3])
        manager_raw = _clean(cells[4])
        posted = _clean(cells[-2]) if len(cells) >= 7 else ""

        if not title or not deadline_raw:
            continue

        bids.append({
            "project_name": title,
            "source_url": href or source_url,
            "source_type": "indiana_armory_board",
            "agency": "Indiana Army National Guard / State Armory Board",
            "solicitation": number,
            "scope": title,
            "location": "Indiana",
            "state": "IN",
            "deadline": deadline_raw,
            "deadline_iso": deadline_iso,
            "posted": posted,
            "requirements": requirement,
            "poc_raw": manager_raw,
            "poc_name": manager_raw.split(" ")[0] if manager_raw else "",
            "poc_email": _extract_email(manager_raw),
            "poc_phone": _extract_phone(manager_raw),
            "bid_text": _clean(" ".join([title, full_title, requirement, "Indiana"])),
        })

    return bids


def scrape_sab_bids(url: str = SAB_BID_URL) -> list[dict[str, Any]]:
    return parse_sab_bids(scrape_url(url), source_url=url)
