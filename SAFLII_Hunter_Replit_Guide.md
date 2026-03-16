# SAFLII Hunter — Replit Integration Guide

Generated: 16 March 2026

---

## What This Document Is

Instructions for integrating the **SAFLII Hunter** confidence-classified citation verification into your Replit Citation Checker app. The hunter accepts any SA citation format and returns one of five confidence levels, replacing the current binary "found / not found" logic.

---

## The Five Confidence Tiers

Every citation lookup now returns a **confidence classification**. These map directly to the status badges and colours in the Citation Checker UI.

| Tier | Constant | UI Label | Badge Colour | What It Means |
|------|----------|----------|-------------|---------------|
| 1 | `EXACT_MATCH` | **Verified** | Green | The case itself exists on SAFLII. Direct URL confirmed (neutral citation) or search result title contains the exact citation reference (law report/case number). Safe to rely on. |
| 2 | `PARTIAL_MATCH` | **Likely Match** | Amber | Strong overlap — right year + series + page but different volume, or case number partially matches. The top result is probably correct but should be verified manually. |
| 3 | `POTENTIAL_MATCH` | **Possible Match** | Blue | Some indicators align (same year and series, or same court) but not enough for confidence. Could be the right case, could be a different one. Manual check required. |
| 4 | `CITED_IN_OTHER_CASES` | **Cited Elsewhere** | Purple | The case is **not on SAFLII itself**, but other SAFLII judgments cite it. This proves the case exists (real courts referenced it) even though SAFLII doesn't host the full text. Returns max 3 citing cases. |
| 5 | `NOT_FOUND` | **Not Found** | Red | Zero results on SAFLII. No other case references this citation. Flag as **potential hallucination**. |

### How Scoring Works

For search results (law report, old-style, and case number citations), each SAFLII result is scored 0–12 against the target citation:

| Score | Tier | How it's determined |
|-------|------|-------------------|
| 10–12 | EXACT | Title contains the full citation reference (e.g. `2020 (6) SA 325 (CC)` appears in the SAFLII result title) |
| 5–9 | PARTIAL | Year + series + page all present but volume differs, or case number prefix + number match |
| 1–4 | POTENTIAL | Year + series present, or year + court match, but page number doesn't match |
| 0 | CITED_BY | Results exist but none match — they are *other* cases that happen to cite the target |

For **neutral citations** (`[2020] ZACC 10`), the URL is built deterministically and verified with an HTTP request. A 200 response = EXACT_MATCH, no search needed.

---

## Citation Formats Supported

The same case can appear in multiple citation formats. The hunter recognises all of them:

### Format 1: Neutral Citation (SAFLII / Court)

```
[2020] ZACC 10
```

- **Resolution**: Direct URL → `saflii.org/za/cases/ZACC/2020/10.pdf`
- **Confidence**: Always EXACT if URL returns 200
- **This is the gold standard** — no ambiguity

### Format 2: Law Report — LexisNexis

```
2020 (8) BCLR 916 (CC)
```

- **Resolution**: Search SAFLII for `2020 (8) BCLR 916` filtered to ZACC court
- **Confidence**: Depends on whether the exact reference appears in result titles

### Format 3: Law Report — Juta

```
2020 (6) SA 325 (CC)
```

- **Resolution**: Same as LexisNexis — search + re-rank
- **Confidence**: Same scoring logic

### Format 4: Case Number

```
CCT 232/19
```

- **Resolution**: Search SAFLII for `CCT 232/19`, filtered to Constitutional Court
- **Confidence**: EXACT if case number appears in result title

### Format 5: Old Provincial Division (pre-SAFLII era)

```
1944 CPD 100
1971 (2) SA 388 (W)
1955 AD 1
```

- **Resolution**: Search SAFLII for `1944 CPD 100`, mapped to successor court (ZAWCHC)
- **Confidence**: Usually CITED_BY or NOT_FOUND (these predate SAFLII's coverage)

### One Case, Four References (Real Example)

```
Economic Freedom Fighters v Gordhan and Others; Public Protector and Another v Gordhan
and Others (CCT 232/19; CCT 233/19) [2020] ZACC 10; 2020 (8) BCLR 916 (CC);
2020 (6) SA 325 (CC) (29 May 2020)
```

| Reference | Format | Expected Confidence |
|-----------|--------|-------------------|
| `[2020] ZACC 10` | Neutral | EXACT |
| `2020 (8) BCLR 916 (CC)` | LexisNexis | EXACT (appears in SAFLII title) |
| `2020 (6) SA 325 (CC)` | Juta | EXACT (appears in SAFLII title) |
| `CCT 232/19` | Case number | EXACT (appears in SAFLII title) |

---

## How to Use in the Replit App

### Option A: Call saflii_hunter.py Directly (Server-Side)

If your Replit server can run Python and reach saflii.org:

```bash
# Single citation — returns JSON with confidence
python3 saflii_hunter.py json '{"action": "hunt", "citation": "2020 (6) SA 325 (CC)"}'

# Scan a text file — returns array of results with confidence
python3 saflii_hunter.py json '{"action": "scan", "file": "uploaded.txt"}'

# Classify only (no network call) — identify citation type
python3 saflii_hunter.py json '{"action": "classify", "citation": "1944 CPD 100"}'

# Extract all citations from text (no network call)
python3 saflii_hunter.py json '{"action": "scan_text", "text": "In EFF v Gordhan [2020] ZACC 10..."}'
```

**JSON output for `hunt`:**
```json
{
  "type": "law_report",
  "confidence": "EXACT_MATCH",
  "confidence_label": "Exact match — the case itself is on SAFLII",
  "results_count": 5,
  "results": [
    {
      "title": "Independent Institute of Education v KZN Law Society [2019] ZACC 47; 2020 (2) SA 325 (CC)",
      "url": "https://www.saflii.org/za/cases/ZACC/2019/47.html",
      "citation": "[2019] ZACC 47",
      "match_score": 12
    }
  ],
  "cited_by": [],
  "downloaded": null
}
```

**JSON output for `scan`:**
```json
[
  {
    "input": "[2020] ZACC 10",
    "type": "neutral",
    "confidence": "EXACT_MATCH",
    "confidence_label": "Exact match — the case itself is on SAFLII",
    "results_count": 1,
    "cited_by_count": 0,
    "downloaded": null
  },
  {
    "input": "1944 CPD 100",
    "type": "old_report",
    "confidence": "CITED_IN_OTHER_CASES",
    "confidence_label": "Not found directly, but cited in other SAFLII judgments",
    "results_count": 3,
    "cited_by_count": 3,
    "downloaded": null
  }
]
```

### Option B: Port the Logic to TypeScript (Recommended for Replit)

Since SAFLII blocks cloud/server IPs (returns 410), the Replit app already builds SAFLII URLs client-side and uses Gemini for lookups. The confidence classification logic should be added to `safliiSearcher.ts`.

---

## TypeScript Integration — Changes to `safliiSearcher.ts`

### Step 1: Add Confidence Types

Add to the top of `safliiSearcher.ts`:

```typescript
// ── Confidence tiers ──────────────────────────────────────
export type ConfidenceLevel =
  | "EXACT_MATCH"
  | "PARTIAL_MATCH"
  | "POTENTIAL_MATCH"
  | "CITED_IN_OTHER_CASES"
  | "NOT_FOUND";

export const CONFIDENCE_LABELS: Record<ConfidenceLevel, string> = {
  EXACT_MATCH:           "Verified — case found on SAFLII",
  PARTIAL_MATCH:         "Likely match — verify manually",
  POTENTIAL_MATCH:       "Possible match — needs verification",
  CITED_IN_OTHER_CASES:  "Not on SAFLII, but cited in other judgments",
  NOT_FOUND:             "Not found — potential hallucination",
};

export const CONFIDENCE_COLOURS: Record<ConfidenceLevel, string> = {
  EXACT_MATCH:          "green",
  PARTIAL_MATCH:        "amber",
  POTENTIAL_MATCH:      "blue",
  CITED_IN_OTHER_CASES: "purple",
  NOT_FOUND:            "red",
};
```

### Step 2: Add Confidence to SearchResult

Update the `SearchResult` interface:

```typescript
export interface SearchResult {
  status: string;
  matchReason: string;
  safliiUrl?: string;
  safliiTitle?: string;
  downloadUrl?: string;
  searchTrail: string[];
  // NEW fields:
  confidence: ConfidenceLevel;
  confidenceLabel: string;
  matchScore: number;          // 0–12
  citedBy?: Array<{            // max 3, only when confidence = CITED_IN_OTHER_CASES
    title: string;
    url: string;
  }>;
}
```

### Step 3: Map Existing Cascade Steps to Confidence

Update each step function to set confidence:

```typescript
// Step 1 — Neutral citation direct URL
function step1NeutralCitation(citation: Citation, trail: string[]): SearchResult | null {
  // ... existing URL-building logic ...
  if (safliiUrl) {
    return {
      status: "verified",
      matchReason: `Direct SAFLII URL from neutral citation`,
      safliiUrl,
      safliiTitle: citation.raw,
      downloadUrl: safliiUrl.replace(".html", ".pdf"),
      searchTrail: trail,
      // NEW:
      confidence: "EXACT_MATCH",
      confidenceLabel: CONFIDENCE_LABELS.EXACT_MATCH,
      matchScore: 12,
    };
  }
  return null;
}

// Step 2 — Gemini returns neutral citation
// If Gemini succeeds: PARTIAL_MATCH (score 7) because we trust Gemini
// but can't verify the URL from a cloud server
async function step2GeminiLookup(citation: Citation, trail: string[]): Promise<SearchResult | null> {
  // ... existing Gemini logic ...
  if (neutralCitation) {
    return {
      status: "needs_verification",
      matchReason: `AI identified neutral citation: ${neutralCitation}`,
      safliiUrl,
      safliiTitle: citation.raw,
      downloadUrl: safliiUrl.replace(".html", ".pdf"),
      searchTrail: trail,
      // NEW:
      confidence: "PARTIAL_MATCH",
      confidenceLabel: CONFIDENCE_LABELS.PARTIAL_MATCH,
      matchScore: 7,
    };
  }
  return null;
}

// Step 3 — Not found on SAFLII
// If Steps 1 and 2 both fail, the citation is NOT_FOUND
function step3NotFound(citation: Citation, trail: string[]): SearchResult {
  trail.push("SAFLII: No matching case found");
  return {
    status: "not_found",
    confidence: "NOT_FOUND",
    confidenceLabel: CONFIDENCE_LABELS.NOT_FOUND,
    matchScore: 0,
    matchReason: `Not found on SAFLII. This citation may be hallucinated.`,
    searchTrail: trail,
  };
}
```

### Step 4: Update `StatusBadge.tsx`

```tsx
const BADGE_CONFIG: Record<string, { label: string; className: string }> = {
  // Map from confidence level to UI
  EXACT_MATCH:          { label: "Verified",        className: "bg-green-100 text-green-800 border-green-300" },
  PARTIAL_MATCH:        { label: "Likely Match",    className: "bg-amber-100 text-amber-800 border-amber-300" },
  POTENTIAL_MATCH:      { label: "Possible Match",  className: "bg-blue-100 text-blue-800 border-blue-300" },
  CITED_IN_OTHER_CASES: { label: "Cited Elsewhere", className: "bg-purple-100 text-purple-800 border-purple-300" },
  NOT_FOUND:            { label: "Not Found",       className: "bg-red-100 text-red-800 border-red-300" },
};

export function StatusBadge({ confidence }: { confidence: string }) {
  const config = BADGE_CONFIG[confidence] ?? BADGE_CONFIG.NOT_FOUND;
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${config.className}`}>
      {config.label}
    </span>
  );
}
```

### Step 5: Update `CitationResultCard.tsx`

Add confidence display and cited-by section:

```tsx
function CitationResultCard({ result }: { result: CaseResult }) {
  return (
    <div className="border rounded-lg p-4 mb-3">
      <div className="flex items-center justify-between mb-2">
        <span className="font-medium">{result.citation.raw}</span>
        <StatusBadge confidence={result.confidence} />
      </div>

      <p className="text-sm text-gray-600 mb-2">{result.confidenceLabel}</p>

      {/* Show SAFLII link for EXACT and PARTIAL */}
      {result.safliiUrl && (
        <a href={result.safliiUrl} target="_blank" className="text-blue-600 hover:underline text-sm">
          View on SAFLII
        </a>
      )}

      {/* Show citing cases for CITED_IN_OTHER_CASES */}
      {result.confidence === "CITED_IN_OTHER_CASES" && result.citedBy?.length > 0 && (
        <div className="mt-2 pl-3 border-l-2 border-purple-200">
          <p className="text-xs font-medium text-purple-700 mb-1">Referenced in:</p>
          {result.citedBy.map((cb, i) => (
            <a key={i} href={cb.url} target="_blank" className="block text-xs text-purple-600 hover:underline">
              {cb.title}
            </a>
          ))}
        </div>
      )}

      {/* Show hallucination warning for NOT_FOUND */}
      {result.confidence === "NOT_FOUND" && (
        <div className="mt-2 p-2 bg-red-50 rounded text-xs text-red-700">
          This citation could not be verified on SAFLII or in any other SAFLII judgment.
          It may be hallucinated. Verify independently before relying on it.
        </div>
      )}
    </div>
  );
}
```

### Step 6: Update Database Schema

Add confidence columns to `caseResultsTable`:

```typescript
export const caseResultsTable = pgTable("case_results", {
  // ... existing columns ...
  confidence: text("confidence").notNull().default("NOT_FOUND"),
  confidenceLabel: text("confidence_label"),
  matchScore: text("match_score").default("0"),
  citedBy: jsonb("cited_by"),  // Array of {title, url}
});
```

Run migration:
```sql
ALTER TABLE case_results ADD COLUMN confidence TEXT NOT NULL DEFAULT 'NOT_FOUND';
ALTER TABLE case_results ADD COLUMN confidence_label TEXT;
ALTER TABLE case_results ADD COLUMN match_score TEXT DEFAULT '0';
ALTER TABLE case_results ADD COLUMN cited_by JSONB;
```

---

## PDF Report — Confidence Summary Section

Update `reportGenerator.ts` to group results by confidence tier in the verification report:

```typescript
function generateConfidenceSummary(results: CaseResult[]): string {
  const groups = {
    EXACT_MATCH: results.filter(r => r.confidence === "EXACT_MATCH"),
    PARTIAL_MATCH: results.filter(r => r.confidence === "PARTIAL_MATCH"),
    POTENTIAL_MATCH: results.filter(r => r.confidence === "POTENTIAL_MATCH"),
    CITED_IN_OTHER_CASES: results.filter(r => r.confidence === "CITED_IN_OTHER_CASES"),
    NOT_FOUND: results.filter(r => r.confidence === "NOT_FOUND"),
  };

  let summary = `VERIFICATION SUMMARY\n`;
  summary += `Total citations checked: ${results.length}\n\n`;

  if (groups.EXACT_MATCH.length)
    summary += `VERIFIED (${groups.EXACT_MATCH.length}): Found on SAFLII with high confidence\n`;
  if (groups.PARTIAL_MATCH.length)
    summary += `LIKELY MATCH (${groups.PARTIAL_MATCH.length}): Strong match, verify manually\n`;
  if (groups.POTENTIAL_MATCH.length)
    summary += `POSSIBLE MATCH (${groups.POTENTIAL_MATCH.length}): Some indicators match\n`;
  if (groups.CITED_IN_OTHER_CASES.length)
    summary += `CITED ELSEWHERE (${groups.CITED_IN_OTHER_CASES.length}): Not on SAFLII but referenced in other judgments\n`;
  if (groups.NOT_FOUND.length)
    summary += `NOT FOUND (${groups.NOT_FOUND.length}): Could not verify — potential hallucinations\n`;

  return summary;
}
```

---

## Old Provincial Citations — Special Handling

Pre-1994 provincial division citations (`1944 CPD 100`, `1971 WLD 23`) require special treatment:

1. **These cases predate SAFLII** — they will almost never return EXACT_MATCH
2. **The division codes map to modern successor courts**:

| Old Code | Division | Modern SAFLII Court |
|----------|----------|-------------------|
| CPD | Cape Provincial Division | ZAWCHC |
| TPD | Transvaal Provincial Division | ZAGPPHC |
| WLD | Witwatersrand Local Division | ZAGPJHC |
| NPD | Natal Provincial Division | ZAKZPHC |
| OPD | Orange Free State Provincial Division | ZAFSHC |
| AD | Appellate Division | ZASCA |
| DCLD | Durban and Coast Local Division | ZAKZDHC |
| EDL | Eastern Districts Local Division | ZAECMKHC |

3. **Expected confidence for old citations**:
   - If a modern SAFLII case cites it → `CITED_IN_OTHER_CASES` (valid, just old)
   - If nothing references it → `NOT_FOUND` (but may still be real — just very old)
   - The app should add a note: *"Pre-SAFLII era citation — absence from SAFLII does not indicate hallucination"*

4. **In the Replit app**, old provincial citations already skip Gemini neutral citation lookup (correct). They should now also get a softer NOT_FOUND label when nothing is found:

```typescript
if (isOldProvincialCitation(citation) && confidence === "NOT_FOUND") {
  confidenceLabel = "Not on SAFLII (pre-digital era case — verify via law library)";
}
```

---

## Anti-Hallucination Rules (Unchanged)

These rules from the original app remain critical:

1. **"Verified" (green / EXACT_MATCH) requires a confirmed SAFLII URL** — never from AI alone
2. **Gemini never invents a URL** — it provides a neutral citation string, the URL is built deterministically
3. **Pre-1994 citations skip Gemini** neutral citation lookup (they predate the system)
4. **SAFLII blocks cloud IPs** — all SAFLII links are for the user's browser, not server-side fetches
5. **When in doubt, classify as NOT_FOUND** — a false negative is far less harmful than a false positive

---

## Quick Reference — Mapping Old Statuses to New Confidence

| Old Status | Old Colour | New Confidence | New Colour |
|-----------|-----------|---------------|-----------|
| `verified` | Green | `EXACT_MATCH` | Green |
| `needs_verification` | Amber | `PARTIAL_MATCH` | Amber |
| `not_found` | Red | `NOT_FOUND` | Red |
