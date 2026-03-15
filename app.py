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
    .status-judiciary { color: #2980B9; font-weight: bold; }
    .status-google { color: #8E44AD; font-weight: bold; }
    .status-mismatch { color: #E74C3C; font-weight: bold; }
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
    .found-via-note {
        font-size: 0.75rem;
        color: #2980B9;
        font-style: italic;
        margin-top: 4px;
    }
    .search-trail {
        font-size: 0.7rem;
        color: #95A5A6;
        margin-top: 6px;
        font-family: 'Courier New', monospace;
        line-height: 1.3;
    }
    .suggestion-note {
        color: #27AE60;
        font-size: 0.85em;
        margin-top: 4px;
        padding: 4px 8px;
        background: #E8F8F0;
        border-left: 3px solid #27AE60;
    }
    .cited-wrong-note {
        color: #E74C3C;
        font-size: 0.85em;
        margin-top: 4px;
        padding: 4px 8px;
        background: #FDEDEC;
        border-left: 3px solid #E74C3C;
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

    # Old provincial division abbreviations
    PROVINCIAL_DIVS = (
        "CPD", "TPD", "WLD", "NPD", "OPD", "EPD", "AD", "SCA",
        "DCLD", "SECLD", "NCHC", "BCHC", "ECD", "NCD",
    )

    # Character class for party names: letters, spaces, &, parentheses, hyphens
    # Explicitly excludes newlines and periods (which caused cross-line leaks)
    _N = r"[A-Za-z\s&()\-']"  # name chars (no period, no comma)
    _NP = r"[A-Za-z\s&()\-'.,]"  # name chars with period/comma (for "v." and "(Pty)")

    PATTERNS = {
        # Standard SA Reports (Juta): Case Name 1995 (3) SA 391 (CC)
        "standard_sa": r"([A-Z]" + _NP + r"+?v\.?\s" + _NP + r"+?)\s(\d{4})\s\((\d+)\)\sSA\s(\d+)\s\(([A-Z]+)\)",
        # BCLR (LexisNexis): Case Name 1995 (6) BCLR 665 (CC)
        "bclr": r"([A-Z]" + _NP + r"+?v\.?\s" + _NP + r"+?)\s(\d{4})\s\((\d+)\)\sBCLR\s(\d+)\s\(([A-Z]+)\)",
        # SACR: Case Name 1995 (2) SACR 1 (CC)
        "sacr": r"([A-Z]" + _NP + r"+?v\.?\s" + _NP + r"+?)\s(\d{4})\s\((\d+)\)\sSACR\s(\d+)\s\(([A-Z]+)\)",
        # All SA (LexisNexis): Case Name 2002 (4) All SA 145 (SCA)
        "all_sa": r"([A-Z]" + _NP + r"+?v\.?\s" + _NP + r"+?)\s(\d{4})\s\((\d+)\)\sAll\sSA\s(\d+)\s\(([A-Z]+)\)",
        # Old provincial: Blotnick v. Turecki, 1944 CPD 100
        "old_provincial": r"([A-Z]" + _NP + r"+?v\.?\s" + _NP + r"+?),?\s(\d{4})\s(CPD|TPD|WLD|NPD|OPD|EPD|AD|SCA|DCLD|SECLD|NCHC|BCHC|ECD|NCD)\s(\d+)",
        # Neutral SCA: Case Name [2023] ZASCA 15
        "neutral_zasca": r"([A-Z]" + _NP + r"+?v\.?\s" + _NP + r"+?)\s\[(\d{4})\]\sZASCA\s(\d+)",
        # Constitutional Court: [2022] ZACC 45
        "neutral_zacc": r"([A-Z]" + _NP + r"+?v\.?\s" + _NP + r"+?)\s\[(\d{4})\]\sZACC\s(\d+)",
        # Regional (captures court code): [2023] ZAWCHC 12
        "neutral_regional": r"([A-Z]" + _NP + r"+?v\.?\s" + _NP + r"+?)\s\[(\d{4})\]\s(ZA[A-Z]{2,8})\s(\d+)",
    }

    # Patterns for footnote citations (name and citation on separate lines)
    # These match citation-only lines (no party name prefix)
    FOOTNOTE_PATTERNS = {
        "standard_sa": r"(\d{4})\s\((\d+)\)\sSA\s(\d+)\s\(([A-Z]+)\)",
        "bclr": r"(\d{4})\s\((\d+)\)\sBCLR\s(\d+)\s\(([A-Z]+)\)",
        "sacr": r"(\d{4})\s\((\d+)\)\sSACR\s(\d+)\s\(([A-Z]+)\)",
        "all_sa": r"(\d{4})\s\((\d+)\)\sAll\sSA\s(\d+)\s\(([A-Z]+)\)",
    }

    def extract_citations(self, text):
        found = []
        seen = set()

        # Run inline patterns per-line to prevent cross-line matches
        lines = text.split("\n")
        ordered_keys = [
            "standard_sa", "bclr", "sacr", "all_sa", "old_provincial",
            "neutral_zasca", "neutral_zacc", "neutral_regional",
        ]
        for line in lines:
            line = line.strip()
            if not line:
                continue
            for label in ordered_keys:
                pattern = self.PATTERNS[label]
                matches = re.findall(pattern, line)
                for m in matches:
                    case_name = m[0].strip().rstrip(",. ")
                    year = m[1]
                    dedup_key = f"{case_name.lower()}|{year}"

                    if label == "neutral_regional" and dedup_key in seen:
                        continue
                    if label in ("bclr", "sacr", "all_sa") and dedup_key in seen:
                        continue

                    seen.add(dedup_key)
                    found.append({"type": label, "data": m})

        # --- Footnote recovery: find orphan citations without party names ---
        # Look for citation patterns that appear alone (no "v" before them)
        # and try to find the party names in nearby preceding text
        lines = text.split("\n")
        for line_idx, line in enumerate(lines):
            line_stripped = line.strip()
            if not line_stripped:
                continue

            for fn_label, fn_pattern in self.FOOTNOTE_PATTERNS.items():
                fn_match = re.search(fn_pattern, line_stripped)
                if not fn_match:
                    continue

                # Skip if this line already has "v" (inline citation, already caught)
                before_citation = line_stripped[:fn_match.start()]
                if re.search(r'\bv\.?\s', before_citation):
                    continue

                # Check this citation wasn't already found inline
                year = fn_match.group(1)
                already_found = any(
                    r["data"][1] == year
                    and r["type"] == fn_label
                    and fn_match.group(3) in str(r["data"])  # page number
                    for r in found
                )
                if already_found:
                    continue

                # Search preceding lines for party names (up to 5 lines back)
                party_name = None
                for back in range(1, min(6, line_idx + 1)):
                    prev_line = lines[line_idx - back].strip()
                    if not prev_line:
                        continue
                    # Look for "A v B" pattern, possibly ending with footnote number
                    name_match = re.search(
                        r"([A-Z][A-Za-z\s&()\-'.,]+?v\.?\s[A-Za-z\s&()\-'.,]+?)(?:\s*\d*\s*$)",
                        prev_line,
                    )
                    if name_match:
                        party_name = name_match.group(1).strip().rstrip(",. 0123456789")
                        break

                if party_name:
                    groups = fn_match.groups()
                    # Build data tuple matching the standard_sa format: (name, year, vol, page, court)
                    data = (party_name,) + groups
                    dedup_key = f"{party_name.lower()}|{year}"
                    if dedup_key not in seen:
                        seen.add(dedup_key)
                        found.append({"type": fn_label, "data": data})

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

    # ----- Helper: add standard keys to any result -----

    @staticmethod
    def _add_standard_keys(result, **overrides):
        """Ensure every result dict has all expected keys."""
        defaults = {
            "search_trail": [],
            "saflii_citation": None,
            "match_confidence": 0,
            "year_discrepancy": None,
            "found_via": None,
            "cited_case_title": None,
            "cited_case_url": None,
            "cited_case_citation": None,
            "suggested_citation": None,
        }
        for k, v in defaults.items():
            if k not in result:
                result[k] = v
        result.update(overrides)
        return result

    # ----- Main entry point -----

    def lookup(self, citation_data):
        """Look up a citation using cascading search: SAFLII → Judiciary → Google.

        When the direct URL points to a different case (name mismatch), the search
        continues by party name to find the intended case and reports both.
        """
        ctype = citation_data["type"]
        data = citation_data["data"]
        display = format_citation_display(citation_data)

        party_a, party_b = extract_party_names(display)
        doc_year = data[1]

        search_trail = []
        mismatch_info = None  # stashed when direct URL hits wrong case

        # ---- Step 1: Direct URL for neutral citations ----
        if ctype in ("neutral_zasca", "neutral_zacc", "neutral_regional"):
            direct_url = self._build_direct_url(citation_data)
            if direct_url:
                result = self._fetch_judgment(direct_url)
                if result["status"] == "found":
                    direct_citation = extract_citation_from_url(direct_url)

                    if party_a:
                        title = result.get("title", "")
                        name_score = fuzz.token_set_ratio(
                            f"{party_a} v {party_b}".lower(),
                            title.lower(),
                        )

                        if name_score >= 50:
                            # Names match → VERIFIED, return immediately
                            search_trail.append({"source": "SAFLII (direct)", "result": "Found"})
                            return self._add_standard_keys(result,
                                search_trail=search_trail,
                                saflii_citation=direct_citation,
                                match_confidence=min(name_score + 10, 100),
                                found_via="SAFLII",
                            )
                        else:
                            # Names DON'T match → stash mismatch, continue searching
                            mismatch_info = {
                                "title": title,
                                "url": direct_url,
                                "citation": direct_citation,
                            }
                            search_trail.append({
                                "source": "SAFLII (direct)",
                                "result": f"Found wrong case ({title[:40]}…)",
                            })
                    else:
                        # No party names to check → return as verified
                        search_trail.append({"source": "SAFLII (direct)", "result": "Found"})
                        return self._add_standard_keys(result,
                            search_trail=search_trail,
                            saflii_citation=direct_citation,
                            match_confidence=100,
                            found_via="SAFLII",
                        )
                else:
                    search_trail.append({"source": "SAFLII (direct)", "result": "Not found"})

        # ---- Step 2: Search SAFLII by party names ----
        search_results = self._search_saflii(citation_data)

        if search_results:
            best = self._fuzzy_match(citation_data, search_results, party_a, party_b, doc_year)
            if best is not None:
                # Check we didn't just find the same wrong case again
                same_as_mismatch = (
                    mismatch_info
                    and best.get("url", "").rstrip("/") == mismatch_info["url"].rstrip("/")
                )

                if not same_as_mismatch:
                    result = self._fetch_judgment(best["url"])
                    if result["status"] == "found":
                        search_trail.append({"source": "SAFLII (search)", "result": "Found"})

                        if mismatch_info:
                            # We found the RIGHT case after the direct URL gave us the WRONG one
                            return self._add_standard_keys(result,
                                status="mismatch_resolved",
                                search_trail=search_trail,
                                saflii_citation=best.get("citation"),
                                match_confidence=best.get("confidence", 0),
                                year_discrepancy=best.get("year_discrepancy"),
                                found_via="SAFLII",
                                cited_case_title=mismatch_info["title"],
                                cited_case_url=mismatch_info["url"],
                                cited_case_citation=mismatch_info["citation"],
                                suggested_citation=best.get("citation"),
                            )
                        else:
                            # Normal search hit (no prior mismatch)
                            status = "typo_detected" if best.get("year_discrepancy") else "found"
                            return self._add_standard_keys(result,
                                status=status,
                                search_trail=search_trail,
                                saflii_citation=best.get("citation"),
                                match_confidence=best.get("confidence", 0),
                                year_discrepancy=best.get("year_discrepancy"),
                                found_via="SAFLII",
                            )
                    else:
                        search_trail.append({"source": "SAFLII (search)", "result": "Match found but page unavailable"})
                else:
                    search_trail.append({"source": "SAFLII (search)", "result": "Same wrong case found"})
            else:
                search_trail.append({"source": "SAFLII (search)", "result": "No matching case"})
        else:
            search_trail.append({"source": "SAFLII (search)", "result": "No results"})

        # ---- Step 3: Search judiciary.org.za ----
        judiciary_result = self._search_judiciary(citation_data)
        if judiciary_result:
            search_trail.append({
                "source": judiciary_result["source_name"],
                "result": "Found",
            })
            return self._add_standard_keys(judiciary_result,
                search_trail=search_trail,
                match_confidence=50,
                found_via=judiciary_result["source_name"],
                cited_case_title=mismatch_info["title"] if mismatch_info else None,
                cited_case_url=mismatch_info["url"] if mismatch_info else None,
                cited_case_citation=mismatch_info["citation"] if mismatch_info else None,
            )
        else:
            site = self._get_judiciary_site(citation_data)
            search_trail.append({"source": site["name"], "result": "Not found"})

        # ---- If we had a mismatch but couldn't find the right case anywhere ----
        if mismatch_info:
            # Return the wrong case with typo_detected so user still sees something
            result = self._fetch_judgment(mismatch_info["url"])
            return self._add_standard_keys(result,
                status="typo_detected",
                search_trail=search_trail,
                saflii_citation=mismatch_info["citation"],
                match_confidence=0,
                year_discrepancy={
                    "document": f"{party_a} v {party_b}",
                    "saflii": mismatch_info["title"][:80],
                },
                found_via="SAFLII",
                cited_case_title=mismatch_info["title"],
                cited_case_url=mismatch_info["url"],
                cited_case_citation=mismatch_info["citation"],
            )

        # ---- Step 4: Google fallback ----
        google_result = self._search_google(citation_data)
        search_trail.append({"source": "Google", "result": "Search link generated"})
        return self._add_standard_keys(google_result,
            search_trail=search_trail,
            found_via="Google (manual)",
        )

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
        elif ctype == "old_provincial":
            # Old provincial: data = (name, year, division, page)
            court_abbrev = data[2]
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

    # ----- Judiciary.org.za fallback search -----

    # Map court codes to judiciary website search endpoints
    JUDICIARY_SITES = {
        "ZACC": {
            "name": "Constitutional Court",
            "search_url": "https://www.concourt.org.za/index.php",
            "base_url": "https://www.concourt.org.za",
        },
        "ZASCA": {
            "name": "Supreme Court of Appeal",
            "search_url": "https://www.supremecourtofappeal.org.za/index.php",
            "base_url": "https://www.supremecourtofappeal.org.za",
        },
    }

    # Fallback for all other courts
    JUDICIARY_DEFAULT = {
        "name": "SA Judiciary",
        "search_url": "https://www.judiciary.org.za/index.php",
        "base_url": "https://www.judiciary.org.za",
    }

    def _get_judiciary_site(self, citation_data):
        """Determine which judiciary website to search based on court code."""
        ctype = citation_data["type"]
        data = citation_data["data"]

        if ctype == "neutral_zacc":
            return self.JUDICIARY_SITES["ZACC"]
        elif ctype == "neutral_zasca":
            return self.JUDICIARY_SITES["ZASCA"]
        elif ctype == "neutral_regional":
            court = resolve_court_code(data[2])
            return self.JUDICIARY_SITES.get(court, self.JUDICIARY_DEFAULT)
        elif ctype == "old_provincial":
            court_abbrev = data[2]
            resolved = resolve_court_code(court_abbrev)
            return self.JUDICIARY_SITES.get(resolved, self.JUDICIARY_DEFAULT)
        elif ctype in ("standard_sa", "bclr", "sacr", "all_sa"):
            court_abbrev = data[4]
            resolved = resolve_court_code(court_abbrev)
            if resolved == "ZACC":
                return self.JUDICIARY_SITES["ZACC"]
            elif resolved == "ZASCA":
                return self.JUDICIARY_SITES["ZASCA"]
        return self.JUDICIARY_DEFAULT

    def _search_judiciary(self, citation_data):
        """Search the relevant judiciary.org.za website.

        Returns a result dict or None if not found.
        """
        display = format_citation_display(citation_data)
        party_a, party_b = extract_party_names(display)
        query = f"{party_a} v {party_b}" if party_a else display

        site = self._get_judiciary_site(citation_data)

        try:
            resp = throttled_get(
                self.session,
                site["search_url"],
                params={
                    "searchword": query,
                    "task": "search",
                    "option": "com_search",
                },
            )
            if resp.status_code != 200:
                return None

            soup = BeautifulSoup(resp.text, "html.parser")

            # Joomla search results are typically in <dl> or <div class="result">
            # We need to match party names in the results to avoid false positives
            result_links = []
            for link in soup.find_all("a", href=True):
                href = link["href"]
                text = link.get_text(strip=True).lower()

                # Must contain at least one party name to be relevant
                if not party_a:
                    continue
                pa_lower = party_a.lower()
                pb_lower = party_b.lower() if party_b else ""

                if pa_lower in text or (pb_lower and pb_lower in text):
                    if href.startswith("/"):
                        href = site["base_url"] + href
                    result_links.append({
                        "title": link.get_text(strip=True),
                        "url": href,
                    })

            if not result_links:
                # Check the full page text for party name mentions
                page_text = soup.get_text().lower()
                if party_a and party_a.lower() in page_text and party_b and party_b.lower() in page_text:
                    return {
                        "status": "found_judiciary",
                        "title": f"Reference found on {site['name']} (no direct link)",
                        "source_url": f"{site['search_url']}?searchword={quote_plus(query)}&task=search",
                        "source_name": site["name"],
                    }
                return None

            # Return the first relevant result
            best = result_links[0]
            return {
                "status": "found_judiciary",
                "title": best["title"][:120],
                "source_url": best["url"],
                "source_name": site["name"],
            }

        except Exception:
            return None

    # ----- Google fallback search -----

    def _search_google(self, citation_data):
        """Search Google as a last resort.

        Returns a result dict with a Google search URL (we don't scrape Google,
        just provide the search link for manual verification).
        """
        display = format_citation_display(citation_data)
        party_a, party_b = extract_party_names(display)

        # Build a targeted legal search query
        if party_a:
            query = f'"{party_a} v {party_b}" site:saflii.org OR site:judiciary.org.za OR site:concourt.org.za'
        else:
            query = f'"{display}" South African judgment'

        google_url = f"https://www.google.com/search?q={quote_plus(query)}"

        return {
            "status": "found_google",
            "title": "Manual verification required (Google search)",
            "source_url": google_url,
            "source_name": "Google Search",
        }

    # ----- Not-found fallback -----

    def _not_found_result(self, citation_data, search_trail=None):
        """Build a not_found result with search trail."""
        display = format_citation_display(citation_data)
        query = quote_plus(display)
        search_link = f"{SEARCH_URL}?method=all&query={query}"
        return {
            "status": "not_found",
            "source_url": search_link,
            "title": "No matching case found",
            "saflii_citation": None,
            "match_confidence": 0,
            "year_discrepancy": None,
            "search_trail": search_trail or [],
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
    elif ctype == "old_provincial":
        return f"{data[0].strip()} {data[1]} {data[2]} {data[3]}"
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
        "old_provincial": "Old Provincial",
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
    mismatches = sum(1 for r in audit_results if r["saflii"]["status"] == "mismatch_resolved")
    judiciary = sum(1 for r in audit_results if r["saflii"]["status"] == "found_judiciary")
    manual = sum(1 for r in audit_results if r["saflii"]["status"] == "found_google")
    not_found = sum(1 for r in audit_results if r["saflii"]["status"] == "not_found")
    errors = sum(1 for r in audit_results if r["saflii"]["status"] in ("error", "timeout"))
    total = len(audit_results)
    score = round(((verified + typos) / total * 100)) if total > 0 else 0

    # Citation log table
    log_rows = []
    for i, r in enumerate(audit_results, 1):
        status_map = {
            "found": "Verified (SAFLII)",
            "mismatch_resolved": "Wrong Case — Suggestion Found",
            "typo_detected": "Typo Detected (SAFLII)",
            "found_judiciary": "Found (Judiciary)",
            "found_google": "Manual Check (Google)",
            "not_found": "Not Found",
            "timeout": "Timeout",
            "error": "Error",
        }
        status_text = status_map.get(r["saflii"]["status"], "Unknown")
        found_via = r["saflii"].get("found_via", "---")
        source = found_via if r["saflii"]["status"] in ("found", "typo_detected", "mismatch_resolved", "found_judiciary") else "---"
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
**Citations Verified (SAFLII):** {verified}
**Citations with Typos:** {typos}
**Wrong Case (Mismatch Resolved):** {mismatches}
**Citations Found (Judiciary):** {judiciary}
**Citations Requiring Manual Check:** {manual}
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

    progress = st.progress(0, text="Searching SAFLII, Judiciary, and web...")

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

        found_via = r["saflii"].get("found_via", "")
        search_trail = r["saflii"].get("search_trail", [])

        cited_case_title = r["saflii"].get("cited_case_title")
        cited_case_url = r["saflii"].get("cited_case_url", "#")
        cited_case_cit = r["saflii"].get("cited_case_citation", "")
        suggested_cit = r["saflii"].get("suggested_citation", "")

        # Status cell
        if status == "found":
            status_html = '<span class="status-verified">VERIFIED</span>'
        elif status == "mismatch_resolved":
            status_html = '<span class="status-mismatch">WRONG CASE</span>'
        elif status == "typo_detected":
            status_html = '<span class="status-typo">TYPO DETECTED</span>'
        elif status == "found_judiciary":
            status_html = '<span class="status-judiciary">FOUND (JUDICIARY)</span>'
        elif status == "found_google":
            status_html = '<span class="status-google">MANUAL CHECK</span>'
        elif status == "not_found":
            status_html = '<span class="status-not-found">NOT FOUND</span>'
        elif status == "timeout":
            status_html = '<span class="status-error">TIMEOUT</span>'
        else:
            status_html = '<span class="status-error">ERROR</span>'

        # Source match cell
        if status == "mismatch_resolved":
            source_html = (
                f'<div class="cited-wrong-note">'
                f'Citation points to: {cited_case_title[:60] if cited_case_title else "Unknown"}'
                f'</div>'
            )
            if suggested_cit or title:
                source_html += (
                    f'<div class="suggestion-note">'
                    f'Suggested: {title[:60] if title else "Unknown"}'
                )
                if suggested_cit:
                    source_html += f'<br/><span class="saflii-citation">{suggested_cit}</span>'
                source_html += '</div>'
        elif status in ("found", "typo_detected"):
            source = title[:80] if title else "SAFLII"
            source_html = source
            if saflii_cit:
                source_html += f'<div class="saflii-citation">{saflii_cit}</div>'
            if year_disc:
                source_html += (
                    f'<div class="discrepancy-note">'
                    f'Doc says {year_disc["document"]}, '
                    f'SAFLII says {year_disc["saflii"]}'
                    f'</div>'
                )
        elif status == "found_judiciary":
            source_html = f'{title[:80]}'
            source_html += f'<div class="found-via-note">Found via {found_via}</div>'
        elif status == "found_google":
            source_html = f'Not found on SAFLII or Judiciary'
            source_html += f'<div class="found-via-note">Google search link provided</div>'
        elif status == "not_found":
            source_html = "---"
        else:
            error_msg = r["saflii"].get("error", "Unknown error")
            source_html = error_msg[:60]

        # Search trail
        if search_trail:
            trail_text = " &rarr; ".join(
                f'{s["source"]}: {s["result"]}' for s in search_trail
            )
            source_html += f'<div class="search-trail">{trail_text}</div>'

        # Confidence cell
        if status in ("found", "typo_detected", "mismatch_resolved") and confidence:
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
        if status == "mismatch_resolved":
            action_html = (
                f'<a href="{cited_case_url}" target="_blank" class="action-link">Cited</a>'
                f' &nbsp;|&nbsp; '
                f'<a href="{url}" target="_blank" class="action-link">Suggested</a>'
            )
        else:
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

    # ----- Discrepancy resolution panels -----
    discrepancy_results = [
        (i, r) for i, r in enumerate(st.session_state.audit_results, 1)
        if r["saflii"].get("status") in ("typo_detected", "mismatch_resolved")
    ]

    if discrepancy_results:
        st.markdown("---")
        st.markdown("### Citation Discrepancies")
        st.markdown("The following citations contain errors or point to the wrong case.")

        for idx, r in discrepancy_results:
            status = r["saflii"].get("status")
            year_disc = r["saflii"].get("year_discrepancy", {})
            saflii_cit = r["saflii"].get("saflii_citation", "---")
            confidence = r["saflii"].get("match_confidence", 0)
            title = r["saflii"].get("title", "---")

            if status == "mismatch_resolved":
                # Three-column layout: Your Citation | What It Points To | Suggested Match
                cited_title = r["saflii"].get("cited_case_title", "---")
                cited_cit = r["saflii"].get("cited_case_citation", "---")
                cited_url = r["saflii"].get("cited_case_url", "#")
                suggested_cit = r["saflii"].get("suggested_citation", "---")
                source_url = r["saflii"].get("source_url", "#")

                with st.expander(f"⚠ Ref {idx:03d} — WRONG CASE: {r['display'][:50]}", expanded=True):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.markdown("**Your Document**")
                        st.info(f"**Citation:** {r['display']}")
                        party_a, party_b = extract_party_names(r['display'])
                        if party_a:
                            st.markdown(f"**Parties:** {party_a} v {party_b}")

                    with col2:
                        st.markdown("**Citation Points To**")
                        st.error(f"**Case:** {cited_title[:80]}")
                        st.markdown(f"**Citation:** {cited_cit}")
                        st.markdown(f"[View on SAFLII]({cited_url})")

                    with col3:
                        st.markdown("**Suggested Correct Case**")
                        st.success(f"**Case:** {title[:80]}")
                        st.markdown(f"**Citation:** {suggested_cit}")
                        st.markdown(f"[View on SAFLII]({source_url})")
                        st.caption(f"Match Confidence: {confidence}%")

            else:
                # Two-column layout for typo_detected (year discrepancy etc.)
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
        if r["saflii"].get("status") in ("found", "typo_detected", "mismatch_resolved")
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
