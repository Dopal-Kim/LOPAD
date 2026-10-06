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
    dict(level=3, name='hurt', label='주인공 피격·방어 판정·적 공격 예고·보스 파훼(61-2)·기둥 무너짐·포물선 술병(61-5)·'
                                   '그림 속 입구 전환·수련장 도장(61-6)',
         events=['PLAYER_DAMAGED', 'PARRY_SUCCESS', 'PERFECT_GUARD', 'PERFECT_SUCCESS', 'ENEMY_TELEGRAPH', 'RUN_ENDED',
                 'BOSS_BREAK', 'ui:boss-break', 'BOSS_ACTION{action:cupStruck}', 'BOSS_ACTION{action:pillarCrack}',
                 'BOSS_ACTION{action:pillarCollapse}', 'BOSS_ACTION{action:lobThrow}',
                 'TRANSITION_BEGIN', 'TRAINING_STAMP']),
    dict(level=2, name='hit', label='타격·처치·공격 동작(주인공·적·보스)·공명 켜짐(61-5)·수련장 과제 완료(61-6)',
         events=['RESONANCE_ON', 'TRAINING_TASK', '(그 밖의 combat·boss 분류)']),
    dict(level=1, name='ambient', label='환경·획득(바닥 줍기 61-5 포함)·이벤트·패시브·상태 부가음·개성 발동 특색 층(61-5)',
         events=['PASSIVE_PROC', 'STATUS_CHANGED', 'BOSS_ACTION{action:flameSnuff}', 'PICKUP_LANDED', 'PICKUP_COLLECTED',
                 'TRAIT_PROC',
                 '(world·pickup·event 분류)']),
    dict(level=0, name='ui', label='UI — 별도 버스, 상한·빼앗기 대상 아님', events=['UI_MENU_*', '(ui 분류)']),
]
# 61-5 P13 개성 발동 행동 갈래(계약 sound §11 — 'move' 는 소리 없음)
TRAIT_ACTS = ('launch', 'slam', 'pull', 'bind', 'clone', 'blink', 'wave', 'throw', 'rain', 'ignite', 'deflect',
              'shield', 'spin', 'mark', 'burst')
_EV = {ev: t['level'] for t in TIERS for ev in t['events'] if not ev.startswith('(')}
# 61-4: 같은 이벤트 안에서 조건 하나로 등급이 갈리는 것(BOSS_ACTION 의 action) — 'EVENT{키:값}' 꼴로 위 표에 적는다.
_AMBIENT_EVENTS = {'PASSIVE_PROC', 'STATUS_CHANGED', 'TRAIT_PROC'}


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
                               'sfx/boss1_flame_snuff': 4, 'sfx/boss1_cup_struck': 2,
                               'sfx/voucher_drop': 3, 'sfx/voucher_pickup': 3, 'sfx/item_pickup': 2,
                               'sfx/boss1_pillar_collapse': 1, 'sfx/boss1_lob_bottle': 1,
                               **{'sfx/trait_%s' % a: 2 for a in TRAIT_ACTS},
                               'sfx/resonance_proc': 2, 'sfx/resonance_on': 1,
                               'sfx/transition_enter': 1, 'sfx/transition_exit': 1, 'sfx/transition_floor': 1,
                               'sfx/training_task': 2, 'sfx/training_stamp': 1},
            layerMax=dict(ids=['sfx/trait_%s' % a for a in TRAIT_ACTS], match='TRAIT_PROC 로 재생된 소리', max=3,
                          note='61-5: 개성 발동 특색 층(TRAIT_PROC 로 고른 trait_<act> 15종 + 개성별 trait_<무기>_<id> 가 생기면 그것도 — '
                               'trait_manifest(TRAIT_GAINED)는 아님) 전체를 '
                               '합쳐 동시 3까지. 넘치면 같은 층에서 가장 오래된 것을 30 ms 페이드로 끊는다(우선순위 1 이라 '
                               'maxSfx 에서도 빼앗기 1순위). resonance_proc 은 이 층에 세지 않는다'),
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
            dict(when='파훼 소리 재생(boss1_break_*·break_finisher) · 기둥 무너짐(boss1_pillar_collapse, 61-5)',
                 target='sfx priority ≤ 2', db=-4.0, attackMs=5, releaseMs=300, hold='300 ms',
                 note='61-2: 트리거 ui:boss-break(break_count 는 제외) · 파훼·결정타의 손맛 — 그 순간 타격·휘두름을 잠깐 눌러 한 방이 앞에 서게. '
                      '61-5: 기둥 무너짐(BOSS_ACTION pillarCollapse)도 같은 규칙'),
            dict(when='sfx priority ≥ 2 재생 시작', target='sfx/voucher_drop·voucher_pickup·item_pickup', db=-4.0,
                 attackMs=10, releaseMs=200, hold='150 ms',
                 note='61-5: 바닥 줍기류는 낮게 — 전투음(타격·피격·예고)이 날 때 떨어짐·줍기 소리를 잠깐 더 누른다. '
                      '처치 직후 전표가 쏟아질 때 처치음이 먼저 들리게(줍기류 priority 1 · 빼앗기 1순위)'),
            dict(when='전환음 재생(transition_enter·transition_exit·transition_floor, 61-6)', target='sfx priority ≤ 2',
                 db=-8.0, attackMs=40, releaseMs=300, hold='그 소리 길이 동안',
                 note='61-6: 그림 속 입구로 넘어가는 동안 남은 전투·줍기·개성 꼬리를 눌러 전환음이 앞에 서게. '
                      '줍기류(priority 1)는 위 줍기 규칙(−4 dB)과 겹치면 더 낮은 값 하나만(−8 dB)'),
            dict(when='전환음 재생(transition_enter·transition_exit·transition_floor) — BGM', target='bgm', db=-4.0, attackMs=60, releaseMs=500,
                 hold='그 소리 길이 동안',
                 note='61-6: 곡이 바뀌는 전환이면 시스템의 BGM 교차 페이드(bgmCrossfadeMs)를 이 덕킹 위에서 진행 — '
                      '새 곡이 들어올 때 덕킹이 풀리며(releaseMs) 방이 열리는 느낌. 같은 곡이 이어지면 덕킹만'),
            dict(when='sfx/training_stamp 재생', target='sfx priority ≤ 1', db=-4.0, attackMs=5, releaseMs=250,
                 hold='300 ms', note='61-6: 도장 순간이 또렷하게(같은 때 울린 마지막 과제 종 training_task 는 priority 2 라 눌리지 않음)'),
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
        transition=dict(
            skipFadeMs=150,
            note='61-6 그림 속 입구 전환(TRANSITION_BEGIN): 연출을 건너뛰면(아무 키) 재생 중인 전환음을 skipFadeMs 로 '
                 '페이드아웃(뚝 끊지 않음). mode floor 는 transition_floor 하나만(없으면 transition_enter) — 둘을 겹치지 않는다. '
                 '전환음은 시간 축이 UI 연출에 맞춰져 있다: enter 1.10 s · floor 1.22 s 에 어둠이 덮이고 그 뒤 붓질이 걷힘, '
                 'exit 0.95 s 에 액자 닫힘 — 연출 시작과 같은 순간에 재생.'),
        variantGroups=variant_groups,
    )
