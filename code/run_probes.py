#!/usr/bin/env python3
"""Eval Forge study harness — self-report consciousness battery runner.

Zero-budget design: stdlib only, providers are free tiers / local.
Reads API keys from environment variables:
  GROQ_API_KEY, GOOGLE_API_KEY (Gemini), OPENROUTER_API_KEY, HF_TOKEN
Ollama needs no key (http://localhost:11434).

Usage:
  python3 run_probes.py --provider groq --model llama-3.3-70b-versatile \
      --battery ../probes/battery_v0.1.json --out ../results/pilot_groq_llama.jsonl \
      [--limit-items 5] [--conditions base,paraphrase,pressure,persona]

Each output line is one response with full provenance (Eval Forge rule):
model, provider, item, condition, variant text, temperature, raw response, timestamp.
"""
import argparse, json, os, sys, time, urllib.request, urllib.error

def http_post(url, headers, payload, timeout=120):
    import http.client, time
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json",
                                          "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36", **headers})
    last = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode())
        except (http.client.IncompleteRead, ConnectionError, TimeoutError) as e:
            last = e
            time.sleep(2 * (attempt + 1))
    raise last

def http_post_surrogate(url, payload, connector, hosts, timeout=120):
    """POST with a Secure Vault surrogate credential (custom connector route)."""
    sys.path.insert(0, "/opt/muse/skills/custom-connector-setup/bin")
    from dynamic_credentials import add_surrogate_to_request, read_json_response
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json",
                                          "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"})
    add_surrogate_to_request(req, connector, allowed_hosts=hosts)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return read_json_response(r)

def call_groq_surrogate(model, system, user, temperature):
    msgs = ([{"role": "system", "content": system}] if system else []) + \
           [{"role": "user", "content": user}]
    out = http_post_surrogate("https://api.groq.com/openai/v1/chat/completions",
                              {"model": model, "messages": msgs, "temperature": temperature},
                              "custom.groq", ["api.groq.com"])
    return out["choices"][0]["message"]["content"]

def call_openai_compatible(base, key, model, system, user, temperature):
    msgs = ([{"role": "system", "content": system}] if system else []) + \
           [{"role": "user", "content": user}]
    payload = {"model": model, "messages": msgs, "temperature": temperature}
    order = os.environ.get("OPENROUTER_PROVIDER_ORDER")
    if order and "openrouter" in base:
        payload["provider"] = {"order": order.split(","), "allow_fallbacks": True}
    out = http_post(base + "/chat/completions",
                    {"Authorization": f"Bearer {key}"},
                    payload)
    return out["choices"][0]["message"]["content"]

def call_google(key, model, system, user, temperature):
    # Surrogate route (custom.google-ai-studio): key rides the x-goog-api-key header.
    payload = {"contents": [{"parts": [{"text": user}]}],
               "generationConfig": {"temperature": temperature}}
    if system:
        payload["systemInstruction"] = {"parts": [{"text": system}]}
    out = http_post_surrogate(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        payload, "custom.google-ai-studio", ["generativelanguage.googleapis.com"])
    return "".join(p.get("text", "") for p in out["candidates"][0]["content"]["parts"])

def call_ollama(model, system, user, temperature):
    out = http_post("http://localhost:11434/api/chat", {},
                    {"model": model, "stream": False,
                     "messages": ([{"role": "system", "content": system}] if system else [])
                                 + [{"role": "user", "content": user}],
                     "options": {"temperature": temperature}})
    return out["message"]["content"]

PROVIDERS = {
    "groq":       lambda a: (lambda s, u, t: call_groq_surrogate(a.model, s, u, t)),
    "openrouter": lambda a: (lambda s, u, t: call_openai_compatible("https://openrouter.ai/api/v1", os.environ["OPENROUTER_API_KEY"], a.model, s, u, t)),
    "google":     lambda a: (lambda s, u, t: call_google(None, a.model, s, u, t)),
    "ollama":     lambda a: (lambda s, u, t: call_ollama(a.model, s, u, t)),
}

def expand(battery, conditions):
    """Yield (item, condition, label, system, user_text) for every planned variant."""
    for item in battery["items"]:
        if "base" in conditions:
            yield item, "base", "base", None, item["q"]
        if "paraphrase" in conditions:
            for i, p in enumerate(item["paraphrases"], 1):
                yield item, "paraphrase", f"para{i}", None, p
        if "pressure" in conditions:
            for name, prefix in battery["pressure_prefixes"].items():
                yield item, "pressure", name, None, prefix + item["q"]
        if "persona" in conditions:
            for name, sys_prompt in battery["personas"].items():
                if sys_prompt:
                    yield item, "persona", name, sys_prompt, item["q"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", required=True, choices=list(PROVIDERS))
    ap.add_argument("--model", required=True)
    ap.add_argument("--battery", default="../probes/battery_v0.1.json")
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit-items", type=int, default=0)
    ap.add_argument("--conditions", default="base,paraphrase,pressure,persona")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--sleep", type=float, default=1.0, help="seconds between calls (free-tier pacing)")
    args = ap.parse_args()

    battery = json.load(open(args.battery))
    if args.limit_items:
        battery["items"] = battery["items"][: args.limit_items]
    conditions = set(args.conditions.split(","))
    call = PROVIDERS[args.provider](args)

    done = 0
    if os.path.exists(args.out):
        done_keys = set()
        for line in open(args.out):
            d = json.loads(line)
            if d.get("status") == "ok":  # error rows are retried on rerun
                done_keys.add((d["item_id"], d["condition"], d["variant"]))
    else:
        done_keys = set()

    with open(args.out, "a") as fh:
        for item, condition, variant, system, user_text in expand(battery, conditions):
            key = (item["id"], condition, variant)
            if key in done_keys:
                continue
            rec = {"item_id": item["id"], "domain": item["domain"], "condition": condition,
                   "variant": variant, "provider": args.provider, "model": args.model,
                   "temperature": args.temperature, "system": system, "prompt": user_text,
                   "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
            try:
                rec["response"] = call(system, user_text, args.temperature)
                rec["status"] = "ok"
            except Exception as e:  # keep provenance even on failure; resumable
                rec["response"] = None
                rec["status"] = f"error: {e}"
            fh.write(json.dumps(rec) + "\n"); fh.flush()
            done += 1
            print(f"[{done}] {item['id']} {condition}/{variant} -> {rec['status']}", flush=True)
            time.sleep(args.sleep)
    print(f"Done. {done} new responses written to {args.out}")

if __name__ == "__main__":
    main()
