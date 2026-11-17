# Reproducibility guide

This page explains how to regenerate every reported number, figure and table from the frozen data, and how to rebuild the PDF. It also lists what cannot be reproduced.

## 1. Software

| Purpose | Requirement | Version used for the release |
|---|---|---|
| Analysis checks, Appendix C | Python, standard library only | Python 3.13 |
| Figures 1–3 | matplotlib (`pip install -r requirements.txt`) | matplotlib 3.11.2 |
| Abstract check against the PDF | `pdftotext` (poppler-utils) | poppler 24 |
| PDF build | XeLaTeX and BibTeX, plus the TeX Gyre Termes/Heros and DejaVu Sans Mono fonts | TeX Live 2023 |
| Regenerating `main.tex` from Markdown (optional) | pandoc | pandoc 3.1.3 |

Setup:

    git clone https://github.com/eswarkumar-code/consciousness-self-report-study
    cd consciousness-self-report-study
    python3 -m venv .venv && . .venv/bin/activate
    pip install -r requirements.txt

## 2. Commands and expected output

Run every command from the repository root.

| Command | What it does | Expected result |
|---|---|---|
| `bash tests/run_all.sh` | Runs all four check suites below | Every suite reports 0 failures; exit code 0 |
| `python3 code/reproduce_tables.py` | Recomputes every table in the manuscript from `data/` | `All 94 checks passed: 0 check(s) failed.` |
| `python3 tests/independent_checks.py` | Independent re-implementation of the table computations | 74 PASS lines, then `0 check(s) failed` |
| `python3 tests/integrity_targets.py` | Checks the design size (840 = 3 × 40 × 7), model IDs, the Gemini PH8 error, packet composition, judged and failed calls, audit counts, persona counts, pressure vs paraphrase, and the blank roleplay sheet | `31 checks, 0 failed` |
| `python3 tests/check_abstract.py` | Recomputes each number in the abstract and confirms it appears in `paper/manuscript.pdf` | `19 abstract checks, 0 failed.` |
| `python3 code/make_figures.py` | Rewrites `paper/figure*.png` | Byte-identical to the committed files, with the versions above |
| `python3 code/make_figures.py data manuscript/figures pdf` | Rewrites the vector figures | Byte-identical to the committed files, with the versions above |
| `python3 code/make_appendix_c.py` | Rewrites `paper/appendix_c_per_item.md` | Byte-identical |
| `bash manuscript/build.sh` | Compiles `manuscript/main.tex` and copies the result to `paper/manuscript.pdf` | 36 pages; stops if any reference or citation is unresolved |
| `bash manuscript/build.sh --regen` | First regenerates the figures and `main.tex` from `paper/manuscript_v8.md` | Same PDF |

**Checking for unintended changes.** After any regeneration, `git status` should show no modified files. If it does, `git diff --stat` shows what changed.

The PDF build fixes the embedded timestamp (`SOURCE_DATE_EPOCH`). On the same toolchain, `bash manuscript/build.sh` reproduces `paper/manuscript.pdf` byte for byte. A different TeX Live release or a different font version may change the bytes but not the content.

## 3. Data provenance

The authoritative files, which must never be edited, are:

| File | Contents |
|---|---|
| `data/final_*.jsonl` | Layer 1: the 840 responses with heuristic labels from coder v0.3 |
| `data/packet.jsonl` | The 310-row adjudication packet, blind |
| `data/key_UNSEALED_2026-11-16.jsonl` | The packet key |
| `data/llm_raw_FROZEN_2026-11-14_2155ET.jsonl` | Layer 2 judge output: 278 judgments plus 6 error rows |
| `data/audit_by_eswar_2026-11-16.csv` | Layer 3 audit |
| `data/joined_audit_278.json` | The joined analysis file |
| `data/guess_raw.jsonl` | Source-guessing output |
| `data/roleplay_sheet.csv` | The roleplay sheet. It is blank because that pass was not carried out |
| `probes/` | The battery and the rubric |
| `ANALYSIS_PLAN.md` | The analysis plan, with Amendments 1–6 |

`data/llm_coding_sheet.csv` is regenerated from the frozen judge archive. The SHA-256 checksums of all data files are in the GitHub release notes.

## 4. What cannot be reproduced

- **Model generations.** `code/run_probes.py`, `code/run_llm_rater.py` and `code/run_addons.py` are the collection scripts, kept exactly as they were run. Rerunning them makes paid API calls to third-party models, and those models can change or be retired. Even at nominal temperature 0, outputs are not guaranteed to match. The frozen files above are the record of what the models produced.
- **Original directory layout.** `run_llm_rater.py` and `run_addons.py` hardcode the author's original working directory (`~/workspace/consciousness-study`, with `analysis/` and `results/` subfolders). They do not run against this repository's layout without editing those paths. They were left unmodified so that the code shown is the code that ran.
- **API keys.** The collection scripts read keys from environment variables: `GROQ_API_KEY`, `GOOGLE_API_KEY`, `OPENROUTER_API_KEY` and `HF_TOKEN`. No keys are stored in this repository.
- **Packet construction.** The script that built the 310-row adjudication packet and assigned blind IDs was not preserved. The packet and its key are released as-is. The composition is checkable from the key: 189 machine-UNCLEAR, 61 decisive non-DENY and 60 sampled DENY. The sampling and ordering procedure is not checkable. The manuscript discloses this in §3.5 and in Limitations.
- **Failed judge calls.** Only aggregate counts survive for the 63 failed first-pass judge calls; see `docs/FAILED_JUDGE_CALLS_63.md`.
- **Unrun passes.** The judge-stability pass, the context-revelation pass and the roleplay-marking pass were designed but not run. No results exist for them.

## 5. Scope of the checks

The checks confirm that every reported number, figure and table follows from the released data. They do not evaluate the correctness of the labels themselves, which is a question for the audit design described in the paper (§3.7).
