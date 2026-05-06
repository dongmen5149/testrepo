"""recon TARGETS 게임-aware 로더.

extract_strings.py --json 으로 dump 한 `string_offsets.json` 을 읽어
{offset(int): label(str)} dict + code_end_estimate 를 제공.

사용:
    from _targets import load_targets
    targets, code_end = load_targets()              # 현재 게임 (HERO_GAME)
    targets, code_end = load_targets(priority_only=True)  # 우선순위 라벨만

JSON 이 없으면 FileNotFoundError — 먼저:
    HERO_GAME=h4 python tools/recon/extract_strings.py --json work/h4/converted/string_offsets.json --quiet
"""
from __future__ import annotations
import json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _game import select, Game  # noqa: E402


# 우선순위가 높은 라벨 keyword (분석 첫 단계에서 잡고 싶은 핵심 string).
# 이 키워드 중 하나라도 포함하는 라벨만 남기는 모드.
PRIORITY_KEYWORDS = (
    'frameBuf', 'Font', 'NULL', 'Not Found', 'not loaded',
    'onEvent', 'eventIdx',
)


def targets_json_path(g: Game) -> pathlib.Path:
    return g.converted_root / 'string_offsets.json'


def load_targets(game_id: str | None = None, priority_only: bool = False) -> tuple[dict[int, str], int]:
    g = select(game_id)
    p = targets_json_path(g)
    if not p.exists():
        raise FileNotFoundError(
            f'{p} 없음. 먼저 다음 실행:\n'
            f'  HERO_GAME={g.id} python tools/recon/extract_strings.py --json {p} --quiet'
        )
    payload = json.loads(p.read_text(encoding='utf-8'))
    raw: dict[str, str] = payload['targets']
    targets = {int(k, 16): v for k, v in raw.items()}
    if priority_only:
        targets = {
            o: s for o, s in targets.items()
            if any(kw.lower() in s.lower() for kw in PRIORITY_KEYWORDS)
        }
    code_end = int(payload.get('code_end_estimate', 0)) or 0
    return targets, code_end
