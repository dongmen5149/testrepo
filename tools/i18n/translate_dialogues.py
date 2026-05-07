"""
dialogue_corpus.json 의 unique 한국어 대사를 Claude Haiku 4.5 로 영어 번역.

특징:
  - 캐릭터/지명 사전을 system prompt 에 주입 (일관된 transliteration)
  - 1시간 prompt caching 으로 system prompt 비용 90% 절감
  - 배치당 N개 텍스트 (기본 30) 로 토큰 효율 극대화
  - 증분 저장 (work/<game>/converted/dialogue_translations_en.json, HERO_GAME default h3)
  - 이미 번역된 항목은 skip (idempotent)

비용 추정:
  9,741 unique × ~12 char = ~110K input tokens
  + cached system prompt × 325 batches = (캐시 적중 시 90% 할인)
  + ~110K output tokens
  Haiku 4.5: $1.00 / $5.00 per 1M tokens
  ≈ $0.66 first run (캐시 적중 시 더 저렴)

사용:
  export ANTHROPIC_API_KEY=...
  python translate_dialogues.py [--limit N] [--batch-size 30] [--dry-run]
"""
from __future__ import annotations
import argparse, json, os, pathlib, sys
from typing import Iterable

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _game import select  # noqa: E402

_g = select()
CORPUS = _g.converted_root / 'dialogue_corpus.json'
OUT = _g.converted_root / 'dialogue_translations_en.json'

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from translation_dict import for_game  # noqa: E402


# 게임별 system prompt 의 게임 식별 문구. 게임 추가 시 여기만 추가.
GAME_HEADERS = {
    'h3': (
        '"영웅서기3 - 운명의수레바퀴" (Hero3 - Wheel of Destiny), a 2008 Korean RPG.\n'
        'The game is a fantasy story about Soltian and Askran factions, the Guardians, '
        'and a Masked Swordsman, set in the world of NEOSOLTIA.'
    ),
    'h4': (
        '"영웅서기4 - 환영의검" (Hero4 - Sword of Illusion), the 2009 sequel by Hanbit Soft.\n'
        'The game features a Celtic-mythology themed world: the four treasure cities of the '
        'Tuatha Dé Danann (Murias, Findias, Falias, Gorias) and surrounding islands '
        '(Wheel Island, Meadow Hill, Annwn Isle, Blackrock/Silverrock Isle, etc).'
    ),
}


def build_system_prompt() -> str:
    bundle = for_game(_g.id)
    char_lines = '\n'.join(f'  {ko} → {en}' for ko, en in bundle['characters'].items()) or '  (none yet — verify after corpus is decoded)'
    place_lines = '\n'.join(f'  {ko} → {en}' for ko, en in bundle['places'].items())
    common_lines = '\n'.join(f'  {ko} → {en}' for ko, en in bundle['common_words'].items())
    header = GAME_HEADERS.get(_g.id, f'a Korean RPG (game id: {_g.id}).')
    return f"""You are a professional Korean→English translator for {header}

# CRITICAL RULES

1. Translate naturally as English game dialogue — preserve tone (exclamations, ellipses, dramatic phrasing).
2. Use the canonical names from the dictionary below — never re-romanize them.
3. Each input is a SHORT NPC line, item name, or dialogue snippet. Some are single words; some are full sentences.
4. Output ONLY the translation. No quotation marks, no explanations, no original Korean.
5. If a snippet is meaningless (single particle, fragment), translate as best you can without leaving Korean.
6. Preserve special tokens: numbers, punctuation, spacing.
7. Untranslatable proper nouns: keep transliteration consistent across responses.

# CHARACTER NAMES (canonical romanization)
{char_lines}

# PLACES (canonical English names)
{place_lines}

# COMMON WORDS / GAME TERMS (preferred translation)
{common_lines}

# OUTPUT FORMAT
You will receive a JSON array of strings.
Respond with a JSON array of the same length where each element is the English translation in the same order.
No other text — JSON only."""


def load_corpus() -> list[str]:
    data = json.loads(CORPUS.read_text(encoding='utf-8'))
    seen = set()
    unique = []
    for line in data['lines']:
        t = line['text']
        if t not in seen:
            seen.add(t)
            unique.append(t)
    return unique


def load_existing() -> dict[str, str]:
    if not OUT.exists():
        return {}
    return json.loads(OUT.read_text(encoding='utf-8'))


def save_translations(translations: dict[str, str]):
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(translations, ensure_ascii=False, indent=2), encoding='utf-8')


def chunk(items: list[str], size: int) -> Iterable[list[str]]:
    for i in range(0, len(items), size):
        yield items[i:i + size]


def translate_batch(client, system_prompt: str, batch: list[str]) -> list[str] | None:
    """Claude Haiku 4.5 로 배치 번역. JSON array 응답 기대."""
    user_msg = json.dumps(batch, ensure_ascii=False)
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=4096,
        system=[{
            "type": "text",
            "text": system_prompt,
            "cache_control": {"type": "ephemeral", "ttl": "1h"},
        }],
        messages=[{"role": "user", "content": user_msg}],
    )
    text = ''.join(b.text for b in response.content if b.type == 'text').strip()

    # JSON 파싱 시도. 일부 LLM은 markdown code fence 를 추가하므로 제거.
    if text.startswith('```'):
        text = text.split('```', 2)[1]
        if text.startswith('json'):
            text = text[4:]
        text = text.strip()
    try:
        result = json.loads(text)
    except json.JSONDecodeError as e:
        print(f'  JSON parse error: {e}', file=sys.stderr)
        print(f'  Raw response: {text[:200]}', file=sys.stderr)
        return None
    if not isinstance(result, list) or len(result) != len(batch):
        print(f'  size mismatch: expected {len(batch)}, got {len(result) if isinstance(result, list) else type(result)}',
              file=sys.stderr)
        return None
    return [str(x) for x in result]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--limit', type=int, default=None,
                    help='상위 N개만 번역 (테스트용)')
    ap.add_argument('--batch-size', type=int, default=30,
                    help='배치당 텍스트 개수')
    ap.add_argument('--dry-run', action='store_true',
                    help='API 호출 없이 system prompt 만 출력')
    args = ap.parse_args()

    if not CORPUS.exists():
        print(f'MISSING: {CORPUS}', file=sys.stderr)
        return 1

    unique_texts = load_corpus()
    existing = load_existing()
    print(f'Total unique: {len(unique_texts)}')
    print(f'Already translated: {len(existing)}')
    todo = [t for t in unique_texts if t not in existing]
    if args.limit is not None:
        todo = todo[:args.limit]
    print(f'To translate: {len(todo)}')

    system_prompt = build_system_prompt()
    if args.dry_run:
        print('\n=== SYSTEM PROMPT ===')
        print(system_prompt)
        return 0

    if not todo:
        print('Nothing to do.')
        return 0

    if not os.environ.get('ANTHROPIC_API_KEY'):
        print('ERROR: ANTHROPIC_API_KEY not set', file=sys.stderr)
        return 2

    try:
        import anthropic
    except ImportError:
        print('Install: pip install anthropic', file=sys.stderr)
        return 2

    client = anthropic.Anthropic()
    total = len(todo)
    done = 0
    failed: list[str] = []

    for batch in chunk(todo, args.batch_size):
        translations = translate_batch(client, system_prompt, batch)
        if translations is None:
            print(f'  batch failed (skipping {len(batch)} items)')
            failed.extend(batch)
            done += len(batch)
            continue
        for ko, en in zip(batch, translations):
            existing[ko] = en
        done += len(batch)
        # 5 배치마다 저장
        if done % (args.batch_size * 5) == 0:
            save_translations(existing)
            print(f'  progress: {done}/{total} ({done*100//total}%)')

    save_translations(existing)
    print(f'\nDone: {done} processed, {len(failed)} failed')
    print(f'Saved: {OUT}')
    if failed:
        print(f'Failed samples: {failed[:5]}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
