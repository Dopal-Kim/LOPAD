# -*- coding: utf-8 -*-
"""
61라운드 P11 — 믹싱 권장값(manifest `mixing`)과 효과음 우선순위 계산.

build.write_manifest() 가 부른다. 시스템이 이 값을 읽어 적용한다(권장 — 확정은 시스템 구현 후 데모 청취로 다듬는다).
우선순위: 보스 신호(예고) 4 > 피격·방어 판정 3 > 타격·공격 2 > 환경·획득·부가음 1, UI 0(별도 버스).
"""

TIERS = [
    dict(level=4, name='telegraph', label='보스 예고·보스 신호·무기 각성(61-4)·주인공 사망 슬로모(62-2)',
         events=['BOSS_TELEGRAPH', 'BOSS_STARTED', 'BOSS_PHASE', 'BOSS_DIED', 'boss:intro',
                 'BOSS_ACTION{action:introRoar}', 'WEAPON_AWAKEN', 'PLAYER_DIED']),
    dict(level=3, name='hurt', label='주인공 피격·방어 판정·적 공격 예고·보스 파훼(61-2)·기둥 무너짐·포물선 술병(61-5)·'
                                   '그림 속 입구 전환·수련장 도장(61-6)·적 등장 예고·마지막 처치 슬로모·노드 시련 성공/실패·'
                                   '1층 끝 결산(62-2)·버팀 깨짐·벽꽝·볼링·낙하·위험물 폭발·연속 처치(P19 — 판단·보상 순간)·'
                                   '처형·주인공 상흔·저HP 심장(P21)',
         events=['PLAYER_DAMAGED', 'PARRY_SUCCESS', 'PERFECT_GUARD', 'PERFECT_SUCCESS', 'ENEMY_TELEGRAPH', 'RUN_ENDED',
                 'BOSS_BREAK', 'ui:boss-break', 'BOSS_ACTION{action:cupStruck}', 'BOSS_ACTION{action:pillarCrack}',
                 'BOSS_ACTION{action:pillarCollapse}', 'BOSS_ACTION{action:lobThrow}',
                 'TRANSITION_BEGIN', 'TRAINING_STAMP',
                 'ENEMY_INCOMING', 'FEEL_SLOWMO', 'NODE_TRIAL_BROKEN', 'NODE_GRADED{grade:perfect}', 'ui:floor-end',
                 'enemy:staggered{kind:stagger}', 'enemy:wall-slam', 'enemy:bowled', 'enemy:fell', 'hazard:exploded',
                 'combo:streak', 'player:execute', 'player:wounded', 'player:low-hp']),
    dict(level=2, name='hit', label='타격·처치·공격 동작(주인공·적·보스)·공명 켜짐(61-5)·수련장 과제 완료(61-6)·'
                                 '유품 획득·기억 해금(62-2)',
         events=['RESONANCE_ON', 'TRAINING_TASK', 'ui:relic-gained', 'MEMORY_UNLOCKED', '(그 밖의 combat·boss 분류)']),
    dict(level=1, name='ambient', label='환경·획득(바닥 줍기 61-5 포함)·이벤트·패시브·상태 부가음·개성 발동 특색 층(61-5)·'
                                     '움찔·넉백 바람(P19 — 타격음 위 꼬리 층, 빼앗기 1순위)·살·뼈·피 층과 적 신음(P21)',
         events=['PASSIVE_PROC', 'STATUS_CHANGED', 'BOSS_ACTION{action:flameSnuff}', 'PICKUP_LANDED', 'PICKUP_COLLECTED',
                 'TRAIT_PROC', 'EVENT_TALK', 'SHOP_TALK', 'enemy:staggered{kind:flinch}', 'enemy:knocked',
                 'enemy:gore', 'enemy:wounded',
                 '(world·pickup·event 분류 — 상점 사기·다시 진열 포함)']),
    dict(level=0, name='ui', label='UI — 별도 버스, 상한·빼앗기 대상 아님(62-2 메뉴 공통 ui_move·ui_select·ui_back·ui_toggle)',
         events=['UI_MENU_*', 'UI_SETTING_TOGGLED', '(ui 분류)']),
]
# 61-5 P13 개성 발동 행동 갈래(계약 sound §11 — 'move' 는 소리 없음)
TRAIT_ACTS = ('launch', 'slam', 'pull', 'bind', 'clone', 'blink', 'wave', 'throw', 'rain', 'ignite', 'deflect',
              'shield', 'spin', 'mark', 'burst')
_EV = {ev: t['level'] for t in TIERS for ev in t['events'] if not ev.startswith('(')}
# 61-4: 같은 이벤트 안에서 조건 하나로 등급이 갈리는 것(BOSS_ACTION 의 action) — 'EVENT{키:값}' 꼴로 위 표에 적는다.
_AMBIENT_EVENTS = {'PASSIVE_PROC', 'STATUS_CHANGED', 'TRAIT_PROC'}

# P19 자유 전투(1-Snd) — 타격음 층 · 같은 소리 상한 · 시간 정점
HIT_IDS = ['sfx/hit_katana', 'sfx/hit_greatsword', 'sfx/hit_dagger', 'sfx/hit_bow', 'sfx/hit_enemy', 'sfx/hit_enemy_crit']
P19_GROUP_MAX = {
    'sfx/hit_katana': 3, 'sfx/hit_greatsword': 2, 'sfx/hit_dagger': 3, 'sfx/hit_bow': 3,
    'sfx/enemy_flinch': 2, 'sfx/enemy_stagger_break': 2,
    'sfx/knock_wind2': 2, 'sfx/knock_wind3': 2, 'sfx/knock_wind4': 1,
    'sfx/wall_slam_wall': 2, 'sfx/wall_slam_prop': 2, 'sfx/wall_slam_pillar': 2, 'sfx/enemy_bowl': 2,
    'sfx/enemy_launch': 2, 'sfx/enemy_land': 2, 'sfx/enemy_land_slam': 2,
    'sfx/fall_water': 2, 'sfx/fall_drop': 2, 'sfx/fall_fire': 2,
    'sfx/explode_small': 2, 'sfx/explode_mid': 2, 'sfx/explode_large': 1,
    'sfx/explode_chain1': 1, 'sfx/explode_chain2': 1, 'sfx/explode_chain3': 1, 'sfx/hazard_ignite': 2,
    'sfx/streak_2': 1, 'sfx/streak_4': 1, 'sfx/streak_6': 1,
    'sfx/drummer_beat': 2, 'sfx/drummer_rally': 1, 'sfx/drummer_death': 1,
    'sfx/bomber_fuse': 2, 'sfx/bomber_swell': 2, 'sfx/bomber_blast': 2,
}
P19_CUES = {
    'sfx/bomber_swell': dict(peakMs=1000, alignTo='ENEMY_TELEGRAPH{enemy:bomber}.ms',
                             note='P19: 1.0 s 에 뚝 끊김 = 터지는 순간. 예고가 1000 ms 가 아니면 재생 속도 = clamp(1000/ms, 0.85, 1.2)'),
    'sfx/drummer_beat': dict(peakMs=0, note='P19: 박 간격 400 ms 권장(f1_jan 150 BPM 한 박) — 곡 재생 위치의 박에 맞추면 더 좋다'),
    'sfx/explode_chain3': dict(peakMs=0, note='P19: chain ≥ 3 은 재생 속도 2^((chain−3)×2/12), 최대 1.26'),
    'sfx/fall_water': dict(peakMs=550, note='P19: 0.55 s 첨벙 — 낙하 연출(떨어져 사라짐)이 0.55 s 가 아니면 재생 위치가 아니라 시작을 늦춘다'),
    'sfx/fall_drop': dict(peakMs=1050, note='P19: 1.05 s 먼 바닥 \'쿵\'(화면 밖)'),
}


# P21 어둠·잔혹 — 같은 소리 상한 · 시간 정점 · 고어 설정
P21_GROUP_MAX = {
    'sfx/flesh_slash': 2, 'sfx/flesh_stab': 2, 'sfx/bone_crush': 2, 'sfx/arrow_stick': 2, 'sfx/blood_splat': 3,
    'sfx/dismember': 2, 'sfx/body_fall': 3, 'sfx/body_fall_armor': 2, 'sfx/execute_hit': 1,
    'sfx/hero_crack': 1, 'sfx/hero_ember_hiss': 1, 'sfx/heartbeat_loop': 1, 'sfx/enemy_groan_1': 2, 'sfx/enemy_groan_2': 2,
}
P21_CUES = {
    'sfx/blood_splat': dict(peakMs=0, delayMs=110, note='P21: 적중(enemy:gore)에서 110 ms 늦게 시작 — 분출한 피가 바닥에 떨어지는 순간. '
                                                    '시체 밑 웅덩이(1.5 s 퍼짐) 시작에도 한 번 쓸 수 있다(gainDb −4 더)'),
    'sfx/dismember': dict(peakMs=420, note='P21: 0 s 찢김(사망 변형과 같은 순간), 0.42 s 떨어져 나간 조각이 바닥에 \'퍽\' — '
                                           '조각 비행(0.5~0.9 s)의 착지가 늦으면 재생 위치가 아니라 시작을 (착지 − 420) ms 늦춘다. 변주 _v2 는 0.50 s'),
    'sfx/body_fall': dict(peakMs=340, note='P21: 0.14 s 무릎 · 0.34 s 몸통 \'쿵\'(변주 _v2 0.30 s, body_fall_armor 0.36 s) — 아트 쓰러짐 시트의 '
                                           '몸통 착지 프레임이 크게 다르면 시작을 옮긴다(음향에 알림)'),
    'sfx/execute_hit': dict(peakMs=0, alignTo='player:execute 의 결정타 프레임',
                            note='P21: 0 s = 결정타(슬로 0.3배 120 ms 시작과 같은 순간). PLAYER_EXECUTE 가 처형 시작에 오면 '
                                 '결정타 프레임까지 늦춰 재생한다(무기 처형 동작의 타격 프레임)'),
    'sfx/heartbeat_loop': dict(peakMs=30, note='P21: player:low-hp{on:true} 에서 fadeIn 400 ms, {on:false} 에서 fadeOut 600 ms. '
                                               '재생 속도 = ratio 0.25 → 1.0, ≤ 0.10 → 1.15(선형). 사망(PLAYER_DIED)이면 death_slow 와 함께 1.1 s 에 걸쳐 끔'),
}
P21_GORE = {
    '2': dict(note='전체 — 모든 P21 소리'),
    '1': dict(mute=['sfx/dismember'], gainDb={'sfx/flesh_slash': -3.0, 'sfx/flesh_stab': -3.0, 'sfx/bone_crush': -2.0,
                                               'sfx/blood_splat': -4.0, 'sfx/arrow_stick': -2.0},
              note='줄임 — 절단 없음(behead·bisect → collapse 라 dismember 는 원래 오지 않지만 안전하게 끔), 살·피 층 낮춤'),
    '0': dict(mute=['sfx/flesh_slash', 'sfx/flesh_stab', 'sfx/bone_crush', 'sfx/blood_splat', 'sfx/dismember'],
              note='끔 — 살·피 층 없음(무기 타격음만). body_fall·execute_hit·hero_*·heartbeat_loop·enemy_groan_* 은 그대로(잔혹 묘사가 아님)'),
}


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
                               'sfx/transition_fade': 1,
                               'sfx/training_task': 2, 'sfx/training_stamp': 1,
                               'sfx/enemy_incoming': 2, 'sfx/last_kill_slow': 1, 'sfx/death_slow': 1,
                               'sfx/trial_win': 1, 'sfx/trial_fail': 1, 'sfx/floor_end_sting': 1,
                               'sfx/memory_unlock': 1, 'sfx/relic_take': 1, 'sfx/shop_buy': 2, 'sfx/shop_reroll': 1,
                               'sfx/npc_talk': 1, 'sfx/door_open': 1, 'sfx/door_walk_out': 1,
                               'sfx/door_walk_in': 1, 'sfx/door_walk_back': 1,
                               **P19_GROUP_MAX, **P21_GROUP_MAX},
            layerMax=dict(ids=['sfx/trait_%s' % a for a in TRAIT_ACTS], match='TRAIT_PROC 로 재생된 소리', max=3,
                          note='61-5: 개성 발동 특색 층(TRAIT_PROC 로 고른 trait_<act> 15종 + 개성별 trait_<무기>_<id> 가 생기면 그것도 — '
                               'trait_manifest(TRAIT_GAINED)는 아님) 전체를 '
                               '합쳐 동시 3까지. 넘치면 같은 층에서 가장 오래된 것을 30 ms 페이드로 끊는다(우선순위 1 이라 '
                               'maxSfx 에서도 빼앗기 1순위). resonance_proc 은 이 층에 세지 않는다'),
            hitLayer=dict(ids=HIT_IDS, match='ENEMY_DAMAGED 로 재생된 타격음(무기별 hit_<무기> + hit_enemy·hit_enemy_crit, 변주 포함)',
                          max=4, windowMs=40, stackDb=-3.0, minGapMs=30,
                          note='P19: 타격음 전체를 합쳐 동시 4까지(layerMax 와 같은 꼴 — ids·match·max). 넘치면 가장 오래된 타격음을 '
                               '30 ms 페이드로 끊는다. 한 휘두름이 여러 적을 맞혀 windowMs(40 ms) 안에 타격음이 몰리면 첫 소리만 제 음량, '
                               '둘째부터 stackDb(−3 dB)씩 더 낮춰(최저 −9 dB) 쌓는다 — 무리를 베어도 한 덩어리로 묵직하게, 귀가 따갑지 않게. '
                               '같은 타격음 id 는 minGapMs(30 ms) 안에 다시 울리지 않는다(dedupeMs 20 보다 넓게 — 단검 연타 대비). '
                               '움찔(enemy_flinch)·넉백 바람(knock_wind*)은 이 층에 세지 않지만 priority 1 이라 maxSfx 에서 먼저 빠진다'),
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
            dict(when='파훼 소리 재생(boss1_break_*·break_finisher·boss1_pillar_collapse) — 61-5 기둥 무너짐 포함',
                 target='sfx priority ≤ 2', db=-4.0, attackMs=5, releaseMs=300, hold='300 ms',
                 note='61-2: 트리거 ui:boss-break(break_count 는 제외) · 파훼·결정타의 손맛 — 그 순간 타격·휘두름을 잠깐 눌러 한 방이 앞에 서게. '
                      '61-5: 기둥 무너짐(BOSS_ACTION pillarCollapse)도 같은 규칙. '
                      '62-2: 시스템 파서는 when 의 첫 괄호 안 이름만 읽으므로 기둥 무너짐을 첫 괄호 안으로 옮김(전에는 빠져 있었음)'),
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
            dict(when='마지막 처치 슬로모 재생(last_kill_slow)', target='sfx priority ≤ 2', db=-5.0, attackMs=10,
                 releaseMs=250, hold='280 ms',
                 note='62-2: 슬로모(280 ms) 동안 남은 타격·휘두름을 눌러 시간이 굳는 느낌 — 처치음(enemy_death, priority 2)도 함께 '
                      '조금 눌려 last_kill_slow 의 깊은 \'웅\'이 앞에 선다'),
            dict(when='마지막 처치 슬로모 재생(last_kill_slow) — BGM', target='bgm', db=-4.0, attackMs=30, releaseMs=350,
                 hold='280 ms', note='62-2: 곡도 슬로모 동안 살짝 물러났다가 시간이 풀릴 때 돌아온다'),
            dict(when='사망 슬로모 재생(death_slow)', target='sfx priority ≤ 2', db=-10.0, attackMs=20, releaseMs=600,
                 hold='그 소리 길이 동안',
                 note='62-2: 죽는 순간 남은 전투음을 크게 눌러 먹 번짐만 남게(주인공 피격 hit_player 는 priority 3 이라 그대로 들림). '
                      'priority 4 기본 규칙(−6 dB)과 겹치면 더 깊은 값 하나만(−10 dB)'),
            dict(when='사망 슬로모 재생(death_slow) — BGM', target='bgm', db=-12.0, attackMs=300, releaseMs=1500,
                 hold='그 소리 길이 동안',
                 note='62-2: 0.3 s 에 걸쳐 곡이 거의 사라지고(슬로모와 함께) 결산 화면으로 넘어가며 1.5 s 에 걸쳐 돌아옴. '
                      '결산에서 곡을 바꾸거나 끄면 시스템 페이드가 우선'),
            dict(when='벽꽝·볼링 재생(wall_slam_wall·wall_slam_prop·wall_slam_pillar·enemy_bowl)', target='sfx priority ≤ 2',
                 db=-3.0, attackMs=5, releaseMs=200, hold='120 ms',
                 note='P19: 벽꽝·볼링의 \'쿵\'이 그 순간 타격·휘두름 위에 서게 살짝(−3 dB) 짧게 — 자주 일어나므로 곡·전투음이 출렁이지 않게 얕게. '
                      '벽꽝 자신은 priority 3 이라 눌리지 않는다'),
            dict(when='큰 폭발 재생(explode_large·bomber_blast)', target='sfx priority ≤ 2', db=-4.0, attackMs=5,
                 releaseMs=300, hold='200 ms',
                 note='P19: 증류기·자폭병 폭발 순간 남은 타격·휘두름을 눌러 한 방이 앞에 서게. 자폭병 폭발(ENEMY_ATTACK)은 priority 2 라 '
                      '자기 자신은 이 규칙에서 빼고 적용(시스템: 덕킹을 일으킨 소리는 대상에서 제외)'),
            dict(when='큰 폭발 재생(explode_large·bomber_blast) — BGM', target='bgm', db=-3.0, attackMs=20, releaseMs=500,
                 hold='300 ms', note='P19: 큰 폭발 때 곡이 잠깐 물러남(연쇄로 0.3초마다 이어지면 hold 가 이어져 한 번 눌린 채 유지)'),
            dict(when='처형 일격 재생(execute_hit)', target='sfx priority ≤ 2', db=-9.0, attackMs=5, releaseMs=350,
                 hold='300 ms',
                 note='P21: 처형 결정타 순간 남은 타격·휘두름·살 층을 크게 눌러 \'짧은 정적\' — 낮은 충격과 먹먹한 꼬리만 남는다. '
                      '처형으로 이어지는 사망 변형 소리(dismember·body_fall, priority 2)도 함께 눌려 뒤로 물러난다'),
            dict(when='처형 일격 재생(execute_hit) — BGM', target='bgm', db=-6.0, attackMs=10, releaseMs=600,
                 hold='300 ms', note='P21: 곡도 슬로(0.3배 120 ms)와 함께 물러났다가 0.6 s 에 걸쳐 돌아온다'),
            dict(when='저HP 심장 박동 재생(heartbeat_loop) — BGM', target='bgm', db=-2.5, attackMs=400, releaseMs=600,
                 hold='그 소리가 도는 동안',
                 note='P21: HP ≤ 25% 동안 곡을 살짝 물려 심장 박동이 바닥에 깔리게(저역끼리 부딪히지 않게). 루프가 멈추면 풀림'),
            dict(when='1층 끝 결산 열림 재생(floor_end_sting) — BGM', target='bgm', db=-6.0, attackMs=200, releaseMs=1200,
                 hold='그 소리 길이 동안',
                 note='62-2: 결산 일기장이 열리는 손풍금 화음이 곡과 부딪히지 않게(보스 처치 뒤 정적이면 영향 없음)'),
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
        bgmIntensity=dict(
            layers={'bgm/f1_jan': 'bgm/f1_jan_perc'},
            onWhen='살아 있는 적 ≥ 6', offWhen='살아 있는 적 ≤ 3 이 2000 ms 이어짐(또는 방 클리어·보스 방)',
            fadeInMs=1500, fadeOutMs=3000, minOnMs=6000, syncPosition=True,
            note='P19 전투 강도 2단: 평시 = 곡(f1_jan)만, 전투 겹 = 같은 재생 위치에서 타악 층(f1_jan_perc, 길이·박자 격자 같음)을 '
                 '함께 돌리며 음량만 올림. 층은 전투 곡이 시작될 때 음량 0(무음)으로 같이 시작해 두고 onWhen 에서 fadeInMs 로 '
                 '자기 gainDb 까지, offWhen 에서 fadeOutMs 로 0 — 켜진 뒤 minOnMs 안에는 끄지 않는다(웨이브 겹침 사이 깜빡임 방지). '
                 '층 음량은 덕킹·BGM 버스를 곡과 같이 받는다. 겹을 켜면 통합 음량 약 +1.4 LU(−19.1 → −17.7 LUFS). '
                 '찾는 법: bgmByFloorState[층].combatLayer(= 이 표의 값) — 없으면 겹 없음'),
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
                 'exit 0.95 s 에 액자 닫힘 — 연출 시작과 같은 순간에 재생. '
                 '62-3: mode fade(노드 이동 짧은 암전)는 transition_fade 하나만(없으면 transition_exit 를 −6 dB·속도 1.2) — '
                 '덕킹 규칙(전환음 → 효과음 −8 dB·BGM −4 dB)은 걸지 않는다(노드마다 울리는 0.66 s 라 곡이 출렁이지 않게. '
                 '곡이 바뀌면 시스템 BGM 교차 페이드만). 건너뛰기가 있으면 같은 skipFadeMs.'),
        cues={
            'sfx/enemy_incoming': dict(peakMs=1000, alignTo='ENEMY_INCOMING.delayMs',
                                       note='62-2: 파일 1.00 s 에 적이 일어서는 \'훅·둥\'. 시작 = max(0, delayMs − 1000) ms 뒤 '
                                            '(노드 첫 웨이브 1500 ms 면 500 ms 늦춰 시작). delayMs < 1000 이면 바로 재생 — '
                                            '앞부분이 짧아질 뿐 정점은 등장보다 늦는다(재생 위치를 1000 − delayMs 로 건너뛰어도 됨)'),
            'sfx/last_kill_slow': dict(peakMs=280, note='62-2: 0~280 ms 시간이 굳음, 280 ms 에 풀림 — FEEL.KILL.SLOW.MS 와 같은 순간에 시작'),
            'sfx/death_slow': dict(peakMs=600, alignTo='ui:death-started{slowMs,inkMs}',
                                   note='62-2: 시스템 data/runEnd.json death(slowMs 600 · inkMs 1100 · holdMs 250)에 맞춤 — 0~600 ms 슬로모, '
                                        '600 ms 먹 방울 \'툭\' + 번짐(1100 ms), 1620 ms 먹이 자리 잡음, 2000 ms 끝(결산). 사망 연출 시작(beginDeath)과 '
                                        '같은 순간 재생. slowMs 가 바뀌면 재생 속도가 아니라 이 정점을 옮겨 다시 만든다(음향에 알림)'),
            'sfx/floor_end_sting': dict(peakMs=1150, note='62-2: 0 s 일기장 열림, 1.15 s 화음이 열림(결산 항목이 차례로 뜨기 시작하기 좋은 순간)'),
            'sfx/memory_unlock': dict(peakMs=450, note='62-2: 0~0.3 s 글씨 세 획, 0.45 s 먹 \'툭\' + 종 — 해금 그림이 떠오르는 순간'),
            'sfx/door_open': dict(peakMs=520, note='62-2 시스템 E: 0 s 빗장, 0.06~0.52 s 널문이 밀림, 0.52 s 판자가 바깥에 내려앉음 — '
                                                 '문 그림 걷힘(0.52 s)과 같은 순간에 시작. 0.68 s 낮은 종 = 문 빛이 다 찬 무렵(0.7 s)'),
            'sfx/door_walk_out': dict(peakMs=480, alignTo='DOOR_WALK.ms',
                                      note='62-2 시스템 E: 걸음 0·0.24·0.48(·0.72 아주 작게) s — 2.5칸 ≈ 700 ms 기준. ms 가 크게 다르면 '
                                           '재생 속도 = clamp(700 / ms, 0.85, 1.15) 권장(안 맞춰도 어둠에 잠기는 꼬리라 어색하지 않음)'),
            'sfx/door_walk_in': dict(peakMs=600, alignTo='DOOR_WALK.ms',
                                     note='62-2 시스템 E: 걸음 0·0.22·0.44·0.60 s — 0.60 s 마지막 디딤 = 조작이 풀리는 순간(≈650 ms 기준). '
                                          '재생 속도 = clamp(650 / ms, 0.85, 1.15) 권장'),
            'sfx/door_walk_back': dict(peakMs=400, note='62-2 시스템 E: 걸음 0·0.22·0.40 s — 문턱 안 1.8칸으로 물러남'),
            'sfx/relic_take': dict(peakMs=220, note='62-2: 0.22 s 쇠붙이를 쥐는 \'철컥\' — 카드가 손으로 들어가는 순간'),
            'sfx/transition_fade': dict(peakMs=380, alignTo='TRANSITION_BEGIN.durationMs',
                                        note='62-3 시스템 H: 0~0.38 s 먹이 번지는 쉭(덮기), 0.38 s 다 덮임(작은 \'툭\'), 0.42~0.64 s 걷힐 때 숨. '
                                             'TRANSITION_BEGIN 과 같은 순간 재생. durationMs(UI 0.25~0.6 s 로 자름)가 400 에서 크게 다르면 '
                                             '재생 속도 = clamp(380 / durationMs, 0.85, 1.2) 권장 — 재시작이 길어 걷기가 늦으면 숨이 먼저 지나가도 '
                                             '작아서 어색하지 않음(걷기 시작에 다시 울리지 않는다)'),
            'sfx/trial_win': dict(peakMs=0, note='62-2: 0 s 完 도장 \'꾹\'. 노드 마지막 처치와 같은 프레임이면(마지막 처치 슬로모 280 ms) '
                                                 '슬로모가 풀린 뒤 재생하면 \'웅\'과 도장·종이 겹치지 않는다(도장 연출이 늦게 뜨면 그 순간에)'),
            **P19_CUES,
            **P21_CUES,
        },
        cuesNote='62-2: 시간 축이 연출에 맞춰진 효과음의 정점(peakMs, 파일 0 기준). 시스템·UI 연출 시각을 이 값에 맞추거나, '
                 '연출이 늦으면 재생을 그만큼 늦춘다. 계약 필드가 아니라 권장값.',
        gore=dict(levels=P21_GORE,
                  note='P21: settings.gore(2 전체 · 1 줄임 · 0 끔, contracts/dark-brutal.md §1)에 따라 효과음을 끄거나(mute) 낮춘다(gainDb, '
                       '항목 gainDb 위에 더함). 변주(variants)도 원본과 같이 적용'),
        variantGroups=variant_groups,
    )
