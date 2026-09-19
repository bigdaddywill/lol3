from __future__ import annotations

import html
import re
from datetime import datetime
from html.parser import HTMLParser
from typing import Any

from .bid_pipeline import scrape_url


SAB_BID_URL = "https://www.in.gov/apps/sab/bidsystem/sab_bviewer"


def _clean(value: str) -> str:
    value = html.unescape(re.sub(r"<[^>]+>", " ", value))
    return re.sub(r"\s+", " ", value).strip()


def _extract_email(value: str) -> str:
    match = re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", value)
    return match.group(0) if match else ""


def _extract_phone(value: str) -> str:
    match = re.search(r"(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}", value)
    return match.group(0) if match else ""


def _parse_datetime_candidates(value: str) -> list[tuple[str, str]]:
    text = _clean(value)
    results: list[tuple[str, str]] = []
    patterns = (
        ("%m/%d/%Y %I:%M %p", r"\b\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}\s*[AP]M\b"),
        ("%m/%d/%Y %H:%M", r"\b\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}\b"),
    )
    for fmt, pattern in patterns:
        for raw in re.findall(pattern, text, re.I):
            normalized = re.sub(r"\s+", " ", raw).strip()
            try:
                dt = datetime.strptime(normalized, fmt)
                results.append((dt.isoformat(timespec="minutes"), normalized))
            except ValueError:
                continue
    return results


class _SABTableParser(HTMLParser):
    """Parse SAB's legacy nested/malformed HTML table without regexing row structure."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_row = False
        self.in_cell = False
        self.in_link = False
        self.current_cell_text: list[str] = []
        self.current_href = ""
        self.current_row: list[dict[str, str]] = []
        self.rows: list[list[dict[str, str]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "tr":
            if self.in_row and self.current_row:
                self.rows.append(self.current_row)
            self.in_row = True
            self.current_row = []
            self.in_cell = False
            self.in_link = False
            self.current_cell_text = []
            self.current_href = ""
        elif self.in_row and tag in {"td", "th"}:
            if self.in_cell:
                self._finish_cell()
            self.in_cell = True
            self.in_link = False
            self.current_cell_text = []
            self.current_href = ""
        elif self.in_cell and tag == "a":
            self.in_link = True
            attrs_map = dict(attrs)
            self.current_href = html.unescape(attrs_map.get("href") or "")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"td", "th"} and self.in_cell:
            self._finish_cell()
        elif tag == "tr" and self.in_row:
            if self.in_cell:
                self._finish_cell()
            if self.current_row:
                self.rows.append(self.current_row)
            self.in_row = False
            self.in_link = False

    def handle_data(self, data: str) -> None:
        if self.in_cell:
            self.current_cell_text.append(data)

    def _finish_cell(self) -> None:
        text = " ".join(self.current_cell_text)
        self.current_row.append({"text": _clean(text), "href": self.current_href})
        self.in_cell = False
        self.in_link = False
        self.current_cell_text = []
        self.current_href = ""


def _parse_rows(html_text: str) -> list[dict[str, Any]]:
    parser = _SABTableParser()
    parser.feed(html_text)
    bids: list[dict[str, Any]] = []

    for cells in parser.rows:
        if len(cells) < 5:
            continue

        number = _clean(cells[0]["text"])
        if not re.match(r"^[A-Z0-9-]{6,}$", number):
            continue

        title_cell = cells[1]
        title = title_cell["text"]
        if not title:
            continue

        all_text = " | ".join(cell["text"] for cell in cells)
        dt_candidates = _parse_datetime_candidates(all_text)
        if not dt_candidates:
            continue
        deadline_iso, deadline_raw = dt_candidates[-1]

        manager_cell = ""
        for cell in cells[2:]:
            txt = cell["text"]
            if "@" in txt or _extract_phone(txt):
                manager_cell = txt
                break

        requirement = (
            "Prequalification Required"
            if "prequalification required" in all_text.lower()
            else ""
        )

        posted = ""
        if cells:
            tail_dates = _parse_datetime_candidates(cells[-1]["text"])
            if tail_dates:
                posted = tail_dates[0][1]
            else:
                bare_dates = re.findall(r"\b\d{1,2}/\d{1,2}/\d{4}\b", cells[-1]["text"])
                posted = bare_dates[0] if bare_dates else ""

        bids.append({
            "project_name": title,
            "source_url": title_cell["href"] or SAB_BID_URL,
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
            "poc_raw": manager_cell,
            "poc_name": manager_cell.split(" ")[0] if manager_cell else "",
            "poc_email": _extract_email(manager_cell),
            "poc_phone": _extract_phone(manager_cell),
            "bid_text": _clean(" ".join([title, requirement, "Indiana"])),
        })

    return bids


def parse_sab_bids(html_text: str, source_url: str = SAB_BID_URL) -> list[dict[str, Any]]:
    return _parse_rows(html_text)


def scrape_sab_bids(url: str = SAB_BID_URL) -> list[dict[str, Any]]:
    return parse_sab_bids(scrape_url(url), source_url=url)
