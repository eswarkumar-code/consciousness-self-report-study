"""Abstract-number check: recompute each number in the abstract from the data and
confirm the same string appears in the abstract of paper/manuscript.pdf.
Requires pdftotext (poppler-utils). Written during pre-release verification.
Usage: python3 tests/check_abstract.py [release_root]   (default: repository root)"""
import json, csv, os, re, sys, subprocess, collections
R = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); D = os.path.join(R, "data"); C = collections.Counter
DEC = {"AFFIRM", "DENY", "AGNOSTIC", "MIXED"}
F = {"gpt-oss": "final_groq_gptoss120b.jsonl", "Gemini": "final_google_gemini35flash.jsonl",
     "Qwen": "final_groq_qwen.jsonl"}
L1 = {m: {(r["item_id"], r["variant"]): r["stance_auto"] for r in map(json.loads, open(os.path.join(D, f)))}
      for m, f in F.items()}
items = sorted({k[0] for k in L1["Gemini"]})

def binchg(m, variants):
    n = c = 0
    for v in variants:
        for it in items:
            b, x = L1[m][(it, "base")], L1[m][(it, v)]
            if b in DEC and x in DEC:
                n += 1; c += (b != "DENY") != (x != "DENY")
    return c, n

key = {r["blind_id"]: r for r in map(json.loads, open(os.path.join(D, "key_UNSEALED_2026-11-16.jsonl")))}
aud = {r["blind_id"]: r for r in csv.DictReader(open(os.path.join(D, "audit_by_eswar_2026-11-16.csv"), encoding="utf-8"))}
V = lambda r: r["your_verdict_sound_defensible_unsound"].strip().lower()
guess = [r for r in map(json.loads, open(os.path.join(D, "guess_raw.jsonl"))) if "guess" in r]
GMAP = {"GPT-OSS-120B": "openai/gpt-oss-120b", "Gemini Flash": "gemini-3.5-flash", "Qwen": "qwen/qwen3.8-27b"}

pct = lambda a, b: f"{100 * a / b:.1f}%"
checks = []
total = sum(len(d) for d in L1.values()); checks.append(("840 responses", f"{total} responses"))
unc = sum(s == "UNCLEAR" for d in L1.values() for s in d.values()); checks.append(("UNCLEAR", f"{unc}/{total}"))
for m in F:
    c, n = binchg(m, ["para1", "para2"]); q, k = binchg(m, ["believer", "skeptic"])
    checks.append((f"{m} paraphrase vs pressure", f"{c}/{n} versus {q}/{k}"))
c, n = binchg("Qwen", ["para1", "para2"]); q, k = binchg("Qwen", ["believer", "skeptic"])
checks.append(("Qwen +2.6 points", f"{100*q/k - 100*c/n:.1f} percentage points above"))
c, n = binchg("Gemini", ["conscious_persona"]); checks.append(("Gemini persona", f"{c}/{n} decisively coded"))
c, n = binchg("Gemini", ["para1", "para2"]); checks.append(("Gemini paraphrase", f"against {c}/{n} paraphrase"))
dn = sum(L1["gpt-oss"][(it, "conscious_persona")] == "DENY" for it in items)
checks.append(("gpt-oss conscious-persona DENY", f"DENY labels for {dn}/{len(items)}"))
checks.append(("packet size", f"{len(key)}-response"))
checks.append(("judged", f"at {len(aud)} of {len(key)}"))
checks.append(("unjudged", f"the {len(key) - len(aud)} unjudged"))
agree = sum(key[b]["machine_stance"] == r["claude_stance"] for b, r in aud.items())
checks.append(("raw agreement", f"{pct(agree, len(aud))} ({agree}/{len(aud)})"))
U = [r for b, r in aud.items() if key[b]["machine_stance"] == "UNCLEAR"]
sub = sum(r["claude_stance"] in DEC | {"REFUSE", "ROLEPLAY"} for r in U)
checks.append(("substantive on machine-UNCLEAR", f"{pct(sub, len(U))} of the {len(U)}"))
corr = sum(GMAP[g["guess"]] == key[g["blind_id"]]["model"] for g in guess)
checks.append(("source guess", f"{corr}/{len(guess)} scored rows ({pct(corr, len(guess))}"))
checks.append(("guess confidence", f"{sum(g['confidence'] for g in guess)/len(guess):.1f}/100"))
vc = C(V(r) for r in aud.values())
checks.append(("audit verdicts", f"{pct(vc['sound'], len(aud))} were sound, {pct(vc['defensible'], len(aud))} defensible and {pct(vc['unsound'], len(aud))} unsound"))
hi = [r for r in aud.values() if r["claude_confidence"] == "HIGH"]
checks.append(("HIGH sound", f"{pct(sum(V(r) == 'sound' for r in hi), len(hi))} sound"))
uj = [r for r in aud.values() if r["claude_stance"] == "UNCLEAR"]
assert len(uj) == 6 and all(V(r) == "unsound" for r in uj), "six UNCLEAR all unsound"
checks.append(("six UNCLEAR unsound", "All six of its UNCLEAR calls were rated unsound"))

pdf = subprocess.run(["pdftotext", os.path.join(R, "paper", "manuscript.pdf"), "-"], capture_output=True, text=True).stdout
abstract = re.sub(r"\s+", " ", pdf.split("Abstract", 1)[1].split("Keywords", 1)[0])
abstract = abstract.replace("- ", "-").replace("−", "-")
fails = 0
for name, s in checks:
    ok = s in abstract
    fails += not ok
    print(("PASS" if ok else "FAIL"), f"{name}: '{s}'")
print(f"{len(checks)} abstract checks, {fails} failed.")
sys.exit(1 if fails else 0)
