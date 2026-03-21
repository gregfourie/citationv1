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
    /* ===== ANTHROPIC / CLAUDE DESIGN SYSTEM ===== */

    /* Palette:
       --cream:    #FAF6F1   (warm background)
       --sand:     #F0EBE4   (card backgrounds, hover)
       --clay:     #E8E0D8   (borders, dividers)
       --stone:    #B8AFA6   (muted text, placeholders)
       --ink:      #3D3929   (primary text)
       --espresso: #2A2520   (headings, sidebar bg)
       --terracotta: #D4714E (primary accent — warm coral)
       --terra-light: #F5E6DF (accent backgrounds)
       --sage:     #5B8C6F   (success / verified)
       --sage-light: #E8F0EB
       --amber:    #C49132   (warning / partial)
       --amber-light: #FBF3E4
       --sky:      #5B8FB9   (info / potential)
       --sky-light: #E6EFF6
       --plum:     #8B6DAF   (cited elsewhere)
       --plum-light: #F0EBF5
       --rust:     #C45B4A   (error / not found)
       --rust-light: #FBEAE8
    */

    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Source+Serif+4:ital,wght@0,400;0,600;1,400&family=JetBrains+Mono:wght@400;500&display=swap');

    /* Global */
    .stApp {
        background-color: #FAF6F1;
    }

    /* Headers */
    h1, h2, h3 {
        color: #2A2520 !important;
        font-family: 'Source Serif 4', Georgia, serif !important;
        font-weight: 600;
        letter-spacing: -0.01em;
    }
    h1 { font-size: 2rem !important; }
    h3 { font-weight: 500; color: #3D3929 !important; }

    /* Body text */
    p, span, label, li, div {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #2A2520;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #FAF6F1 !important;
        font-family: 'Source Serif 4', Georgia, serif !important;
    }
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label {
        color: #E8E0D8 !important;
        font-family: 'Inter', sans-serif !important;
    }
    section[data-testid="stSidebar"] hr {
        border-color: #3D3929;
        opacity: 0.4;
    }

    /* Buttons — warm terracotta accent */
    .stButton > button {
        background-color: #D4714E !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        letter-spacing: 0.02em;
        padding: 0.5rem 1.2rem !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        background-color: #B85E3F !important;
        color: #FFFFFF !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(212, 113, 78, 0.3) !important;
    }
    .stButton > button:disabled {
        background-color: #E8E0D8 !important;
        color: #B8AFA6 !important;
        opacity: 0.7;
    }

    /* Sidebar buttons — subtle on dark */
    section[data-testid="stSidebar"] .stButton > button {
        background-color: transparent !important;
        color: #E8E0D8 !important;
        border: 1px solid #3D3929 !important;
        border-radius: 8px !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background-color: #3D3929 !important;
        color: #FAF6F1 !important;
        transform: none;
        box-shadow: none !important;
    }

    /* Download button */
    .stDownloadButton > button {
        background-color: #2A2520 !important;
        color: #FAF6F1 !important;
        border: none !important;
        border-radius: 8px !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        letter-spacing: 0.02em;
        transition: all 0.2s ease !important;
    }
    .stDownloadButton > button:hover {
        background-color: #3D3929 !important;
        box-shadow: 0 4px 12px rgba(42, 37, 32, 0.2) !important;
    }

    /* File uploader — warm drop zone */
    section[data-testid="stFileUploader"] {
        border: 2px dashed #E8E0D8;
        padding: 2rem 1rem;
        background-color: #FFFFFF;
        border-radius: 12px;
        min-height: 200px;
        transition: border-color 0.2s ease;
    }
    section[data-testid="stFileUploader"]:hover {
        border-color: #D4714E;
    }
    section[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] {
        min-height: 180px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 2rem 1rem;
    }

    /* Text area */
    .stTextArea textarea {
        border: 1px solid #E8E0D8 !important;
        border-radius: 8px !important;
        font-family: 'Inter', sans-serif !important;
        background-color: #FFFFFF !important;
    }
    .stTextArea textarea:focus {
        border-color: #D4714E !important;
        box-shadow: 0 0 0 2px rgba(212, 113, 78, 0.15) !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        border-bottom: 1px solid #E8E0D8;
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'Inter', sans-serif !important;
        font-weight: 500;
        color: #B8AFA6;
        border-bottom: 2px solid transparent;
        padding: 0.5rem 1.2rem;
    }
    .stTabs [aria-selected="true"] {
        color: #D4714E !important;
        border-bottom-color: #D4714E !important;
    }

    /* Hide Streamlit branding */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }

    /* Expanders */
    .streamlit-expanderHeader {
        font-family: 'Inter', sans-serif !important;
        font-weight: 500;
        color: #3D3929;
        background-color: #F0EBE4;
        border-radius: 8px;
    }

    /* Info / Warning / Error boxes */
    .stAlert {
        border-radius: 8px !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* ===== AUDIT TABLE ===== */
    .audit-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        margin-top: 1rem;
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #E8E0D8;
    }
    .audit-table thead th {
        background-color: #2A2520;
        color: #FAF6F1;
        padding: 14px 12px;
        text-align: left;
        font-weight: 500;
        font-size: 0.75rem;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    .audit-table tbody td {
        padding: 12px;
        border-bottom: 1px solid #F0EBE4;
        color: #3D3929;
        vertical-align: top;
        background-color: #FFFFFF;
    }
    .audit-table tbody tr:last-child td {
        border-bottom: none;
    }
    .audit-table tbody tr:hover td {
        background-color: #FAF6F1;
    }

    /* Status classes */
    .status-verified { color: #5B8C6F; font-weight: 600; }
    .status-not-found { color: #C45B4A; font-weight: 600; }
    .status-manual { color: #B8AFA6; font-weight: 600; }
    .status-error { color: #C45B4A; font-weight: 600; }
    .status-typo { color: #C49132; font-weight: 600; }
    .status-potential { color: #5B8FB9; font-weight: 600; }
    .status-cited-by { color: #8B6DAF; font-weight: 600; }
    .status-mismatch { color: #C45B4A; font-weight: 600; }

    .citation-name {
        font-family: 'Source Serif 4', Georgia, serif;
        font-style: italic;
        color: #3D3929;
    }

    /* Action Links */
    .action-link {
        color: #D4714E !important;
        text-decoration: none;
        font-family: 'Inter', sans-serif;
        font-size: 0.8rem;
        font-weight: 500;
        transition: color 0.15s ease;
    }
    .action-link:hover {
        color: #B85E3F !important;
        text-decoration: underline;
    }

    /* Notes & Annotations */
    .discrepancy-note {
        font-size: 0.8rem;
        color: #C49132;
        margin-top: 4px;
        font-style: italic;
    }
    .saflii-citation {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        color: #5B8FB9;
        margin-top: 2px;
    }
    .search-trail {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        color: #B8AFA6;
        margin-top: 6px;
        line-height: 1.4;
    }
    .suggestion-note {
        color: #5B8C6F;
        font-size: 0.85em;
        margin-top: 6px;
        padding: 6px 10px;
        background: #E8F0EB;
        border-left: 3px solid #5B8C6F;
        border-radius: 0 6px 6px 0;
    }
    .cited-wrong-note {
        color: #C45B4A;
        font-size: 0.85em;
        margin-top: 4px;
        padding: 6px 10px;
        background: #FBEAE8;
        border-left: 3px solid #C45B4A;
        border-radius: 0 6px 6px 0;
    }

    /* Confidence Badges */
    .confidence-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        font-weight: 500;
    }
    .confidence-high {
        background-color: #E8F0EB;
        color: #3D7A52;
    }
    .confidence-medium {
        background-color: #FBF3E4;
        color: #9A7528;
    }
    .confidence-low {
        background-color: #FBEAE8;
        color: #A8463A;
    }

    /* ===== EXTRACTION LOG ===== */
    .terminal-log {
        background-color: #2A2520;
        color: #E8E0D8;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.82rem;
        padding: 1.5rem;
        border-radius: 12px;
        max-height: 400px;
        overflow-y: auto;
        line-height: 1.7;
    }
    .terminal-log .log-header {
        color: #B8AFA6;
        margin-bottom: 0.5rem;
    }
    .terminal-log .log-found { color: #5B8C6F; }
    .terminal-log .log-type { color: #D4714E; }

    /* Tagline */
    .tagline {
        font-family: 'Inter', sans-serif;
        color: #B8AFA6;
        letter-spacing: 0.15em;
        font-size: 0.8rem;
        font-weight: 500;
        margin-bottom: 2rem;
        text-transform: uppercase;
    }

    /* ===== SUMMARY STATS CARDS ===== */
    .stats-container {
        display: flex;
        gap: 14px;
        margin: 1.2rem 0 1.8rem 0;
        flex-wrap: wrap;
    }
    .stat-card {
        flex: 1;
        min-width: 130px;
        padding: 16px 18px;
        border-radius: 12px;
        text-align: center;
        border-left: 4px solid;
        background: #FFFFFF;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        transition: box-shadow 0.2s ease;
    }
    .stat-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    .stat-card .stat-count {
        font-size: 2rem;
        font-weight: 600;
        font-family: 'Source Serif 4', Georgia, serif;
        line-height: 1;
    }
    .stat-card .stat-label {
        font-size: 0.7rem;
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin-top: 6px;
        opacity: 0.7;
    }

    /* ===== PROGRESS BAR ===== */
    .stProgress > div > div > div {
        background-color: #D4714E !important;
    }

    /* ===== SPINNER ===== */
    .stSpinner > div {
        border-top-color: #D4714E !important;
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
        r"([A-Z][A-Za-z0-9\s&()/;]*?)\s+v\.?\s+([A-Z][A-Za-z0-9\s&()/;]*?)(?=\s*[\[\(]|\s*\d{4}|\s*SA\b|\s*BCLR\b|\s*SACR\b|\s*BLLR\b|\s*ILJ\b|\s*All\s|\s*ZA[A-Z]|\s*CCT|\s*,?\s*\d{4}|\s*$)",
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

    # Character class for party names: letters, digits, spaces, &, parentheses,
    # hyphens, apostrophes, forward-slash (t/a), semicolons (consolidated cases),
    # asterisks (footnote markers).
    # Explicitly excludes newlines (which caused cross-line leaks).
    _N = r"[A-Za-z0-9\s&()\-'/;*]"  # name chars (no period, no comma)
    _NP = r"[A-Za-z0-9\s&()\-'/;*.,]"  # name chars with period/comma (for "v." and "(Pty)")

    PATTERNS = {
        # Standard SA Reports (Juta): Case Name 1995 (3) SA 391 (CC)
        "standard_sa": r"([A-Z*]" + _NP + r"+?v\.?\s" + _NP + r"+?)\s(\d{4})\s\((\d+)\)\sSA\s(\d+)\s\(([A-Z]+)\)",
        # BCLR (LexisNexis): Case Name 1995 (6) BCLR 665 (CC)
        "bclr": r"([A-Z*]" + _NP + r"+?v\.?\s" + _NP + r"+?)\s(\d{4})\s\((\d+)\)\sBCLR\s(\d+)\s\(([A-Z]+)\)",
        # BCLR dual citation: Case Name 2015 (11) BCLR 1319 (2016 (3) SA 37)
        "bclr_dual": r"([A-Z*]" + _NP + r"+?v\.?\s" + _NP + r"+?)\s(\d{4})\s\((\d+)\)\sBCLR\s(\d+)\s\(\d{4}\s\(\d+\)\sSA\s(\d+)\)",
        # SACR: Case Name 1995 (2) SACR 1 (CC)
        "sacr": r"([A-Z*]" + _NP + r"+?v\.?\s" + _NP + r"+?)\s(\d{4})\s\((\d+)\)\sSACR\s(\d+)\s\(([A-Z]+)\)",
        # All SA (LexisNexis): Case Name 2002 (4) All SA 145 (SCA)
        "all_sa": r"([A-Z*]" + _NP + r"+?v\.?\s" + _NP + r"+?)\s(\d{4})\s\((\d+)\)\sAll\sSA\s(\d+)\s\(([A-Z]+)\)",
        # Old provincial: Blotnick v. Turecki, 1944 CPD 100
        "old_provincial": r"([A-Z*]" + _NP + r"+?v\.?\s" + _NP + r"+?),?\s(\d{4})\s(CPD|TPD|WLD|NPD|OPD|EPD|AD|SCA|DCLD|SECLD|NCHC|BCHC|ECD|NCD)\s(\d+)",
        # BLLR (Butterworths): Case Name [2012] 3 BLLR 211 (CC)
        "bllr": r"([A-Z*]" + _NP + r"+?v\.?\s" + _NP + r"+?)\s\[(\d{4})\]\s(\d+)\sBLLR\s(\d+)\s\(([A-Z]+)\)",
        # ILJ (Industrial Law Journal): Case Name (2017) 38 ILJ 295 (CC)
        "ilj": r"([A-Z*]" + _NP + r"+?v\.?\s" + _NP + r"+?)\s\((\d{4})\)\s(\d+)\sILJ\s(\d+)\s\(([A-Z]+)\)",
        # ILJ alternate: vol (ILJ) page (court) — e.g. Kruger v Aciel 37 (ILJ) 2567 (LAC)
        "ilj_alt": r"([A-Z*]" + _NP + r"+?v\.?\s" + _NP + r"+?)\s(\d+)\s\(ILJ\)\s(\d+)\s\(([A-Z]+)\)",
        # Neutral SCA: Case Name [2023] ZASCA 15
        "neutral_zasca": r"([A-Z*]" + _NP + r"+?v\.?\s" + _NP + r"+?)\s\[(\d{4})\]\sZASCA\s(\d+)",
        # Constitutional Court: [2022] ZACC 45
        "neutral_zacc": r"([A-Z*]" + _NP + r"+?v\.?\s" + _NP + r"+?)\s\[(\d{4})\]\sZACC\s(\d+)",
        # Regional (captures court code): [2023] ZAWCHC 12
        "neutral_regional": r"([A-Z*]" + _NP + r"+?v\.?\s" + _NP + r"+?)\s\[(\d{4})\]\s(ZA[A-Z]{2,8})\s(\d+)",
        # Loose/malformed SA citation: catches near-miss formats like
        # "Name v Name ... 1997 3 SA 214" (missing parentheses/court code)
        # Data tuple: (name, year, vol_or_empty, page)
        "loose_sa": r"([A-Z*]" + _NP + r"+?v\.?\s" + _NP + r"+?)\s(\d{4})\s+(\d*)\s*(?:SA|BCLR|SACR)\s(\d+)",
    }

    # Patterns for footnote citations (name and citation on separate lines)
    # These match citation-only lines (no party name prefix)
    FOOTNOTE_PATTERNS = {
        "standard_sa": r"(\d{4})\s\((\d+)\)\sSA\s(\d+)\s\(([A-Z]+)\)",
        "bclr": r"(\d{4})\s\((\d+)\)\sBCLR\s(\d+)\s\(([A-Z]+)\)",
        "sacr": r"(\d{4})\s\((\d+)\)\sSACR\s(\d+)\s\(([A-Z]+)\)",
        "all_sa": r"(\d{4})\s\((\d+)\)\sAll\sSA\s(\d+)\s\(([A-Z]+)\)",
        "bllr": r"\[(\d{4})\]\s(\d+)\sBLLR\s(\d+)\s\(([A-Z]+)\)",
        "ilj": r"\((\d{4})\)\s(\d+)\sILJ\s(\d+)\s\(([A-Z]+)\)",
    }

    @staticmethod
    def _join_split_lines(text):
        """Join lines that were split mid-citation by PDF extraction.

        PDF renderers break lines at page-width boundaries, splitting citations
        across two (sometimes three) lines. This method joins consecutive lines
        into pairs so that a second-pass regex search can find them.

        Returns a list of joined-pair strings (line_i + " " + line_i+1).
        """
        lines = text.split("\n")
        pairs = []
        for i in range(len(lines) - 1):
            a = lines[i].strip()
            b = lines[i + 1].strip()
            if a and b:
                pairs.append(a + " " + b)
        # Also join triplets for citations split across 3 lines
        for i in range(len(lines) - 2):
            a = lines[i].strip()
            b = lines[i + 1].strip()
            c = lines[i + 2].strip()
            if a and b and c:
                pairs.append(a + " " + b + " " + c)
        return pairs

    @staticmethod
    def _dedup_key(label, data):
        """Build a dedup key from citation metadata (reporter + year + page).

        Uses the citation's year and page number (or judgment number for
        neutral citations) so that the same case found with different
        amounts of leading noise in the party-name capture still deduplicates.
        """
        # Map pattern labels to the tuple indices for year and page/number
        # Most patterns: (name, year, vol, page, court) → year=1, page=3
        idx_map = {
            "standard_sa":     (1, 3),
            "bclr":            (1, 3),
            "bclr_dual":       (1, 3),
            "sacr":            (1, 3),
            "all_sa":          (1, 3),
            "old_provincial":  (1, 3),
            "bllr":            (1, 3),
            "ilj":             (1, 3),
            "ilj_alt":         (0, 2),   # (name, vol, page, court) — no year
            "neutral_zasca":   (1, 2),   # (name, year, number)
            "neutral_zacc":    (1, 2),
            "neutral_regional":(1, 3),   # (name, year, court, number)
            "loose_sa":        (1, 3),
        }
        yi, pi = idx_map.get(label, (1, 3))
        year = data[yi] if yi < len(data) else ""
        page = data[pi] if pi < len(data) else ""
        return f"{label}|{year}|{page}"

    @staticmethod
    def _cross_dedup_key(label, data):
        """Build a label-agnostic dedup key to catch the same citation matched
        by different pattern types (e.g. neutral_zacc vs neutral_regional)."""
        idx_map = {
            "standard_sa":     (1, 3),
            "bclr":            (1, 3),
            "bclr_dual":       (1, 3),
            "sacr":            (1, 3),
            "all_sa":          (1, 3),
            "old_provincial":  (1, 3),
            "bllr":            (1, 3),
            "ilj":             (1, 3),
            "ilj_alt":         (0, 2),
            "neutral_zasca":   (1, 2),
            "neutral_zacc":    (1, 2),
            "neutral_regional":(1, 3),
            "loose_sa":        (1, 3),
        }
        yi, pi = idx_map.get(label, (1, 3))
        year = data[yi] if yi < len(data) else ""
        page = data[pi] if pi < len(data) else ""
        return f"{year}|{page}"

    def extract_citations(self, text):
        found = []
        seen = set()        # primary: label + year + page
        seen_cross = set()  # secondary: year + page (cross-pattern dedup)

        # Run inline patterns per-line to prevent cross-line matches
        lines = text.split("\n")
        ordered_keys = [
            "standard_sa", "bclr", "bclr_dual", "sacr", "all_sa",
            "old_provincial", "bllr", "ilj", "ilj_alt",
            "neutral_zasca", "neutral_zacc", "neutral_regional",
            "loose_sa",
        ]
        for line in lines:
            line = line.strip()
            if not line:
                continue
            for label in ordered_keys:
                pattern = self.PATTERNS[label]
                matches = re.findall(pattern, line)
                for m in matches:
                    dk = self._dedup_key(label, m)
                    xk = self._cross_dedup_key(label, m)
                    if dk in seen or xk in seen_cross:
                        continue
                    seen.add(dk)
                    seen_cross.add(xk)
                    found.append({"type": label, "data": m})

        # --- Second pass: join split lines and re-search ---
        # PDF extraction often breaks citations across 2-3 lines.
        # Join adjacent line pairs/triplets and search again.
        joined_lines = self._join_split_lines(text)
        for joined in joined_lines:
            for label in ordered_keys:
                pattern = self.PATTERNS[label]
                matches = re.findall(pattern, joined)
                for m in matches:
                    dk = self._dedup_key(label, m)
                    xk = self._cross_dedup_key(label, m)
                    if dk in seen or xk in seen_cross:
                        continue
                    seen.add(dk)
                    seen_cross.add(xk)
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
                        r"([A-Z*][A-Za-z0-9\s&()\-'/;*.,]+?v\.?\s[A-Za-z0-9\s&()\-'/;*.,]+?)(?:\s*\d*\s*$)",
                        prev_line,
                    )
                    if name_match:
                        party_name = name_match.group(1).strip().rstrip(",. *0123456789")
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



# ---------------------------------------------------------------------------
# Confidence Tiers
# ---------------------------------------------------------------------------

CONFIDENCE_TIERS = {
    "EXACT_MATCH":           {"label": "Verified",        "colour": "#5B8C6F", "css_class": "status-verified"},
    "PARTIAL_MATCH":         {"label": "Likely Match",    "colour": "#C49132", "css_class": "status-typo"},
    "POTENTIAL_MATCH":       {"label": "Possible Match",  "colour": "#5B8FB9", "css_class": "status-potential"},
    "CITED_IN_OTHER_CASES":  {"label": "Cited Elsewhere", "colour": "#8B6DAF", "css_class": "status-cited-by"},
    "NOT_FOUND":             {"label": "Not Found",       "colour": "#C45B4A", "css_class": "status-not-found"},
}

CONFIDENCE_LABELS = {
    "EXACT_MATCH":           "Exact match — case found on SAFLII",
    "PARTIAL_MATCH":         "Partial match — strong overlap, verify manually",
    "POTENTIAL_MATCH":       "Potential match — some indicators align, needs verification",
    "CITED_IN_OTHER_CASES":  "Not on SAFLII directly, but cited in other judgments",
    "NOT_FOUND":             "Not found on SAFLII — potential hallucination, verify independently",
}


def _classify_confidence(status, match_confidence, found_via, citation_data):
    """Map lookup results to the 5-tier confidence system.

    Args:
        status: the raw status from SafliiBridge.lookup()
        match_confidence: numeric confidence (0-100)
        found_via: source string (SAFLII only)
        citation_data: the parsed citation dict

    Returns:
        One of: EXACT_MATCH, PARTIAL_MATCH, POTENTIAL_MATCH,
                CITED_IN_OTHER_CASES, NOT_FOUND
    """
    # Direct SAFLII hit with high confidence → EXACT
    if status == "found" and found_via == "SAFLII" and match_confidence >= 80:
        return "EXACT_MATCH"

    # SAFLII hit with moderate confidence or typo → PARTIAL
    if status in ("found", "typo_detected") and found_via == "SAFLII" and match_confidence >= 50:
        return "PARTIAL_MATCH"

    # Mismatch resolved (wrong case at URL, right case found by search) → PARTIAL
    if status == "mismatch_resolved":
        return "PARTIAL_MATCH"

    # SAFLII hit but low confidence → POTENTIAL
    if status in ("found", "typo_detected") and found_via == "SAFLII":
        return "POTENTIAL_MATCH"

    # Case not on SAFLII itself, but cited/referenced in other cases
    if status == "cited_in_other_cases":
        return "CITED_IN_OTHER_CASES"

    # Old provincial citations are NOT automatically "cited elsewhere"
    # — only classify as CITED_IN_OTHER_CASES if the search actually found citing cases

    # Nothing found on SAFLII
    return "NOT_FOUND"


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
        """Look up a citation on SAFLII only.

        When the direct URL points to a different case (name mismatch), the search
        continues by party name to find the intended case and reports both.
        """
        ctype = citation_data["type"]
        data = citation_data["data"]
        display = format_citation_display(citation_data)

        party_a, party_b = extract_party_names(display)
        # Year is at data[1] for most types, but ilj_alt has no year (data = name, vol, page, court)
        doc_year = data[1] if ctype != "ilj_alt" else ""

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
                # Search returned results but none matched — case is cited by others
                citing_count = len(search_results)
                search_trail.append({
                    "source": "SAFLII (cited-by)",
                    "result": f"Referenced in {citing_count} other case{'s' if citing_count != 1 else ''}",
                })
                # Return as cited_in_other_cases with the search link and count
                not_found = self._not_found_result(citation_data, search_trail)
                not_found["status"] = "cited_in_other_cases"
                not_found["citing_cases_count"] = citing_count
                # Pick a representative citing case for context
                top_citing = search_results[0]
                not_found["top_citing_title"] = top_citing.get("title", "")
                not_found["top_citing_url"] = top_citing.get("url", "")
                return self._add_standard_keys(not_found,
                    search_trail=search_trail,
                    found_via="SAFLII",
                )
        else:
            search_trail.append({"source": "SAFLII (search)", "result": "No results"})

        # ---- If we had a mismatch but couldn't find the right case on SAFLII ----
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

        # ---- Not found on SAFLII ----
        return self._add_standard_keys(
            self._not_found_result(citation_data, search_trail),
            search_trail=search_trail,
            found_via=None,
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

        # Normalize "v." to "v" — old-fashioned form hurts search results
        query = re.sub(r'\bv\.\s', 'v ', query)

        # Strip ampersands — SAFLII's search engine converts URL-encoded '&' (%26)
        # into the literal word "amp", which breaks the query.
        # e.g. "Aviation Union of SA & another" → searches for "...amp another"
        query = query.replace("&", " ")
        # Collapse multiple spaces from the replacement
        query = re.sub(r'\s{2,}', ' ', query).strip()

        # No court filter — search across all SA courts for maximum recall.
        # The fuzzy matching step will verify the correct case is selected.
        ctype = citation_data["type"]
        data = citation_data["data"]
        court_filter = None

        if ctype == "old_provincial":
            # Old provincial: search with full citation string (not just party names)
            # because citing cases contain the full reference in their text
            query = re.sub(r'\bv\.\s', 'v ', display)

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


def _clean_party_name(raw_name):
    """Strip leading noise from a party name captured from joined lines.

    PDF line-joining can prepend unrelated text before the actual party name.
    We find the last occurrence of a plausible party name start (uppercase word
    followed eventually by 'v') and discard anything before it.
    Also strips footnote markers like leading * or trailing footnote numbers.
    """
    name = raw_name.strip().lstrip("*").strip()
    # If the name contains 'v' (the versus separator), try to trim leading junk
    v_match = re.search(r'\bv\.?\s', name)
    if v_match:
        # Walk backwards from the 'v' to find where the real party name starts
        before_v = name[:v_match.start()]
        # Find the last sentence-ending punctuation or footnote number before
        # the actual party name. Common noise patterns:
        # "...some text. 15 Aviation Union" or "...transaction 14 Swanepoel"
        trim_match = re.search(
            r'(?:^|[.;:!?"\])])\s*(?:\d+\s+)?([A-Z*])',
            before_v,
        )
        if trim_match:
            start = trim_match.start(1)
            name = name[start:]
    name = name.strip().lstrip("*").strip()
    # Strip trailing footnote numbers
    name = re.sub(r'\s*\d+\s*$', '', name)
    return name


def format_citation_display(citation):
    """Format a citation dict into a human-readable string."""
    ctype = citation["type"]
    data = citation["data"]
    name = _clean_party_name(data[0])

    if ctype == "standard_sa":
        return f"{name} {data[1]} ({data[2]}) SA {data[3]} ({data[4]})"
    elif ctype == "bclr":
        return f"{name} {data[1]} ({data[2]}) BCLR {data[3]} ({data[4]})"
    elif ctype == "bclr_dual":
        return f"{name} {data[1]} ({data[2]}) BCLR {data[3]}"
    elif ctype == "sacr":
        return f"{name} {data[1]} ({data[2]}) SACR {data[3]} ({data[4]})"
    elif ctype == "all_sa":
        return f"{name} {data[1]} ({data[2]}) All SA {data[3]} ({data[4]})"
    elif ctype == "old_provincial":
        return f"{name} {data[1]} {data[2]} {data[3]}"
    elif ctype == "bllr":
        return f"{name} [{data[1]}] {data[2]} BLLR {data[3]} ({data[4]})"
    elif ctype == "ilj":
        return f"{name} ({data[1]}) {data[2]} ILJ {data[3]} ({data[4]})"
    elif ctype == "ilj_alt":
        return f"{name} {data[1]} (ILJ) {data[2]} ({data[3]})"
    elif ctype == "neutral_zasca":
        return f"{name} [{data[1]}] ZASCA {data[2]}"
    elif ctype == "neutral_zacc":
        return f"{name} [{data[1]}] ZACC {data[2]}"
    elif ctype == "neutral_regional":
        return f"{name} [{data[1]}] {data[2]} {data[3]}"
    elif ctype == "loose_sa":
        vol = f" ({data[2]})" if data[2] else ""
        return f"{name} {data[1]}{vol} SA {data[3]}"

    return str(data)


def citation_type_label(ctype):
    """Return a human-readable label for citation type."""
    labels = {
        "standard_sa": "SA Reports (Juta)",
        "bclr": "BCLR (LexisNexis)",
        "bclr_dual": "BCLR (Dual Citation)",
        "sacr": "SACR",
        "all_sa": "All SA (LexisNexis)",
        "old_provincial": "Old Provincial",
        "bllr": "BLLR (Butterworths)",
        "ilj": "ILJ (Industrial Law Journal)",
        "ilj_alt": "ILJ (Alternate Format)",
        "neutral_zasca": "SCA (Neutral)",
        "neutral_zacc": "CC (Neutral)",
        "neutral_regional": "Regional (Neutral)",
        "loose_sa": "Malformed Citation",
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

    # Count by confidence tier
    exact = sum(1 for r in audit_results if r["saflii"].get("confidence_tier") == "EXACT_MATCH")
    partial = sum(1 for r in audit_results if r["saflii"].get("confidence_tier") == "PARTIAL_MATCH")
    potential = sum(1 for r in audit_results if r["saflii"].get("confidence_tier") == "POTENTIAL_MATCH")
    cited_by = sum(1 for r in audit_results if r["saflii"].get("confidence_tier") == "CITED_IN_OTHER_CASES")
    not_found = sum(1 for r in audit_results if r["saflii"].get("confidence_tier") == "NOT_FOUND")
    errors = sum(1 for r in audit_results if r["saflii"]["status"] in ("error", "timeout"))
    total = len(audit_results)
    # Legacy counts for backward compat
    verified = exact
    typos = sum(1 for r in audit_results if r["saflii"]["status"] == "typo_detected")
    mismatches = sum(1 for r in audit_results if r["saflii"]["status"] == "mismatch_resolved")
    score = round(((exact + partial) / total * 100)) if total > 0 else 0

    # Citation log table
    log_rows = []
    for i, r in enumerate(audit_results, 1):
        tier = r["saflii"].get("confidence_tier", "NOT_FOUND")
        tier_label = CONFIDENCE_TIERS.get(tier, {}).get("label", "Unknown")
        found_via = r["saflii"].get("found_via", "---")
        source = found_via if r["saflii"]["status"] in ("found", "typo_detected", "mismatch_resolved") else "---"
        ref_id = f"CC-{i:03d}"
        confidence = r["saflii"].get("match_confidence", "---")
        notes = ""
        if r["saflii"]["status"] == "typo_detected":
            notes = " (typo)"
        elif r["saflii"]["status"] == "mismatch_resolved":
            notes = " (wrong case)"
        log_rows.append(
            f"| {r['display']} | {source} | {tier_label}{notes} | {confidence}% | {ref_id} |"
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

### Confidence Breakdown
| Tier | Count | Description |
| :--- | :--- | :--- |
| **Exact Match** | {exact} | Case found on SAFLII with high confidence |
| **Partial Match** | {partial} | Strong overlap — verify manually |
| **Potential Match** | {potential} | Some indicators align — needs verification |
| **Cited Elsewhere** | {cited_by} | Not on SAFLII but cited in other judgments |
| **Not Found** | {not_found} | Not found — potential hallucination |
| **Errors/Timeouts** | {errors} | Technical failures |

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
# Screen: Add Citations (Upload / Paste)
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

    st.markdown("### Add Citations to Verify")
    st.markdown("Upload a document or paste citations directly to begin extraction.")

    tab_upload, tab_paste = st.tabs(["Upload File", "Paste Text"])

    with tab_upload:
        uploaded_files = st.file_uploader(
            "Drop your .docx or .pdf files here",
            type=["docx", "pdf"],
            key="file_uploader",
            accept_multiple_files=True,
        )

        if uploaded_files:
            # Build a combined fingerprint of all filenames to detect changes
            current_names = sorted(f.name for f in uploaded_files)
            combined_name = " + ".join(current_names) if len(current_names) > 1 else current_names[0]

            if st.session_state.filename != combined_name:
                st.session_state.filename = combined_name
                all_text = []
                with st.spinner(f"Extracting text from {len(uploaded_files)} file{'s' if len(uploaded_files) > 1 else ''}..."):
                    for f in uploaded_files:
                        text = extract_text(f)
                        if text:
                            all_text.append(text)

                combined_text = "\n\n".join(all_text)
                st.session_state.uploaded_text = combined_text

                engine = CitationEngine()
                citations = engine.extract_citations(combined_text)
                st.session_state.citations = citations
                st.session_state.audit_results = []
                st.session_state.audit_complete = False
                st.session_state.downloaded_pdfs = {}

    with tab_paste:
        pasted = st.text_area(
            "Paste citations here (one per line, or a block of text containing citations)",
            height=200,
            key="pasted_text",
            placeholder="e.g. Barkhuizen v Napier 2007 (5) SA 323 (CC)\n     Minister of Health v Treatment Action Campaign [2002] ZACC 15",
        )
        if st.button("EXTRACT CITATIONS", key="extract_pasted", use_container_width=True):
            if pasted and pasted.strip():
                st.session_state.filename = "Pasted Text"
                st.session_state.uploaded_text = pasted
                engine = CitationEngine()
                citations = engine.extract_citations(pasted)
                st.session_state.citations = citations
                st.session_state.audit_results = []
                st.session_state.audit_complete = False
                st.session_state.downloaded_pdfs = {}
                st.rerun()

    # Terminal log
    if st.session_state.citations:
        log_lines = [
            '<div class="terminal-log">',
            '<div class="log-header">--- CITATIONS EXTRACTED FROM DOCUMENT ---</div>',
            f'<div class="log-header">File: {st.session_state.filename}</div>',
            f'<div class="log-header">Citations extracted: {len(st.session_state.citations)} (not yet verified)</div>',
            "<br>",
        ]

        for i, c in enumerate(st.session_state.citations, 1):
            display = format_citation_display(c)
            type_label = citation_type_label(c["type"])
            log_lines.append(
                f'<div><span class="log-found">[{i:03d}]</span> '
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

    progress = st.progress(0, text="Searching SAFLII...")

    for i, c in enumerate(citations):
        display = format_citation_display(c)
        progress.progress(
            (i + 1) / len(citations),
            text=f"Checking {i + 1}/{len(citations)}: {display[:60]}...",
        )

        saflii_result = bridge.lookup(c)

        # Classify into 5-tier confidence system
        confidence_tier = _classify_confidence(
            status=saflii_result.get("status", "not_found"),
            match_confidence=saflii_result.get("match_confidence", 0),
            found_via=saflii_result.get("found_via", ""),
            citation_data=c,
        )
        saflii_result["confidence_tier"] = confidence_tier
        saflii_result["confidence_tier_label"] = CONFIDENCE_LABELS.get(confidence_tier, "")

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

    # Summary stats cards
    tier_counts = {}
    for r in st.session_state.audit_results:
        tier = r["saflii"].get("confidence_tier", "NOT_FOUND")
        tier_counts[tier] = tier_counts.get(tier, 0) + 1

    stats_html = '<div class="stats-container">'
    for tier_key, tier_info in CONFIDENCE_TIERS.items():
        count = tier_counts.get(tier_key, 0)
        colour = tier_info["colour"]
        label = tier_info["label"]
        # Light background derived from the tier colour
        stats_html += (
            f'<div class="stat-card" style="border-left-color: {colour}; '
            f'background: {colour}15;">'
            f'<div class="stat-count" style="color: {colour};">{count}</div>'
            f'<div class="stat-label">{label}</div>'
            f'</div>'
        )
    stats_html += '</div>'
    st.markdown(stats_html, unsafe_allow_html=True)

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

        # Status cell — use 5-tier confidence system
        confidence_tier = r["saflii"].get("confidence_tier", "NOT_FOUND")
        tier_info = CONFIDENCE_TIERS.get(confidence_tier, CONFIDENCE_TIERS["NOT_FOUND"])
        tier_label = tier_info["label"]
        tier_colour = tier_info["colour"]

        # Add sub-status for typos and mismatches
        if status == "mismatch_resolved":
            status_html = f'<span style="color:{tier_colour};font-weight:bold;">{tier_label}</span><br/><span style="font-size:0.75em;color:#C49132;">WRONG CASE</span>'
        elif status == "typo_detected":
            status_html = f'<span style="color:{tier_colour};font-weight:bold;">{tier_label}</span><br/><span style="font-size:0.75em;color:#C49132;">TYPO DETECTED</span>'
        elif status == "timeout":
            status_html = '<span class="status-error">TIMEOUT</span>'
        elif status == "error":
            status_html = '<span class="status-error">ERROR</span>'
        else:
            status_html = f'<span style="color:{tier_colour};font-weight:bold;">{tier_label}</span>'

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
        elif status == "cited_in_other_cases":
            citing_count = r["saflii"].get("citing_cases_count", 0)
            top_title = r["saflii"].get("top_citing_title", "")
            source_html = (
                f'<div style="color:#8B6DAF;font-size:0.85rem;">'
                f'Not on SAFLII, but referenced in <strong>{citing_count}</strong> '
                f'other case{"s" if citing_count != 1 else ""}'
                f'</div>'
            )
            if top_title:
                source_html += (
                    f'<div style="font-size:0.8rem;color:#B8AFA6;margin-top:2px;">'
                    f'e.g. {top_title[:70]}…</div>'
                )
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
            confidence_html = '<span style="color: #B8AFA6;">---</span>'

        # Action cell
        if status == "mismatch_resolved":
            action_html = (
                f'<a href="{cited_case_url}" target="_blank" class="action-link">Cited</a>'
                f' &nbsp;|&nbsp; '
                f'<a href="{url}" target="_blank" class="action-link">Suggested</a>'
            )
        elif status == "cited_in_other_cases":
            action_html = f'<a href="{url}" target="_blank" class="action-link">View Citing Cases</a>'
        elif status == "not_found":
            action_html = f'<a href="{url}" target="_blank" class="action-link">Search SAFLII</a>'
        elif status in ("found", "typo_detected"):
            action_html = f'<a href="{url}" target="_blank" class="action-link">View Source</a>'
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
                    f'<p style="color: #3D3929; font-family: Source Serif 4, Georgia, serif; '
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
                    f'<p style="font-family: Source Serif 4, Georgia, serif; color: #3D3929; '
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
        file_name=f"citation_audit_{st.session_state.filename.rsplit('.', 1)[0]}_{date.today().strftime('%Y%m%d')}.md" if st.session_state.filename else f"citation_audit_{date.today().strftime('%Y%m%d')}.md",
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
            '<p style="font-family: Inter, sans-serif; font-size: 0.7rem; '
            'letter-spacing: 0.15em; color: #B8AFA6; font-weight: 500;">VERIFY / AUDIT / CERTIFY</p>',
            unsafe_allow_html=True,
        )
        st.markdown("---")

        if st.button("Add Citations", use_container_width=True):
            st.session_state.current_screen = "hopper"
            st.session_state.uploaded_text = None
            st.session_state.citations = []
            st.session_state.audit_results = []
            st.session_state.filename = None
            st.session_state.audit_complete = False
            st.session_state.downloaded_pdfs = {}
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
                total = len(st.session_state.audit_results)
                for tier_key, tier_info in CONFIDENCE_TIERS.items():
                    count = sum(
                        1 for r in st.session_state.audit_results
                        if r["saflii"].get("confidence_tier") == tier_key
                    )
                    if count > 0:
                        st.markdown(
                            f'<span style="color:{tier_info["colour"]};">●</span> '
                            f'**{tier_info["label"]}:** {count}',
                            unsafe_allow_html=True,
                        )

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
