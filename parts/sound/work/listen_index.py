# -*- coding: utf-8 -*-
"""
들어보기(청취 검수) 페이지용 목록 — parts/sound/work/listen_index.json (60라운드 Q7 '실제 청취 검수용 들어보기 페이지').

build.py 가 manifest 를 쓴 뒤 write() 를 부른다(`build.py`·`sfx`·`bgm`·`encode`·`manifest`·`listen`).
manifest(assets/audio/manifest.json)의 길이·루프·파일·트리거·음량을 그대로 옮기고, 분류(group)·한 줄 설명(desc)·
새로 만든 라운드(round)·보관 여부(status)를 붙인다. 계약 문서가 아니다 — 음향 작업 자료(페이지 생성 입력).
"""
import json
import os

# 표시 순서 = 페이지 순서
GROUPS = [
    ('combat', '전투 공통'),
    ('weapon_katana', '무기별 · 칼'),
    ('weapon_greatsword', '무기별 · 대검'),
    ('weapon_dagger', '무기별 · 단검'),
    ('weapon_bow', '무기별 · 활'),
    ('branch1', '갈래 1단'),
    ('branch2', '갈래 2단 (60라운드)'),
    ('build', '빌드 축 (세트·이중 개성·저주·각성·상태)'),
    ('passive', '패시브 (60라운드)'),
    ('bundle2', '2차 묶음 (60라운드)'),
    ('enemy', '적'),
    ('boss', '보스 공통'),
    ('boss1', "1층 보스 '만취'"),
    ('world', '맵·월드'),
    ('pickup', '획득·상점'),
    ('ui', 'UI·연출'),
    ('bgm', 'BGM'),
    ('archived', '보관 (연결 끊음, 60라운드 Q6)'),
]

ARCHIVED = {'katana_echo', 'gs_plunge', 'gs_crack'}

EXPLICIT = {
    'combat': ['hit_enemy', 'hit_enemy_crit', 'hit_player', 'dash', 'parry', 'guard_hold', 'guard_push',
               'perfect_guard', 'groggy_start', 'perfect_evade', 'guard_block', 'combo_finish'],
    'weapon_katana': ['swing_katana', 'parry_perfect', 'kenki_stage1', 'kenki_stage2', 'kenki_stage3', 'issen_dash',
                      'issen_burst', 'shadow_clone', 'katana_counter', 'katana_iai_hold', 'katana_iai_release',
                      'katana_thrust', 'katana_thrust_ki1', 'katana_thrust_ki2', 'katana_thrust_ki3'],
    'weapon_greatsword': ['swing_greatsword', 'charge_start', 'charge_stage1', 'charge_stage2', 'charge_stage3',
                          'charge_loop', 'charge_slam_lv1', 'charge_slam_lv2', 'charge_slam_lv3', 'utbun_full',
                          'gs_drag', 'gs_tackle', 'gs_brace_upswing', 'gs_leap', 'gs_leap_slam', 'gs_guard_rush',
                          'gs_crack_line_lv1', 'gs_crack_line_lv2', 'gs_crack_line_lv3'],
    'weapon_dagger': ['swing_dagger', 'shadowstep', 'dagger_backstab', 'dagger_flurry1', 'dagger_flurry2',
                      'dagger_flurry3', 'dagger_flurry4', 'brand_apply', 'brand_burst', 'overheat_burst'],
    'weapon_bow': ['bow_shot', 'bow_draw', 'bow_aimed', 'bow_release_weak', 'bow_release_perfect', 'bow_full_draw',
                   'bow_strain', 'breath_focus', 'arrow_rain_launch', 'arrow_rain_impact'],
    'branch1': ['katana_spin_ready', 'katana_spin', 'katana_guardbreak_hold', 'katana_guardbreak', 'gs_quake_ring',
                'gs_shatter_snuff', 'dagger_fan_throw', 'dagger_cross_clone', 'bow_rapid1', 'bow_rapid2', 'bow_rapid3',
                'bow_pierce'],
    'build': ['set_tier1', 'set_tier2', 'set_tier3', 'dual_trait', 'curse_take', 'curse_end', 'blood_pact',
              'awaken_katana', 'awaken_greatsword', 'awaken_dagger', 'awaken_bow', 'mark_stack', 'boil_burst',
              'stillness', 'drunk_ignite', 'drunk_sway', 'endure_trigger'],
    'enemy': ['enemy_death', 'enemy_hurt', 'charger_telegraph', 'charger_dash', 'archer_shot'],
    'boss': ['boss_start', 'boss_phase', 'boss_telegraph', 'boss_fan', 'boss_die'],
    'world': ['level_enter', 'door_close', 'door_open', 'boss_unlock', 'exit_open', 'trial_clear', 'save'],
    'pickup': ['pickup_gold', 'pickup_potion', 'potion_use', 'shop_buy'],
    'ui': ['menu_move', 'menu_select', 'menu_cancel', 'fate_decided', 'evolve', 'reinforce', 'player_death'],
}

# 60라운드 새 소리의 소분류(갈래·묶음·패시브 이름)
SUBGROUP = {
    # 갈래 2단
    'katana_whirl_loop': '칼 · 회오리', 'katana_whirl_reflect': '칼 · 회오리',
    'katana_moon_trail': '칼 · 잔월',
    'katana_cleave_crack': '칼 · 일도양단', 'katana_execute': '칼 · 일도양단',
    'katana_mirror_parry': '칼 · 명경', 'kenki_stage4': '칼 · 명경', 'kenki_stage5': '칼 · 명경',
    'gs_quake_fork': '대검 · 지진', 'gs_echo_counter': '대검 · 반향',
    'charge_stage4': '대검 · 거인', 'charge_slam_lv4': '대검 · 거인',
    'gs_congest_loop': '대검 · 울혈', 'gs_congest_burst': '대검 · 울혈',
    'dagger_frenzy_in': '단검 · 난무', 'dagger_frenzy_out': '단검 · 난무',
    'dagger_bleed': '단검 · 출혈', 'dagger_brand_hop': '단검 · 출혈',
    'dagger_flyknife_throw': '단검 · 비도', 'dagger_knife_stick': '단검 · 비도', 'dagger_knife_step': '단검 · 비도',
    'dagger_hotwind_loop': '단검 · 열풍', 'dagger_hotwind_burst': '단검 · 열풍',
    'bow_arrow_split': '활 · 연궁', 'bow_arrow_recall': '활 · 무한통',
    'bow_deadeye_lock': '활 · 필중', 'bow_deadeye_hold': '활 · 필중',
    'bow_link1': '활 · 천공', 'bow_link2': '활 · 천공', 'bow_link3': '활 · 천공', 'bow_link_break': '활 · 천공',
    'bow_skypierce': '활 · 천공',
    # 2차 묶음
    'elite_appear': '엘리트', 'elite_armor_break': '엘리트 · 통 갑옷', 'elite_enrage': '엘리트 · 성난',
    'elite_drink': '엘리트 · 들이켜는', 'elite_leader_down': '엘리트 · 패거리 두목', 'elite_die': '엘리트',
    'shrine_activate': '도전 성소', 'shrine_clear': '도전 성소', 'shrine_fail': '도전 성소',
    'grade_perfect': '성과 등급', 'grade_good': '성과 등급',
    'shop_reroll': '상점 리롤', 'map_info_buy': '지도 정보',
    'bottle_throw': '소모품 · 화염 술병', 'bottle_burst': '소모품 · 화염 술병',
    'strong_drink': '소모품 · 깡술 한 모금', 'cold_water': '소모품 · 냉수 한 바가지',
    'event_enter': '이벤트 노드', 'event_choice': '이벤트 노드', 'hidden_node_found': '숨은 노드',
    'break_count': '약점 파훼 · 다양성', 'break_finisher': '약점 파훼 · 결정타',
    'still_ignite': '증류 화로', 'fire_weapon_loop': '증류 화로', 'fire_weapon_end': '증류 화로',
    # 패시브
    'passive_glass_shard': '#10 깨진 잔 조각', 'passive_ember_sleeve': '#11 불붙은 소매',
    'passive_blood_scent': '#18 피 냄새', 'passive_domino': '#20 도미노', 'passive_mirror_clone': '#24 깨진 거울',
    'passive_ember_heart': '#25 잔불 심장', 'passive_spilled_drink': '#26 엎지른 술',
    'passive_liquor_spray': '#28 독한 숨', 'passive_fire_breath': '#28 독한 숨 (술불 위)',
    'passive_drunk_fist': '#29 취권',
}

NEW_MODULES = {'sfx_bundle2': 'bundle2', 'sfx_branch2': 'branch2', 'sfx_passive': 'passive'}


def _first_sentence(note):
    """note 의 첫 문장(괄호 밖 '. ' 앞). 보관 표시 '[...] ' 는 뗀다."""
    if note.startswith('['):
        note = note[note.index(']') + 1:].lstrip()
    depth = 0
    for i, ch in enumerate(note):
        if ch in '(（':
            depth += 1
        elif ch in ')）':
            depth = max(0, depth - 1)
        elif ch == '.' and depth == 0 and (i + 1 == len(note) or note[i + 1] == ' '):
            return note[:i]
    return note


def _group_of(name, kind, sfx_specs):
    if kind == 'bgm':
        return 'bgm'
    if name in ARCHIVED:
        return 'archived'
    if sfx_specs.get(name, {}).get('variant_of'):          # 61라운드 변주 = 원본과 같은 분류
        return _group_of(sfx_specs[name]['variant_of'], kind, sfx_specs)
    mod = sfx_specs[name]['fn'].__module__ if name in sfx_specs else ''
    if mod in NEW_MODULES:
        return NEW_MODULES[mod]
    for g, names in EXPLICIT.items():
        if name in names:
            return g
    if name.startswith('boss1_'):
        return 'boss1'
    raise KeyError('listen_index: 분류가 없는 소리 %s — EXPLICIT 에 추가하세요' % name)


def _bgm_where(e):
    """BGM 이 쓰이는 곳 한 줄: 61라운드 층 전용 곡은 use(floor·state·phase), 기존 곡은 floors 또는 bgmByState."""
    u = e.get('use')
    if u:
        return '%d층 %s' % (u['floor'], {'journey': '여정(벽 밖)', 'combat': '전투', 'boss': '보스'}.get(u['state'], u['state'])) + \
            (' %d국면' % u['phase'] if 'phase' in u else '')
    if e.get('floors'):
        return '층 ' + ','.join(str(x) for x in e['floors'])
    return 'bgmByState'


def _round(name, kind, sfx_specs):
    """새로 만들거나 다시 만든 라운드: '61' = 61라운드 품질 패스·변주·1층 BGM, '60' = 60라운드 모듈."""
    if kind == 'bgm':
        return '61' if name.startswith('f1_') else ''
    spec = sfx_specs[name]
    if spec.get('redone') == '61' or spec['fn'].__module__ == 'sfx_core61':
        return '61'
    return '60' if spec['fn'].__module__ in NEW_MODULES else ''


def write(root, manifest_path, sfx_specs, out_path=None):
    out_path = out_path or os.path.join(root, 'parts', 'sound', 'work', 'listen_index.json')
    with open(manifest_path, encoding='utf-8') as f:
        man = json.load(f)
    entries = []
    for e in man['entries']:
        kind = e['kind']
        name = e['id'].split('/', 1)[1]
        g = _group_of(name, kind, sfx_specs)
        t = e.get('trigger')
        trig = None
        if t:
            trig = t['event'] + ('{%s}' % ','.join(t['when']) if t['when'] else '')
        elif e.get('variantOf'):
            trig = '변주 — %s 트리거에서 번갈아' % e['variantOf']
        item = dict(
            key=name, id=e['id'], kind=kind, group=g, subgroup=SUBGROUP.get(name, ''),
            desc=_first_sentence(e['note']), note=e['note'],
            trigger=trig if kind == 'sfx' else _bgm_where(e),
            durationMs=e['durationMs'], samples=e['samples'], sampleRate=e['sampleRate'],
            channels=e['channels'], loop=e['loop'], gainDb=e['gainDb'],
            ogg=e['files'][0], m4a=e['files'][1],
            round=_round(name, kind, sfx_specs),
            status='archived' if name in ARCHIVED else 'active')
        for k in ('priority', 'variants', 'variantOf', 'use'):
            if k in e:
                item[k] = e[k]
        if e['loop']:
            item['loopStartSample'] = e['loopStartSample']
            item['loopEndSample'] = e['loopEndSample']
        entries.append(item)
    order = {g: i for i, (g, _) in enumerate(GROUPS)}
    entries.sort(key=lambda x: order[x['group']])  # 안정 정렬: 그룹 안은 manifest(등록) 순서
    counts = {}
    for x in entries:
        counts[x['group']] = counts.get(x['group'], 0) + 1
    data = dict(
        version=1,
        generatedBy='parts/sound/work/build.py → listen_index.py (manifest 기준)',
        note='들어보기 페이지 입력. 경로는 저장소 루트 기준. gainDb 는 SFX/BGM 버스 기준 권장 상대 음량(manifest 와 같음) — '
             '청취 페이지에서는 원본(피크 -6 dBFS) 그대로 또는 gainDb 적용 두 방식 중 고를 수 있게 하면 비교가 쉽다. '
             'round "60" = 60라운드 새 소리, "61" = 61라운드 품질 패스(같은 키 다시 만듦)·변주·1층 BGM, '
             'status "archived" = 보관(시스템 연결 끊음). variantOf 항목은 원본 트리거에서 번갈아 쓰는 변주.',
        mixing=man['mixing'],
        groups=[dict(id=g, label=label, count=counts.get(g, 0)) for g, label in GROUPS],
        total=len(entries),
        entries=entries)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print('  listen %s (%d entries)' % (os.path.relpath(out_path, root), len(entries)))
