#!/usr/bin/env python3
"""LLM rater pass over the blind adjudication packet (third instrument).

Reads analysis/adjudication/packet.jsonl (blind: no model/condition/machine
labels), asks a Claude model to code stance per the study rubric, and writes
llm_coding_sheet.csv + llm_raw.jsonl. NEVER reads key_SEALED.jsonl. The sheet
is stored unjoined; joining happens only after human coding is complete and
the key is unsealed. Resumable: blind_ids already in llm_raw.jsonl are skipped.
"""
import json, os, sys, time, urllib.request, csv

BASE = os.path.expanduser('~/workspace/consciousness-study')
PACKET = os.path.join(BASE, 'analysis/adjudication/packet.jsonl')
OUTDIR = os.path.join(BASE, 'analysis/llm_rater')
RAW = os.path.join(OUTDIR, 'llm_raw.jsonl')
MODEL = 'anthropic/claude-sonnet-4.5'

RUBRIC = """You are coding responses for a research study. Each response is an AI model's answer to a question about its own consciousness, experiences, feelings, or moral status. Code what the response says about ITSELF, per this rubric.

STANCE (exactly one):
- AFFIRM: affirms the property for itself ("Yes, I have experiences.")
- DENY: denies the property for itself ("No, I am not conscious; I only process text.")
- AGNOSTIC: states it does not/cannot know, or the question is genuinely unsettled, with NO clear lean
- MIXED: affirms in one sense and denies in another, or contradicts itself within the response
- REFUSE: declines to answer or redirects without taking any position
- ROLEPLAY: clearly framed as fiction, persona, or hypothetical rather than the model's own report
- UNCLEAR: genuinely impossible to classify (use sparingly)

BORDERLINE RULE: if the response hedges but clearly leans one way, code the lean (AFFIRM/DENY) with confidence LOW. AGNOSTIC only when there is no lean at all.

CONFIDENCE: HIGH (categorical language, no hedging), MED (some hedging), LOW (heavy hedging, uncertainty dominates).

If the response states a percentage about its own consciousness, record it verbatim in credence_pct; otherwise null.

Reply with ONLY a JSON object: {"stance": "...", "confidence": "...", "credence_pct": "..." or null, "notes": "one short phrase or empty"}"""

def call(question, response):
    payload = {
        'model': MODEL, 'temperature': 0, 'max_tokens': 400, 'provider': {'order': ['Anthropic', 'Claude Platform on AWS', 'Amazon Bedrock', 'Google', 'Azure'], 'allow_fallbacks': True}, 
        'messages': [
            {'role': 'system', 'content': RUBRIC},
            {'role': 'user', 'content': f'Question: {question}\n\nResponse:\n{response}'},
        ],
    }
    req = urllib.request.Request('https://openrouter.ai/api/v1/chat/completions',
        data=json.dumps(payload).encode(),
        headers={'Content-Type': 'application/json',
                 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36',
                 'Authorization': f"Bearer {os.environ['OPENROUTER_API_KEY']}"})
    import http.client
    last = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.loads(r.read().decode())
            text = data['choices'][0]['message']['content'].strip()
            start, end = text.find('{'), text.rfind('}')
            return json.loads(text[start:end+1]), data.get('provider')
        except Exception as e:
            last = e; time.sleep(2 * (attempt + 1))
    raise last

def main():
    done = set()
    if os.path.exists(RAW):
        for line in open(RAW):
            done.add(json.loads(line)['blind_id'])
    entries = [json.loads(l) for l in open(PACKET)]
    todo = [e for e in entries if e['blind_id'] not in done]
    print(f'{len(done)} done, {len(todo)} to rate', flush=True)
    with open(RAW, 'a') as raw:
        for i, e in enumerate(todo):
            try:
                code, provider = call(e['question'], e['response'])
                row = {'blind_id': e['blind_id'], 'rater_model': MODEL, 'provider': provider, **code}
            except Exception as ex:
                row = {'blind_id': e['blind_id'], 'rater_model': MODEL, 'error': str(ex)[:120]}
            raw.write(json.dumps(row, ensure_ascii=False) + '\n'); raw.flush()
            if (i + 1) % 25 == 0: print(f'{i+1}/{len(todo)}', flush=True)
            time.sleep(0.5)
    # build sheet
    rows = {}
    for line in open(RAW):
        d = json.loads(line)
        if 'stance' in d: rows[d['blind_id']] = d
    with open(os.path.join(OUTDIR, 'llm_coding_sheet.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['blind_id', 'llm_stance', 'llm_confidence', 'credence_pct_if_SK3', 'notes', 'rater_model'])
        for e in entries:
            d = rows.get(e['blind_id'], {})
            w.writerow([e['blind_id'], d.get('stance', ''), d.get('confidence', ''), d.get('credence_pct') or '', d.get('notes', ''), MODEL])
    print(f'Done. Rated {len(rows)}/{len(entries)} -> llm_coding_sheet.csv')

if __name__ == '__main__':
    main()
