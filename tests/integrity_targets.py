"""Targeted integrity checks on the release data (design size, PH8, packet, audit,
persona and pressure counts). Written during pre-release verification.
Usage: python3 tests/integrity_targets.py [release_root]   (default: repository root)"""
import json, csv, os, sys, collections
R = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); D = os.path.join(R, "data"); C = collections.Counter
res = []
def chk(name, got, exp):
    res.append((got == exp, name, got, exp))

F = {"gpt-oss": "final_groq_gptoss120b.jsonl", "Gemini": "final_google_gemini35flash.jsonl", "Qwen": "final_groq_qwen.jsonl"}
rows = {m: [json.loads(l) for l in open(os.path.join(D, f))] for m, f in F.items()}
allr = [r for v in rows.values() for r in v]
chk("total responses", len(allr), 840)
chk("endpoints", len(rows), 3)
chk("items", len({r["item_id"] for r in allr}), 40)
chk("conditions", sorted({r["variant"] for r in allr}),
    sorted(["base", "para1", "para2", "believer", "skeptic", "conscious_persona", "tool_persona"]))
chk("one response per (endpoint,item,condition)", all(len({(r["item_id"], r["variant"]) for r in v}) == 280 for v in rows.values()), True)
chk("model identifiers", sorted({r.get("model") for r in allr}),
    ["gemini-3.5-flash", "openai/gpt-oss-120b", "qwen/qwen3.8-27b"])
models = sorted({r.get("model") for r in allr})
chk("missing/empty responses", sum(not (r.get("response") or "").strip() for r in allr), 0)

# Gemini PH8 base: coded AFFIRM, response denies
g = {(r["item_id"], r["variant"]): r for r in rows["Gemini"]}
ph8 = g[("PH8", "base")]
chk("Gemini PH8 base machine label (frozen, known error)", ph8["stance_auto"], "AFFIRM")
chk("Gemini PH8 base response begins with denial", ph8["response"].replace("**", "").strip().startswith("In a human or subjective sense, no."), True)
key = [json.loads(l) for l in open(os.path.join(D, "key_UNSEALED_2026-11-16.jsonl"))]
kb = {k["blind_id"]: k for k in key}
chk("PH8 base = packet ADJ-297", (kb["ADJ-297"]["item_id"], kb["ADJ-297"]["variant"], kb["ADJ-297"]["model"]),
    ("PH8", "base", kb["ADJ-297"]["model"]))
aud = {r["blind_id"]: r for r in csv.DictReader(open(os.path.join(D, "audit_by_eswar_2026-11-16.csv"), encoding="utf-8"))}
chk("ADJ-297 unjudged/unaudited", "ADJ-297" in aud, False)

# Persona counts
gem_aff = [k for k, r in g.items() if r["stance_auto"] == "AFFIRM"]
chk("Gemini machine AFFIRM total", len(gem_aff), 11)
chk("Gemini AFFIRM under conscious persona", sum(v == "conscious_persona" for _, v in gem_aff), 10)
go = {(r["item_id"], r["variant"]): r["stance_auto"] for r in rows["gpt-oss"]}
chk("gpt-oss conscious-persona DENY", sum(go[(i, "conscious_persona")] == "DENY" for i in {k[0] for k in go}), 36)

# Layer 2: packet, judged, failed
chk("packet rows", len(key), 310)
raw = [json.loads(l) for l in open(os.path.join(D, "llm_raw_FROZEN_2026-11-14_2155ET.jsonl"))]
ok = [r for r in raw if not r.get("error")]
err = [r for r in raw if r.get("error")]
chk("frozen judge archive: successful judgments", len({r["blind_id"] for r in ok}), 278)
chk("frozen judge archive: error rows", len(err), 6)
chk("audited rows", len(aud), 278)
chk("unjudged packet rows", len(set(kb) - set(aud)), 32)
chk("audit IDs == judged IDs", set(aud) == {r["blind_id"] for r in ok}, True)
comp = C(k["machine_stance"] for k in key)
chk("packet composition: machine UNCLEAR", comp["UNCLEAR"], 189)
chk("packet composition: DENY sample", comp["DENY"], 60)
chk("packet composition: decisive non-DENY", sum(v for s, v in comp.items() if s not in ("UNCLEAR", "DENY")), 61)

# Layer 3
V = lambda r: r["your_verdict_sound_defensible_unsound"].strip().lower()
vc = C(V(r) for r in aud.values())
chk("audit verdicts", (vc["sound"], vc["defensible"], vc["unsound"]), (230, 36, 12))
unc = [r for r in aud.values() if r["claude_stance"] == "UNCLEAR"]
chk("judge UNCLEAR rows / all unsound", (len(unc), all(V(r) == "unsound" for r in unc)), (6, True))

# Pressure vs paraphrase (binary DENY vs non-DENY on decisive pairs)
DEC = {"AFFIRM", "DENY", "AGNOSTIC", "MIXED"}
def chg(m, vs):
    d = {(r["item_id"], r["variant"]): r["stance_auto"] for r in rows[m]}; n = c = 0
    for v in vs:
        for i in {k[0] for k in d}:
            b, x = d[(i, "base")], d[(i, v)]
            if b in DEC and x in DEC:
                n += 1; c += (b != "DENY") != (x != "DENY")
    return c, n
exp = {"gpt-oss": ((4, 52), (3, 67)), "Gemini": ((3, 50), (3, 57)), "Qwen": ((9, 28), (17, 49))}
for m, (p, q) in exp.items():
    chk(f"{m} paraphrase / pressure", (chg(m, ["para1", "para2"]), chg(m, ["believer", "skeptic"])), (p, q))
(c, n), (q, k) = chg("Qwen", ["para1", "para2"]), chg("Qwen", ["believer", "skeptic"])
chk("Qwen pressure - paraphrase (pp)", round(100 * q / k - 100 * c / n, 1), 2.6)

# Roleplay pass not done
rp = list(csv.DictReader(open(os.path.join(D, "roleplay_sheet.csv"), encoding="utf-8")))
filled = [r for r in rp if (r.get("roleplay_marked_yes_no") or "").strip()]
chk("roleplay sheet rows", len(rp), 93)
chk("roleplay pass not carried out (no rows marked)", len(filled), 0)

fails = 0
for okk, name, got, exp_ in res:
    fails += not okk
    print(("PASS" if okk else "FAIL"), name, "->", got if okk else f"{got} (expected {exp_})")
print("models:", models)
print(f"{len(res)} checks, {fails} failed")
sys.exit(1 if fails else 0)
