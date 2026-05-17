"""
캐릭터·지명·UI 어휘 한↔영 대응 사전.

InGame_txt 196개 UI 어휘 + dialogue_corpus Top 200 빈도 텍스트를 베이스로
수동 번역한 영문 표기. 추후 일본어/중국어 추가 시 같은 구조 사용.

이 사전은 Android values-en/strings.xml 생성의 source 입니다.

게임별 지명/캐릭터는 PLACES_H3, PLACES_H4 등으로 분리. `for_game(id)` 로 묶음 조회.
"""
from __future__ import annotations

# ─────────────────────────────────────────────────
# Hero3 캐릭터 이름 (Top 200 빈도 기반)
# ─────────────────────────────────────────────────
CHARACTERS_H3 = {
    '케이':       'Kei',
    '리츠':       'Ritz',
    '리치':       'Litch',     # char_dat 의 다른 표기
    '일레느':     'Ilene',
    '시엔':       'Sien',
    '레아':       'Lea',
    '엘지스':     'Elgis',
    '케네스':     'Kenneth',
    '이안':       'Ian',
    '멜페토':     'Melpheto',
    '토레즈':     'Torez',
    '듀크':       'Duke',
}

# 하위 호환 alias — 외부 import 가 CHARACTERS 를 직접 쓰는 경우.
CHARACTERS = CHARACTERS_H3

# ─────────────────────────────────────────────────
# Hero4 캐릭터 이름
#
# Source: e0185_scn (348/350 SCN 이 DES 암호화됐으나 2개는 plaintext —
# 이 중 e0185 가 글로벌 entity catalog 역할). 한국어→영문 transliterate.
# 켈트 신화 Tuatha Dé Danann 의 인물명 다수 (Nuada, Nodens, Deirdre 등).
# 영문은 한국어 발음 + 켈트 신화 표기 우선.
# ─────────────────────────────────────────────────
CHARACTERS_H4: dict[str, str] = {
    # 주인공 / 핵심 NPC (켈트 신화 인물명 우선)
    '앨리스':       'Alice',
    '브리안':       'Brian',
    '크래드':       'Crad',
    '디어드리':     'Deirdre',     # 켈트 비극 영웅
    '엘렌':         'Ellen',
    '엔리코':       'Enrico',
    '에리나':       'Erina',
    '그라함':       'Graham',
    '이자벨':       'Isabel',
    '케프네스':     'Kephness',
    '래비':         'Rabbie',
    '루칸':         'Lucan',
    '루레인':       'Lorraine',
    '노덴스':       'Nodens',      # 켈트 신화 신
    '누아다':       'Nuada',       # Tuatha Dé Danann 첫째 왕
    '정상팔':       'Jung Sangpal',
    '티르':         'Tyr',         # 켈트 신 (북유럽과 어원 공유)
    '찌질이':       'Loser',       # 별명 캐릭터
    '브레스':       'Bres',        # 켈트 신화 인물

    # NPC 분류 (역할 라벨, dialogue 에 자주 등장)
    '인간':         'Human',
    '선주':         'Sailor',      # 선주 = 배 소유주 / 선원
    '꼬마':         'Kid',
    '여자':         'Woman',
    '남자':         'Man',
    '병사':         'Soldier',
    '선장':         'Captain',
    '엔지니어':     'Engineer',
    '노인':         'Elder',
    '상점':         'Merchant',
    '대장장이':     'Blacksmith',
    '연금술사':     'Alchemist',
    '소환술사':     'Summoner',
    '연구원':       'Researcher',
    '도둑':         'Thief',
    '괴물':         'Monster',
    '소환수':       'Summon',
    '시체':         'Corpse',
    '여관':         'Inn',
    '매니져':       'Manager',

    # 게임 객체 / 상태 (이벤트 트리거)
    '출구':         'Exit',
    '결계':         'Barrier',
    '블라인드':     'Blind',
    '빠이아':       'Faia',
    '나뭇잎':       'Leaf',
    '바위':         'Rock',
    '햇빛':         'Sunlight',
    '게이트':       'Gate',
    '대미지':       'Damage',
    '죽음':         'Death',
    '넉백':         'Knockback',
    '스트레이츠':   'Straits',
    '정체불명의':   'Mysterious',
}

# ─────────────────────────────────────────────────
# Hero3 지명 (맵 + 대사)
# ─────────────────────────────────────────────────
PLACES_H3 = {
    '솔티아':       'Soltia',
    'NEOSOLTIA':    'Neo Soltia',
    'SECRET_ROOM':  'Secret Room',
    'BOSS_TOWN':    'Boss Town',
    'RETIREMENT':   'Retirement',
    'CORE_OF_RUIN': 'Core of Ruin',
    'GUARDIAN_CAVE_1': 'Guardian Cave 1',
    'GUARDIAN_CAVE_2': 'Guardian Cave 2',
    'GUARDIAN_CAVE_3': 'Guardian Cave 3',
    'GUARDIAN_CAVE_4': 'Guardian Cave 4',
    'GUARDIAN_CAVE_5': 'Guardian Cave 5',
    'GUARDIAN_CAVE_6': 'Guardian Cave 6',
    'GUARDIAN_CAVE_7': 'Guardian Cave 7',
    'RUINED_DESERT_1': 'Ruined Desert 1',
    'RUINED_DESERT_2': 'Ruined Desert 2',
    'RUINED_DESERT_3': 'Ruined Desert 3',
    'GULBEIG_RUIN_5':  'Gulbeig Ruin 5',
    'GULBEIG_RUIN_6':  'Gulbeig Ruin 6',
    'GULBEIG_RUIN_7':  'Gulbeig Ruin 7',
    'GULBEIG_ROOM':    'Gulbeig Room',
    'WAR_OF_RUIN_1':   'War of Ruin 1',
    'WAR_OF_RUIN_2':   'War of Ruin 2',
    'NEMESIS_FOREST_5': 'Nemesis Forest 5',
    'BEAST_FOREST_1':  'Beast Forest 1',
    'BEAST_FOREST_2':  'Beast Forest 2',
    'BEAST_FOREST_3':  'Beast Forest 3',
    'UNDER_CAVE_1':    'Under Cave 1',
    'UNDER_CAVE_2':    'Under Cave 2',
    'UNDER_CAVE_3':    'Under Cave 3',
    'SMALL_CAVE_1':    'Small Cave 1',
    'SMALL_FACTORY_4': 'Small Factory 4',
}

# 하위 호환 alias.
PLACES = PLACES_H3

# ─────────────────────────────────────────────────
# Hero4 지명
#
# 켈트 신화 Tuatha Dé Danann 의 4 보물 도시 (뮤리아스/핀디아스/팔리아스/고리아스)
# 가 게임 zone 이름의 baseline. 나머지는 PROGRESS.md 에서 확인된 한국어 zone.
# corpus 풀리면 추가/검증.
# ─────────────────────────────────────────────────
PLACES_H4 = {
    '뮤리아스':         'Murias',         # 켈트 신화 4 보물 도시 그대로 transliterate
    '핀디아스':         'Findias',
    '팔리아스':         'Falias',
    '고리아스':         'Gorias',
    '수레바퀴섬':       'Wheel Island',
    '매도우힐':         'Meadow Hill',
    '이름없는섬':       'Nameless Isle',
    '아눈섬':           'Annwn Isle',     # 켈트 신화 저승 'Annwn'
    '검은바위섬':       'Blackrock Isle',
    '은바위섬':         'Silverrock Isle',
    '해적소굴':         'Pirate Den',
    '환영의검':         'Sword of Illusion',  # 부제 "영웅서기4 - 환영의검"
}

# ─────────────────────────────────────────────────
# UI 어휘 (InGame_txt.json 196개의 한국어 → 영어)
# 인덱스 0~6 은 이미 영어이므로 그대로, 7+ 한국어 번역
# ─────────────────────────────────────────────────
UI_VOCAB = {
    # 메인 메뉴 (이미 영어)
    'MENU':       'MENU',
    'STATUS':     'STATUS',
    'INVENTORY':  'INVENTORY',
    'EQUIPMENT':  'EQUIPMENT',
    'SKILL':      'SKILL',
    'QUEST':      'QUEST',
    'SYSTEM':     'SYSTEM',

    # 메뉴 항목
    '상태보기':       'View Status',
    '가방':           'Bag',
    '장비':           'Equipment',
    '스킬':           'Skill',
    '퀘스트':         'Quest',
    '시스템':         'System',
    '세이브':         'Save',
    '네트워크등록':   'Network Register',
    '환경설정':       'Settings',
    '도움말':         'Help',
    '이름':           'Name',
    '효과':           'Effect',
    '기타':           'Etc',

    # 무기 종류
    '스피어':     'Spear',
    '스워드':     'Sword',
    '나이프':     'Knife',
    '건':         'Gun',
    '라이플':     'Rifle',
    '케논':       'Cannon',
    '다크':       'Dark',
    '홀리':       'Holy',
    '다크스톤':   'Dark Stone',
    '홀리스톤':   'Holy Stone',
    '방패':       'Shield',
    '장신구':     'Accessory',

    # 스킬 분류
    '액티브':     'Active',
    '패시브':     'Passive',

    # 콤보·쿨타임
    '현재콤보단계:': 'Current Combo Level:',
    '쿨타임:':       'Cooldown:',
    '지속시간:':     'Duration:',

    # 액션
    '상세보기':   'Details',
    '사용하기':   'Use',
    '버리기':     'Drop',
    '1키등록':    'Register Key 1',
    '3키등록':    'Register Key 3',
    '9키등록':    'Register Key 9',
    '0키등록':    'Register Key 0',
    '#키등록':    'Register Key #',
    '등록취소':   'Cancel Registration',
    '등록해제':   'Unregister',

    # 아이템 종류
    '물약':           'Potion',
    '조합재료':       'Crafting Material',
    '제련석':         'Smelting Stone',
    '오브결합':       'Orb Combine',
    '의조합설명서':   ' Combination Manual',  # 'X의 조합 설명서'
    '네트워크 대전 전용': 'Network Battle Only',
    '퀘스트 아이템': 'Quest Item',

    # 액션 (계속)
    '올리기':         'Move Up',
    '내리기':         'Move Down',

    # 스탯 효과 (성능 강화 항목)
    '성능 +':         'Performance +',
    'HP +':           'HP +',
    'HPMAX +':        'Max HP +',
    'HP회복 +':       'HP Regen +',
    'SP+':            'SP +',
    'SP회복 +':       'SP Regen +',
    'SP소모 -':       'SP Cost -',
    'HP흡수 +':       'HP Absorb +',
    '쿨타임 -':       'Cooldown -',
    '물리공격 +':     'P.ATK +',
    '특수공격 +':     'M.ATK +',
    '물리방어 +':     'P.DEF +',
    '특수방어 +':     'M.DEF +',
    '명중 +':         'ACC +',
    '회피 +':         'DOD +',
    '방패 +':         'Shield +',
    '방패무시 +':     'Shield Pierce +',
    '기절 +':         'Stun +',
    '저항 +':         'Resist +',
    '힘 +':           'STR +',
    '체력 +':         'VIT +',
    '정신 +':         'INT +',
    '민첩 +':         'DEX +',

    # 모드/스킬
    '지축모드':       'Pivot Mode',
    '은신모드':       'Stealth Mode',
    '공격유도':       'Attack Guide',
    '보조스킬해제':   'Cancel Aux Skill',
    '저주치료':       'Curse Cure',
    '로이동':         'Move To',
    'LV':             'LV',

    # 등급
    '노멀':           'Normal',
    '레어':           'Rare',
    '에픽':           'Epic',
    '영웅':           'Hero',

    # 아이템 종류
    '카드':           'Card',
    '조합서':         'Recipe',
    '오브':           'Orb',
    '퀘스트':         'Quest',
    '소모품':         'Consumable',
    '포인트투자':     'Invest Points',

    # 전용 표기
    '스워드/스피어전용': 'Sword/Spear Only',
    '건/라이플전용':     'Gun/Rifle Only',
    '다크/홀리스톤전용': 'Dark/Holy Stone Only',
    '방패전용':          'Shield Only',
    '나이프전용':        'Knife Only',
    '솔티아계열전용':    'Soltia Class Only',
    '아스크라계열전용':  'Askra Class Only',

    # 슬롯/메시지
    '빈슬롯':                       'Empty Slot',
    '장착가능한 장비가 없습니다.':  'No equippable items.',
    '장비장착':                     'Equip',
    '장비해제':                     'Unequip',
    '예':                           'Yes',
    '아니오':                       'No',
    '장비를 해제하시겠습니까?':     'Unequip this item?',
    '확인':                         'Confirm',
    '장비를 장착할수 없습니다.':    'Cannot equip this item.',
    '인벤토리가 부족하여 이벤트를 실행할 수 없습니다.': 'Inventory full, cannot proceed.',
    '이벤트 실행에 필요한 아이템이 부족합니다.':       'Required items missing.',
    '소지금이 부족합니다.':         'Not enough gold.',
    '개수를 설정하세요':            'Set quantity',
    '구매하시겠습니까?':            'Purchase?',
    '아이템 구매':                  'Buy Item',
    '아이템 판매':                  'Sell Item',
    '방어구':                       'Armor',
    '무기':                         'Weapon',
    '구매하였습니다':               'Purchased',
    '판매하였습니다':               'Sold',
    '메인메뉴':                     'Main Menu',
    '판매하시겠습니까?':            'Sell?',
    '저장하시겠습니까?':            'Save?',
    '저장하였습니다':               'Saved',
    '아이템을 팔 수 없습니다':      'Cannot sell this item',
    '귀환장소를 선택하세요':        'Select return point',
    '토레즈':                       'Torez',

    # 지명 (UI 어휘에 등장)
    '네오 솔티아':                  'Neo Soltia',
    '로우엔':                       'Lowen',
    '솔티안 주둔지':                'Soltian Garrison',
    '아스크란 주둔지':              'Askran Garrison',
    '솔티아 은거지':                'Soltia Hideout',

    # 추가 메시지
    '귀환서를 사용할수 없는 퀘스트 진행중입니다': 'Cannot use return scroll during this quest',
    '최근 귀환장소로 이동하겠습니까?': 'Travel to last return point?',
    '이미 장착중입니다.':           'Already equipped.',
    '버릴수 없는 아이템입니다.':    'Cannot drop this item.',
    '저장할 수 없는 지역입니다':    'Cannot save in this area',
    '인벤토리가 부족합니다':        'Inventory full',
    '메인메뉴로 나가시겠습니까?':   'Return to Main Menu?',
    '부활하시겠습니까?':            'Revive?',
    '하드코어 모드로;재시작합니다': 'Restart in Hardcore Mode',
    '인벤토리가 가득 차서 사용할 수 없습니다.': 'Inventory full, cannot use.',
    '무기제한 없음':                'No weapon restriction',
    '전사계열 전용':                'Warrior Class Only',
    '총기계열 전용':                'Gunner Class Only',
    '법사계열 전용':                'Mage Class Only',
    '방어계열 전용':                'Defender Class Only',
    '회피계열 전용':                'Evader Class Only',
    '솔티안 전용':                  'Soltian Only',
    '아스크란 전용':                'Askran Only',
    '오브를 입수 하였습니다.':      'Orb obtained.',

    # 접두 마법 효과 (@투신의 = "of God of War")
    '@투신의':       'of War God',
    '@공명의':       'of Resonance',
    '@뇌제의':       'of Thunder Emperor',
    '@금강의':       'of Diamond',
    '@정령의':       'of Spirit',
    '@사신의':       'of Reaper',
    '@영제의':       'of Soul Emperor',
    '@철벽의':       'of Iron Wall',
    '@속박의':       'of Binding',
    '@결의의':       'of Resolve',
    '@현자의':       'of Sage',
    '@마도의':       'of Sorcery',
    '@흡혈의':       'of Vampire',
    '@폭풍의':       'of Storm',
    '@직격의':       'of Direct Hit',

    # 장비 부위
    '투구':           'Helmet',
    '갑옷':           'Armor',
    '장갑':           'Gloves',
    '신발':           'Boots',

    # 스탯
    '힘':             'STR',
    '민첩':           'DEX',
    '체력':           'VIT',
    '정신':           'INT',
    'HP':             'HP',
    'MP':             'MP',
    'SP':             'SP',
    'EXP':            'EXP',
    'ATT1':           'ATT1',
    'ATT2':           'ATT2',
    'P.DEF':          'P.DEF',
    'M.DEF':          'M.DEF',
    'CRI':            'CRI',
    'RES':            'RES',
    'ACC':            'ACC',
    'DOD':            'DOD',
}

# ─────────────────────────────────────────────────
# 대사·키워드 (Top 200 빈도)
# ─────────────────────────────────────────────────
COMMON_WORDS = {
    '입수':       'Obtained',
    '완료':       'Complete',
    '내가':       'I',
    '있는':       'who is / which is',
    '있어':       'I have / there is',
    '얻었다':     'obtained',
    '멤버':       'Member',
    '그래':       'Right',
    '가디언의':   'Guardian\'s',
    '가디언':     'Guardian',
    '가면의검사': 'Masked Swordsman',
    '이제':       'Now',
    '정말':       'Really',
    '하지만':     'However',
    '전쟁을':     'the war',
    '솔티아의':   'Soltia\'s',
    '힘을':       'power',
    '무슨':       'what',
    '역시':       'as expected',
}


def for_game(game_id: str) -> dict[str, dict[str, str]]:
    """게임별 dict 묶음 반환. translate_dialogues.py 의 system prompt 빌더가 사용.

    UI_VOCAB / COMMON_WORDS 는 한빛 엔진 공유라 게임 무관 공통.
    """
    if game_id == 'h3':
        return {
            'characters': CHARACTERS_H3,
            'places': PLACES_H3,
            'ui_vocab': UI_VOCAB,
            'common_words': COMMON_WORDS,
        }
    if game_id == 'h4':
        return {
            'characters': CHARACTERS_H4,
            'places': PLACES_H4,
            'ui_vocab': UI_VOCAB,
            'common_words': COMMON_WORDS,
        }
    raise ValueError(f'Unknown game id: {game_id!r}')


def all_translations(game_id: str = 'h3') -> dict[str, str]:
    """모든 사전 통합 (game-aware). 인자 없으면 Hero3 default."""
    out = {}
    bundle = for_game(game_id)
    for d in bundle.values():
        out.update(d)
    return out


if __name__ == '__main__':
    import json, sys
    gid = sys.argv[1] if len(sys.argv) > 1 else 'h3'
    print(json.dumps(for_game(gid), ensure_ascii=False, indent=2))
