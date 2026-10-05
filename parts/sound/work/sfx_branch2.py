# -*- coding: utf-8 -*-
"""
60라운드 Q7 — 2단 갈래 16종 효과음 (칼 회오리·잔월·일도양단·명경 / 대검 지진·반향·거인·울혈 /
단검 난무·출혈·비도·열풍 / 활 연궁·무한통·필중·천공).

build.py 가 sfx_bundle2 다음에 import 한다(시드 = 1000 + 등록 순서). 새 소리는 이 파일 끝이 아니라
마지막 모듈(sfx_passive) 끝에만 추가한다 — 여기 끼우면 뒤 모듈 소리가 바뀐다.

근거: 설계안 design-2026-10-04-build-axis.md 2.2~2.5(57라운드 Q22~Q37 채택), 계약 art-assets.md §21
      2단 갈래 fx 와 각 fx JSON(assets/sprites/fx/v3/*.json)의 frameDurationsMs·spawn·spawnAtMs·hitTiming —
      파일 안 시각(판정·틱·폭발)은 그 JSON 에 맞췄다(아래 각 note).
트리거: 기존 이벤트(PLAYER_SKILL·PLAYER_CHARGE·PLAYER_ATTACK·PLAYER_SECONDARY·KENKI_CHANGED·PARRY_SUCCESS·
        PERFECT_GUARD·GROGGY·BRAND_BURST·OVERHEAT·BREATH_FOCUS)에 조건 키 branch:<id> 를 붙이는 것을 기본으로,
        규칙형(β) 사건은 제안 이벤트 BRANCH_EFFECT{branch,effect}. 갈래 id(whirl·moon·cleave·mirror·quake·echo·
        giant·congest·frenzy·bleed·flyknife·hotwind·split·quiver·deadeye·skypierce)는 음향 제안 — 시스템 id 로 바꿔 적는다.
재료: 칼 = 칼날 울림(blade_ring)·찢김, 대검 = 징(jing)·돌·흙, 단검 = 재·지짐·그림자 역바람, 활 = 시위·화살대·유리 반짝임.
      음높이는 D 단조 축(D·A·F) 유지 — 검기 A4·D5·A5(→ D6·A6), 차지 D4·A4·D5(→ A5).
"""
from build import *  # noqa: F401,F403
from build import GLASS, BLADE, AMBER_D, blade_ring, tear, sizzle, ash_pop, heavy_step, arrow_thunk, jing, \
    gravel, slam_impact, crackle, droplets, heartbeat, latch, tone_f  # noqa: F401


# ---------------------------------------------------------------------------
# 재료
# ---------------------------------------------------------------------------

def crack_run(sr, rng, dur, run, cracks, f_hi=2300, f_lo=900, g=0.75, end_g=0.5):
    """균열이 run 초 동안 달려감: 갈라짐 cracks 번(멀어질수록 어둡고 작게) + 끝 '툭' + 땅울림."""
    s = zeros(sec(sr, dur))
    for k in range(cracks):
        t0 = 0.004 + run * k / cracks + rng.uniform(-0.003, 0.003)
        gk = g * (1 - 0.4 * k / cracks)
        mix_into(s, burst(sr, 0.04, rng, fc=max(600, f_hi - (f_hi - f_lo) * k / cracks), q=0.9, tau=0.008), sec(sr, max(0.0, t0)), gk)
        mix_into(s, thud(sr, 0.045, 170 - 40 * k / cracks, 80, 0.012), sec(sr, max(0.0, t0)), gk * 0.35)
    mix_into(s, burst(sr, 0.1, rng, fc=900, q=0.7, tau=0.022), sec(sr, run), end_g)
    mix_into(s, thud(sr, 0.16, 120, 45, 0.035), sec(sr, run), end_g * 0.9)
    rum = mul(svf(noise(sr, dur, rng), sr, 160, 0.8, 'low'), env_adsr(sr, dur, max(0.01, run * 0.5), 0.0, 1.0, dur * 0.6))
    mix_into(s, rum, 0, 0.5)
    return s


def flame_roar(sr, rng, dur, f0=250, f1=2400, a=0.04, g=1.0):
    n = sec(sr, dur)
    s = svf(noise(sr, dur, rng), sr, sweep(sr, n, f0, f1), 0.7, 'low')
    return scale(mul(s, env_adsr(sr, dur, a, dur * 0.2, 0.5, dur * 0.6)), g)


def glassy(sr, dur, f, rng, tau=0.15):
    """유리·거울 '팅': 유리 배음 + 아주 맑은 윗소리."""
    return metal(sr, dur, f, rng, partials=GLASS, tau=tau, jitter=0.003)


# ===========================================================================
# 칼
# ===========================================================================

# ---- 회오리(旋渦) 2단 A-α: 회전 베기 홀드 유지 = 지속 회전(최대 1.5 s, 초당 4타), 회전 중 투사체 반사 ----

@sfx('katana_whirl_loop', 'PLAYER_SKILL{weapon:katana,move:whirl,phase:hold}', "회오리 지속 회전 루프(0.96 s = 한 바퀴 240 ms × 4, fx katana_whirl_loop 와 같은 주기). 바퀴마다 올라갔다 내려오는 칼바람 + 바퀴 시작(= 판정, fx f0)마다 작은 칼날 틱 + 낮게 도는 바람. katana_spin 1회 뒤 이어서, 떼면 80 ms 페이드아웃", -6, loop=True)
def _katana_whirl_loop(sr, rng):
    dur = 0.96
    n = sec(sr, dur)
    rev = n // 4
    ph = [(i % rev) / rev for i in range(n)]
    fc = [1300 * (1 + 2.4 * math.sin(math.pi * p) ** 1.5) for p in ph]
    w = wrap2(lambda x: svf(x, sr, fc + fc, 1.6, 'band'), noise_loop(sr, n, rng))
    w = mul(w, [0.25 + 0.75 * math.sin(math.pi * p) ** 0.8 for p in ph])
    low = wrap2(lambda x: svf(x, sr, 420, 0.8, 'band'), noise_loop(sr, n, rng))
    mix_into(w, mul(low, lfo_loop(sr, n, 1 / 0.24, 0.3, 0.7, 0.75)), 0, 0.35)
    for k in range(4):  # 판정마다 칼날 틱(경계에서 감긴다)
        tk = blade_ring(sr, 0.12, 587.33, rng, bright=0.3, tau=0.035)
        mix_into(tk, click(sr, rng, 0.003, 4800), 0, 0.5)
        mix_into(w, tk, sec(sr, 0.24 * k + 0.012), 0.22, wrap=True)
    return w


@sfx('katana_whirl_reflect', 'PLAYER_SKILL{weapon:katana,move:whirl,phase:reflect}', "회오리 회전 중 적 투사체 되받아침(fx katana_whirl_reflect, impactFrame 0). 칼날에 맞는 맑은 '팅' + 칼날 울림 D6 + 되돌아 나가는 바람(2k→6.5k). 투사체마다(20 ms 규칙)", -3)
def _katana_whirl_reflect(sr, rng):
    s = zeros(sec(sr, 0.3))
    mix_into(s, click(sr, rng, 0.003, 6000), 0, 0.8)
    mix_into(s, metal(sr, 0.15, 2600, rng, tau=0.03, jitter=0.02), 0, 0.35)
    mix_into(s, blade_ring(sr, 0.25, 1174.66, rng, bright=0.8, tau=0.06), sec(sr, 0.003), 0.35)
    mix_into(s, whoosh(sr, 0.18, rng, 2000, 6500, q=1.6, a=0.1, r=0.7), sec(sr, 0.03), 0.55)
    return tail(s, sr, 0.02)


# ---- 잔월(殘月) 2단 A-β: 검기를 쓴 일섬·회전이 지나간 자리에 달 궤적 1.2 s(0.3 s 마다 피해) ----

@sfx('katana_moon_trail', 'BRANCH_EFFECT{branch:moon,effect:trail}', "잔월 달 궤적이 깔림(검기 쓴 일섬·회전 뒤, 궤적 한 줄에 1회 — 초승달 조각마다 아님). fx katana_moon_trail 수명에 맞춤: 0~0.1 s 생김 '시잉'(A4, 어둡게) → 0.1·0.4·0.7·1.0 s 작은 틱(0.3 s 피해 틱) + 은은한 A5 험 → 1.3 s 재로 부서짐. 시스템 지속이 1.2 s 와 다르면 끝에서 페이드아웃", -6)
def _katana_moon_trail(sr, rng):
    dur = 1.55
    s = zeros(sec(sr, dur))
    mix_into(s, lowpass(blade_ring(sr, 0.4, 440.0, rng, bright=0.0, tau=0.12), sr, 3000), 0, 0.5)
    hum = add(tone(sr, 1.2, 880.0), scale(tone(sr, 1.2, 883.3), 0.7))  # 3.3 Hz 일렁임
    mix_into(s, mul(hum, env_adsr(sr, 1.2, 0.1, 0.0, 1.0, 0.25)), sec(sr, 0.1), 0.04)
    for k, t0 in enumerate((0.1, 0.4, 0.7, 1.0)):
        tk = mul(tone(sr, 0.08, 2200, 2100), env_exp(sr, 0.08, 0.015))
        mix_into(tk, click(sr, rng, 0.002, 5000), 0, 0.4)
        mix_into(s, tk, sec(sr, t0), 0.16)
        mix_into(s, lowpass(thud(sr, 0.06, 160, 90, 0.012), sr, 500), sec(sr, t0), 0.2)
    mix_into(s, gravel(sr, rng, 0.25, 8, 0.0, 0.2, 0.12), sec(sr, 1.28))
    return reverb(s, sr, size=0.7, decay=0.5, wet=0.2)


# ---- 일도양단(一刀兩斷) 2단 B-α: 내려베기 끝에서 직선 균열 4칸 추가 + HP 30% 이하 일반 적 처형 ----

@sfx('katana_cleave_crack', 'PLAYER_SKILL{weapon:katana,move:guardbreak,phase:cleave}', "일도양단 균열 4칸 더(fx katana_cleave_crack: 몸 hitAt + 40 ms, 칸당 30 ms → 0.12 s 끝). 빠르게 달리는 굵은 갈라짐 12 + 끝 '툭' + 돌 조각·불티. katana_guardbreak 재생 시작 + 140 ms(그 파일 0.1 s = 판정)", -1)
def _katana_cleave_crack(sr, rng):
    s = crack_run(sr, rng, 0.62, 0.12, 12, 2600, 1100, 0.8, 0.55)
    mix_into(s, gravel(sr, rng, 0.4, 9, 0.02, 0.3, 0.25), 0)
    mix_into(s, crackle(sr, rng, 0.3, 5, 0.25), sec(sr, 0.05))
    return reverb(softclip(s, 1.4), sr, size=0.7, decay=0.5, wet=0.12)


@sfx('katana_execute', 'BRANCH_EFFECT{branch:cleave,effect:execute}', "일도양단 처형(HP 30% 이하 일반 적, fx katana_execute impactFrame 0 · 히트스톱 80 ms). 세로로 가르는 '쉭' + 칼끝 틱 → 0.08 s 두 쪽으로 갈라지는 젖은 재 폭발 둘 + 밝은 칼날 울림 D6 + 둔탁한 바닥. 보스·엘리트(×1.5)는 이 소리 없음", 0)
def _katana_execute(sr, rng):
    dur = 0.72
    s = zeros(sec(sr, dur))
    mix_into(s, whoosh(sr, 0.06, rng, 8500, 2200, q=2.0, a=0.05, r=0.6), 0, 0.8)
    mix_into(s, click(sr, rng, 0.003, 6500), 0, 0.8)
    mix_into(s, metal(sr, 0.12, 3100, rng, tau=0.025, jitter=0.02), 0, 0.2)
    t = sec(sr, 0.08)
    mix_into(s, ash_pop(sr, rng, 0.45, 180, 50, 0.9), t, 0.8)
    mix_into(s, ash_pop(sr, rng, 0.4, 150, 45, 0.7), t + sec(sr, 0.025), 0.6)
    mix_into(s, droplets(sr, rng, 0.3, 6, 0.0, 0.2, 500, 1200, 0.25), t)
    mix_into(s, blade_ring(sr, 0.55, 1174.66, rng, bright=1.0, tau=0.2), t, 0.3)
    mix_into(s, thud(sr, 0.2, 110, 40, 0.05), t, 0.6)
    s = softclip(s, 1.3)
    return reverb(tail(s, sr, 0.02), sr, size=0.6, decay=0.5, wet=0.15)


# ---- 명경(明鏡) 2단 B-β: 검기 상한 5단, 패링 시 2단 충전, 5단 일섬 = 분신 2체 ----

@sfx('katana_mirror_parry', 'PARRY_SUCCESS{weapon:katana,branch:mirror}', "명경 패링 = 검기 2단 충전(fx katana_mirror_parry: 거울 면 → 두 조각이 주인공 쪽으로). 1 kHz 위만: 거울 '팅'(유리 A6·E7 근처) → 0.08~0.2 s 날아드는 두 조각 바람 → 0.2 s 닿는 칼날 틱 둘. parry + parry_perfect 위에 겹침(같은 프레임)", -3)
def _katana_mirror_parry(sr, rng):
    dur = 0.5
    s = zeros(sec(sr, dur))
    mix_into(s, glassy(sr, 0.35, 1760.0, rng, tau=0.09), 0, 0.5)
    mix_into(s, glassy(sr, 0.3, 2637.0, rng, tau=0.07), sec(sr, 0.004), 0.3)
    for k in range(2):
        t0 = sec(sr, 0.08 + 0.03 * k)
        mix_into(s, whoosh(sr, 0.12, rng, 6500 - 800 * k, 2200, q=1.8, a=0.2, r=0.4), t0, 0.5)
        mix_into(s, blade_ring(sr, 0.18, [880.0, 1174.66][k], rng, bright=0.6, tau=0.05), t0 + sec(sr, 0.11), 0.3)
    s = highpass(highpass(s, sr, 1000), sr, 1000)
    return reverb(tail(s, sr, 0.02), sr, size=0.5, decay=0.45, wet=0.15)


def _kenki_hi(sr, rng, stage):
    f = {4: 1174.66, 5: 1760.0}[stage]
    dur = {4: 0.95, 5: 1.15}[stage]
    s = blade_ring(sr, dur, f, rng, bright=1.0, tau=0.32 + 0.06 * (stage - 4), vib=0.002)
    mix_into(s, blade_ring(sr, dur * 0.85, f * 0.5, rng, bright=0.5, tau=0.28), sec(sr, 0.004), 0.35)
    if stage == 5:
        mix_into(s, blade_ring(sr, dur * 0.8, 587.33, rng, bright=0.2, tau=0.3), sec(sr, 0.008), 0.25)
        for k in range(5):  # 다섯 초승달이 점선 고리로 이어짐
            mix_into(s, mul(tone(sr, 0.06, 3520, 3500), env_exp(sr, 0.06, 0.015)), sec(sr, 0.12 + 0.07 * k), 0.06)
    hi = mul(tone(sr, 0.7, 3520, 3540), env_adsr(sr, 0.7, 0.03, 0.0, 1.0, 0.6))
    mix_into(s, hi, sec(sr, 0.02), 0.03)
    return reverb(tail(s, sr, 0.04), sr, size=0.6, decay=0.55, wet=0.18)


@sfx('kenki_stage4', 'KENKI_CHANGED{stage:4,delta>0}', "검기 4단 도달(명경 전용, 상한 5). kenki_stage1~3(A4·D5·A5) 다음 단 — 칼날 울림 D6 + 아래 옥타브 D5, 백열 고음. 오를 때만", -4)
def _kenki_stage4(sr, rng):
    return _kenki_hi(sr, rng, 4)


@sfx('kenki_stage5', 'KENKI_CHANGED{stage:5,delta>0}', "검기 5단 도달(명경 최대 — 다음 일섬 분신 2체). 칼날 울림 A6 + A5 + D5 쌓임 + 발밑 다섯 초승달이 이어지는 작은 틱 다섯, 울림. 5단 일섬 = 기존 shadow_clone 두 번(+90 ms)", -3)
def _kenki_stage5(sr, rng):
    return _kenki_hi(sr, rng, 5)


# ===========================================================================
# 대검
# ===========================================================================

# ---- 지진(地震) 2단 A-α: 균열 끝에서 3갈래(±25°, 각 2칸), 공중제비 착지에도 균열 1줄 ----

@sfx('gs_quake_fork', 'PLAYER_CHARGE{weapon:greatsword,phase:release,branch:quake,part:fork}', "지진 세 갈래(fx greatsword_quake_fork: 파쇄 균열 앞머리가 끝에 닿은 순간, 30 ms × 3 = 0.09 s 에 2칸 끝). 세 줄이 동시에 터져 나가는 갈라짐(조금씩 어긋남) + 끝 '툭' 셋 + 땅울림. gs_crack_line_lvN 재생 + 균열 달리는 시간(칸 × 0.06 s) 뒤", -1)
def _gs_quake_fork(sr, rng):
    dur = 0.65
    s = zeros(sec(sr, dur))
    for k, off in enumerate((0.0, 0.006, 0.012)):
        mix_into(s, crack_run(sr, rng, 0.6, 0.09, 6, 2400 - 200 * k, 1000, 0.55, 0.35), sec(sr, off), 0.75)
    mix_into(s, gravel(sr, rng, 0.45, 10, 0.0, 0.3, 0.25), 0)
    return reverb(softclip(s, 1.4), sr, size=0.8, decay=0.5, wet=0.15)


# ---- 반향(反響) 2단 A-β: 퍼펙트 가드 순간 울분 30% 소모해 균열 즉발 반격(차지 1단 위력, 3칸) ----

@sfx('gs_echo_counter', 'PERFECT_GUARD{weapon:greatsword,branch:echo}', "반향 반격(퍼펙트 가드 + 울분 30% 이상, fx greatsword_echo_counter impactFrame 0 → 30 ms × 3 = 3칸). 땅이 되받아치는 낮은 '둥' + 70 ms 간격으로 두 번 메아리치는 징 D4 + 앞으로 달리는 균열 3칸. perfect_guard 와 같은 프레임에 겹침(울분 30% 미만이면 재생 안 함)", 0)
def _gs_echo_counter(sr, rng):
    dur = 0.9
    s = zeros(sec(sr, dur))
    mix_into(s, thud(sr, 0.3, 110, 38, 0.07), 0, 1.0)
    mix_into(s, burst(sr, 0.15, rng, fc=450, q=0.6, tau=0.03, mode='low'), 0, 0.6)
    for k in range(3):  # 메아리 호 두 겹(원음 + 2)
        j = lowpass(jing(sr, 0.5, 293.66, rng, bright=0.3, tau=0.25), sr, 2600 - 700 * k)
        mix_into(s, j, sec(sr, 0.07 * k), 0.35 * (0.6 ** k))
    mix_into(s, crack_run(sr, rng, 0.75, 0.09, 9, 2300, 1000, 0.6, 0.45), sec(sr, 0.005), 0.8)
    s = softclip(s, 1.4)
    return reverb(s, sr, size=0.8, decay=0.55, wet=0.18)


# ---- 거인(巨人) 2단 B-α: 차지 4단(1.6 s ×3.8, 진동 반경 5칸), 차지·꽂기 중 끊기지 않음 ----

@sfx('charge_stage4', 'PLAYER_CHARGE{weapon:greatsword,phase:stage,stage:4}', "차지 4단 도달(거인 전용, 1.6 s · fx greatsword_charge_flash_lv4). charge_stage1~3(징 D4·A4·D5) 다음 단 — '징' A5 백열 + D5·D4 겹침 + 3.5k 반짝임 + 치솟는 바람 + 거인의 낮은 '쿵'. 오를 때만", -2)
def _charge_stage4(sr, rng):
    dur = 1.5
    s = zeros(sec(sr, dur))
    mix_into(s, jing(sr, 1.4, 880.0, rng, bright=1.0, tau=0.75, bend=0.016), 0, 0.5)
    mix_into(s, jing(sr, 1.3, 587.33, rng, bright=0.7, tau=0.7), sec(sr, 0.006), 0.3)
    mix_into(s, jing(sr, 1.2, 293.66, rng, bright=0.3, tau=0.7), sec(sr, 0.01), 0.3)
    hi = mul(tone(sr, 0.9, 3520, 3560), env_adsr(sr, 0.9, 0.02, 0.0, 1.0, 0.8))
    mix_into(s, hi, sec(sr, 0.02), 0.035)
    mix_into(s, whoosh(sr, 0.5, rng, 600, 5500, q=0.9, a=0.6, r=0.35), 0, 0.2)
    mix_into(s, lowpass(thud(sr, 0.4, 70, 34, 0.12), sr, 250), 0, 0.8)
    return reverb(s, sr, size=0.9, decay=0.6, wet=0.22)


@sfx('charge_slam_lv4', 'PLAYER_CHARGE{weapon:greatsword,phase:release,stage:4}', "차지 4단 내려찍기(거인, ×3.8 · fx greatsword_giant_ring 반경 5칸: 0~0.15 s 퍼짐 → 0.15~0.38 s 끌어당김 → 가라앉음). 가장 무거운 강타(×1.9) + 퍼져 나가는 바람 링 → 안으로 빨려드는 바람 → 0.38 s 짓눌림 '쿵' + 오래 가는 땅울림 + 자갈 + 백열 쇳소리. 이 단에서는 charge_slam_lv3·gs_quake_ring 대신 이것 하나", 0)
def _charge_slam_lv4(sr, rng):
    dur = 1.9
    n = sec(sr, dur)
    s = zeros(n)
    mix_into(s, slam_impact(sr, rng, 0.8, 100, 24, 0.13, 1.9), 0, 1.0)
    m1 = sec(sr, 0.15)
    out = svf(noise(sr, 0.15, rng), sr, sweep(sr, m1, 2600, 260), 1.0, 'band')
    mix_into(s, mul(out, env_adsr(sr, 0.15, 0.01, 0.0, 1.0, 0.1)), 0, 0.6)  # 퍼짐
    m2 = sec(sr, 0.23)
    pull = svf(noise(sr, 0.23, rng), sr, sweep(sr, m2, 2200, 330), 1.3, 'band')
    mix_into(s, mul(pull, [(i / m2) ** 1.5 for i in range(m2)]), m1, 0.5)  # 끌어당김
    t = sec(sr, 0.38)
    mix_into(s, thud(sr, 0.35, 95, 30, 0.08), t, 1.0)
    mix_into(s, burst(sr, 0.2, rng, fc=450, q=0.6, tau=0.04, mode='low'), t, 0.7)
    vib = mul(tone(sr, 1.3, 46, 30), [0.55 + 0.45 * math.sin(TAU * 12 * i / sr) for i in range(sec(sr, 1.3))])
    mix_into(s, mul(vib, env_adsr(sr, 1.3, 0.02, 0.0, 1.0, 1.0)), 0, 0.7)  # 땅울림
    mix_into(s, gravel(sr, rng, 1.2, 22, 0.0, 0.9, 0.25), 0)
    mix_into(s, metal(sr, 0.6, 1300, rng, tau=0.12, jitter=0.02), sec(sr, 0.004), 0.18)
    s = softclip(s, 1.6)
    return reverb(s, sr, size=1.1, decay=0.65, wet=0.2)


# ---- 울혈(鬱血) 2단 B-β: 그로기 진입 시 울분 +50%, 그로기 중 퍼펙트 가드 창 2배, 풀리는 순간 울분 100% 면 자동 진동 폭발 ----

@sfx('gs_congest_loop', 'GROGGY{weapon:greatsword,branch:congest,phase:hold}', "울혈 맺힘 루프(0.75 s = fx greatsword_congest_aura 한 바퀴, 그로기 1.5 s 동안 2바퀴). 바퀴마다 무거운 심장 한 번 + 피가 몰리는 낮은 D2 웅웅(한 번 부풂) + 드문 잔불 타닥. groggy_start 와 함께 시작, 그로기 끝에 60 ms 페이드아웃", -10, loop=True)
def _gs_congest_loop(sr, rng):
    dur = 0.75
    n = sec(sr, dur)
    dr = wrap2(lambda x: lowpass(lowpass(x, sr, 220), sr, 400), tone_loop(sr, n, 73.42, 'saw'))
    swell = lfo_loop(sr, n, 1 / 0.75, 0.35, 0.65, 0.75)
    s = scale(mul(dr, swell), 0.8)
    hb = heartbeat(sr, rng, 1.0)
    mix_into(s, hb, sec(sr, 0.05), 0.9)
    pul = wrap2(lambda x: svf(x, sr, 160, 0.8, 'low'), noise_loop(sr, n, rng))
    mix_into(s, mul(pul, swell), 0, 0.35)
    mix_into(s, fade_edges(crackle(sr, rng, dur - 0.08, 4, 0.3), sr, 0.005), sec(sr, 0.03))
    return s


@sfx('gs_congest_burst', 'GROGGY{weapon:greatsword,branch:congest,phase:end,burst:true}', "울혈 폭발(그로기가 풀리는 순간 울분 100% → 전부 소모, 차지 2단 위력 · fx greatsword_congest_burst 반경 2.25칸 · 흔들림 180 ms). 0.04 s 빨려드는 숨 → 핏빛 재 폭발 '퍽'(×1.4) + 강타 + 치솟는 불기둥 + 길게 식는 연기 쉿. 파일 0.04 s = 폭발", 0)
def _gs_congest_burst(sr, rng):
    dur = 1.25
    s = zeros(sec(sr, dur))
    m = sec(sr, 0.04)
    pre = svf(noise(sr, 0.04, rng), sr, sweep(sr, m, 700, 4000), 1.4, 'band')
    mix_into(s, mul(pre, [(i / m) ** 2 for i in range(m)]), 0, 0.5)
    mix_into(s, ash_pop(sr, rng, 0.7, 130, 32, 1.4), m, 1.0)
    mix_into(s, thud(sr, 0.3, 105, 34, 0.07), m, 0.8)
    mix_into(s, flame_roar(sr, rng, 0.6, 220, 2800, 0.03), m + sec(sr, 0.02), 0.6)  # 불기둥
    mix_into(s, droplets(sr, rng, 0.3, 6, 0.0, 0.2, 400, 900, 0.2), m)
    ns = sec(sr, 0.9)
    sm = svf(noise(sr, 0.9, rng), sr, sweep(sr, ns, 4500, 1500), 0.7, 'band')
    mix_into(s, mul(sm, env_adsr(sr, 0.9, 0.08, 0.0, 1.0, 0.75)), sec(sr, 0.25), 0.25)
    s = softclip(s, 1.5)
    return reverb(s, sr, size=0.8, decay=0.55, wet=0.15)


# ===========================================================================
# 단검
# ===========================================================================

# ---- 난무(亂舞) 2단 A-α: 낙인 5스택 기폭 뒤 분신 3 s 상주(연격을 반대편에서 따라 함) ----

@sfx('dagger_frenzy_in', 'BRANCH_EFFECT{branch:frenzy,effect:clone_in}', "난무 분신 나타남(낙인 5스택 기폭 뒤, fx dagger_frenzy_clone_in 0.22 s). 재 알갱이가 모여드는 빨려드는 어두운 역바람 + 점점 촘촘해지는 재 틱 → 0.22 s 형태가 잡히는 딸깍 + 낮은 몸통. 분신 연격음 = swing_dagger 를 rate 0.94 · -6 dB 로 따라 재생(권장)", -3)
def _dagger_frenzy_in(sr, rng):
    dur = 0.42
    s = zeros(sec(sr, dur))
    m = sec(sr, 0.22)
    nz = svf(noise(sr, 0.22, rng), sr, sweep(sr, m, 320, 2600), 1.4, 'band')
    mix_into(s, mul(nz, [(i / m) ** 1.6 for i in range(m)]), 0, 0.55)
    for k in range(14):
        t0 = 0.22 * (1 - (1 - k / 14) ** 0.5)
        mix_into(s, click(sr, rng, 0.002, rng.uniform(2500, 5500)), sec(sr, t0), 0.08 + 0.02 * k)
    mix_into(s, click(sr, rng, 0.004, 3200), m, 0.6)
    mix_into(s, thud(sr, 0.12, 140, 60, 0.03), m, 0.5)
    lo = mul(tone(sr, 0.22, 60, 130), [(i / m) ** 1.2 for i in range(m)])
    mix_into(s, lo, 0, 0.2)
    return reverb(tail(s, sr, 0.02), sr, size=0.5, decay=0.45, wet=0.18)


@sfx('dagger_frenzy_out', 'BRANCH_EFFECT{branch:frenzy,effect:clone_out}', "난무 분신 사라짐(3 s 끝, fx dagger_frenzy_clone_out 0.41 s). 발부터 재로 부서져 흩어지는 알갱이 + 위로 빠지는 바람 + 아주 낮게 꺼지는 숨", -6)
def _dagger_frenzy_out(sr, rng):
    dur = 0.5
    s = zeros(sec(sr, dur))
    mix_into(s, gravel(sr, rng, 0.45, 16, 0.0, 0.35, 0.2), 0)
    ns = sec(sr, 0.4)
    w = svf(noise(sr, 0.4, rng), sr, sweep(sr, ns, 1200, 4500), 1.2, 'band')
    mix_into(s, mul(w, env_adsr(sr, 0.4, 0.05, 0.0, 1.0, 0.3)), 0, 0.35)
    lo = mul(tone(sr, 0.35, 120, 50), env_adsr(sr, 0.35, 0.02, 0.0, 1.0, 0.3))
    mix_into(s, lowpass(lo, sr, 300), 0, 0.3)
    return reverb(tail(s, sr, 0.02), sr, size=0.5, decay=0.45, wet=0.15)


# ---- 출혈(出血) 2단 A-β: 기폭 = 즉시 60% + 4 s 출혈, 출혈 중 처치되면 남은 낙인이 반경 3칸 적 1명에게 옮겨감 ----

@sfx('dagger_bleed', 'BRAND_BURST{branch:bleed}', "출혈 시작(기폭 = 60% + 4 s 출혈, fx dagger_brand_bleed). 젖은 찢김 + 핏방울 넷 + 옅은 지짐. brand_burst 와 같은 프레임에 겹침(그 파일 0.06 s = 폭발이라 같은 시작). 0.5 s 출혈 틱에는 소리 없음(피격 번쩍임만)", -3)
def _dagger_bleed(sr, rng):
    dur = 0.7
    s = zeros(sec(sr, dur))
    rip = lowpass(tear(sr, 0.16, rng, 1200, 3200, rate=60.0, q=1.3), sr, 3500)
    mix_into(s, rip, sec(sr, 0.06), 0.6)
    mix_into(s, droplets(sr, rng, 0.55, 5, 0.1, 0.5, 380, 750, 0.35), sec(sr, 0.06))
    mix_into(s, sizzle(sr, rng, 0.3, fc=4200, tau=0.08), sec(sr, 0.08), 0.15)
    return tail(s, sr, 0.02)


@sfx('dagger_brand_hop', 'BRANCH_EFFECT{branch:bleed,effect:transfer}', "출혈 낙인이 옮겨감(출혈 중 처치 → 반경 3칸 적 1명, fx dagger_brand_hop 이동 약 0.2 s). 꼬리를 끄는 지짐 바람(혜성 '츠츠') → 0.2 s 도착 '칙'(brand_apply 결). 도착에 brand_apply 를 따로 울리지 않아도 됨", -6)
def _dagger_brand_hop(sr, rng):
    dur = 0.34
    s = zeros(sec(sr, dur))
    ns = sec(sr, 0.2)
    w = svf(noise(sr, 0.2, rng), sr, sweep(sr, ns, 2500, 5200), 1.6, 'band')
    w = mul(w, [0.6 + 0.4 * math.sin(TAU * 45 * i / sr) for i in range(ns)])
    mix_into(s, mul(w, env_adsr(sr, 0.2, 0.03, 0.0, 1.0, 0.05)), 0, 0.5)
    mix_into(s, sizzle(sr, rng, 0.12, fc=5600, tau=0.04, q=1.0), sec(sr, 0.2), 0.7)
    mix_into(s, click(sr, rng, 0.003, 4200), sec(sr, 0.2), 0.5)
    return tail(s, sr, 0.02)


# ---- 비도(飛刀) 2단 B-α: 투척 5개(45°), 박힌 단검 위치로 그림자 걸음 ----

@sfx('dagger_flyknife_throw', 'PLAYER_SKILL{weapon:dagger,move:fan_throw,branch:flyknife}', "비도 투척 다섯 자루(45°, dagger_fan_throw 의 5자루판). 손목 딸깍 + 18 ms 간격 높은 바람 다섯(음높이 모두 다름) + 칼날 틱. 비도 런에서는 dagger_fan_throw 대신", -2)
def _dagger_flyknife_throw(sr, rng):
    s = zeros(sec(sr, 0.42))
    mix_into(s, click(sr, rng, 0.003, 4800), 0, 0.6)
    pitches = [(7200, 3000), (8200, 3500), (6400, 2600), (7700, 3200), (6900, 2800)]
    for k, (f0, f1) in enumerate(pitches):
        t0 = sec(sr, 0.018 * k)
        mix_into(s, whoosh(sr, 0.16, rng, f0, f1, q=2.0, a=0.08, r=0.7), t0, 0.5)
        mix_into(s, metal(sr, 0.05, 3400 + 250 * k, rng, tau=0.012, jitter=0.03), t0, 0.07)
    return tail(s, sr, 0.02)


@sfx('dagger_knife_stick', 'BRANCH_EFFECT{branch:flyknife,effect:stick}', "비도 단검이 바닥에 박힘(fx dagger_stuck_blade f0, 2 s 유지). 짧게 꽂히는 '톡' + 날이 떠는 쇠 울림(30 Hz 떨림). 다섯이 거의 함께 떨어지면 20 ms 규칙으로 묶이므로 30~60 ms 시차 권장", -7)
def _dagger_knife_stick(sr, rng):
    dur = 0.36
    s = zeros(sec(sr, dur))
    mix_into(s, burst(sr, 0.025, rng, fc=2400, q=0.8, tau=0.005), 0, 0.9)
    mix_into(s, thud(sr, 0.06, 320, 190, 0.012), 0, 0.6)
    tw = metal(sr, 0.3, 1450, rng, partials=[(1, 1), (2.7, 0.3), (5.1, 0.12)], tau=0.08, jitter=0.01)
    tw = mul(tw, [0.55 + 0.45 * math.sin(TAU * 30 * i / sr) for i in range(len(tw))])
    mix_into(s, tw, sec(sr, 0.004), 0.3)
    return tail(s, sr, 0.02)


@sfx('dagger_knife_step', 'PLAYER_SECONDARY{kind:shadowstep,target:knife}', "비도: 박힌 단검 자리로 그림자 걸음(과열 −10%). 도착 순간 단검을 뽑아 드는 '칭'(위로 긁는 쇠) + 단검이 재로 부서짐 + 낮은 몸통. 기존 shadowstep 의 끝 딸깍(0.26 s)에 맞춰 겹침", -3)
def _dagger_knife_step(sr, rng):
    dur = 0.45
    s = zeros(sec(sr, dur))
    ns = sec(sr, 0.09)
    sc = svf(noise(sr, 0.09, rng), sr, sweep(sr, ns, 2000, 6500), 2.2, 'band')
    mix_into(s, mul(sc, env_adsr(sr, 0.09, 0.02, 0.0, 1.0, 0.05)), 0, 0.6)
    mix_into(s, blade_ring(sr, 0.25, 1174.66, rng, bright=0.5, tau=0.06), sec(sr, 0.03), 0.25)
    mix_into(s, gravel(sr, rng, 0.3, 9, 0.06, 0.25, 0.15), 0)
    mix_into(s, thud(sr, 0.1, 130, 60, 0.025), 0, 0.4)
    return reverb(tail(s, sr, 0.02), sr, size=0.5, decay=0.45, wet=0.15)


# ---- 열풍(熱風) 2단 B-β: 이동기마다 과열↑, 50% 이상 빨라짐, 100% 폭발 ×2 + 화상 + 무적 0.5 s ----

@sfx('dagger_hotwind_loop', 'OVERHEAT{weapon:dagger,branch:hotwind,over50:true,moving:true}', "열풍 달아오른 질주 루프(1.12 s = fx dagger_hotwind_trail 280 ms × 4). 발 뒤로 흘러가는 낮은 불혀(3.57 Hz 일렁임) + 열 아지랑이 쉿 + 드문 타닥. 과열 50% 이상 + 이동 중일 때만, 멈추거나 50% 미만이면 120 ms 페이드아웃", -12, loop=True)
def _dagger_hotwind_loop(sr, rng):
    dur = 1.12
    n = sec(sr, dur)
    s = wrap2(lambda x: svf(x, sr, 650, 0.8, 'low'), noise_loop(sr, n, rng))
    fl = [a * b for a, b in zip(lfo_loop(sr, n, 1 / 0.28, 0.3, 0.7), lfo_loop(sr, n, 1 / 0.56, 0.15, 0.85, 0.2))]
    s = mul(s, fl)
    haze = wrap2(lambda x: svf(x, sr, 4200, 0.9, 'band'), noise_loop(sr, n, rng))
    mix_into(s, mul(haze, lfo_loop(sr, n, 1 / 0.28, 0.3, 0.7, 0.5)), 0, 0.08)
    mix_into(s, fade_edges(crackle(sr, rng, dur - 0.06, 7, 0.35), sr, 0.005), sec(sr, 0.025))
    return s


@sfx('dagger_hotwind_burst', 'OVERHEAT{full:true,branch:hotwind}', "열풍 과열 폭발(반경 ×2 · 화상 3 s · 무적 0.5 s, fx dagger_hotwind_burst — dagger_overheat_burst 를 교체하듯 이 소리가 overheat_burst 를 교체). 큰 재 폭발(×1.8) + 엇갈린 작은 폭발 여섯 + 사방으로 눕는 불혀 '화르륵' + 길게 식는 증기", 0)
def _dagger_hotwind_burst(sr, rng):
    dur = 1.75
    s = zeros(sec(sr, dur))
    mix_into(s, ash_pop(sr, rng, 0.9, 115, 28, 1.8), 0, 1.0)
    for t0, f0, g in [(0.04, 200, 0.55), (0.08, 165, 0.5), (0.13, 220, 0.45), (0.18, 180, 0.4), (0.24, 205, 0.35), (0.3, 170, 0.3)]:
        mix_into(s, ash_pop(sr, rng, 0.35, f0, 50, 0.8), sec(sr, t0), g)
    mix_into(s, flame_roar(sr, rng, 0.8, 300, 3200, 0.03), sec(sr, 0.02), 0.7)
    ns = sec(sr, 1.3)
    st = svf(noise(sr, 1.3, rng), sr, sweep(sr, ns, 6500, 2300), 0.7, 'band')
    mix_into(s, mul(st, env_adsr(sr, 1.3, 0.08, 0.0, 1.0, 1.1)), sec(sr, 0.3), 0.3)
    mix_into(s, crackle(sr, rng, 1.3, 26, 0.3), sec(sr, 0.15))
    s = softclip(s, 1.7)
    return reverb(s, sr, size=0.9, decay=0.55, wet=0.15)


# ===========================================================================
# 활
# ===========================================================================

# ---- 연궁(連弓) 2단 A-α: 연사 3발마다 1발이 2갈래로 분열 ----

@sfx('bow_arrow_split', 'PLAYER_ATTACK{weapon:bow,move:rapid,branch:split,phase:split}', "연궁 분열(연사 3발마다, fx bow_arrow_split impactFrame 0 · ±12°). 갈림목의 작은 '팅' + 위·아래로 벌어지는 짧은 바람 둘. 그 발의 bow_rapidN 위에 겹침. 패시브 '흩어진 촉'의 벽·사거리 끝 분열에도 재사용 권장", -5)
def _bow_arrow_split(sr, rng):
    s = zeros(sec(sr, 0.24))
    mix_into(s, metal(sr, 0.1, 3500, rng, partials=GLASS, tau=0.02, jitter=0.01), 0, 0.4)
    mix_into(s, click(sr, rng, 0.002, 6000), 0, 0.5)
    mix_into(s, whoosh(sr, 0.15, rng, 4500, 6800, q=1.8, a=0.1, r=0.7), sec(sr, 0.01), 0.45)
    mix_into(s, whoosh(sr, 0.15, rng, 4500, 3000, q=1.8, a=0.1, r=0.7), sec(sr, 0.016), 0.45)
    return tail(s, sr, 0.02)


# ---- 무한통(無限筒) 2단 A-β: 재장전 없음, 처치 시 화살 +3, 박힌 화살 밟으면 +1 ----

@sfx('bow_arrow_recall', 'BRANCH_EFFECT{branch:quiver,effect:recall}', "무한통 화살 회수(박힌 화살 밟기 +1 · 처치 +3, fx bow_arrow_recall). 화살통에 화살대가 떨어져 들어가는 나무 딸깍 넷 + 위로 솟는 불씨 블립 다섯 + 작게 오르는 바람. 처치 +3 은 같은 파일 한 번", -6)
def _bow_arrow_recall(sr, rng):
    dur = 0.45
    s = zeros(sec(sr, dur))
    for k in range(4):
        t0 = sec(sr, 0.02 + 0.035 * k)
        mix_into(s, thud(sr, 0.04, rng.uniform(520, 700), 380, 0.008), t0, 0.5)
        mix_into(s, click(sr, rng, 0.002, 3800), t0, 0.3)
    for k in range(5):
        f = 1200 * (1.15 ** k)
        b = mul(tone(sr, 0.05, f, f * 1.4), env_exp(sr, 0.05, 0.015))
        mix_into(s, b, sec(sr, 0.1 + 0.04 * k), 0.12)
    ns = sec(sr, 0.3)
    w = svf(noise(sr, 0.3, rng), sr, sweep(sr, ns, 1500, 5000), 1.3, 'band')
    mix_into(s, mul(w, env_adsr(sr, 0.3, 0.1, 0.0, 1.0, 0.15)), sec(sr, 0.05), 0.2)
    return tail(s, sr, 0.02)


# ---- 필중(必中) 2단 B-α: 정밀 조준 1.2 → 2.0 s, 정밀 조준 중 완벽 놓기 = 치명 확정 ----

@sfx('bow_deadeye_lock', 'BREATH_FOCUS{weapon:bow,branch:deadeye,phase:full}', "필중 조준 다 좁혀짐(fx bow_deadeye_scope 진행도 100% = f5). 괄호 넷이 좁혀 드는 빨라지는 틱(점점 높게) → 0.15 s 맑은 '딸깍-팅' + 아주 희미한 D7 + 낮은 심장 한 번. 이 뒤 완벽 놓기 = 치명 확정. 이어서 bow_deadeye_hold", -4)
def _bow_deadeye_lock(sr, rng):
    dur = 0.6
    s = zeros(sec(sr, dur))
    for k, t0 in enumerate((0.0, 0.06, 0.1, 0.13)):
        tk = mul(tone(sr, 0.03, 1400 + 250 * k, 1350 + 250 * k), env_exp(sr, 0.03, 0.008))
        mix_into(s, tk, sec(sr, t0), 0.25)
        mix_into(s, click(sr, rng, 0.002, 4000 + 500 * k), sec(sr, t0), 0.3)
    t = sec(sr, 0.15)
    mix_into(s, click(sr, rng, 0.004, 6500), t, 0.8)
    mix_into(s, bell(sr, 0.4, 1760.0, rng, tau=0.15), t, 0.3)
    sh = mul(tone(sr, 0.4, 2349.3, 2352.0), env_adsr(sr, 0.4, 0.02, 0.0, 1.0, 0.35))
    mix_into(s, sh, t, 0.03)
    mix_into(s, lowpass(thud(sr, 0.15, 70, 42, 0.04), sr, 250), t, 0.7)
    return reverb(tail(s, sr, 0.02), sr, size=0.6, decay=0.5, wet=0.15)


@sfx('bow_deadeye_hold', 'BREATH_FOCUS{weapon:bow,branch:deadeye,phase:hold}', "필중 조준 유지 루프(0.72 s = fx bow_deadeye_scope 루프 360 ms × 2). 멈춘 공기의 좁은 숨결(900 Hz) + 360 ms 마다 아주 작은 맥박 + 희미한 D7 한 가닥. 놓거나 취소하면 60 ms 페이드아웃. 숨 감속 중 다른 소리 아래 깔리게 아주 작게", -14, loop=True)
def _bow_deadeye_hold(sr, rng):
    dur = 0.72
    n = sec(sr, dur)
    air = wrap2(lambda x: svf(x, sr, 900, 3.0, 'band'), noise_loop(sr, n, rng))
    s = mul(air, lfo_loop(sr, n, 1 / 0.36, 0.25, 0.75, 0.75))
    hum = mul(tone_loop(sr, n, 2349.3, 'sine', 0.25), lfo_loop(sr, n, 1 / 0.36, 0.5, 0.5, 0.0))
    mix_into(s, hum, 0, 0.02)
    for t0 in (0.04, 0.4):
        mix_into(s, lowpass(thud(sr, 0.12, 64, 42, 0.03), sr, 200), sec(sr, t0), 0.5)
    return s


# ---- 천공(穿空) 2단 B-β: 완벽 놓기 연달아 = '연결' 스택(놓치면 0), 3스택 화살 = 벽 관통 + 지나간 선이 0.5 s 뒤 터짐 ----

def _link(sr, rng, stack):
    f = {1: 587.33, 2: 880.0, 3: 1174.66}[stack]
    dur = {1: 0.45, 2: 0.55, 3: 0.8}[stack]
    s = zeros(sec(sr, dur))
    pk = mul(pluck(sr, dur, f, rng, damp=0.997, bright=0.9), env_exp(sr, dur, 0.15 + 0.05 * stack))
    mix_into(s, highpass(pk, sr, 400), 0, 0.5)
    mix_into(s, glassy(sr, dur - 0.05, f * 2, rng, tau=0.12 + 0.04 * stack), sec(sr, 0.004), 0.25)
    mix_into(s, click(sr, rng, 0.002, 5500), 0, 0.4)
    if stack == 3:
        mix_into(s, latch(sr, rng, 0.6, heavy=0.0), sec(sr, 0.02), 0.6)
        mix_into(s, bell(sr, 0.7, 587.33, rng, tau=0.3), sec(sr, 0.03), 0.2)
        return reverb(tail(s, sr, 0.03), sr, size=0.6, decay=0.5, wet=0.18)
    return tail(s, sr, 0.02)


@sfx('bow_link1', 'BRANCH_EFFECT{branch:skypierce,effect:link,stack:1}', "천공 연결 1스택(완벽 놓기 연속, fx bow_link_stack 행 1). 화살촉 '틱' + 팽팽한 시위 하모닉 D5 + 유리 반짝임. bow_release_perfect 위에 겹침", -6)
def _bow_link1(sr, rng):
    return _link(sr, rng, 1)


@sfx('bow_link2', 'BRANCH_EFFECT{branch:skypierce,effect:link,stack:2}', "천공 연결 2스택. 시위 하모닉 A5 + 반짝임", -5)
def _bow_link2(sr, rng):
    return _link(sr, rng, 2)


@sfx('bow_link3', 'BRANCH_EFFECT{branch:skypierce,effect:link,stack:3}', "천공 연결 3스택(다음 화살 = 벽 관통 + 선 폭발). 시위 하모닉 D6 + 걸쇠 '철컥'(고리가 이어짐) + 종 D5, 짧은 울림", -4)
def _bow_link3(sr, rng):
    return _link(sr, rng, 3)


@sfx('bow_link_break', 'BRANCH_EFFECT{branch:skypierce,effect:link_break}', "천공 연결 끊김(완벽 놓기를 놓쳐 스택 0). 힘 빠진 낮은 시위 '퉁'(D3, 둔하게) + 내려앉는 짧은 음 + 작은 나무 틱. 1스택 이상일 때만", -7)
def _bow_link_break(sr, rng):
    s = zeros(sec(sr, 0.36))
    pk = mul(pluck(sr, 0.3, 146.83, rng, damp=0.985, bright=0.5), env_exp(sr, 0.3, 0.07))
    mix_into(s, lowpass(pk, sr, 1200), 0, 0.7)
    dn = mul(tone(sr, 0.18, 620, 310), env_exp(sr, 0.18, 0.05))
    mix_into(s, dn, sec(sr, 0.02), 0.15)
    mix_into(s, thud(sr, 0.04, 380, 260, 0.008), 0, 0.4)
    return tail(s, sr, 0.02)


@sfx('bow_skypierce', 'BRANCH_EFFECT{branch:skypierce,effect:line}', "천공 3스택 화살(벽 관통 + 지나간 선이 0.5 s 뒤 터짐, fx bow_skypierce_line burstAtMs 500). 하늘을 찢는 화살 비명(3k→9k) + 0.06 s 벽을 뚫는 돌·나무 '퍽' + 선 위를 흐르는 가는 반짝임 → 0.5 s 선을 따라 번지는 파열 아홉 + 낮은 폭음 + 칼날 울림 D6(일섬 선 결). 파일 0.5 s = 선 폭발", -1)
def _bow_skypierce(sr, rng):
    dur = 1.3
    s = zeros(sec(sr, dur))
    mix_into(s, whoosh(sr, 0.22, rng, 3000, 9000, q=1.6, a=0.05, r=0.8), 0, 0.7)
    mix_into(s, mul(pluck(sr, 0.3, 110, rng, damp=0.99, bright=0.6), env_exp(sr, 0.3, 0.08)), 0, 0.4)
    t1 = sec(sr, 0.06)
    mix_into(s, burst(sr, 0.05, rng, fc=1600, q=0.8, tau=0.01), t1, 0.6)
    mix_into(s, thud(sr, 0.08, 260, 140, 0.015), t1, 0.4)
    mix_into(s, gravel(sr, rng, 0.2, 5, 0.0, 0.12, 0.2), t1)
    sh = mul(add(tone(sr, 0.42, 2637.0), scale(tone(sr, 0.42, 2650.0), 0.7)), env_adsr(sr, 0.42, 0.05, 0.0, 1.0, 0.1))
    mix_into(s, sh, sec(sr, 0.08), 0.03)  # 선 위 반짝임
    t = sec(sr, 0.5)
    for k in range(9):  # 선을 따라 번지는 파열
        mix_into(s, burst(sr, 0.05, rng, fc=rng.uniform(1500, 3200), q=0.8, tau=0.01), t + sec(sr, 0.011 * k), 0.5 - 0.03 * k)
    mix_into(s, thud(sr, 0.3, 95, 34, 0.06), t, 0.9)
    mix_into(s, burst(sr, 0.15, rng, fc=420, q=0.6, tau=0.03, mode='low'), t, 0.6)
    mix_into(s, blade_ring(sr, 0.6, 1174.66, rng, bright=0.9, tau=0.2), t, 0.25)
    s = softclip(s, 1.3)
    return reverb(s, sr, size=0.8, decay=0.55, wet=0.18)
