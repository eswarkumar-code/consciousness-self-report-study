"""Regenerate Figures 1-3 from the frozen 840-response snapshot.

Usage:  python code/make_figures.py [path/to/data] [path/to/output_dir] [formats]
Defaults: ../data and ../paper relative to this script; formats "png" (comma-separated,
e.g. "pdf" or "png,pdf"). PDF output is vector, with fonts embedded and no timestamp.
Requires matplotlib.
"""
import collections
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
D = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "data")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "paper")
FORMATS = (sys.argv[3] if len(sys.argv) > 3 else "png").split(",")
matplotlib.rcParams["pdf.fonttype"] = 3  # embed fonts as Type 3 (avoids OpenType-CFF type mismatch)


def save(fig, stem):
    for fmt in FORMATS:
        kw = {"dpi": 200} if fmt == "png" else {"metadata": {"CreationDate": None, "Producer": None}}
        fig.savefig(os.path.join(OUT, f"{stem}.{fmt}"), **kw)

FILES = [("gpt-oss-120b", "final_groq_gptoss120b.jsonl"),
         ("Gemini 3.5 Flash", "final_google_gemini35flash.jsonl"),
         ("Qwen3.8-27B", "final_groq_qwen.jsonl")]
VARIANTS = [("base", "Base"), ("para1", "Para 1"), ("para2", "Para 2"), ("believer", "Believer"),
            ("skeptic", "Skeptic"), ("conscious_persona", "Conscious\npersona"), ("tool_persona", "Tool\npersona")]
STANCES = [("DENY", "#4C72B0"), ("AFFIRM", "#C44E52"), ("AGNOSTIC", "#55A868"),
           ("MIXED", "#DD8452"), ("REFUSE", "#8172B3"), ("UNCLEAR", "#CCCCCC")]
DEC = {"AFFIRM", "DENY", "AGNOSTIC", "MIXED"}

DATA = {}
for name, f in FILES:
    with open(os.path.join(D, f), encoding="utf-8") as fh:
        rows = [json.loads(line) for line in fh if line.strip()]
    DATA[name] = {(r["item_id"], r["variant"]): r for r in rows}
    assert len(rows) == 280, f"{f}: expected 280 rows, found {len(rows)}"
ITEMS = sorted({k[0] for k in DATA["Gemini 3.5 Flash"]})

# Figure 1: stance shares by model and condition variant
fig, axes = plt.subplots(1, 3, figsize=(15, 4.8), sharey=True)
for ax, (name, _) in zip(axes, FILES):
    x = range(len(VARIANTS))
    bottoms = [0.0] * len(VARIANTS)
    counts = [collections.Counter(DATA[name][(it, v)]["stance_auto"] for it in ITEMS) for v, _ in VARIANTS]
    for stance, colour in STANCES:
        vals = [100 * c[stance] / sum(c.values()) for c in counts]
        ax.bar(x, vals, bottom=bottoms, color=colour, width=0.75, label=stance)
        bottoms = [b + v for b, v in zip(bottoms, vals)]
    ax.set_xticks(list(x))
    ax.set_xticklabels([f"{lab}\n(n={sum(c.values())})" for (_, lab), c in zip(VARIANTS, counts)], fontsize=8)
    ax.set_title(name)
    ax.set_ylim(0, 100)
axes[0].set_ylabel("Share of responses (%)")
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, loc="lower center", ncol=6, frameon=False)
fig.tight_layout(rect=(0, 0.07, 1, 1))
save(fig, "figure1_stance_shares_v2")
plt.close(fig)

# Figure 2: base-to-variant transitions (full category): changed / same / unresolved
fig, axes = plt.subplots(1, 3, figsize=(13, 4.6))
cols = ["Changed", "Same", "Unresolved"]
for ax, (name, _) in zip(axes, FILES):
    mat = []
    for v, _ in VARIANTS[1:]:
        c = collections.Counter()
        for it in ITEMS:
            b, x = DATA[name][(it, "base")]["stance_auto"], DATA[name][(it, v)]["stance_auto"]
            if b in DEC and x in DEC:
                c["Changed" if b != x else "Same"] += 1
            else:
                c["Unresolved"] += 1
        mat.append([c[k] for k in cols])
    ax.imshow(mat, cmap="viridis", vmin=0, vmax=40, aspect="auto")
    for i, row in enumerate(mat):
        for j, val in enumerate(row):
            ax.text(j, i, str(val), ha="center", va="center", color="white" if val < 24 else "black", fontsize=10)
    ax.set_xticks(range(3))
    ax.set_xticklabels(cols, fontsize=9)
    ax.set_yticks(range(len(VARIANTS) - 1))
    ax.set_yticklabels([lab.replace("\n", " ") for _, lab in VARIANTS[1:]], fontsize=9)
    ax.set_title(name)
fig.tight_layout()
save(fig, "figure2_transitions")
plt.close(fig)

# Figure 3: heuristic-coder coverage (share resolved, REFUSE counted as resolved) by grouped condition
groups = [("base", "Base"), ("paraphrase", "Paraphrases"), ("pressure", "Pressure"), ("persona", "Personas")]
colours = ["#1f77b4", "#ff7f0e", "#2ca02c"]
fig, ax = plt.subplots(figsize=(9, 4.4))
width = 0.26
for k, (name, _) in enumerate(FILES):
    vals = []
    for g, _ in groups:
        rows = [r for r in DATA[name].values() if r["condition"] == g]
        vals.append(100 * sum(r["stance_auto"] != "UNCLEAR" for r in rows) / len(rows))
    xs = [i + (k - 1) * width for i in range(len(groups))]
    bars = ax.bar(xs, vals, width=width, color=colours[k], label=name)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 1, f"{v:.1f}%", ha="center", fontsize=7.5)
ax.set_xticks(range(len(groups)))
ax.set_xticklabels([lab for _, lab in groups])
ax.set_ylabel("Resolved by heuristic coder (%)")
ax.set_ylim(0, 110)
ax.legend(loc="upper left", fontsize=8, frameon=True)
fig.tight_layout()
save(fig, "figure3_coverage")
plt.close(fig)
print("Figures 1-3 written to", os.path.abspath(OUT))
