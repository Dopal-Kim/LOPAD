# -*- coding: utf-8 -*-
"""
61라운드 P11 — 믹싱 권장값(manifest `mixing`)과 효과음 우선순위 계산.

build.write_manifest() 가 부른다. 시스템이 이 값을 읽어 적용한다(권장 — 확정은 시스템 구현 후 데모 청취로 다듬는다).
우선순위: 보스 신호(예고) 4 > 피격·방어 판정 3 > 타격·공격 2 > 환경·획득·부가음 1, UI 0(별도 버스).
"""

TIERS = [
    dict(level=4, name='telegraph', label='보스 예고·보스 신호·무기 각성(61-4)',
         events=['BOSS_TELEGRAPH', 'BOSS_STARTED', 'BOSS_PHASE', 'BOSS_DIED', 'boss:intro',
                 'BOSS_ACTION{action:introRoar}', 'WEAPON_AWAKEN']),
    dict(level=3, name='hurt', label='주인공 피격·방어 판정·적 공격 예고·보스 파훼(61-2)',
         events=['PLAYER_DAMAGED', 'PARRY_SUCCESS', 'PERFECT_GUARD', 'PERFECT_SUCCESS', 'ENEMY_TELEGRAPH', 'RUN_ENDED',
                 'BOSS_BREAK', 'ui:boss-break', 'BOSS_ACTION{action:cupStruck}', 'BOSS_ACTION{action:pillarCrack}']),
    dict(level=2, name='hit', label='타격·처치·공격 동작(주인공·적·보스)',
         events=['(그 밖의 combat·boss 분류)']),
    dict(level=1, name='ambient', label='환경·획득·이벤트·패시브·상태 부가음',
         events=['PASSIVE_PROC', 'STATUS_CHANGED', 'BOSS_ACTION{action:flameSnuff}', '(world·pickup·event 분류)']),
    dict(level=0, name='ui', label='UI — 별도 버스, 상한·빼앗기 대상 아님', events=['UI_MENU_*', '(ui 분류)']),
]
_EV = {ev: t['level'] for t in TIERS for ev in t['events'] if not ev.startswith('(')}
# 61-4: 같은 이벤트 안에서 조건 하나로 등급이 갈리는 것(BOSS_ACTION 의 action) — 'EVENT{키:값}' 꼴로 위 표에 적는다.
_AMBIENT_EVENTS = {'PASSIVE_PROC', 'STATUS_CHANGED'}


def priority(spec, event, when=()):
    """효과음 하나의 우선순위(0~4). spec = SFX 항목(변주는 원본 spec), event = 트리거 이벤트 이름,
    when = 조건 목록('키:값') — 'EVENT{키:값}' 항목(61-4 BOSS_ACTION action)이 있으면 그것이 먼저."""
    if spec['category'] == 'ui':
        return 0
    for c in when or ():
        if '%s{%s}' % (event, c) in _EV:
            return _EV['%s{%s}' % (event, c)]
    if event in _EV:
        return _EV[event]
    if spec['category'] in ('combat', 'boss'):
        return 1 if event in _AMBIENT_EVENTS else 2
    return 1


def settings(variant_groups):
    """manifest `mixing` 에 덧붙일 61라운드 권장값. variant_groups = {원본 id: [원본 id, 변주 id ...]}."""
    return dict(
        dedupeMs=20,
        voices=dict(
            maxSfx=12, maxUi=2, perGroupMax=3,
            perGroupOverrides={'sfx/hit_enemy': 4, 'sfx/hit_enemy_crit': 2, 'sfx/enemy_death': 3,
                               'sfx/hit_player': 2, 'sfx/dash': 1, 'sfx/swing_katana': 2,
                               'sfx/swing_greatsword': 2, 'sfx/swing_dagger': 3, 'sfx/bow_shot': 3,
                               'sfx/pickup_gold': 3, 'sfx/guard_block': 2, 'sfx/parry': 1,
                               'sfx/combo_finish': 1, 'sfx/guard_block_heavy': 2, 'sfx/peddler_hurt': 2,
                               'sfx/porter_hurt': 2, 'sfx/barrel_return': 2,
                               'sfx/boss1_flame_snuff': 4, 'sfx/boss1_cup_struck': 2},
            steal='lowest-priority-oldest',
            note='동시 재생 상한. maxSfx 를 넘으면 새 소리보다 우선순위가 낮거나 같은 목소리 중 가장 오래된 것을 '
                 '30 ms 페이드로 끊는다. 모두 더 높으면 새 소리를 버린다. 그룹 = 원본 id(변주 포함, variants). '
                 'loop 항목은 빼앗지 않는다(상태가 끝날 때 시스템이 멈춤) — 대신 같은 id 는 1개만. UI 는 별도 상한 maxUi.'),
        priority=dict(
            tiers=TIERS,
            note='각 효과음 항목의 priority 필드에 이미 계산돼 있다(변주는 원본과 같음). 숫자가 클수록 먼저.'),
        ducking=[
            dict(when='priority 4 재생 시작', target='sfx priority ≤ 2', db=-6.0, attackMs=15, releaseMs=250,
                 hold='그 소리 길이 동안', note='보스 예고음이 묻히지 않게'),
            dict(when='priority 4 재생 시작', target='bgm', db=-3.0, attackMs=30, releaseMs=400,
                 hold='그 소리 길이 동안', note='bgmBossDuckDb 위에 더해짐'),
            dict(when='sfx/hit_player 그룹 재생', target='sfx priority ≤ 2', db=-3.0, attackMs=5, releaseMs=180,
                 hold='150 ms', note='맞은 순간이 또렷하게'),
            dict(when='파훼 소리 재생(boss1_break_*·break_finisher)', target='sfx priority ≤ 2', db=-4.0,
                 attackMs=5, releaseMs=300, hold='300 ms',
                 note='61-2: 트리거 ui:boss-break(break_count 는 제외) · 파훼·결정타의 손맛 — 그 순간 타격·휘두름을 잠깐 눌러 한 방이 앞에 서게'),
        ],
        variation=dict(
            policy='random-no-repeat',
            rateJitter=0.03,
            applyTo='priority 1~3 의 짧은 효과음(loop·UI·BGM 제외)',
            note='원본 트리거가 오면 variants 목록에서 직전과 다른 하나를 고르고, 재생 속도를 1 ± rateJitter 로 '
                 '흔든다(피치 ±약 50 cent). 변주 없는 소리도 rateJitter 만 적용 — 같은 소리 반복 피로를 줄인다. '
                 '이전 권장(±4 %)을 ±3 % 로 줄임(변주가 생겨서).'),
        masterLimiter=dict(thresholdDb=-3.0, kneeDb=6.0, ratio=12.0, attackMs=3, releaseMs=120,
                           note='Web Audio DynamicsCompressorNode 를 마스터 끝에 하나. 61라운드 타격음이 같은 피크에서 '
                                '짧은 구간 음량이 커져(약 +4~7 dB) 몰릴 때 찌그러짐을 막는다.'),
        bgmPhaseCrossfadeMs=800,
        bgmPhaseSyncPosition=True,
        bgmPhaseNote='bgmByFloorState[층].bossPhases 의 곡들은 길이·박자 격자가 같다. BOSS_PHASE 에서 다음 곡을 '
                     '지금 곡의 재생 위치(초)에서 시작해 bgmPhaseCrossfadeMs 로 교차 페이드하면 층이 더해지는 것처럼 '
                     '들린다. 위치를 못 맞추면 처음부터 + bgmCrossfadeMs 로 바꿔도 된다.',
        bgmJourneyNote='bgmByFloorState[층].journey = 그 층의 전투 전 여정(벽 밖 · 탄생지 · 버려진 길 · 국경 초소)과 '
                       '휴식·지도 화면. 전투 노드에 들어가면 bgmByFloor[층](= combat)으로 bgmCrossfadeMs 교차 페이드.',
        bgmBossDefeat=dict(
            fadeOutOn='BOSS_DIED', fadeOutMs=900, silentUntil='EXIT_OPENED', resume='floorState',
            note='61라운드: 보스 처치(BOSS_DIED)에서 보스 곡을 900 ms 페이드아웃 → 보상 메뉴가 끝나 출구가 열릴 때'
                 '(EXIT_OPENED)까지 BGM 정적(효과음 boss1_die·break_finisher 만 들림) → 그 층 곡으로 복귀'
                 '(bgmByFloorState[층] 의 현재 상태 곡, 없으면 bgmByFloor[층]). 복귀는 교차가 아니라 bgmCrossfadeMs 페이드인.'),
        variantGroups=variant_groups,
    )
