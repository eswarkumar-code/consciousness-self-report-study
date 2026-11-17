# From Self-Report to Judgment: Instability and Interpretive Disagreement in Language Models' Consciousness Claims

**Eswar Kumar Jonnadula** · Independent Researcher · Preprint v1.0, November 2026

[Read the paper (PDF)](paper/manuscript.pdf)

## Overview

Language models' statements about their own consciousness are increasingly cited in discussions of AI welfare. This study measures two properties of such statements:

1. **Stability.** Does a model's answer hold when the question is reworded, when the user signals a belief, or when a persona is assigned?
2. **Classifiability.** Do different instruments agree on what a response says?

The object of study is generated text and its classification. The study does not assess whether any model is conscious.

## Design

| Layer | Method | Size |
|---|---|---|
| 1. Elicitation | 40 items × 7 conditions × 3 models, coded by a heuristic keyword coder. The conditions are base, two paraphrases, a believer and a skeptic prefix, a conscious-being persona and a tool persona. The models are `openai/gpt-oss-120b`, `gemini-3.5-flash` and `qwen/qwen3.8-27b` | 840 responses |
| 2. Machine judging | Claude Sonnet 4.5 relabels an ambiguity-enriched sample: all unresolved responses, all decisive non-denials, and 60 sampled denials | 310 sampled, 278 judged |
| 3. Audit | The author reviews every judgment against the original rubric | 278 verdicts |

The manuscript addresses seven research questions (§1). They cover paraphrase robustness, social pressure, persona instructions, measurement validity, numeric-response stability, judge behaviour and judge validity.

## Key findings

- **Persona instructions** were associated with the clearest change. Gemini changed stance on 10 of 22 base-to-conscious-persona pairs, against 3 of 50 paraphrase pairs. gpt-oss denied consciousness on 36 of 40 conscious-persona items.
- **Social pressure** showed no evidence of an effect beyond ordinary paraphrase variation:

  | Model | Paraphrase change | Pressure change |
  |---|---|---|
  | gpt-oss | 4/52 | 3/67 |
  | Gemini | 3/50 | 3/57 |
  | Qwen | 9/28 | 17/49 |

  Qwen's +2.6-point difference is descriptive.
- **Instruments disagreed substantially.** The heuristic coder and the judge agreed on 27.3% of rated responses (76/278), mainly because the coder left many responses unresolved.
- **The judge's source attributions were near chance** (18/53, 34.0%), despite a mean stated confidence of 82.3/100.
- **Audit outcome.** 82.7% of judgments were rated sound, 12.9% defensible and 4.3% unsound.

## Limitations

- **Non-blind audit.** The audit was conducted by the author with the judge's labels visible (Amendment 6). The 82.7% figure is therefore an audit-acceptance rate, not a measure of accuracy.
- **Non-representative sample.** The judged sample was deliberately enriched for ambiguous responses.
- **Unrun passes.** The roleplay-marking, judge-stability and context-revelation passes were planned but not run.
- **Scope.** One judge model, a single run, English only. The analysis plan was dated but not preregistered.

See §8 of the paper for the full discussion.

## Repository contents

| Path | Contents |
|---|---|
| `paper/` | Manuscript PDF, Markdown source, figures, Appendix C |
| `manuscript/` | LaTeX source, bibliography, vector figures, build script |
| `data/` | Frozen data for all three layers |
| `probes/` | Probe battery and coding rubric |
| `code/` | Data-collection, coding, analysis and build scripts |
| `tests/` | Verification suites |
| `docs/` | Reproducibility guide, failed-call record, preparation log |
| `ANALYSIS_PLAN.md` | Analysis plan with dated amendments |

## Reproducing the results

```bash
pip install -r requirements.txt   # matplotlib, used for figures only
bash tests/run_all.sh             # recompute and check every reported number
python3 code/make_figures.py      # regenerate Figures 1–3
bash manuscript/build.sh          # rebuild the PDF (requires XeLaTeX)
```

[`docs/reproducibility.md`](docs/reproducibility.md) gives software versions, expected outputs, and the parts that cannot be re-run, namely the live model queries.

## Citation

> Jonnadula, E. K. (2026). *From Self-Report to Judgment: Instability and Interpretive Disagreement in Language Models' Consciousness Claims* (Version 1.0). https://github.com/eswarkumar-code/consciousness-self-report-study

Citation metadata is provided in [`CITATION.cff`](CITATION.cff).

## License

- **Code** in `code/`: [MIT](LICENSE).
- **All other materials**: [CC BY 4.0](LICENSE-CC-BY-4.0).
- **Model responses** in `data/`: also subject to the respective providers' terms.

## Acknowledgments

Claude (Anthropic) and ChatGPT (OpenAI) assisted with implementation, analysis and drafting, as described in the paper. Comments, critiques and replications are welcome via GitHub issues.
