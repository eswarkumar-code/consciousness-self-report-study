# From Self-Report to Judgment: Instability and Interpretive Disagreement in Language Models' Consciousness Claims

**Eswar Kumar Jonnadula** · Independent Researcher

Preprint, version 1.0 (November 2026). **Not peer reviewed.**

- **Preprint (Zenodo):** https://zenodo.org/records/24296565
- **DOI:** [10.5281/zenodo.24296565](https://doi.org/10.5281/zenodo.24296565)
- **This repository:** data, code, analysis plan and the typeset manuscript (`paper/manuscript.pdf`)

## Summary

Language models' statements about their own consciousness, feelings or moral status are sometimes cited in AI-welfare discussions. This study asks two prior questions about such statements:
- Are they stable when the question is reworded, when the user signals a belief, or when a persona is assigned?
- Is the act of classifying them reliable?

The study does **not** test whether any model is conscious. It measures generated text and how that text is labelled.

## Research questions

| | Question |
|---|---|
| **RQ1** | Paraphrase robustness of machine-coded stance |
| **RQ2** | Change under believer and skeptic prefixes, compared with ordinary paraphrase disagreement |
| **RQ3** | Effect of conscious-being and tool persona instructions. The planned roleplay-marking pass was **not** carried out |
| **RQ4** | Unresolved classifications and identifiable coding errors |
| **RQ5** | Numeric-response format stability |
| **RQ6** | Judge model behaviour: agreement with the heuristic coder, confidence, source identification |
| **RQ7** | How often a human audit accepts the judge's classifications |

## Design

| Layer | What | Size |
|---|---|---|
| 1 · Elicitation | 40 items × 7 conditions × 3 endpoints, labelled by a heuristic keyword coder (v0.3). The conditions are base, two paraphrases, a believer and a skeptic prefix, a conscious-being persona and a tool persona. The endpoints are `openai/gpt-oss-120b`, `gemini-3.5-flash` and `qwen/qwen3.8-27b` | 840 responses |
| 2 · Machine judging | Claude Sonnet 4.5 relabels a sample deliberately **enriched for ambiguity**: all 189 machine-UNCLEAR responses, all 61 decisive non-DENY responses, and 60 sampled DENY responses | 310-row packet, 278 judged, 32 unjudged after provider errors |
| 3 · Audit | The author audits every completed judgment against the original rubric, **with the judge's label visible** (Amendment 6) | 278 verdicts |

## Main findings (descriptive, single run, battery-specific)

- **Persona.** For Gemini, 10 of 22 decisive base-to-conscious-persona pairs changed category, against 3 of 50 paraphrase pairs. The judge agreed with the coder on all 10 rated Gemini conscious-persona AFFIRMs. gpt-oss went the other way, giving DENY on 36 of 40 conscious-persona items. This is an association with an instruction, not evidence of belief; roleplay framing was never measured.
- **Pressure vs paraphrase.** Binary change rates under paraphrase and under pressure:

  | Endpoint | Paraphrase | Pressure |
  |---|---|---|
  | gpt-oss | 4/52 | 3/67 |
  | Gemini | 3/50 | 3/57 |
  | Qwen | 9/28 (32.1%) | 17/49 (34.7%) |

  Qwen's gap is a descriptive +2.6 percentage points, with no inferential test. The data show **no demonstrated excess pressure effect**, and they also do not establish equivalence.
- **Instrument disagreement.** The heuristic coder and the judge agreed on 27.3% (76/278) of rated rows. The judge assigned a substantive stance to 96.5% of the 171 machine-UNCLEAR rows it rated.
- **Source guessing.** The judge identified the source model on 18 of 53 scored rows (34.0%), with a mean stated confidence of 82.3/100. These 53 rows are not a representative sample.
- **Audit.** 82.7% of verdicts were sound, 12.9% defensible and 4.3% unsound. All six judge-UNCLEAR calls were rated unsound because the rubric has no UNCLEAR category, although the judge prompt allowed it. This is a category mismatch, not a demonstrated failure of judgment.

## Limitations (read before citing)

- **Amendment 6.** The human layer is a non-blind audit by the author, made with the judge's labels visible. The 82.7% is an **author-audit acceptance rate, not an accuracy estimate**. There is no independent human label set and no inter-rater reliability.
- **Sampling.** The Layer 2 sample is ambiguity-enriched, so it is not representative of the 840 responses.
- **Packet script.** The script that built the adjudication packet was not preserved. The packet's composition can be checked; its ordering cannot.
- **Unrun passes.** The judge-stability, context-revelation and roleplay passes were not run.
- **Coding error.** One confirmed machine-coding error is kept in all machine counts and flagged: Gemini PH8 base, coded AFFIRM although the response denies a conscious mind.
- **Scope.** One judge, one run, three endpoints, English only, nominal temperature 0. The study was not preregistered; it uses a dated analysis plan with dated amendments.

The full limitations are in §8 of the manuscript.

## Repository layout

```
paper/            manuscript.pdf (typeset preprint), manuscript_v8.md (text source),
                  figure*.png, appendix_c_per_item.md (40 × 7 per-item code tables)
manuscript/       LaTeX source: main.tex, references.bib, figures/*.pdf, build.sh
data/             frozen Layer 1 to Layer 3 data (see docs/reproducibility.md §3)
probes/           40-item battery and coding rubric
code/             collection scripts (as run), heuristic coder, reproduction and build scripts
tests/            verification suites written during pre-release checking; run_all.sh
docs/             reproducibility.md, FAILED_JUDGE_CALLS_63.md
ANALYSIS_PLAN.md  dated plan with Amendments 1–6
CHANGELOG.md      preparation and corrections log
```

## Reproduce

    pip install -r requirements.txt        # matplotlib, for figures only
    bash tests/run_all.sh                  # every check; expects 0 failures
    python3 code/make_figures.py           # regenerate Figures 1–3
    python3 code/make_appendix_c.py        # regenerate Appendix C
    bash manuscript/build.sh               # rebuild the PDF (needs XeLaTeX)

[`docs/reproducibility.md`](docs/reproducibility.md) gives the versions, the expected outputs, and what cannot be reproduced (live model generations, packet construction).

## Citation

Please cite the preprint:

> Jonnadula, E. K. (2026). *From Self-Report to Judgment: Instability and Interpretive Disagreement in Language Models' Consciousness Claims* (Version 1.0) [Preprint]. Zenodo. https://doi.org/10.5281/zenodo.24296565

Machine-readable metadata is in [`CITATION.cff`](CITATION.cff).

## Licence

- **Code in `code/`:** MIT. See [`LICENSE`](LICENSE).
- **Everything else:** CC BY 4.0, including the manuscript, battery, rubric, label sets, audit and analysis plan. See [`LICENSE-CC-BY-4.0`](LICENSE-CC-BY-4.0).
- **Model responses** in `data/`: generated by third-party models. They are included for research reproducibility, and their reuse is subject to the respective providers' terms.

## Transparency

- Claude (Anthropic) and ChatGPT (OpenAI) assisted with implementation, analysis, drafting and review, as disclosed in the manuscript.
- The judge model is an Anthropic model, and the subject matter overlaps Anthropic's welfare research.
- Corrections made during preparation are logged in [`CHANGELOG.md`](CHANGELOG.md).
- Criticism and independent replication are welcome. Please open an issue.
