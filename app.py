"""
Citation Checker App - South African Legal Citation Verification
Verify / Audit / Certify
"""

import re
import io
import os
import time
from datetime import date
from urllib.parse import quote_plus, urljoin

import streamlit as st
import requests
from bs4 import BeautifulSoup
from docx import Document
import pdfplumber
from rapidfuzz import fuzz


# ---------------------------------------------------------------------------
# ERA-Style CSS
# ---------------------------------------------------------------------------

def inject_era_css():
    st.markdown("""
    <style>
    /* Global */
    .stApp { background-color: #F4F4F4; }

    /* Headers */
    h1, h2, h3 {
        color: #2C3E50 !important;
        font-family: Georgia, 'Times New Roman', serif !important;
        font-weight: normal;
        letter-spacing: 0.5px;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #2C3E50;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label {
        color: #F4F4F4 !important;
    }
    section[data-testid="stSidebar"] hr {
        border-color: #7F8C8D;
    }

    /* Buttons */
    .stButton > button {
        background-color: #2C3E50 !important;
        color: #F4F4F4 !important;
        border: 1px solid #7F8C8D !important;
        border-radius: 2px !important;
        font-family: Georgia, serif !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .stButton > button:hover {
        background-color: #7F8C8D !important;
        color: #F4F4F4 !important;
    }
    .stButton > button:disabled {
        background-color: #7F8C8D !important;
        opacity: 0.5;
    }

    /* Download button */
    .stDownloadButton > button {
        background-color: #2C3E50 !important;
        color: #F4F4F4 !important;
        border: 1px solid #7F8C8D !important;
        border-radius: 2px !important;
        font-family: Georgia, serif !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* File uploader */
    section[data-testid="stFileUploader"] {
        border: 2px dashed #7F8C8D;
        padding: 1rem;
        background-color: #FFFFFF;
    }

    /* Hide Streamlit branding */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }

    /* Audit table */
    .audit-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Courier New', 'Roboto Mono', monospace;
        font-size: 0.85rem;
        margin-top: 1rem;
    }
    .audit-table thead th {
        background-color: #2C3E50;
        color: #F4F4F4;
        padding: 12px 10px;
        text-align: left;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-size: 0.75rem;
        border-bottom: 2px solid #7F8C8D;
    }
    .audit-table tbody td {
        padding: 10px;
        border-bottom: 1px solid #D5D8DC;
        color: #2C3E50;
        vertical-align: top;
    }
    .audit-table tbody tr:hover {
        background-color: #EAECEE;
    }
    .status-verified { color: #27AE60; font-weight: bold; }
    .status-not-found { color: #C0392B; font-weight: bold; }
    .status-manual { color: #7F8C8D; font-weight: bold; }
    .status-error { color: #C0392B; font-weight: bold; }
    .status-typo { color: #F39C12; font-weight: bold; }
    .citation-name { font-family: Georgia, serif; font-style: italic; }
    .action-link {
        color: #2C3E50;
        text-decoration: underline;
        font-family: 'Courier New', monospace;
        font-size: 0.8rem;
    }
    .discrepancy-note {
        font-size: 0.75rem;
        color: #F39C12;
        font-style: italic;
        margin-top: 4px;
    }
    .saflii-citation {
        font-size: 0.75rem;
        color: #7F8C8D;
        margin-top: 2px;
    }
    .confidence-badge {
        display: inline-block;
        padding: 2px 6px;
        border-radius: 3px;
        font-size: 0.7rem;
        font-weight: bold;
    }
    .confidence-high { background-color: #D5F5E3; color: #1E8449; }
    .confidence-medium { background-color: #FEF9E7; color: #B7950B; }
    .confidence-low { background-color: #FADBD8; color: #922B21; }

    /* Terminal log */
    .terminal-log {
        background-color: #1a1a2e;
        color: #00ff88;
        font-family: 'Courier New', monospace;
        font-size: 0.85rem;
        padding: 1.2rem;
        border-radius: 2px;
        border: 1px solid #7F8C8D;
        max-height: 400px;
        overflow-y: auto;
        line-height: 1.6;
    }
    .terminal-log .log-header {
        color: #7F8C8D;
        margin-bottom: 0.5rem;
    }
    .terminal-log .log-found { color: #27AE60; }
    .terminal-log .log-type { color: #F39C12; }

    /* Tagline */
    .tagline {
        font-family: 'Courier New', monospace;
        color: #7F8C8D;
        letter-spacing: 3px;
        font-size: 0.9rem;
        margin-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Court Code Resolution (from saflii_fetcher.py)
# ---------------------------------------------------------------------------

COURT_ALIASES = {
    "CC": "ZACC",
    "SCA": "ZASCA",
    "ConCourt": "ZACC",
    "Constitutional Court": "ZACC",
    "Supreme Court of Appeal": "ZASCA",
    "WCC": "ZAWCHC",
    "GJ": "ZAGPJHC",
    "GP": "ZAGPPHC",
    "KZD": "ZAKZDHC",
    "KZP": "ZAKZPHC",
    "EC": "ZAECHC",
    "ECG": "ZAECGHC",
    "ECM": "ZAECMHC",
    "FS": "ZAFSHC",
    "NC": "ZANCHC",
    "NW": "ZANWHC",
    "LP": "ZALMPHC",
    "MP": "ZAMPMBHC",
    "LAC": "ZALAC",
    "LC": "ZALC",
    "LCC": "ZALCC",
    "A": "ZASCA",
    "W": "ZAWCHC",
    "N": "ZAKZDHC",
    "C": "ZAWCHC",
    "T": "ZAGPPHC",
    "D": "ZAKZDHC",
    "ECD": "ZAECMHC",
    "CPD": "ZAWCHC",
    "TPD": "ZAGPPHC",
    "NPD": "ZAKZDHC",
    "WLD": "ZAGPJHC",
    "GSJ": "ZAGPJHC",
}

VALID_COURT_CODES = {
    "ZACC", "ZASCA",
    # High Courts
    "ZAECBHC", "ZAECGHC", "ZAECQBHC", "ZAECMKHC", "ZAECMHC", "ZAECELLC",
    "ZAECPEHC", "ZAECHC", "ZAFSHC", "ZAGPHC", "ZAGPPHC", "ZAGPJHC",
    "ZAKZHC", "ZAKZDHC", "ZAKZPHC", "ZALMPHC", "ZALMPPHC", "ZALMPTHC",
    "ZAMPMBHC", "ZAMPMHC", "ZANCHC", "ZANWHC", "ZAWCHC",
    # Labour Courts
    "ZAIC", "ZALAC", "ZALC", "ZALCCT", "ZALCJHB", "ZALCPE", "ZALCD", "ZACCMA",
    # Specialist Courts
    "ZACAC", "ZACCP", "ZACOMMC", "ZACONAF", "ZAEC", "ZAEQC",
    "ZALCC", "ZARMC", "ZATC", "ZACT", "COMPTRI", "ZACGSO",
    "ZANCT", "ZAST", "ZAWT",
}


def resolve_court_code(code):
    """Resolve a court code or alias to the canonical SAFLII code."""
    upper = code.upper().strip()
    if upper in VALID_COURT_CODES:
        return upper
    if upper in COURT_ALIASES:
        return COURT_ALIASES[upper]
    with_za = f"ZA{upper}"
    if with_za in VALID_COURT_CODES:
        return with_za
    return upper


# ---------------------------------------------------------------------------
# Party Name Extraction (from File 05 design)
# ---------------------------------------------------------------------------

def extract_party_names(citation_string):
    """Extract Party A and Party B from a citation string.

    Returns (party_a, party_b) or (None, None) if no 'v' separator found.
    """
    match = re.search(
        r"([A-Z][A-Za-z\s&()]*?)\s+v\s+([A-Z][A-Za-z\s&()]*?)(?=\s*[\[\(]|\s*\d{4}|\s*SA\b|\s*BCLR\b|\s*SACR\b|\s*All\s|\s*ZA[A-Z]|\s*CCT|\s*$)",
        citation_string,
    )
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return None, None


def extract_citation_from_url(url):
    """Extract a neutral citation from a SAFLII URL path."""
    m = re.search(r'/za/cases/([A-Z]+)/(\d{4})/(\d+)', url)
    if m:
        return f"[{m.group(2)}] {m.group(1)} {m.group(3)}"
    return None


# ---------------------------------------------------------------------------
# CitationEngine
# ---------------------------------------------------------------------------

class CitationEngine:
    """Core logic for identifying South African legal citations."""

    PATTERNS = {
        # Standard SA Reports (Juta): Case Name 1995 (3) SA 391 (CC)
        "standard_sa": r"([A-Z][A-Za-z\s&()]+?v\s[A-Za-z\s&()]+?)\s(\d{4})\s\((\d+)\)\sSA\s(\d+)\s\(([A-Z]+)\)",
        # BCLR (LexisNexis): Case Name 1995 (6) BCLR 665 (CC)
        "bclr": r"([A-Z][A-Za-z\s&()]+?v\s[A-Za-z\s&()]+?)\s(\d{4})\s\((\d+)\)\sBCLR\s(\d+)\s\(([A-Z]+)\)",
        # SACR: Case Name 1995 (2) SACR 1 (CC)
        "sacr": r"([A-Z][A-Za-z\s&()]+?v\s[A-Za-z\s&()]+?)\s(\d{4})\s\((\d+)\)\sSACR\s(\d+)\s\(([A-Z]+)\)",
        # All SA (LexisNexis): Case Name 2002 (4) All SA 145 (SCA)
        "all_sa": r"([A-Z][A-Za-z\s&()]+?v\s[A-Za-z\s&()]+?)\s(\d{4})\s\((\d+)\)\sAll\sSA\s(\d+)\s\(([A-Z]+)\)",
        # Neutral SCA: Case Name [2023] ZASCA 15
        "neutral_zasca": r"([A-Z][A-Za-z\s&()]+?v\s[A-Za-z\s&()]+?)\s\[(\d{4})\]\sZASCA\s(\d+)",
        # Constitutional Court: [2022] ZACC 45
        "neutral_zacc": r"([A-Z][A-Za-z\s&()]+?v\s[A-Za-z\s&()]+?)\s\[(\d{4})\]\sZACC\s(\d+)",
        # Regional (captures court code): [2023] ZAWCHC 12
        "neutral_regional": r"([A-Z][A-Za-z\s&()]+?v\s[A-Za-z\s&()]+?)\s\[(\d{4})\]\s(ZA[A-Z]{2,8})\s(\d+)",
    }

    def extract_citations(self, text):
        found = []
        seen = set()

        # Process report-series patterns first, then neutral (to avoid duplicates)
        ordered_keys = [
            "standard_sa", "bclr", "sacr", "all_sa",
            "neutral_zasca", "neutral_zacc", "neutral_regional",
        ]
        for label in ordered_keys:
            pattern = self.PATTERNS[label]
            matches = re.findall(pattern, text)
            for m in matches:
                case_name = m[0].strip()
                year = m[1]
                # Dedup key: normalised party names + year
                dedup_key = f"{case_name.lower()}|{year}"

                # Skip if regional matches an already-found ZASCA/ZACC
                if label == "neutral_regional" and dedup_key in seen:
                    continue

                # Skip if a report-series citation was already found for same parties+year
                if label in ("bclr", "sacr", "all_sa") and dedup_key in seen:
                    continue

                seen.add(dedup_key)
                found.append({"type": label, "data": m})

        return found


# ---------------------------------------------------------------------------
# SafliiBridge - Forensic Search Pipeline
# ---------------------------------------------------------------------------

BASE_URL = "https://www.saflii.org"
SEARCH_URL = f"{BASE_URL}/cgi-bin/sinosrch-adw.cgi"

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

CRAWL_DELAY = 2  # seconds between requests


def create_session():
    """Create a requests session with browser-like headers."""
    session = requests.Session()
    session.headers.update(BROWSER_HEADERS)
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    return session


_last_request_time = 0.0


def throttled_get(session, url, **kwargs):
    """GET with crawl-delay throttling and retry logic."""
    global _last_request_time

    for attempt in range(1, 4):
        elapsed = time.time() - _last_request_time
        if elapsed < CRAWL_DELAY:
            time.sleep(CRAWL_DELAY - elapsed)

        try:
            resp = session.get(url, timeout=30, verify=False, **kwargs)
            _last_request_time = time.time()

            if resp.status_code == 200:
                return resp
            if resp.status_code == 404:
                return resp
            if resp.status_code == 410:
                if attempt < 3:
                    time.sleep(5 * attempt)
                    continue
            if resp.status_code >= 500:
                if attempt < 3:
                    time.sleep(5 * attempt)
                    continue
            return resp

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            if attempt < 3:
                time.sleep(5 * attempt)
                continue
            raise

    return resp


class SafliiBridge:
    """Forensic search pipeline for SAFLII lookups.

    Strategy:
    1. For neutral citations: try direct URL first
    2. For all types: search SAFLII by party names
    3. Fuzzy-match results to handle typos and name variations
    4. Download PDF on demand
    """

    def __init__(self, session=None):
        self.session = session or create_session()

    # ----- Main entry point -----

    def lookup(self, citation_data):
        """Look up a citation on SAFLII using forensic search pipeline.

        Returns a rich result dict with status, title, confidence, discrepancies, etc.
        """
        ctype = citation_data["type"]
        data = citation_data["data"]
        display = format_citation_display(citation_data)

        # Extract party names for fuzzy matching later
        party_a, party_b = extract_party_names(display)
        doc_year = data[1]  # year is always at index 1

        # ---- Strategy 1: Direct URL for neutral citations ----
        if ctype in ("neutral_zasca", "neutral_zacc", "neutral_regional"):
            direct_url = self._build_direct_url(citation_data)
            if direct_url:
                result = self._fetch_judgment(direct_url)
                if result["status"] == "found":
                    result["saflii_citation"] = extract_citation_from_url(direct_url)
                    result["year_discrepancy"] = None

                    # Cross-check: do the party names match the SAFLII title?
                    if party_a:
                        title = result.get("title", "")
                        name_score = fuzz.token_set_ratio(
                            f"{party_a} v {party_b}".lower(),
                            title.lower(),
                        )
                        result["match_confidence"] = min(name_score + 10, 100)
                        if name_score < 50:
                            # Party names don't match — flag as mismatch
                            result["status"] = "typo_detected"
                            result["year_discrepancy"] = {
                                "document": f"{party_a} v {party_b}",
                                "saflii": title[:80],
                            }
                    else:
                        result["match_confidence"] = 100

                    return result

        # ---- Strategy 2: Search SAFLII by party names ----
        search_results = self._search_saflii(citation_data)

        if not search_results:
            return self._not_found_result(citation_data)

        # ---- Strategy 3: Fuzzy match and reconcile ----
        best = self._fuzzy_match(citation_data, search_results, party_a, party_b, doc_year)

        if best is None:
            return self._not_found_result(citation_data)

        # Fetch the judgment page for the best match
        result = self._fetch_judgment(best["url"])
        if result["status"] != "found":
            return self._not_found_result(citation_data)

        result["saflii_citation"] = best.get("citation")
        result["match_confidence"] = best.get("confidence", 0)
        result["year_discrepancy"] = best.get("year_discrepancy")

        # If there's a year discrepancy, mark as typo_detected
        if best.get("year_discrepancy"):
            result["status"] = "typo_detected"

        return result

    # ----- Direct URL construction -----

    def _build_direct_url(self, citation_data):
        """Build a deterministic SAFLII URL for neutral citations."""
        ctype = citation_data["type"]
        data = citation_data["data"]

        if ctype == "neutral_zasca":
            court, year, num = "ZASCA", data[1], data[2]
        elif ctype == "neutral_zacc":
            court, year, num = "ZACC", data[1], data[2]
        elif ctype == "neutral_regional":
            court, year, num = data[2], data[1], data[3]
        else:
            return None

        court = resolve_court_code(court)
        return f"{BASE_URL}/za/cases/{court}/{year}/{num}.html"

    # ----- SAFLII search -----

    def _search_saflii(self, citation_data):
        """Search SAFLII using party names and optional court filter.

        Returns list of dicts: [{title, url, snippet, citation}, ...]
        """
        display = format_citation_display(citation_data)
        party_a, party_b = extract_party_names(display)

        if not party_a:
            # Fallback: use the full display string as query
            query = display
        else:
            query = f"{party_a} v {party_b}"

        # Determine court filter
        ctype = citation_data["type"]
        data = citation_data["data"]
        court_filter = None

        if ctype in ("standard_sa", "bclr", "sacr", "all_sa"):
            # Court abbreviation is in the parenthetical, e.g. (CC)
            court_abbrev = data[4]
            resolved = resolve_court_code(court_abbrev)
            if resolved in VALID_COURT_CODES:
                court_filter = resolved
        elif ctype == "neutral_zasca":
            court_filter = "ZASCA"
        elif ctype == "neutral_zacc":
            court_filter = "ZACC"
        elif ctype == "neutral_regional":
            court_filter = resolve_court_code(data[2])

        params = {
            "query": query,
            "method": "all",
            "results": "20",
            "meta": "/saflii",
        }
        if court_filter:
            params["mask_path"] = f"za/cases/{court_filter}"

        try:
            resp = throttled_get(self.session, SEARCH_URL, params=params)
            if resp.status_code != 200:
                return []

            resp.encoding = "windows-1252"
            soup = BeautifulSoup(resp.text, "html.parser")

            results = []
            for li in soup.find_all("li"):
                link = li.find("a")
                if not link or not link.get("href"):
                    continue
                href = link["href"]
                if "/za/cases/" not in href and "/cases/" not in href:
                    continue

                title = link.get_text(strip=True)
                snippet = li.get_text(strip=True)
                if title in snippet:
                    snippet = snippet.replace(title, "", 1).strip()
                    snippet = snippet.lstrip("- ").strip()

                # Normalize the URL, then extract citation from normalized URL
                full_url = self._normalize_url(href)
                citation = extract_citation_from_url(full_url)

                results.append({
                    "title": title,
                    "url": full_url,
                    "snippet": snippet[:200],
                    "citation": citation,
                })

            # If no results with court filter, try without
            if not results and court_filter:
                params.pop("mask_path", None)
                resp = throttled_get(self.session, SEARCH_URL, params=params)
                if resp.status_code == 200:
                    resp.encoding = "windows-1252"
                    soup = BeautifulSoup(resp.text, "html.parser")
                    for li in soup.find_all("li"):
                        link = li.find("a")
                        if not link or not link.get("href"):
                            continue
                        href = link["href"]
                        if "/za/cases/" not in href:
                            continue
                        title = link.get_text(strip=True)
                        full_url = self._normalize_url(href)
                        citation = extract_citation_from_url(full_url)
                        results.append({
                            "title": title,
                            "url": full_url,
                            "snippet": "",
                            "citation": citation,
                        })

            return results

        except Exception:
            return []

    # ----- Fuzzy matching / reconciliation -----

    def _fuzzy_match(self, citation_data, search_results, party_a, party_b, doc_year):
        """Find the best matching search result using fuzzy name matching.

        Returns the best result dict (with added 'confidence' and 'year_discrepancy' keys),
        or None if no match meets the threshold.
        """
        if not party_a:
            # Can't fuzzy match without party names — return first result with year check
            for r in search_results:
                r_citation = r.get("citation")
                if r_citation:
                    m = re.search(r'\[(\d{4})\]', r_citation)
                    if m:
                        r_year = m.group(1)
                        if r_year == doc_year:
                            r["confidence"] = 70
                            r["year_discrepancy"] = None
                            return r
                        else:
                            r["confidence"] = 60
                            r["year_discrepancy"] = {"document": doc_year, "saflii": r_year}
                            return r
            # No citation extracted — return first result with low confidence
            if search_results:
                search_results[0]["confidence"] = 50
                search_results[0]["year_discrepancy"] = None
                return search_results[0]
            return None

        doc_parties = f"{party_a} v {party_b}"
        best_match = None
        best_score = 0

        for r in search_results:
            title = r.get("title", "")

            # Fuzzy compare party names against the SAFLII title
            score = fuzz.token_set_ratio(doc_parties.lower(), title.lower())

            # Extract year from SAFLII result
            r_year = None
            r_citation = r.get("citation")
            if r_citation:
                m = re.search(r'\[(\d{4})\]', r_citation)
                if m:
                    r_year = m.group(1)

            # If no citation-based year, try extracting from URL
            if not r_year:
                m = re.search(r'/(\d{4})/', r.get("url", ""))
                if m:
                    r_year = m.group(1)

            # Year match bonus
            year_discrepancy = None
            if r_year:
                if r_year == doc_year:
                    score += 10  # bonus for exact year match
                else:
                    year_discrepancy = {"document": doc_year, "saflii": r_year}
                    # Don't penalise — the fuzzy name match is more important

            if score > best_score:
                best_score = score
                r["confidence"] = min(score, 100)
                r["year_discrepancy"] = year_discrepancy
                best_match = r

        # Threshold: require at least 75% name similarity
        if best_match and best_score >= 75:
            return best_match

        return None

    # ----- URL normalization -----

    def _normalize_url(self, url):
        """Normalize SAFLII URLs (handle cgi-bin/disp.pl wrappers, etc.)."""
        m = re.search(r'[?&]file=(za/cases/[^&]+)', url)
        if m:
            return f"{BASE_URL}/{m.group(1)}"

        url = re.sub(r'^http://', 'https://', url)
        url = re.sub(r'://saflii\.org', '://www.saflii.org', url)

        if not url.startswith("http"):
            return urljoin(BASE_URL, url)

        return url

    # ----- Fetch judgment page -----

    def _fetch_judgment(self, url):
        """Fetch and parse a SAFLII judgment HTML page."""
        try:
            resp = throttled_get(self.session, url)

            if resp.status_code in (404, 410):
                return {"status": "not_found", "source_url": url}
            if resp.status_code != 200:
                return {"status": "error", "error": f"HTTP {resp.status_code}", "source_url": url}

            soup = BeautifulSoup(resp.content, "html.parser")
            title_el = soup.find("title")
            title_text = title_el.get_text(strip=True) if title_el else ""

            flynote_el = soup.find("p", class_="flynote")
            flynote = flynote_el.get_text(strip=True) if flynote_el else None

            full_text = soup.get_text()

            return {
                "status": "found",
                "title": title_text,
                "flynote": flynote,
                "full_text": full_text[:5000],
                "source_url": url,
            }

        except requests.Timeout:
            return {"status": "timeout", "source_url": url}
        except Exception as e:
            return {"status": "error", "error": str(e), "source_url": url}

    # ----- Not-found fallback -----

    def _not_found_result(self, citation_data):
        """Build a not_found result with a manual search link."""
        display = format_citation_display(citation_data)
        query = quote_plus(display)
        search_link = f"{SEARCH_URL}?method=all&query={query}"
        return {
            "status": "not_found",
            "source_url": search_link,
            "title": "No matching case found on SAFLII",
            "saflii_citation": None,
            "match_confidence": 0,
            "year_discrepancy": None,
        }

    # ----- PDF Download -----

    def download_pdf(self, source_url):
        """Download a judgment PDF from SAFLII.

        Returns (pdf_bytes, filename) or (None, None) on failure.
        """
        url = self._normalize_url(source_url)

        # Convert HTML URL to PDF URL
        if url.endswith(".html"):
            pdf_url = url.replace(".html", ".pdf")
        elif url.endswith(".pdf"):
            pdf_url = url
        else:
            pdf_url = url + ".pdf"

        # Try PDF first, then RTF, then HTML
        for fmt_url, ext in [(pdf_url, "pdf"), (pdf_url.replace(".pdf", ".rtf"), "rtf")]:
            try:
                resp = throttled_get(self.session, fmt_url)
                if resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    # Check we didn't get an HTML error page instead of PDF
                    if ext == "pdf" and "text/html" in content_type:
                        # Check for meta-refresh redirect
                        soup = BeautifulSoup(resp.text, "html.parser")
                        meta_refresh = soup.find("meta", attrs={"http-equiv": "refresh"})
                        if meta_refresh:
                            content = meta_refresh.get("content", "")
                            m = re.search(r'url=(.+)', content, re.IGNORECASE)
                            if m:
                                redirect_url = urljoin(fmt_url, m.group(1).strip())
                                resp = throttled_get(self.session, redirect_url)
                                if resp.status_code == 200:
                                    filename = self._filename_from_url(redirect_url)
                                    return resp.content, filename
                        continue  # Got HTML, not PDF

                    filename = self._filename_from_url(fmt_url)
                    return resp.content, filename

            except Exception:
                continue

        return None, None

    def _filename_from_url(self, url):
        """Generate a filename from a SAFLII URL."""
        m = re.search(r'/za/cases/([A-Z]+)/(\d{4})/(\d+)\.\w+', url)
        if m:
            court, year, number = m.group(1), m.group(2), m.group(3)
            ext = url.rsplit(".", 1)[-1] if "." in url else "pdf"
            return f"{court}-{year}-{number}.{ext}"
        return url.rsplit("/", 1)[-1] or "judgment.pdf"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def extract_text_from_docx(uploaded_file):
    """Extract text from a .docx file, including footnotes."""
    doc = Document(io.BytesIO(uploaded_file.read()))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]

    footnotes = []
    try:
        footnote_rel = (
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/footnotes"
        )
        footnote_part = doc.part.package.part_related_by(footnote_rel)
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        for fn in footnote_part.element.findall(".//w:footnote", ns):
            fn_id = fn.get(f'{{{ns["w"]}}}id')
            if fn_id in ("0", "-1"):
                continue
            texts = [t.text for t in fn.findall(".//w:t", ns) if t.text]
            if texts:
                footnotes.append(" ".join(texts))
    except Exception:
        pass

    return "\n".join(paragraphs + footnotes)


def extract_text_from_pdf(uploaded_file):
    """Extract text from a PDF file."""
    text_parts = []
    with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


def extract_text(uploaded_file):
    """Extract text from an uploaded file (.docx or .pdf)."""
    name = uploaded_file.name.lower()
    if name.endswith(".pdf"):
        return extract_text_from_pdf(uploaded_file)
    elif name.endswith(".docx"):
        return extract_text_from_docx(uploaded_file)
    else:
        return ""


def format_citation_display(citation):
    """Format a citation dict into a human-readable string."""
    ctype = citation["type"]
    data = citation["data"]

    if ctype == "standard_sa":
        return f"{data[0].strip()} {data[1]} ({data[2]}) SA {data[3]} ({data[4]})"
    elif ctype == "bclr":
        return f"{data[0].strip()} {data[1]} ({data[2]}) BCLR {data[3]} ({data[4]})"
    elif ctype == "sacr":
        return f"{data[0].strip()} {data[1]} ({data[2]}) SACR {data[3]} ({data[4]})"
    elif ctype == "all_sa":
        return f"{data[0].strip()} {data[1]} ({data[2]}) All SA {data[3]} ({data[4]})"
    elif ctype == "neutral_zasca":
        return f"{data[0].strip()} [{data[1]}] ZASCA {data[2]}"
    elif ctype == "neutral_zacc":
        return f"{data[0].strip()} [{data[1]}] ZACC {data[2]}"
    elif ctype == "neutral_regional":
        return f"{data[0].strip()} [{data[1]}] {data[2]} {data[3]}"

    return str(data)


def citation_type_label(ctype):
    """Return a human-readable label for citation type."""
    labels = {
        "standard_sa": "SA Reports (Juta)",
        "bclr": "BCLR (LexisNexis)",
        "sacr": "SACR",
        "all_sa": "All SA (LexisNexis)",
        "neutral_zasca": "SCA (Neutral)",
        "neutral_zacc": "CC (Neutral)",
        "neutral_regional": "Regional (Neutral)",
    }
    return labels.get(ctype, ctype)


def _party_name_filename(display_citation, fallback_filename):
    """Generate a PDF filename from party names, e.g. 'Smith v Jones.pdf'.

    Falls back to the SAFLII-derived filename if party names can't be extracted.
    """
    party_a, party_b = extract_party_names(display_citation)
    if not party_a:
        return fallback_filename

    # Clean party names for use as filename
    def clean(name):
        # Take the primary surname/name (first word for multi-word names like "Minister of Health")
        # But keep short names as-is
        name = re.sub(r'[^\w\s-]', '', name).strip()
        return name

    a = clean(party_a)
    b = clean(party_b)

    # Get extension from fallback
    ext = fallback_filename.rsplit(".", 1)[-1] if "." in fallback_filename else "pdf"

    return f"{a} v {b}.{ext}"


def generate_certificate(audit_results, filename):
    """Generate a Certificate of Accuracy report in Markdown."""
    today = date.today().strftime("%Y-%m-%d")
    matter = filename.replace(".docx", "").replace(".pdf", "").replace("_", " ").title() if filename else "Unknown"

    verified = sum(1 for r in audit_results if r["saflii"]["status"] == "found")
    typos = sum(1 for r in audit_results if r["saflii"]["status"] == "typo_detected")
    not_found = sum(1 for r in audit_results if r["saflii"]["status"] == "not_found")
    errors = sum(1 for r in audit_results if r["saflii"]["status"] in ("error", "timeout"))
    total = len(audit_results)
    score = round(((verified + typos) / total * 100)) if total > 0 else 0

    # Citation log table
    log_rows = []
    for i, r in enumerate(audit_results, 1):
        status_map = {
            "found": "Verified",
            "typo_detected": "Typo Detected",
            "not_found": "Not Found",
            "timeout": "Timeout",
            "error": "Error",
        }
        status_text = status_map.get(r["saflii"]["status"], "Unknown")
        source = "SAFLII" if r["saflii"]["status"] in ("found", "typo_detected") else "---"
        ref_id = f"CC-{i:03d}"
        confidence = r["saflii"].get("match_confidence", "---")
        log_rows.append(
            f"| {r['display']} | {source} | {status_text} | {confidence}% | {ref_id} |"
        )

    log_table = "\n".join(log_rows)

    # Discrepancy section
    discrepancy_rows = []
    for i, r in enumerate(audit_results, 1):
        disc = r["saflii"].get("year_discrepancy")
        if disc:
            discrepancy_rows.append(
                f"- **Ref CC-{i:03d}** ({r['display'][:60]}): "
                f"Document says **{disc['document']}**, SAFLII says **{disc['saflii']}**"
            )

    discrepancy_section = "\n".join(discrepancy_rows) if discrepancy_rows else "*No discrepancies detected.*"

    report = f"""# CERTIFICATE OF ACCURACY: CITATION AUDIT
**Date of Audit:** {today}
**Verified By:** Citation Checker App (v2.0)
**Matter:** {matter}

---

## 1. EXECUTIVE SUMMARY
This document certifies that the uploaded document has been electronically audited against primary legal databases, including **SAFLII** and **The South African Judiciary** records.

**Overall Accuracy Score:** {score}%
**Citations Verified:** {verified}
**Citations with Typos:** {typos}
**Citations Not Found:** {not_found}
**Errors/Timeouts:** {errors}

---

## 2. CITATION VERIFICATION LOG
| Citation Found | Source | Status | Confidence | Ref ID |
| :--- | :--- | :--- | :--- | :--- |
{log_table}

---

## 3. DISCREPANCIES DETECTED
{discrepancy_section}

---

## 4. QUOTATION INTEGRITY AUDIT (Visual Match)
*This section will be populated in Phase 2 of development.*

---

## 5. BUNDLE INDEX
*This section will be populated in Phase 3 of development.*

---

## 6. DECLARATION
The Citation Checker App hereby certifies that the citations contained in the audited document have been checked against the primary sources listed above as of the date of this report.

**[Digital Signature: CERTIFIED]**
"""
    return report


# ---------------------------------------------------------------------------
# Session State Init
# ---------------------------------------------------------------------------

def init_session_state():
    defaults = {
        "current_screen": "hopper",
        "uploaded_text": None,
        "citations": [],
        "audit_results": [],
        "filename": None,
        "audit_complete": False,
        "downloaded_pdfs": {},
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ---------------------------------------------------------------------------
# Screen: The Hopper (Upload)
# ---------------------------------------------------------------------------

def render_hopper():
    st.markdown(
        '<h1 style="margin-bottom:0;">CITATION CHECKER</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="tagline">VERIFY &nbsp;/&nbsp; AUDIT &nbsp;/&nbsp; CERTIFY</p>',
        unsafe_allow_html=True,
    )

    st.markdown("### The Hopper")
    st.markdown("Upload a Heads of Argument or legal document (.docx or .pdf) to begin citation extraction.")

    uploaded = st.file_uploader(
        "Drop your .docx or .pdf file here",
        type=["docx", "pdf"],
        key="file_uploader",
    )

    if uploaded is not None and (
        st.session_state.filename != uploaded.name
    ):
        st.session_state.filename = uploaded.name
        with st.spinner("Extracting text..."):
            text = extract_text(uploaded)
            st.session_state.uploaded_text = text

        engine = CitationEngine()
        citations = engine.extract_citations(text)
        st.session_state.citations = citations
        st.session_state.audit_results = []
        st.session_state.audit_complete = False
        st.session_state.downloaded_pdfs = {}

    # Terminal log
    if st.session_state.citations:
        log_lines = [
            '<div class="terminal-log">',
            '<div class="log-header">--- CITATION EXTRACTION LOG ---</div>',
            f'<div class="log-header">File: {st.session_state.filename}</div>',
            f'<div class="log-header">Citations found: {len(st.session_state.citations)}</div>',
            "<br>",
        ]

        for i, c in enumerate(st.session_state.citations, 1):
            display = format_citation_display(c)
            type_label = citation_type_label(c["type"])
            log_lines.append(
                f'<div><span class="log-found">[FOUND]</span> '
                f'<span class="log-type">[{type_label}]</span> '
                f"{display}</div>"
            )

        log_lines.append("</div>")
        st.markdown("\n".join(log_lines), unsafe_allow_html=True)

        st.markdown("")

        if st.button("RUN AUDIT", use_container_width=True):
            run_saflii_audit()

    elif st.session_state.uploaded_text is not None:
        st.warning("No citations found in the uploaded document.")


def run_saflii_audit():
    """Look up each citation on SAFLII using the forensic search pipeline."""
    session = create_session()
    bridge = SafliiBridge(session=session)
    citations = st.session_state.citations
    results = []

    progress = st.progress(0, text="Connecting to SAFLII...")

    for i, c in enumerate(citations):
        display = format_citation_display(c)
        progress.progress(
            (i + 1) / len(citations),
            text=f"Checking {i + 1}/{len(citations)}: {display[:60]}...",
        )

        saflii_result = bridge.lookup(c)

        results.append({
            "citation": c,
            "display": display,
            "saflii": saflii_result,
        })

    progress.empty()
    st.session_state.audit_results = results
    st.session_state.audit_complete = True
    st.session_state.current_screen = "auditor"
    st.rerun()


# ---------------------------------------------------------------------------
# Screen: The Auditor (Audit Table)
# ---------------------------------------------------------------------------

def render_auditor():
    st.markdown(
        '<h1 style="margin-bottom:0;">CITATION CHECKER</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="tagline">VERIFY &nbsp;/&nbsp; AUDIT &nbsp;/&nbsp; CERTIFY</p>',
        unsafe_allow_html=True,
    )

    st.markdown("### The Auditor")

    if not st.session_state.audit_results:
        st.info("No audit results yet. Upload a document in The Hopper and run the audit.")
        return

    st.markdown(
        f"**Document:** {st.session_state.filename} &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"**Citations:** {len(st.session_state.audit_results)} &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"**Date:** {date.today().strftime('%d %B %Y')}"
    )

    # Build HTML audit table
    rows_html = ""
    for i, r in enumerate(st.session_state.audit_results, 1):
        status = r["saflii"].get("status", "error")
        url = r["saflii"].get("source_url", "#")
        title = r["saflii"].get("title", "---")
        saflii_cit = r["saflii"].get("saflii_citation", "")
        confidence = r["saflii"].get("match_confidence", 0)
        year_disc = r["saflii"].get("year_discrepancy")

        # Status cell
        if status == "found":
            status_html = '<span class="status-verified">VERIFIED</span>'
        elif status == "typo_detected":
            status_html = '<span class="status-typo">TYPO DETECTED</span>'
        elif status == "not_found":
            status_html = '<span class="status-not-found">NOT FOUND</span>'
        elif status == "timeout":
            status_html = '<span class="status-error">TIMEOUT</span>'
        else:
            status_html = '<span class="status-error">ERROR</span>'

        # Source match cell
        if status in ("found", "typo_detected"):
            source = title[:80] if title else "SAFLII"
            source_html = source
            if saflii_cit:
                source_html += f'<div class="saflii-citation">{saflii_cit}</div>'
            if year_disc:
                source_html += (
                    f'<div class="discrepancy-note">'
                    f'Discrepancy: doc says {year_disc["document"]}, '
                    f'SAFLII says {year_disc["saflii"]}'
                    f'</div>'
                )
        elif status == "not_found":
            source_html = "---"
        else:
            error_msg = r["saflii"].get("error", "Unknown error")
            source_html = error_msg[:60]

        # Confidence cell
        if status in ("found", "typo_detected") and confidence:
            if confidence >= 90:
                conf_class = "confidence-high"
            elif confidence >= 75:
                conf_class = "confidence-medium"
            else:
                conf_class = "confidence-low"
            confidence_html = f'<span class="confidence-badge {conf_class}">{confidence}%</span>'
        else:
            confidence_html = '<span style="color: #7F8C8D;">---</span>'

        # Action cell
        action_html = f'<a href="{url}" target="_blank" class="action-link">View Source</a>'

        rows_html += f"""
        <tr>
            <td>{i:03d}</td>
            <td class="citation-name">{r['display']}</td>
            <td>{status_html}</td>
            <td>{source_html}</td>
            <td>{confidence_html}</td>
            <td>{action_html}</td>
        </tr>"""

    table_html = f"""
    <table class="audit-table">
        <thead>
            <tr>
                <th>Ref #</th>
                <th>Document Citation</th>
                <th>Status</th>
                <th>Source Match</th>
                <th>Confidence</th>
                <th>Action / Link</th>
            </tr>
        </thead>
        <tbody>{rows_html}</tbody>
    </table>
    """
    st.markdown(table_html, unsafe_allow_html=True)

    # ----- Discrepancy resolution panels (File 08 design) -----
    typo_results = [
        (i, r) for i, r in enumerate(st.session_state.audit_results, 1)
        if r["saflii"].get("status") == "typo_detected"
    ]

    if typo_results:
        st.markdown("---")
        st.markdown("### Citation Discrepancies")
        st.markdown("The following citations were found on SAFLII but contain errors in your document.")

        for idx, r in typo_results:
            year_disc = r["saflii"].get("year_discrepancy", {})
            saflii_cit = r["saflii"].get("saflii_citation", "---")
            confidence = r["saflii"].get("match_confidence", 0)
            title = r["saflii"].get("title", "---")

            with st.expander(f"Ref {idx:03d} - {r['display'][:60]}", expanded=True):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Your Document**")
                    st.info(f"**Citation:** {r['display']}")
                    if year_disc:
                        st.markdown(f"**Year:** {year_disc.get('document', '---')}")
                    party_a, party_b = extract_party_names(r['display'])
                    if party_a:
                        st.markdown(f"**Parties:** {party_a} v {party_b}")

                with col2:
                    st.markdown("**SAFLII Match**")
                    st.success(f"**Citation:** {saflii_cit}")
                    if year_disc:
                        st.markdown(f"**Year:** {year_disc.get('saflii', '---')}")
                    st.markdown(f"**Title:** {title[:100]}")
                    st.caption(f"Match Confidence: {confidence}%")

    # ----- PDF Download section -----
    st.markdown("---")
    st.markdown("### Download Judgments")

    downloadable = [
        (i, r) for i, r in enumerate(st.session_state.audit_results, 1)
        if r["saflii"].get("status") in ("found", "typo_detected")
    ]

    if downloadable:
        for idx, r in downloadable:
            col1, col2 = st.columns([0.75, 0.25])
            with col1:
                st.markdown(
                    f'<p style="color: #2C3E50; font-family: Georgia, serif; '
                    f'font-size: 0.95rem; margin: 0.5rem 0;">'
                    f'<strong>Ref {idx:03d}:</strong> '
                    f'<em>{r["display"][:70]}</em></p>',
                    unsafe_allow_html=True,
                )
            with col2:
                btn_key = f"dl_pdf_{idx}"
                if st.button("Download PDF", key=btn_key):
                    source_url = r["saflii"].get("source_url", "")
                    if source_url:
                        session = create_session()
                        bridge = SafliiBridge(session=session)
                        with st.spinner(f"Downloading PDF for Ref {idx:03d}..."):
                            pdf_bytes, pdf_filename = bridge.download_pdf(source_url)
                        if pdf_bytes:
                            # Rename to party names
                            party_filename = _party_name_filename(r["display"], pdf_filename)
                            st.session_state.downloaded_pdfs[idx] = {
                                "bytes": pdf_bytes,
                                "filename": party_filename,
                            }
                            st.rerun()
                        else:
                            st.warning(f"PDF not available for Ref {idx:03d}. Try viewing the HTML source instead.")

                # Show download button if PDF already fetched
                if idx in st.session_state.get("downloaded_pdfs", {}):
                    pdf_data = st.session_state.downloaded_pdfs[idx]
                    st.download_button(
                        label=f"Save {pdf_data['filename']}",
                        data=pdf_data["bytes"],
                        file_name=pdf_data["filename"],
                        mime="application/pdf",
                        key=f"save_pdf_{idx}",
                    )
    else:
        st.markdown("*No verified citations available for download.*")

    # ----- Flynote expanders -----
    st.markdown("---")
    st.markdown("### Flynote Extracts")

    has_flynotes = False
    for i, r in enumerate(st.session_state.audit_results, 1):
        flynote = r["saflii"].get("flynote")
        if flynote:
            has_flynotes = True
            with st.expander(f"Ref {i:03d} - {r['display'][:60]}"):
                st.markdown(
                    f'<p style="font-family: Georgia, serif; color: #2C3E50; '
                    f'line-height: 1.6;">{flynote[:2000]}</p>',
                    unsafe_allow_html=True,
                )

    if not has_flynotes:
        st.markdown(
            '*No flynotes were extracted. Flynote availability depends on SAFLII page structure.*'
        )

    # Certificate download
    st.markdown("---")
    cert = generate_certificate(st.session_state.audit_results, st.session_state.filename)
    st.download_button(
        label="DOWNLOAD CERTIFICATE OF ACCURACY",
        data=cert,
        file_name=f"citation_audit_{date.today().strftime('%Y%m%d')}.md",
        mime="text/markdown",
        use_container_width=True,
    )


# ---------------------------------------------------------------------------
# Screen: The Librarian (Placeholder)
# ---------------------------------------------------------------------------

def render_librarian():
    st.markdown(
        '<h1 style="margin-bottom:0;">CITATION CHECKER</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="tagline">VERIFY &nbsp;/&nbsp; AUDIT &nbsp;/&nbsp; CERTIFY</p>',
        unsafe_allow_html=True,
    )

    st.markdown("### The Librarian")
    st.markdown("#### Paginated Court Bundle Generator")

    st.info(
        "Bundle generation is under development. This feature will allow you to "
        "select verified citations and produce a sequentially paginated, "
        "indexed court bundle in PDF format."
    )

    if st.session_state.audit_results:
        st.markdown("#### Citations available for bundling:")
        for i, r in enumerate(st.session_state.audit_results, 1):
            col1, col2 = st.columns([0.85, 0.15])
            with col1:
                status = r["saflii"].get("status", "error")
                icon = "+" if status in ("found", "typo_detected") else "-"
                st.text(f"  [{icon}] {r['display']}")
            with col2:
                st.checkbox("Include", key=f"bundle_{i}", disabled=True)

    st.button("GENERATE BUNDLE (COMING SOON)", disabled=True, use_container_width=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    st.set_page_config(
        page_title="Citation Checker",
        page_icon=None,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    inject_era_css()
    init_session_state()

    # Sidebar navigation
    with st.sidebar:
        st.markdown("## CITATION CHECKER")
        st.markdown(
            '<p style="font-family: Courier New, monospace; font-size: 0.75rem; '
            'letter-spacing: 2px; color: #7F8C8D;">VERIFY / AUDIT / CERTIFY</p>',
            unsafe_allow_html=True,
        )
        st.markdown("---")

        if st.button("The Hopper", use_container_width=True):
            st.session_state.current_screen = "hopper"
            st.rerun()
        if st.button("The Auditor", use_container_width=True):
            st.session_state.current_screen = "auditor"
            st.rerun()
        if st.button("The Librarian", use_container_width=True):
            st.session_state.current_screen = "librarian"
            st.rerun()

        st.markdown("---")

        # Status summary
        if st.session_state.filename:
            st.markdown(f"**File:** {st.session_state.filename}")
            st.markdown(f"**Citations:** {len(st.session_state.citations)}")
            if st.session_state.audit_complete:
                verified = sum(
                    1 for r in st.session_state.audit_results
                    if r["saflii"]["status"] in ("found", "typo_detected")
                )
                st.markdown(f"**Verified:** {verified}/{len(st.session_state.audit_results)}")

    # Dispatch
    screen = st.session_state.current_screen
    if screen == "hopper":
        render_hopper()
    elif screen == "auditor":
        render_auditor()
    elif screen == "librarian":
        render_librarian()


if __name__ == "__main__":
    main()
