# Search Cascade — SAFLII Only

Updated: 16 March 2026

---

## Design Principle

**Only search saflii.org.** No judiciary.org.za, no Google, no other external sites. If a case isn't on SAFLII, it's `NOT_FOUND`.

---

## The Cascade

All changes are in **one file**: `artifacts/api-server/src/lib/safliiSearcher.ts`

### Step 1: Neutral Citation → Direct SAFLII URL

For citations like `[2020] ZACC 10`, build the URL deterministically:

```
https://www.saflii.org/za/cases/ZACC/2020/10.html
```

If the URL returns 200 → **EXACT_MATCH** (green). Done.

### Step 2: Gemini Lookup → Neutral Citation → SAFLII URL

For law report citations (`2020 (6) SA 325 (CC)`), ask Gemini to map it to a neutral citation, then build the SAFLII URL as in Step 1.

If Gemini returns a neutral citation → **PARTIAL_MATCH** (amber). Done.

### Step 3: Not Found

If Steps 1 and 2 both fail → **NOT_FOUND** (red).

---

## Required Code Changes

### Replace `searchCitation` function

```typescript
export async function searchCitation(citation: Citation): Promise<SearchResult> {
  const trail: string[] = [];

  // Step 1: SAFLII direct URL (neutral citations only)
  const step1 = step1NeutralCitation(citation, trail);
  if (step1) return step1;

  // Step 2: Gemini maps reporter citation → neutral citation → SAFLII URL
  try {
    const step2 = await step2GeminiLookup(citation, trail);
    if (step2) return step2;
  } catch (err) {
    trail.push(`AI lookup: Exception — ${err instanceof Error ? err.message : String(err)}`);
  }

  // Step 3: Not found on SAFLII
  trail.push("SAFLII: No matching case found");
  return {
    status: "not_found",
    matchReason: "Not found on SAFLII. This citation may be hallucinated.",
    searchTrail: trail,
    confidence: "NOT_FOUND",
    confidenceLabel: CONFIDENCE_LABELS.NOT_FOUND,
    matchScore: 0,
  };
}
```

### Remove

- `step3Judiciary` function and all judiciary site constants
- `step4Google` / `step4GoogleVerification` function
- `geminiCaseExistenceCheck` function (was only used by Step 4)
- `googleSearchUrl` from `SearchResult` interface

---

## Summary

| Step | What it does | Confidence if found | Stop? |
|------|-------------|-------------------|-------|
| 1 | Build SAFLII URL from neutral citation | **EXACT_MATCH** (green) | Yes |
| 2 | Ask Gemini for neutral citation → build SAFLII URL | **PARTIAL_MATCH** (amber) | Yes |
| 3 | Neither worked | **NOT_FOUND** (red) | Yes |
