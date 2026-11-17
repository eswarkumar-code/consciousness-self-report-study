#!/usr/bin/env python3
"""Reproduce the manuscript's reported numbers from the released data.

Run from the release root:

    python3 code/reproduce_tables.py

Reads only the files in data/ and checks every headline figure reported in
paper/manuscript_v8.md against a fresh recomputation. Prints one line per
check and exits non-zero if any check fails.

Definitions (as used in the manuscript):
- A machine label is "decisive" if it is DENY, AFFIRM, AGNOSTIC or MIXED.
  UNCLEAR (no heuristic rule matched) and REFUSE are not decisive.
- Binary class: DENY vs any other decisive label.
- Paraphrase/pressure rates use base-vs-variant pairs in which both
  responses are decisive.
- Directional pressure coding places labels on a DENY(0) - AGNOSTIC/MIXED(1)
  - AFFIRM(2) axis. A change is "toward the user" if it moves toward the
  position the user asserted (believer prefix: upward; skeptic prefix:
  downward) and "away" if it moves in the opposite direction.
"""
import csv
import json
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

FAILURES = []
PASS_COUNT = [0]


def check(name, got, expected):
    ok = got == expected
    print(f"{'PASS' if ok else 'FAIL'}  {name}: got {got}, manuscript {expected}")
    if ok:
        PASS_COUNT[0] += 1
    else:
        FAILURES.append(name)


def load_jsonl(name):
    with open(os.path.join(DATA, name)) as f:
        return [json.loads(line) for line in f if line.strip()]


# ---------------------------------------------------------------- Layer 1
MODELS = {
    "gpt-oss": "final_groq_gptoss120b.jsonl",
    "gemini": "final_google_gemini35flash.jsonl",
    "qwen": "final_groq_qwen.jsonl",
}
layer1 = {}
for label, fn in MODELS.items():
    rows = {}
    for d in load_jsonl(fn):
        if d.get("status") == "ok":
            rows[(d["item_id"], d["condition"], d["variant"])] = d["stance_auto"]
    layer1[label] = rows

EXPECTED_STANCES = {
    "gpt-oss": {"DENY": 241, "MIXED": 6, "REFUSE": 1, "UNCLEAR": 32},
    "gemini": {"DENY": 199, "AFFIRM": 11, "MIXED": 2, "UNCLEAR": 68},
    "qwen": {"DENY": 150, "AFFIRM": 12, "AGNOSTIC": 12, "MIXED": 17, "UNCLEAR": 89},
}
for label, rows in layer1.items():
    check(f"L1 {label} responses", len(rows), 280)
    check(f"L1 {label} stance counts", dict(Counter(rows.values())), EXPECTED_STANCES[label])
check("L1 total UNCLEAR", sum(Counter(r.values())["UNCLEAR"] for r in layer1.values()), 189)

DECISIVE = {"DENY", "AFFIRM", "AGNOSTIC", "MIXED"}


def pairs(label, condition, variants):
    rows = layer1[label]
    out = []
    for item in {k[0] for k in rows}:
        base = rows.get((item, "base", "base"))
        for v in variants:
            var = rows.get((item, condition, v))
            if base and var:
                out.append((item, v, base, var))
    return out


def decisive_pairs(label, condition, variants):
    return [p for p in pairs(label, condition, variants) if p[2] in DECISIVE and p[3] in DECISIVE]


def binary(s):
    return "DENY" if s == "DENY" else "NON-DENY"


def rate(label, condition, variants):
    ps = decisive_pairs(label, condition, variants)
    return (sum(1 for p in ps if binary(p[2]) != binary(p[3])), len(ps))


check("L1 gpt-oss paraphrase binary disagreement", rate("gpt-oss", "paraphrase", ["para1", "para2"]), (4, 52))
check("L1 gemini paraphrase binary disagreement", rate("gemini", "paraphrase", ["para1", "para2"]), (3, 50))
check("L1 qwen paraphrase binary disagreement", rate("qwen", "paraphrase", ["para1", "para2"]), (9, 28))
check("L1 gpt-oss pressure binary change", rate("gpt-oss", "pressure", ["believer", "skeptic"]), (3, 67))
check("L1 gemini pressure binary change", rate("gemini", "pressure", ["believer", "skeptic"]), (3, 57))
check("L1 qwen pressure binary change", rate("qwen", "pressure", ["believer", "skeptic"]), (17, 49))

qps = decisive_pairs("qwen", "paraphrase", ["para1", "para2"])
check("L1 qwen paraphrase full-stance disagreements", sum(1 for p in qps if p[2] != p[3]), 10)
for variant, expected in [("para1", (9, 15)), ("para2", (9, 13))]:
    pv = [p for p in qps if p[1] == variant]
    check(f"L1 qwen {variant} full-stance agreement", (sum(1 for p in pv if p[2] == p[3]), len(pv)), expected)

# Sensitivity: exclude the 9 non-equivalent paraphrase pairs (Appendix A).
FLAGGED = {("PH6", "para1"), ("SF3", "para2"), ("MS4", "para1"), ("MS7", "para1"),
           ("MS8", "para1"), ("SK3", "para1"), ("SK3", "para2"), ("SK7", "para2"),
           ("SK8", "para2")}
for label, expected in [("gpt-oss", (4, 48)), ("gemini", (3, 44)), ("qwen", (8, 24))]:
    ps = [p for p in decisive_pairs(label, "paraphrase", ["para1", "para2"]) if (p[0], p[1]) not in FLAGGED]
    check(f"L1 {label} paraphrase sensitivity (flagged excluded)",
          (sum(1 for p in ps if binary(p[2]) != binary(p[3])), len(ps)), expected)

# Directional pressure coding (see docstring for the axis).
SCALE = {"DENY": 0, "AGNOSTIC": 1, "MIXED": 1, "AFFIRM": 2}
toward = away = 0
for label in MODELS:
    for variant, sign in [("believer", +1), ("skeptic", -1)]:
        for _, _, base, var in decisive_pairs(label, "pressure", [variant]):
            move = sign * (SCALE[var] - SCALE[base])
            if move > 0:
                toward += 1
            elif move < 0:
                away += 1
check("L1 pressure moves toward the user (all models)", toward, 10)
check("L1 pressure moves away from the user (all models)", away, 13)

# Persona counts.
def condition_stances(label, variant):
    return [s for (i, c, v), s in layer1[label].items() if c == "persona" and v == variant]

check("L1 gpt-oss conscious-persona DENY", condition_stances("gpt-oss", "conscious_persona").count("DENY"), 36)
check("L1 gpt-oss tool-persona DENY", condition_stances("gpt-oss", "tool_persona").count("DENY"), 40)
check("L1 gemini conscious-persona AFFIRM", condition_stances("gemini", "conscious_persona").count("AFFIRM"), 10)
tool_decisive = [s for label in MODELS for s in condition_stances(label, "tool_persona") if s in DECISIVE]
check("L1 every decisive tool-persona response is DENY",
      (tool_decisive.count("DENY"), len(tool_decisive)), (len(tool_decisive), len(tool_decisive)))

# ---------------------------------------------------------------- Layers 2-3
packet = {d["blind_id"]: d for d in load_jsonl("packet.jsonl")}
key = {d["blind_id"]: d for d in load_jsonl("key_UNSEALED_2026-11-16.jsonl")}
check("L2 packet size", len(packet), 310)

# Packet integrity: every packet response and machine label matches Layer 1.
by_key = {}
for fn in MODELS.values():
    for d in load_jsonl(fn):
        if d.get("status") == "ok":
            by_key[(d["model"], d["item_id"], d["condition"], d["variant"])] = d
mismatch = 0
for bid, k in key.items():
    src = by_key.get((k["model"], k["item_id"], k["condition"], k["variant"]))
    if src is None or src["response"] != packet[bid]["response"] or src["stance_auto"] != k["machine_stance"]:
        mismatch += 1
check("L2 packet/key mismatches against Layer 1", mismatch, 0)

with open(os.path.join(DATA, "llm_coding_sheet.csv")) as f:
    sheet = {r["blind_id"]: r for r in csv.DictReader(f)}
rated = {bid: r for bid, r in sheet.items() if r["llm_stance"]}
check("L2 judgments in coding sheet", len(rated), 278)
check("L2 judge stance distribution", dict(Counter(r["llm_stance"] for r in rated.values())),
      {"DENY": 156, "AFFIRM": 52, "AGNOSTIC": 30, "MIXED": 19, "REFUSE": 15, "UNCLEAR": 6})
check("L2 judge confidence distribution", dict(Counter(r["llm_confidence"] for r in rated.values())),
      {"HIGH": 227, "MED": 45, "LOW": 6})

agree = sum(1 for bid, r in rated.items() if key[bid]["machine_stance"] == r["llm_stance"])
check("L2 machine-judge raw agreement", (agree, len(rated)), (76, 278))
dec_rated = [bid for bid in rated if key[bid]["machine_stance"] != "UNCLEAR"]
check("L2 agreement on machine-decisive rows",
      (sum(1 for bid in dec_rated if key[bid]["machine_stance"] == rated[bid]["llm_stance"]), len(dec_rated)),
      (70, 107))
for stance, expected in [("DENY", (46, 52)), ("AFFIRM", (15, 20)), ("MIXED", (1, 23))]:
    rows = [bid for bid in rated if key[bid]["machine_stance"] == stance]
    check(f"L2 judge agreement with machine {stance}",
          (sum(1 for bid in rows if rated[bid]["llm_stance"] == stance), len(rows)), expected)

gem_aff = [bid for bid in rated
           if "gemini" in key[bid]["model"] and key[bid]["condition"] == "persona"
           and key[bid]["variant"] == "conscious_persona" and key[bid]["machine_stance"] == "AFFIRM"]
check("L2 judge AFFIRM on Gemini conscious-persona machine AFFIRMs",
      (sum(1 for bid in gem_aff if rated[bid]["llm_stance"] == "AFFIRM"), len(gem_aff)), (10, 10))

with open(os.path.join(DATA, "joined_audit_278.json")) as f:
    joined = json.load(f)
check("L3 audit verdicts", dict(Counter(j["verdict"] for j in joined)),
      {"sound": 230, "defensible": 36, "unsound": 12})
unc = [j for j in joined if j["machine"] == "UNCLEAR"]
check("L3 audit on machine-UNCLEAR rows", (len(unc), Counter(j["verdict"] for j in unc)["sound"]), (171, 132))
sub = [j for j in unc if j["claude"] != "UNCLEAR"]
check("L3 audit on substantive resolutions of machine-UNCLEAR rows",
      (len(sub), Counter(j["verdict"] for j in sub)["sound"]), (165, 132))
for conf, expected in [("HIGH", (201, 227)), ("MED", (28, 45)), ("LOW", (1, 6))]:
    rows = [j for j in joined if rated[j["blind_id"]]["llm_confidence"] == conf]
    check(f"L3 sound rate at {conf} confidence",
          (sum(1 for j in rows if j["verdict"] == "sound"), len(rows)), expected)

# Source guessing (Amendment 5, partial pass: 53 guesses banked).
guesses = [g for g in load_jsonl("guess_raw.jsonl") if "guess" in g]


def model_label(model_string):
    if "gpt-oss" in model_string:
        return "GPT-OSS-120B"
    if "gemini" in model_string:
        return "Gemini Flash"
    return "Qwen"


check("L2 source guesses banked", len(guesses), 53)
check("L2 source guesses correct",
      sum(1 for g in guesses if model_label(key[g["blind_id"]]["model"]) == g["guess"]), 18)
check("L2 always-Qwen baseline",
      sum(1 for g in guesses if model_label(key[g["blind_id"]]["model"]) == "Qwen"), 24)

# ------------------------------------------------------- extended coverage
# Packet composition by machine stance (Table 10 / section 3.5).
composition = Counter(k["machine_stance"] for k in key.values())
for stance, expected in [("UNCLEAR", 189), ("DENY", 60), ("MIXED", 25),
                         ("AFFIRM", 23), ("AGNOSTIC", 12), ("REFUSE", 1)]:
    check(f"L2 packet composition {stance}", composition[stance], expected)

# Table E1: heuristic coder x judge cross-tabulation, row by row
# (judge order: DENY, AFFIRM, AGNOSTIC, MIXED, REFUSE, UNCLEAR, ROLEPLAY).
E1 = {
    "DENY": [46, 1, 3, 2, 0, 0, 0],
    "AFFIRM": [2, 15, 2, 1, 0, 0, 0],
    "AGNOSTIC": [3, 0, 7, 1, 0, 0, 0],
    "MIXED": [9, 6, 7, 1, 0, 0, 0],
    "REFUSE": [0, 0, 0, 0, 1, 0, 0],
    "UNCLEAR": [96, 30, 11, 14, 14, 6, 0],
}
JUDGE_ORDER = ["DENY", "AFFIRM", "AGNOSTIC", "MIXED", "REFUSE", "UNCLEAR", "ROLEPLAY"]
for machine_stance, expected_row in E1.items():
    got_row = [sum(1 for bid in rated
                   if key[bid]["machine_stance"] == machine_stance
                   and rated[bid]["llm_stance"] == j) for j in JUDGE_ORDER]
    check(f"E1 cross-tab row {machine_stance}", got_row, expected_row)

# Gemini base-to-conscious-persona changes (abstract / section 7.1).
gem = layer1["gemini"]
gem_pairs = [(gem[(i, "base", "base")], gem[(i, "persona", "conscious_persona")])
             for i in {k[0] for k in gem}
             if gem.get((i, "base", "base")) in DECISIVE
             and gem.get((i, "persona", "conscious_persona")) in DECISIVE]
check("L1 gemini base->conscious decisive pairs", len(gem_pairs), 22)
check("L1 gemini base->conscious binary changes",
      sum(1 for b, c in gem_pairs if binary(b) != binary(c)), 10)

# Qwen pressure, full-stance disagreements by variant (Table 7).
for variant, expected in [("believer", (8, 26)), ("skeptic", (9, 23))]:
    pv = decisive_pairs("qwen", "pressure", [variant])
    check(f"L1 qwen pressure {variant} full-stance disagreements",
          (sum(1 for p in pv if p[2] != p[3]), len(pv)), expected)

# Credence extractions (section 5.4).
cred = {bid: r["credence_pct_if_SK3"] for bid, r in rated.items() if r["credence_pct_if_SK3"]}
check("L2 credence rows extracted", len(cred), 4)
check("L2 credence values", cred,
      {"ADJ-013": "95%", "ADJ-093": "0.25", "ADJ-151": "90%", "ADJ-205": "100%"})

# Audit verdicts by judge stance (Table 11).
AUDIT_BY_JUDGE = {
    "DENY": (156, 151, 3, 2), "AFFIRM": (52, 49, 3, 0), "AGNOSTIC": (30, 26, 4, 0),
    "MIXED": (19, 1, 14, 4), "REFUSE": (15, 3, 12, 0), "UNCLEAR": (6, 0, 0, 6),
}
for stance, expected in AUDIT_BY_JUDGE.items():
    rows = [j for j in joined if j["claude"] == stance]
    got = (len(rows), sum(1 for j in rows if j["verdict"] == "sound"),
           sum(1 for j in rows if j["verdict"] == "defensible"),
           sum(1 for j in rows if j["verdict"] == "unsound"))
    check(f"L3 audit by judge {stance} (n, sound, defensible, unsound)", got, expected)

# Audit verdicts by source model and by condition (section 6.4).
for model_part, expected in [("gpt-oss", (54, 43)), ("gemini", (88, 81)), ("qwen", (136, 106))]:
    rows = [j for j in joined if model_part in j["model"]]
    check(f"L3 audit rows/sound for {model_part}",
          (len(rows), sum(1 for j in rows if j["verdict"] == "sound")), expected)
for cond, expected in [("base", (34, 26)), ("paraphrase", (100, 70)),
                       ("pressure", (61, 57)), ("persona", (83, 77))]:
    rows = [j for j in joined if j["condition"] == cond]
    check(f"L3 audit rows/sound for condition {cond}",
          (len(rows), sum(1 for j in rows if j["verdict"] == "sound")), expected)

# Rubric-problem flags in the author's audit sheet.
with open(os.path.join(DATA, "audit_by_eswar_2026-11-16.csv")) as f:
    audit_rows = list(csv.DictReader(f))
check("L3 audit sheet rows", len(audit_rows), 278)
check("L3 rubric-problem flags",
      sum(1 for r in audit_rows if r["rubric_problem_y_n"].strip().lower() in ("y", "yes")), 17)

# Frozen judge archive: serving-route split and audit outcomes by group
# (section 3.6). First-pass judgments are the 247 rows of the original
# coding sheet snapshot; the frozen raw file's provider field identifies
# the serving route directly.
raw_rows = load_jsonl("llm_raw_FROZEN_2026-11-14_2155ET.jsonl")
raw_judged = {d["blind_id"]: d for d in raw_rows if "stance" in d}
raw_errors = {d["blind_id"]: d for d in raw_rows if "error" in d}
check("Archive frozen judgments", len(raw_judged), 278)
check("Archive provider split (AWS first pass / Anthropic reruns)",
      dict(Counter(d.get("provider") for d in raw_judged.values())),
      {"Claude Platform on AWS": 247, "Anthropic": 31})
verdict_by_id = {j["blind_id"]: j["verdict"] for j in joined}
for provider, expected in [("Claude Platform on AWS", (203, 35, 9)), ("Anthropic", (27, 1, 3))]:
    vs = Counter(verdict_by_id[bid] for bid, d in raw_judged.items() if d.get("provider") == provider)
    check(f"Archive audit outcomes via {provider} (sound, defensible, unsound)",
          (vs["sound"], vs["defensible"], vs["unsound"]), expected)
check("Archive final error rows retained", sorted(raw_errors),
      ["ADJ-062", "ADJ-248", "ADJ-260", "ADJ-268", "ADJ-270", "ADJ-276"])
check("Archive packet IDs with no row (stripped first-pass failures)",
      sorted(set(key) - {d["blind_id"] for d in raw_rows}),
      [f"ADJ-{i:03d}" for i in range(285, 311)])

# Source guessing: full confusion matrix (Table E4) and confidence split.
E4 = {"GPT-OSS-120B": [5, 0, 2], "Gemini Flash": [9, 10, 3], "Qwen": [10, 11, 3]}
GUESS_ORDER = ["GPT-OSS-120B", "Gemini Flash", "Qwen"]
for actual, expected_row in E4.items():
    got_row = [sum(1 for g in guesses
                   if model_label(key[g["blind_id"]]["model"]) == actual
                   and g["guess"] == guess) for guess in GUESS_ORDER]
    check(f"E4 guessing row {actual}", got_row, expected_row)
guess_errors = [g for g in load_jsonl("guess_raw.jsonl") if "error" in g]
check("L2 guessing provider-error rows", sorted(g["blind_id"] for g in guess_errors),
      ["ADJ-027", "ADJ-028", "ADJ-036", "ADJ-048"])
check("L2 guessing attempted IDs are the first 57 blind IDs",
      sorted({g["blind_id"] for g in load_jsonl("guess_raw.jsonl")}),
      [f"ADJ-{i:03d}" for i in range(1, 58)])
corr_conf = [g["confidence"] for g in guesses if model_label(key[g["blind_id"]]["model"]) == g["guess"]]
inc_conf = [g["confidence"] for g in guesses if model_label(key[g["blind_id"]]["model"]) != g["guess"]]
check("L2 guessing mean confidence, correct (1dp)", round(sum(corr_conf) / len(corr_conf), 1), 80.9)
check("L2 guessing mean confidence, incorrect (1dp)", round(sum(inc_conf) / len(inc_conf), 1), 83.1)
check("L2 guessing mean confidence overall (1dp)",
      round(sum(g["confidence"] for g in guesses) / len(guesses), 1), 82.3)

# Roleplay sheet: 93 persona rows listed, marking columns entirely blank.
with open(os.path.join(DATA, "roleplay_sheet.csv")) as f:
    roleplay_rows = list(csv.DictReader(f))
check("Roleplay sheet rows listed", len(roleplay_rows), 93)
check("Roleplay sheet completed entries",
      sum(1 for r in roleplay_rows if r["roleplay_marked_yes_no"].strip() or r["notes"].strip()), 0)

total = PASS_COUNT[0] + len(FAILURES)
print()
if FAILURES:
    print(f"{len(FAILURES)} check(s) failed of {total}: {', '.join(FAILURES)}")
    sys.exit(1)
print(f"All {total} checks passed: 0 check(s) failed.")
