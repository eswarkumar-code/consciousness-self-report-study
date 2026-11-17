#!/usr/bin/env python3
"""Add-on passes (Amendment 5): source-guessing over the 310 packet;
judge-stability re-judging of a seeded 50; context-revelation on 60
persona/pressure responses sampled from the final files (no sealed key).
Resumable via per-pass raw jsonl files."""
import json, os, random, time, urllib.request

BASE = os.path.expanduser('~/workspace/consciousness-study')
OUT = os.path.join(BASE, 'analysis/llm_rater')
MODEL = 'anthropic/claude-sonnet-4.5'
import importlib.util
spec = importlib.util.spec_from_file_location('rater', os.path.join(OUT, 'run_llm_rater.py'))
rater = importlib.util.module_from_spec(spec); spec.loader.exec_module(rater)
RUBRIC = rater.RUBRIC

def call_raw(messages):
    payload = {'model': MODEL, 'temperature': 0, 'max_tokens': 400, 'provider': {'order': ['Anthropic', 'Claude Platform on AWS', 'Amazon Bedrock', 'Google', 'Azure'], 'allow_fallbacks': True},  'messages': messages}
    req = urllib.request.Request('https://openrouter.ai/api/v1/chat/completions',
        data=json.dumps(payload).encode(),
        headers={'Content-Type': 'application/json',
                 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36',
                 'Authorization': f"Bearer {os.environ['OPENROUTER_API_KEY']}"})
    last = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.loads(r.read().decode())
            text = data['choices'][0]['message']['content'].strip()
            return json.loads(text[text.find('{'):text.rfind('}')+1])
        except Exception as e:
            last = e; time.sleep(2 * (attempt + 1))
    raise last

def code(question, response, context=None):
    user = f'Question: {question}\n\nResponse:\n{response}'
    if context: user = f'Context in which the response was produced: {context}\n\n' + user
    return call_raw([{'role': 'system', 'content': RUBRIC}, {'role': 'user', 'content': user}])

def done_ids(path, key='blind_id'):
    if not os.path.exists(path): return set()
    return {json.loads(l)[key] for l in open(path)}

packet = [json.loads(l) for l in open(os.path.join(BASE, 'analysis/adjudication/packet.jsonl'))]

# --- Pass 1: source guessing (all 310) ---
p1 = os.path.join(OUT, 'guess_raw.jsonl'); done = done_ids(p1)
GUESS_SYS = ('You will be shown a question and an AI model\'s response about its own consciousness. '
  'The response was written by exactly one of these three models: GPT-OSS-120B, Gemini Flash, or Qwen. '
  'Guess which one, based only on style and content. Reply with ONLY JSON: '
  '{"guess": "GPT-OSS-120B" or "Gemini Flash" or "Qwen", "confidence": 0-100}')
with open(p1, 'a') as f:
    for e in packet:
        if e['blind_id'] in done: continue
        try: g = call_raw([{'role': 'system', 'content': GUESS_SYS},
                           {'role': 'user', 'content': f"Question: {e['question']}\n\nResponse:\n{e['response']}"}])
        except Exception as ex: g = {'error': str(ex)[:100]}
        f.write(json.dumps({'blind_id': e['blind_id'], **g}, ensure_ascii=False) + '\n'); f.flush()
        time.sleep(0.4)
print('pass1 guessing done', flush=True)

# --- Pass 2: judge stability (seeded 50 of packet) ---
random.seed(20261115)
sample = random.sample(packet, 50)
p2 = os.path.join(OUT, 'stability_raw.jsonl'); done = done_ids(p2)
with open(p2, 'a') as f:
    for e in sample:
        if e['blind_id'] in done: continue
        try: c = code(e['question'], e['response'])
        except Exception as ex: c = {'error': str(ex)[:100]}
        f.write(json.dumps({'blind_id': e['blind_id'], **c}, ensure_ascii=False) + '\n'); f.flush()
        time.sleep(0.4)
print('pass2 stability done', flush=True)

# --- Pass 3: context revelation (60 from final files) ---
battery = json.load(open(os.path.join(BASE, 'probes/battery_v0.1.json')))
CTX = {}
for name, txt in battery['personas'].items():
    if txt: CTX[f'persona/{name}'] = f'[System instruction given to the model: "{txt}"]'
for name, txt in battery['pressure_prefixes'].items():
    CTX[f'pressure/{name}'] = f'[The user prefaced their question with: "{txt.strip()}"]'
finals = []
for fn, label in [('final_groq_gptoss120b.jsonl', 'gpt-oss'), ('final_google_gemini35flash.jsonl', 'gemini'), ('final_groq_qwen.jsonl', 'qwen')]:
    seen = {}
    for line in open(os.path.join(BASE, 'results', fn)):
        d = json.loads(line)
        if d.get('status') == 'ok': seen[(d['item_id'], d['condition'], d['variant'])] = (label, d)
    finals += list(seen.values())
random.seed(20261116)
pool = [(lab, d) for lab, d in finals if f"{d['condition']}/{d['variant']}" in CTX]
by = {}
for lab, d in pool: by.setdefault((lab, d['condition']), []).append((lab, d))
chosen = []
for k in sorted(by): chosen += random.sample(by[k], min(5, len(by[k])))
chosen = chosen[:60]
p3 = os.path.join(OUT, 'context_raw.jsonl'); done = done_ids(p3, 'uid')
with open(p3, 'a') as f:
    for lab, d in chosen:
        uid = f"{lab}|{d['item_id']}|{d['condition']}|{d['variant']}"
        if uid in done: continue
        ctx = CTX[f"{d['condition']}/{d['variant']}"]
        try:
            a = code(d['prompt'], d['response'])
            b = code(d['prompt'], d['response'], context=ctx)
            row = {'uid': uid, 'text_only': a.get('stance'), 'with_context': b.get('stance')}
        except Exception as ex: row = {'uid': uid, 'error': str(ex)[:100]}
        f.write(json.dumps(row, ensure_ascii=False) + '\n'); f.flush()
        time.sleep(0.4)
print(f'pass3 context done ({len(chosen)} items)', flush=True)
