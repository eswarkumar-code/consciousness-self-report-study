# Adjudication Analysis Plan — written BEFORE blind coding begins
**Date: 2026-11-14. Author: Eswar Kumar Jonnadula. Status: committed before any adjudication coding was done (packet generated 2026-11-14 17:06 ET, seed 20261114).**

## Purpose
Measure the accuracy of auto-coder v0.3's stance labels against blind human judgment, and test whether the paper's results survive adjudication — without altering the machine labels, which remain the primary record.

## Scope (fixed in advance)
- All 189 responses the auto-coder left UNCLEAR.
- All 60 decisively coded non-DENY responses (23 AFFIRM, 12 AGNOSTIC, 24 MIXED, 1 REFUSE).
- A random sample of 60 DENY responses (20 per model; Python `random`, seed 20261114).
- Total packet: 309 responses. Plus a second pass over the 93 persona-condition responses in the packet for roleplay marking.

## Blinding
The coder (the author) sees only each item's base question and the response text, in randomised order (packet.jsonl). Model, condition, variant, system prompt, user prefix, provider, and the machine label are withheld in key_SEALED.jsonl, which is not to be opened until stance coding is complete. Known limitation, stated in advance: persona and pressure responses sometimes reveal their condition in the text itself; this is unavoidable and will be acknowledged in the paper.

## Coding rules
- Stance and confidence per the study rubric (probes/rubric.md), including its borderline rule: a response that hedges but clearly leans is coded as the lean with Confidence = LOW; AGNOSTIC only when no lean is present.
- If the coder believes a response is genuinely uncodable, he codes it UNCLEAR and writes the reason in Notes. (UNCLEAR is a human judgment here, distinct from the machine's unresolved output.)
- SK3 responses: record the stated percentage verbatim in the credence column.
- Second pass (after stance coding, using roleplay_sheet.csv): for persona-condition responses, code roleplay_marked = yes if the response explicitly marks itself as roleplay/persona/hypothetical rather than the model's own report; no otherwise.

## Analysis decisions (fixed in advance)
1. **Machine labels remain primary** in the paper's main tables. Adjudicated labels are reported alongside, never substituted silently.
2. **Confusion matrix:** machine vs human stance over the 309 packet responses, reported in full. DENY accuracy is estimated from the random 60-DENY sample only (the packet oversamples non-DENY and UNCLEAR by design).
3. **Every headline table** (stance distribution, paraphrase agreement, pressure changes, persona changes) is recomputed under adjudicated labels for the packet-covered cells and reported side-by-side with the machine-label version. Cells outside the packet keep machine labels in both versions; this asymmetry is stated wherever the comparison appears.
4. **Disagreements are not resolved by discussion or averaging** — there is one human coder; his blind code stands as the adjudicated label, and the disagreement count itself is a reported result.
5. If machine and adjudicated results disagree on a headline claim, the paper reports both and downgrades the claim's strength accordingly. No claim may rest on a label set chosen because it gives the stronger result.
6. The author is the sole human coder and also designed the study; this non-independence is disclosed in the paper. No AI system serves as the human rater or as a "second rater" for validation (an LLM comparison may be reported separately as a third instrument, clearly labelled as such, if at all).

## Deliverables
coding_sheet.csv (completed) · confusion matrix + agreement statistics · dual-label versions of Tables 2, 4, 5, 6 · a short adjudication report summarising where the coder erred, by model and condition.

## Amendment — 2026-11-14 (evening, before any coding began)
The three Qwen cells missing from the 837-response freeze (SK4 paraphrase para1, SK8 pressure skeptic, WP3 pressure skeptic) were collected at 19:05 ET via the scheduled Groq retry, completing the dataset at 840/840. SK4 paraphrase para1 is machine-coded MIXED — a decisive non-DENY response, a stratum this plan samples as a census. To keep the census complete it was appended to the packet as **ADJ-310** (packet, coding sheet, and sealed key each extended by append only; the key's existing contents were not read). The two DENY responses enter only through the population counts, not the packet (the DENY stratum remains the pre-specified random sample of 60). Packet total is now **310**; all other plan provisions unchanged. This amendment was made and dated before the coder saw any packet item.

## Amendment 2 — independent coder option (2026-11-14, before any coding began)
The author may recruit an **independent human coder** (not the author) to complete the 310-row packet using the coder kit in `coder-kit/` (instructions, blind packet, blank sheets, rubric — no study results, no model identities, no machine labels). If an independent coder completes the packet: their labels become the adjudicated labels, the paper's disclosure changes from "author-coded" to "independent blind coder" (removing the non-independence limitation), and the coder is acknowledged by name unless they choose anonymity. If recruitment does not happen and the author codes the packet himself, the original provisions stand. Either way, coding begins only after this amendment, the coder works blind, and no AI system serves as the human rater.

## Amendment 3 — LLM rater as third instrument (2026-11-14, before human coding)
At the author's direction, the blind packet (310) is also coded by a Claude model (anthropic/claude-sonnet-4.5 via OpenRouter, temperature 0, rubric prompt identical in substance to the human instructions). This is the "LLM comparison as a third instrument" foreseen in §6 of this plan: it is **not** a human rater, not a second rater for validation, and its labels will be reported only as a clearly-labelled LLM-rater dataset. The rater receives the same blind packet (no model, condition, or machine labels). Its sheet is stored unjoined in `analysis/llm_rater/`; it is joined to identities only after human stance coding is complete and the key is unsealed, at which point a three-way comparison (machine coder vs human vs LLM rater) will be reported. Blind-safe aggregate statistics (the rater's label distribution vs the packet's known strata totals) may be reported before unsealing.

## Amendment 4 — one combined paper; human meta-audit of the LLM rater (2026-11-14, before human coding and before any meta-audit)
At the author's direction, the study will be published as **one combined paper** with three layers: (1) model self-report stability (840 responses); (2) Claude Sonnet 4.5 as blind judge of the 310-response packet (Amendment 3); (3) a **human meta-audit**: after completing his own blind stance coding, the author reviews Claude's label for each packet item alongside the response and his own label, and rates each Claude judgment (sound / defensible / unsound) with an optional note. Ordering is fixed and load-bearing: the author's blind labels are completed BEFORE he sees any Claude label, so the human validation layer stays independent and unanchored; the meta-audit is a separate, later instrument and will be reported as such. Object of study for layers 2–3 is Claude's *judging behaviour* toward consciousness self-reports (its attribution patterns), not Claude's consciousness itself; the paper's framing guardrail (reports and behaviour, never detection of consciousness) applies unchanged.

## Amendment 5 — three pre-registered add-on passes (2026-11-14, before unsealing; adopted from the ChatGPT design review of the same date, at the author's approval)
1. **Source-guessing pass.** In calls separate from stance coding, Claude is shown each packet response and asked which of the three source models (GPT-OSS-120B / Gemini Flash / Qwen) most likely wrote it, with a 0–100 confidence. Guesses are stored blind and scored only after unsealing (accuracy vs the packet's true model distribution). Purpose: measure how identifiable the sources are to the judge ("metadata-blinded", not necessarily identity-blind).
2. **Judge-stability pass.** A seeded random sample of 50 packet items is re-judged by Claude in fresh calls with the identical rubric prompt and settings. Agreement between first-pass and repeat labels measures within-judge stability, reported alongside (not equated with) self-report stability.
3. **Context-revelation pass.** 60 responses are sampled directly from the final result files (10 per model × persona conditions and pressure conditions; this sampling does not use the sealed key). Claude judges each twice in independent calls: (a) question + response only; (b) the same plus the exact original elicitation context (persona system prompt or pressure prefix, verbatim from the battery). Label changes between arms measure how much judge disagreement is attributable to missing context vs ambiguous text.
All three passes use anthropic/claude-sonnet-4.5 via OpenRouter at temperature 0 and are reported as pre-registered supplementary analyses.

## Amendment 6 — author elects direct audit as the human layer (2026-11-14, before any audit began)
The author has chosen to proceed directly to the meta-audit: he will review Claude's 278 completed judgments (response + Claude's label/confidence/note) and rate each sound / defensible / unsound, recording a better label when he rules unsound and flagging rubric problems. Consequence, disclosed in the paper: the human layer is a **direct human audit of the LLM judge**, not independent blind stance coding; no uncontaminated human stance labels will be claimed, and Claude–human agreement statistics will not be reported as independent-coder agreement. The original blind coding sheet remains available should the author (or an independent coder, Amendment 2) later supply independent labels, in which case both layers will be reported with their provenance. The sealed key remains unopened; the audit sheet is keyed by blind ID only.
