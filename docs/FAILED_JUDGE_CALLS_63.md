# The 63 failed judge calls (Layer 2, first pass, 2026-11-14) — what survives

**No per-item log of the 63 failed calls exists.** The error rows were stripped
from `llm_raw.jsonl` on 2026-11-14 so the resumable rater script would
re-attempt those packet IDs; the per-item error list was not preserved.
What survives is the exact aggregate record made that night, plus the rerun
logs (`rerun.log`, `rerun2.log`, `rerun3.log`, counts only).

## Aggregate record (exact)

First pass: 247 of 310 judgments succeeded; 63 calls failed:

- 53 × HTTP 404 "Not Found"
- 8 × remote end closed connection without response
- 2 × IncompleteRead

Verified root cause: the rater script set no `max_tokens`, so OpenRouter
reserved the model's full 64,000-token maximum per request and its
affordability check rejected calls (a direct test returned HTTP 402:
"You requested up to 64000 tokens, but can only afford 60879").
Fix applied: `max_tokens` capped at 400 and provider order pinned
(Anthropic, then Claude Platform on AWS, Amazon Bedrock, Google, Azure).

## What happened next

Reruns under the identical prompt recovered 31 of the 63, reaching 278
judgments. The runs were then frozen at the author's instruction on
2026-11-14 at 21:55 ET. No completed judgment was ever re-asked.

Serving routes differed between the passes, as recorded in the frozen raw
file's `provider` field: the 247 first-pass judgments were served through
OpenRouter's Claude Platform on AWS endpoint (no max_tokens setting); the
31 rerun judgments were served through Anthropic's own endpoint
(max_tokens = 400, provider order pinned). Model, prompt and temperature
were identical.

The 32 unjudged responses are failed calls that were not retried before
the freeze: 26 of them (ADJ-285 to ADJ-310) failed in the first pass and
have no row in the frozen raw, because their error rows were among those
stripped; 6 (ADJ-062, ADJ-248, ADJ-260, ADJ-268, ADJ-270, ADJ-276) failed
again on rerun, and their final error rows are retained in the frozen raw
(ADJ-268: remote end closed connection; the other five: HTTP Error 404).
Their absence reflects provider errors, not response content.

## Correction owed to the manuscript

Section 3.6 of the v7 manuscript states that "the 63 failed calls are
preserved with their errors in the rater archive." That is not accurate:
only the aggregate counts and causes above were preserved. The sentence
should be corrected before posting.
