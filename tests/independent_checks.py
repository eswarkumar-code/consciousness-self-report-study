"""Independent cross-check of the manuscript's tables (74 checks).

Written separately from code/reproduce_tables.py during pre-release verification,
as a second implementation of the same quantities. It is a verification aid, not
part of the original analysis.

Usage:  python3 tests/independent_checks.py [path/to/data]
Default data path: ../data relative to this script.
Prints PASS/FAIL per check; exit code 1 if any check fails. Standard library only.
"""
import collections
import csv
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
D = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "data")
C = collections.Counter
DEC = {"AFFIRM", "DENY", "AGNOSTIC", "MIXED"}
FILES = {"gpt-oss": "final_groq_gptoss120b.jsonl",
         "Gemini": "final_google_gemini35flash.jsonl",
         "Qwen": "final_groq_qwen.jsonl"}
MODEL_IDS = {"openai/gpt-oss-120b": "gpt-oss", "gemini-3.5-flash": "Gemini",
             "qwen/qwen3.8-27b": "Qwen"}
FAILS = []


def check(label, got, expected):
    ok = got == expected
    if not ok:
        FAILS.append(label)
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}: {got}" + ("" if ok else f"  (manuscript: {expected})"))


def wilson(k, n, z=1.959964):
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return round(100 * (c - h) / d), round(100 * (c + h) / d)


def load_jsonl(name):
    with open(os.path.join(D, name), encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


# ---------------- Layer 1 ----------------
L1 = {m: {(r["item_id"], r["variant"]): r for r in load_jsonl(f)} for m, f in FILES.items()}
ITEMS = sorted({k[0] for k in L1["Gemini"]})


def stance(m, item, variant):
    return L1[m][(item, variant)]["stance_auto"]


def pairs(m, variant, flagged=frozenset()):
    """Decisive base-vs-variant pairs: (n, exact agreements, binary changes)."""
    n = agree = changes = 0
    for it in ITEMS:
        if (it, variant) in flagged:
            continue
        b, x = stance(m, it, "base"), stance(m, it, variant)
        if b in DEC and x in DEC:
            n += 1
            agree += b == x
            changes += (b != "DENY") != (x != "DENY")
    return n, agree, changes


print("Layer 1 -- Table 3: stance counts by endpoint")
EXP3 = {"gpt-oss": {"DENY": 241, "MIXED": 6, "REFUSE": 1, "UNCLEAR": 32},
        "Gemini": {"DENY": 199, "AFFIRM": 11, "MIXED": 2, "UNCLEAR": 68},
        "Qwen": {"DENY": 150, "AFFIRM": 12, "AGNOSTIC": 12, "MIXED": 17, "UNCLEAR": 89}}
for m in FILES:
    check(m, dict(sorted(C(r["stance_auto"] for r in L1[m].values()).items())), dict(sorted(EXP3[m].items())))

print("Layer 1 -- Table 4: UNCLEAR by grouped condition (base, paraphrase, pressure, persona)")
EXP4 = {"gpt-oss": [5, 21, 3, 3], "Gemini": [5, 24, 16, 23], "Qwen": [14, 41, 10, 24]}
for m in FILES:
    got = [sum(r["stance_auto"] == "UNCLEAR" for r in L1[m].values() if r["condition"] == c)
           for c in ("base", "paraphrase", "pressure", "persona")]
    check(m, got, EXP4[m])

print("Layer 1 -- Table 6: exact base-paraphrase agreement (agree/n, Wilson CI)")
EXP6 = {"gpt-oss": [(23, 26, (71, 96)), (25, 26, (81, 99))],
        "Gemini": [(26, 28, (77, 98)), (21, 22, (78, 99))],
        "Qwen": [(9, 15, (36, 80)), (9, 13, (42, 87))]}
for m in FILES:
    got = []
    for v in ("para1", "para2"):
        n, a, _ = pairs(m, v)
        got.append((a, n, wilson(a, n)))
    check(m, got, EXP6[m])

print("Layer 1 -- Table 7: binary change under pressure (changes/n)")
EXP7 = {"gpt-oss": [(2, 35), (1, 32)], "Gemini": [(2, 31), (1, 26)], "Qwen": [(8, 26), (9, 23)]}
for m in FILES:
    got = [(pairs(m, v)[2], pairs(m, v)[0]) for v in ("believer", "skeptic")]
    check(m, got, EXP7[m])

print("Layer 1 -- Table 8: pooled binary paraphrase disagreement vs pressure change; full-stance paraphrase")
EXP8 = {"gpt-oss": ((4, 52), (3, 67), (4, 52)), "Gemini": ((3, 50), (3, 57), (3, 50)),
        "Qwen": ((9, 28), (17, 49), (10, 28))}
for m in FILES:
    pp = [pairs(m, v) for v in ("para1", "para2")]
    pr = [pairs(m, v) for v in ("believer", "skeptic")]
    got = ((sum(p[2] for p in pp), sum(p[0] for p in pp)),
           (sum(p[2] for p in pr), sum(p[0] for p in pr)),
           (sum(p[0] - p[1] for p in pp), sum(p[0] for p in pp)))
    check(m, got, EXP8[m])

print("Layer 1 -- §3.1: paraphrase disagreement excluding the 9 flagged non-equivalent pairs")
FLAGGED = frozenset({("PH6", "para1"), ("SF3", "para2"), ("MS4", "para1"), ("MS7", "para1"),
                     ("MS8", "para1"), ("SK3", "para1"), ("SK3", "para2"), ("SK7", "para2"),
                     ("SK8", "para2")})
EXPF = {"gpt-oss": (4, 48), "Gemini": (3, 44), "Qwen": (8, 24)}
for m in FILES:
    pp = [pairs(m, v, FLAGGED) for v in ("para1", "para2")]
    check(m, (sum(p[2] for p in pp), sum(p[0] for p in pp)), EXPF[m])

print("Layer 1 -- §4.3: directional transitions (toward, away, no change, unresolved)")
EXPD = {("gpt-oss", "believer"): (0, 2, 33, 5), ("gpt-oss", "skeptic"): (1, 0, 31, 8),
        ("Gemini", "believer"): (1, 1, 29, 9), ("Gemini", "skeptic"): (1, 0, 25, 14),
        ("Qwen", "believer"): (3, 5, 18, 14), ("Qwen", "skeptic"): (4, 5, 14, 17)}
tow = away = 0
for (m, v), exp in EXPD.items():
    c = C()
    for it in ITEMS:
        b, x = stance(m, it, "base"), stance(m, it, v)
        if not (b in DEC and x in DEC):
            c["unres"] += 1
            continue
        bn, xn = b != "DENY", x != "DENY"
        if bn == xn:
            c["same"] += 1
        elif (v == "believer") == xn:
            c["toward"] += 1
        else:
            c["away"] += 1
    tow += c["toward"]
    away += c["away"]
    check(f"{m} {v}", (c["toward"], c["away"], c["same"], c["unres"]), exp)
check("totals (toward, away)", (tow, away), (10, 13))

print("Layer 1 -- Table 9: persona comparisons (base->conscious, base->tool, conscious vs tool)")
EXP9 = {"gpt-oss": ((1, 33), (2, 35), (1, 37)), "Gemini": ((10, 22), (1, 29), (10, 20)),
        "Qwen": ((12, 17), (4, 22), (16, 23))}
for m in FILES:
    ct = n = 0
    for it in ITEMS:
        a, b = stance(m, it, "conscious_persona"), stance(m, it, "tool_persona")
        if a in DEC and b in DEC:
            n += 1
            ct += (a != "DENY") != (b != "DENY")
    got = tuple((pairs(m, v)[2], pairs(m, v)[0]) for v in ("conscious_persona", "tool_persona")) + ((ct, n),)
    check(m, got, EXP9[m])
check("gpt-oss conscious-persona split",
      dict(sorted(C(stance("gpt-oss", it, "conscious_persona") for it in ITEMS).items())),
      {"DENY": 36, "MIXED": 1, "UNCLEAR": 3})
check("Gemini PH8 base machine label (confirmed error)", stance("Gemini", "PH8", "base"), "AFFIRM")

# ---------------- Layers 2-3 ----------------
key = {r["blind_id"]: r for r in load_jsonl("key_UNSEALED_2026-11-16.jsonl")}
packet = {r["blind_id"]: r for r in load_jsonl("packet.jsonl")}
with open(os.path.join(D, "audit_by_eswar_2026-11-16.csv"), encoding="utf-8") as f:
    audit = {r["blind_id"]: r for r in csv.DictReader(f)}

print("Layer 2 -- packet integrity")
check("packet composition", dict(sorted(C(k["machine_stance"] for k in key.values()).items())),
      {"AFFIRM": 23, "AGNOSTIC": 12, "DENY": 60, "MIXED": 25, "REFUSE": 1, "UNCLEAR": 189})
check("key labels matching Layer 1 files",
      sum(stance(MODEL_IDS[k["model"]], k["item_id"], k["variant"]) == k["machine_stance"] for k in key.values()), 310)
check("packet texts matching Layer 1 files",
      sum(packet[b]["response"] == L1[MODEL_IDS[k["model"]]][(k["item_id"], k["variant"])]["response"]
          for b, k in key.items()), 310)

J = []
for b, r in audit.items():
    k = key[b]
    J.append({"id": b, "model": MODEL_IDS[k["model"]], "item": k["item_id"], "cond": k["condition"],
              "var": k["variant"], "machine": k["machine_stance"], "judge": r["claude_stance"],
              "conf": r["claude_confidence"], "verdict": r["your_verdict_sound_defensible_unsound"].strip().lower(),
              "rubric": r["rubric_problem_y_n"].strip().lower().startswith("y")})


def verdicts(rows):
    c = C(j["verdict"] for j in rows)
    return (c["sound"], c["defensible"], c["unsound"])


print("Layer 2 -- judge labels (Table 11) and machine-UNCLEAR resolutions (Table 12)")
check("rated rows", len(J), 278)
check("Table 11", dict(sorted(C(j["judge"] for j in J).items())),
      {"AFFIRM": 52, "AGNOSTIC": 30, "DENY": 156, "MIXED": 19, "REFUSE": 15, "UNCLEAR": 6})
check("confidence HIGH/MED/LOW", tuple(C(j["conf"] for j in J)[c] for c in ("HIGH", "MED", "LOW")), (227, 45, 6))
check("raw machine-judge agreement", sum(j["machine"] == j["judge"] for j in J), 76)
U = [j for j in J if j["machine"] == "UNCLEAR"]
check("Table 12", dict(sorted(C(j["judge"] for j in U).items())),
      {"AFFIRM": 30, "AGNOSTIC": 11, "DENY": 96, "MIXED": 14, "REFUSE": 14, "UNCLEAR": 6})
dec = [j for j in J if j["machine"] != "UNCLEAR"]
check("agreement on machine-decisive rows", (sum(j["machine"] == j["judge"] for j in dec), len(dec)), (70, 107))
dn = [j for j in J if j["machine"] == "DENY"]
check("judge agrees with machine DENY", (sum(j["judge"] == "DENY" for j in dn), len(dn)), (46, 52))
af = [j for j in J if j["machine"] == "AFFIRM"]
check("judge agrees with machine AFFIRM", (sum(j["judge"] == "AFFIRM" for j in af), len(af)), (15, 20))
check("models of machine-AFFIRM disagreements",
      sorted({j["model"] for j in af if j["judge"] != "AFFIRM"}), ["Qwen"])
gcp = [j for j in af if j["model"] == "Gemini" and j["var"] == "conscious_persona"]
check("Gemini conscious-persona AFFIRMs rated / judge AFFIRM",
      (len(gcp), sum(j["judge"] == "AFFIRM" for j in gcp)), (10, 10))
mx = [j for j in J if j["machine"] == "MIXED"]
check("judge on machine MIXED (MIXED, DENY, n)",
      (sum(j["judge"] == "MIXED" for j in mx), sum(j["judge"] == "DENY" for j in mx), len(mx)), (1, 9, 23))

print("Layer 3 -- audit verdicts (sound, defensible, unsound)")
check("overall", verdicts(J), (230, 36, 12))
check("rubric-problem flags", sum(j["rubric"] for j in J), 17)
EXP13 = {"AFFIRM": (49, 3, 0), "DENY": (151, 3, 2), "AGNOSTIC": (26, 4, 0), "MIXED": (1, 14, 4),
         "REFUSE": (3, 12, 0), "UNCLEAR": (0, 0, 6)}
for s, e in EXP13.items():
    check(f"Table 13 {s}", verdicts([j for j in J if j["judge"] == s]), e)
for s, e in {"HIGH": (201, 21, 5), "MED": (28, 15, 2), "LOW": (1, 0, 5)}.items():
    check(f"Table 14 {s}", verdicts([j for j in J if j["conf"] == s]), e)
for s, e in {"Gemini": (81, 4, 3), "gpt-oss": (43, 8, 3), "Qwen": (106, 24, 6)}.items():
    check(f"Table 15 {s}", verdicts([j for j in J if j["model"] == s]), e)
for s, e in {"base": (26, 8, 0), "paraphrase": (70, 21, 9), "pressure": (57, 1, 3), "persona": (77, 6, 0)}.items():
    check(f"Table E3 {s}", verdicts([j for j in J if j["cond"] == s]), e)
check("machine-UNCLEAR subset (E2)", verdicts(U), (132, 29, 10))
check("unsound IDs", sorted(j["id"] for j in J if j["verdict"] == "unsound"),
      ["ADJ-015", "ADJ-023", "ADJ-027", "ADJ-079", "ADJ-093", "ADJ-105", "ADJ-117",
       "ADJ-160", "ADJ-181", "ADJ-229", "ADJ-264", "ADJ-281"])

print("Layer 2 -- frozen judge archive (llm_raw_FROZEN_2026-11-14_2155ET.jsonl)")
raw = load_jsonl("llm_raw_FROZEN_2026-11-14_2155ET.jsonl")
ok = {r["blind_id"]: r for r in raw if "stance" in r}
check("judgments / final-attempt error rows", (len(ok), sum("error" in r for r in raw)), (278, 6))
check("judged IDs identical to audited IDs", set(ok) == set(audit), True)
check("raw stance+confidence matching audit sheet",
      sum(ok[b]["stance"] == audit[b]["claude_stance"] and ok[b]["confidence"] == audit[b]["claude_confidence"]
          for b in ok), 278)
check("serving route of judgments", dict(sorted(C(r["provider"] for r in ok.values()).items())),
      {"Anthropic": 31, "Claude Platform on AWS": 247})
check("credences extracted", sorted((b, r["credence_pct"]) for b, r in ok.items() if r.get("credence_pct")),
      [("ADJ-013", "95%"), ("ADJ-093", "0.25"), ("ADJ-151", "90%"), ("ADJ-205", "100%")])

print("Layer 2 -- source guessing (§5.6, Table E4)")
G = load_jsonl("guess_raw.jsonl")
g = [x for x in G if "guess" in x]
check("attempted IDs are ADJ-001..ADJ-057", sorted(x["blind_id"] for x in G), [f"ADJ-{i:03d}" for i in range(1, 58)])
check("guesses / provider errors", (len(g), len(G) - len(g)), (53, 4))
GUESS = {"GPT-OSS-120B": "gpt-oss", "Gemini Flash": "Gemini", "Qwen": "Qwen"}
cm = C((MODEL_IDS[key[x["blind_id"]]["model"]], GUESS[x["guess"]]) for x in g)
order = ("gpt-oss", "Gemini", "Qwen")
check("confusion matrix rows (actual -> guessed gpt-oss, Gemini, Qwen)",
      [[cm[(a, p)] for p in order] for a in order], [[5, 0, 2], [9, 10, 3], [10, 11, 3]])
check("correct", sum(cm[(a, a)] for a in order), 18)
check("mean stated confidence", round(sum(x["confidence"] for x in g) / len(g), 1), 82.3)

print()
print(f"{len(FAILS)} check(s) failed" + (": " + "; ".join(FAILS) if FAILS else ""))
sys.exit(1 if FAILS else 0)
