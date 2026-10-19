# -*- coding: utf-8 -*-
"""
P21 음향 1차 — 어두운 성인 톤 · 잔혹한 현실 전투 · 상흔. round 'P21'.

build.py 가 sfx_p16 다음(마지막)에 import 한다. 시드 = 1000 + 등록 순서 — 새 소리는 끝에 붙으므로 기존 370개는 바이트 불변.
**새 효과음은 이 파일 끝에만.**

근거: 결정 `parts/producer/decisions/2026-10-19-P21-dark-brutal.md` §2·§4 음향, 계약 `contracts/dark-brutal.md` §2(이벤트)·§9(키).
도영 님 '19세 게임처럼 … 어둡고 칙칙하고 두려운 … 전투 양상도 … 잔인해지고 진짜 현실 전투 같게'.

원칙: 기존 타격음(hit_<무기>·hit_player) **위에 겹치는 층**이다 — 쇠·바람은 기존 소리가 맡고, 이 층은 살·뼈·피·숨만.
저역·질감 위주, 5 kHz 위는 거의 없음(lowpass), 길이 짧게(층 0.2~0.4 s). 목소리(성대음)는 쓰지 않는다 — 신음은 숨·'끙'의
노이즈 포먼트(sfx_stage61.breath/grunt)만. 트리거 = dark-brutal §2 이벤트 문자열 그대로(P19 free-combat 과 같은 꼴).
"""
from build import *  # noqa: F401,F403
from build import SFX, gravel, droplets, tear  # noqa: F401
from sfx_core61 import punch, flesh, crunch, rustle, sub, wood_tok, snap, variant  # noqa: F401
from sfx_stage61 import breath, grunt, scuff, body_fall as _thump

ROUND21 = 'P21'


def sfx21(name, trigger, note, gain_db=0.0, loop=False, category='combat'):
    """sfx() + round 표시(P21)."""
    def deco(fn):
        sfx(name, trigger, note, gain_db, loop=loop, category=category)(fn)
        SFX[name]['round'] = ROUND21
        return fn
    return deco


def variant21(base, k, note):
    def deco(fn):
        variant(base, k, note)(fn)
        SFX['%s_v%d' % (base, k)]['round'] = ROUND21
        return fn
    return deco


# ===========================================================================
# 재료 — 살 · 피 · 뼈 · 숯
# ===========================================================================

def wet(sr, rng, dur, fc=650, rate=30.0, q=2.0, g=1.0):
    """젖은 살 '철퍽': 좁은 대역 노이즈를 무작위로 떨리는 진폭(rate Hz)으로 + 낮은 거품 몇."""
    n = sec(sr, dur)
    s = svf(noise(sr, dur, rng), sr, sweep(sr, n, fc * 1.25, fc * 0.8), q, 'band')
    am = normalize(lowpass([rng.uniform(0, 1) ** 3 for _ in range(n)], sr, rate), 1.0)
    s = mul(mul(s, [0.25 + 0.75 * a for a in am]), env_adsr(sr, dur, 0.004, 0.0, 1.0, dur * 0.8, curve=1.6))
    mix_into(s, droplets(sr, rng, dur, 3, 0.0, dur * 0.6, fc * 0.4, fc * 0.9, 0.35), 0)
    return scale(s, g)


def spurt(sr, rng, dur, times, fc=1400, g=1.0):
    """피가 뿜어짐: 맥박처럼 끊기는 젖은 분사(times 마다 한 번, 점점 약하게)."""
    s = zeros(sec(sr, dur))
    for k, t in enumerate(times):
        d = 0.06 + 0.01 * k
        p = svf(noise(sr, d, rng), sr, fc * rng.uniform(0.85, 1.1), 1.2, 'band')
        p = mul(p, env_adsr(sr, d, 0.006, 0.0, 1.0, d * 0.75, curve=1.4))
        mix_into(s, p, sec(sr, t), g * (0.8 ** k))
    return lowpass(s, sr, 4200)


def splat(sr, rng, fc=520, g=1.0, drops=5):
    """바닥에 '철썩': 낮은 액체 때림 + 짧은 '착' + 뒤따르는 방울."""
    s = zeros(sec(sr, 0.3))
    mix_into(s, burst(sr, 0.09, rng, fc=fc, q=0.7, tau=0.016, mode='low'), 0, 1.0)
    mix_into(s, lowpass(snap(sr, rng, 1300, 0.012, 0.002), sr, 3200), 0, 0.5)
    mix_into(s, wet(sr, rng, 0.08, fc * 1.4, 45.0, 1.6), sec(sr, 0.004), 0.5)
    mix_into(s, droplets(sr, rng, 0.3, drops, 0.03, 0.22, 380, 1100, 0.22), 0)
    return scale(s, g)


def cracks(sr, rng, count, t0, t1, fc=(1000, 2600), hold=5, g=1.0, dur=0.12):
    """뼈 부러짐: 샘플 홀드로 거칠게 만든 짧은 '딱' 무리(울림 없음, 4 kHz 아래)."""
    s = zeros(sec(sr, dur))
    for _ in range(count):
        c = burst(sr, 0.02, rng, fc=rng.uniform(*fc), q=1.1, tau=rng.uniform(0.0018, 0.004))
        mix_into(s, c, sec(sr, rng.uniform(t0, t1)), rng.uniform(0.5, 1.0))
    return scale(lowpass(crunch(s, hold), sr, 4000), g)


# ===========================================================================
# 1. 살 · 뼈 타격 층 (enemy:gore — 적중마다, 기존 hit_<무기> 위)
# ===========================================================================

def _flesh_slash(sr, rng, fc=650, sl=(3200, 700), body=(180, 80)):
    dur = 0.24
    s = zeros(sec(sr, dur))
    n = sec(sr, 0.07)
    cut = svf(noise(sr, 0.07, rng), sr, sweep(sr, n, sl[0], sl[1]), 1.1, 'band')
    mix_into(s, mul(cut, env_adsr(sr, 0.07, 0.006, 0.0, 1.0, 0.06)), 0, 0.5)      # 천·살을 가르는 '슥'
    mix_into(s, wet(sr, rng, 0.18, fc, 32.0, 2.0), sec(sr, 0.005), 0.9)          # 젖은 살 '철퍽'
    mix_into(s, punch(sr, body[0], body[1], 0.08, 0.02, 1.3), 0, 0.35)            # 아래 무게(얕게)
    return lowpass(softclip(s, 1.3), sr, 5000)


@sfx21('flesh_slash', 'enemy:gore{cut:slash}', "P21 새 — 젖은 베임(칼·대검 베기 적중마다, hit_<무기> 위에 겹치는 살 층). 0 s 천·살을 가르는 낮은 '슥'(3.2k→700 Hz) + 젖은 살 '철퍽'(650 Hz 좁은 대역, 떨리는 진폭) + 얕은 몸통(180→80 Hz). 0.24 s, 5 kHz 위 없음 — 쇠·바람은 기존 타격음이 맡는다. 변주 _v2·_v3", -3)
def _flesh_slash21(sr, rng):
    return _flesh_slash(sr, rng)


@variant21('flesh_slash', 2, "젖은 베임 변주 2 — 살 560 Hz, 가름 2.8k→600")
def _flesh_slash_v2(sr, rng):
    return _flesh_slash(sr, rng, fc=560, sl=(2800, 600), body=(165, 72))


@variant21('flesh_slash', 3, "젖은 베임 변주 3 — 살 760 Hz, 가름 3.6k→800")
def _flesh_slash_v3(sr, rng):
    return _flesh_slash(sr, rng, fc=760, sl=(3600, 800), body=(195, 86))


def _flesh_stab(sr, rng, fc=450, sp=(0.045, 0.105, 0.175), spf=1400, body=(140, 60)):
    dur = 0.34
    s = zeros(sec(sr, dur))
    mix_into(s, punch(sr, body[0], body[1], 0.1, 0.025, 1.6), 0, 0.6)             # 날이 들어가는 '푹'
    mix_into(s, wet(sr, rng, 0.13, fc, 26.0, 2.2), 0, 0.85)                        # 진한 살
    mix_into(s, spurt(sr, rng, 0.3, sp, spf), sec(sr, 0.01), 0.55)                 # 맥박처럼 뿜음
    return lowpass(softclip(s, 1.4), sr, 4500)


@sfx21('flesh_stab', 'enemy:gore{cut:stab}', "P21 새 — 찌름·뿜음(단검·칼 찌르기 적중마다, hit_<무기> 위 살 층). 0 s 날이 들어가는 '푹'(140→60 Hz) + 진한 살(450 Hz) → 45·105·175 ms 맥박처럼 끊기며 뿜는 피(1.4 kHz 젖은 분사, 점점 약하게). 0.34 s. 변주 _v2·_v3", -3)
def _flesh_stab21(sr, rng):
    return _flesh_stab(sr, rng)


@variant21('flesh_stab', 2, "찌름 변주 2 — 살 400 Hz, 뿜음 40·95·160 ms(1.25 kHz)")
def _flesh_stab_v2(sr, rng):
    return _flesh_stab(sr, rng, fc=400, sp=(0.04, 0.095, 0.16), spf=1250, body=(130, 56))


@variant21('flesh_stab', 3, "찌름 변주 3 — 살 520 Hz, 뿜음 두 번(50·120 ms, 1.6 kHz)")
def _flesh_stab_v3(sr, rng):
    return _flesh_stab(sr, rng, fc=520, sp=(0.05, 0.12), spf=1600, body=(150, 64))


def _bone_crush(sr, rng, body=(90, 40), n1=7, fc=(1000, 2600), hold=5):
    dur = 0.32
    s = zeros(sec(sr, dur))
    mix_into(s, punch(sr, body[0], body[1], 0.22, 0.05, 1.8, 0.03), 0, 0.75)       # 내려친 무게
    mix_into(s, cracks(sr, rng, n1, 0.0, 0.035, fc, hold), 0, 0.75)                 # 뼈가 꺾이는 '우두둑'
    mix_into(s, cracks(sr, rng, 3, 0.0, 0.03, (700, 1600), hold + 2), sec(sr, 0.055), 0.4)   # 쪼개진 뼈가 한 번 더
    mix_into(s, wet(sr, rng, 0.14, 380, 22.0, 1.8), sec(sr, 0.008), 0.45)
    return lowpass(softclip(s, 1.8), sr, 4200)


@sfx21('bone_crush', 'enemy:gore{cut:crush}', "P21 새 — 뼈 부러짐(대검 내려치기·강타 적중마다, hit_greatsword 위 뼈 층). 0 s 내려친 무게(90→40 Hz) + 뼈가 꺾이는 '우두둑'(1~2.6 kHz 짧은 딱 7개를 35 ms 안에, 거칠게) → 55 ms 쪼개진 뼈 한 번 더 + 젖은 살(380 Hz). 0.32 s. 변주 _v2·_v3", -4.5)
def _bone_crush21(sr, rng):
    return _bone_crush(sr, rng)


@variant21('bone_crush', 2, "뼈 부러짐 변주 2 — 몸통 82→36 Hz, 딱 9개(더 잘게)")
def _bone_crush_v2(sr, rng):
    return _bone_crush(sr, rng, body=(82, 36), n1=9, fc=(900, 2300), hold=6)


@variant21('bone_crush', 3, "뼈 부러짐 변주 3 — 몸통 98→44 Hz, 딱 5개(굵게)")
def _bone_crush_v3(sr, rng):
    return _bone_crush(sr, rng, body=(98, 44), n1=5, fc=(800, 2000), hold=7)


def _arrow_stick(sr, rng, body=(220, 90), fc=700):
    dur = 0.24
    s = zeros(sec(sr, dur))
    mix_into(s, lowpass(snap(sr, rng, 1800, 0.01, 0.0018), sr, 3500), 0, 0.45)       # 촉이 살을 뚫는 '툭'
    mix_into(s, punch(sr, body[0], body[1], 0.07, 0.018, 1.5), 0, 0.7)
    mix_into(s, wet(sr, rng, 0.08, fc, 40.0, 2.0), sec(sr, 0.003), 0.55)
    mix_into(s, wood_tok(sr, rng, 640, 0.04, 0.007, 0.5), sec(sr, 0.006), 0.22)      # 화살대가 멈추는 나무 '톡'
    return lowpass(s, sr, 4500)


@sfx21('arrow_stick', 'enemy:gore{cut:pierce}', "P21 새 — 화살이 살에 박힘(활 적중마다 hit_bow 위 살 층 · 주인공 몸에 화살이 박힐 때 player:wounded{arrows 증가} · 꿰어 고정 enemy:death-variant{pinned} 의 몸 쪽). 0 s 촉이 살을 뚫는 '툭'(1.8 kHz, 3.5 kHz 아래) + 박히는 몸통(220→90 Hz) + 젖은 살(700 Hz) + 화살대가 멈추는 나무 '톡'. 0.24 s. 화살대 떨림은 hit_bow 가 맡으므로 없음. 변주 _v2", -0.5)
def _arrow_stick21(sr, rng):
    return _arrow_stick(sr, rng)


@variant21('arrow_stick', 2, "박힘 변주 2 — 몸통 200→82 Hz, 살 620 Hz")
def _arrow_stick_v2(sr, rng):
    return _arrow_stick(sr, rng, body=(200, 82), fc=620)


def _blood_splat(sr, rng, fc=520, drops=5):
    return lowpass(tail(splat(sr, rng, fc, 1.0, drops), sr, 0.02), sr, 4000)


@sfx21('blood_splat', 'enemy:gore{amount:2+}', "P21 새 — 피가 바닥에 튐(분출 amount ≥ 2 인 적중 · 시체 밑 웅덩이 시작). 낮은 액체 때림 '철썩'(520 Hz 저역) + 짧은 '착' + 뒤따르는 방울 5. 0.32 s. 적중보다 늦게(피가 떨어지는 순간 — 권장 +110 ms, mixing.cues). 변주 _v2·_v3", -3)
def _blood_splat21(sr, rng):
    return _blood_splat(sr, rng)


@variant21('blood_splat', 2, "피 튐 변주 2 — 440 Hz, 방울 4")
def _blood_splat_v2(sr, rng):
    return _blood_splat(sr, rng, fc=440, drops=4)


@variant21('blood_splat', 3, "피 튐 변주 3 — 600 Hz, 방울 7(넓게 흩뿌림)")
def _blood_splat_v3(sr, rng):
    return _blood_splat(sr, rng, fc=600, drops=7)


# ===========================================================================
# 2. 죽음 — 찢김 · 쓰러짐 · 처형 (enemy:death-variant · player:execute)
# ===========================================================================

def _dismember(sr, rng, fall=0.42, bounce=0.53):
    dur = 0.85
    s = zeros(sec(sr, dur))
    rip = lowpass(tear(sr, 0.16, rng, 1800, 500, rate=45.0, q=1.3), sr, 3500)
    mix_into(s, rip, 0, 0.55)                                                         # 힘줄이 찢기는 '찌익'
    mix_into(s, wet(sr, rng, 0.2, 600, 34.0, 1.8), 0, 0.75)
    mix_into(s, cracks(sr, rng, 3, 0.0, 0.03, (900, 2200), 6), sec(sr, 0.015), 0.6)    # 뼈가 끊김
    mix_into(s, spurt(sr, rng, 0.35, (0.03, 0.09, 0.16, 0.24), 1300), sec(sr, 0.02), 0.6)
    t = sec(sr, fall)                                                                 # 떨어져 나간 부위가 바닥에 '퍽'
    mix_into(s, punch(sr, 150, 60, 0.12, 0.03, 1.5), t, 0.55)
    mix_into(s, splat(sr, rng, 480, 0.5, 3), t)
    mix_into(s, punch(sr, 120, 55, 0.08, 0.02, 1.3), sec(sr, bounce), 0.22)           # 한 번 구름
    mix_into(s, scuff(sr, rng, 0.16, 900, 0.18), sec(sr, bounce + 0.02))
    return lowpass(softclip(s, 1.4), sr, 4500)


@sfx21('dismember', 'enemy:death-variant{variant:behead|bisect}', "P21 새 — 찢김 + 둔탁한 떨어짐(목 베기·두 동강 사망 변형 — 처형 칼·대검 포함). 0 s 힘줄이 찢기는 '찌익'(1.8k→500 Hz 떨리는 찢김) + 젖은 살 + 뼈가 끊기는 딱 셋 + 맥박처럼 뿜는 피 넷(30~240 ms) → **0.42 s** 떨어져 나간 머리·윗몸이 바닥에 둔탁한 '퍽' + 피 철썩 → 0.53 s 한 번 구름 + 흙. 0.85 s. body_fall 과 함께 재생(남은 몸이 쓰러짐). 잘린 조각 비행 0.5~0.9 s 중 착지가 0.42 s 보다 크게 늦으면 시작을 늦춘다(mixing.cues). 변주 _v2", 0)
def _dismember21(sr, rng):
    return _dismember(sr, rng)


@variant21('dismember', 2, "찢김 변주 2 — 떨어짐 0.50 s · 구름 0.62 s(더 멀리 날아감)")
def _dismember_v2(sr, rng):
    return _dismember(sr, rng, fall=0.50, bounce=0.62)


def _body_fall(sr, rng, knee=0.14, torso=0.34, f=(100, 34), armor=0.0):
    dur = 0.9 if not armor else 1.0
    s = zeros(sec(sr, dur))
    mix_into(s, breath(sr, rng, 0.38, (520, 360), (1050, 900), rough=0.5, a=0.01, chest=0.6), 0, 0.22)   # 숨이 빠짐(목소리 없음)
    mix_into(s, rustle(sr, rng, 0.3, 1100, 30.0), 0, 0.18)                            # 옷이 접힘
    mix_into(s, punch(sr, 120, 50, 0.12, 0.03, 1.4), sec(sr, knee), 0.45)              # 무릎이 꺾여 닿음
    mix_into(s, gravel(sr, rng, 0.15, 3, 0.0, 0.08, 0.15), sec(sr, knee))
    t = sec(sr, torso)
    mix_into(s, _thump(sr, rng, f, 0.34, 0.085, 1.0, 7), t)                            # 몸통이 무겁게 '쿵'
    mix_into(s, wet(sr, rng, 0.12, 300, 20.0, 1.6), t, 0.35)                           # 피 젖은 몸
    mix_into(s, punch(sr, 140, 60, 0.07, 0.02, 1.2), sec(sr, torso + 0.12), 0.28)      # 머리·팔이 뒤따라 닿음
    for k, tc in enumerate((torso + 0.04, torso + 0.11)):
        mix_into(s, wood_tok(sr, rng, 480 + 150 * k, 0.05, 0.007, 0.8), sec(sr, tc), 0.25)   # 장비 덜그럭
    if armor:   # 사슬·판갑 '짤그락': 무릎에 작게, 몸통에 크게 + 판 '텅'
        for t0, t1, cnt, gg in ((knee, knee + 0.05, 3, 0.5), (torso, torso + 0.28, 9, 1.0)):
            for _ in range(cnt):
                m = metal(sr, 0.14, rng.uniform(1100, 2100), rng,
                          partials=[(1.0, 1.0), (1.37, 0.55), (2.11, 0.3)], tau=rng.uniform(0.012, 0.03), jitter=0.04)
                mix_into(s, m, sec(sr, rng.uniform(t0, t1)), armor * gg * rng.uniform(0.12, 0.26))
        plate = metal(sr, 0.3, 430, rng, partials=[(1.0, 1.0), (1.52, 0.5), (2.3, 0.25)], tau=0.06, jitter=0.03)
        mix_into(s, lowpass(plate, sr, 2500), t, armor * 0.3)
    return lowpass(softclip(s, 1.5), sr, 5000)


@sfx21('body_fall', 'enemy:death-variant{variant:collapse|behead|bisect|pinned|burn}', "P21 새 — 몸 쓰러짐(사망 변형이 오는 일반 적 — enemy_death 를 대신). 0 s 숨이 빠짐(목소리 없음) + 옷이 접힘 → 0.14 s 무릎이 꺾여 닿음 → **0.34 s** 몸통이 무겁게 '쿵'(100→34 Hz) + 흙 + 피 젖은 몸 → 0.46 s 머리·팔이 뒤따라 닿음 + 장비 덜그럭. 0.90 s. 현실의 무너짐(무릎 → 몸통 → 머리) 순서. drown 은 fall_water 가 맡아 없음. 변주 _v2", -2)
def _body_fall21(sr, rng):
    return _body_fall(sr, rng)


@variant21('body_fall', 2, "쓰러짐 변주 2 — 무릎 0.12 s · 몸통 0.30 s(앞으로 고꾸라짐), 110→38 Hz")
def _body_fall_v2(sr, rng):
    return _body_fall(sr, rng, knee=0.12, torso=0.30, f=(110, 38))


@sfx21('body_fall_armor', 'enemy:death-variant{armored:true}', "P21 새 — 갑옷 입은 몸 쓰러짐(body_fall 의 갑옷 판 — 같은 자리에 이것만). body_fall 뼈대 + 무릎에 사슬 '짤그락' 셋 → 0.34 s 몸통과 함께 사슬·판갑 쇳조각 아홉이 0.28 s 동안 흩어지며 '짤그락'(1.1~2.1 kHz, 울림 짧게) + 판 '텅'(430 Hz, 2.5 kHz 아래). 1.00 s. 조건 armored 는 제안 — 시스템이 갑옷 적(엘리트·근위 등)을 표시하거나 kind 목록으로 고른다", -2)
def _body_fall_armor21(sr, rng):
    return _body_fall(sr, rng, knee=0.15, torso=0.36, f=(95, 32), armor=1.0)


def _execute_hit(sr, rng, body=(70, 30), subf=(48, 26)):
    dur = 1.3
    s = zeros(sec(sr, dur))
    mix_into(s, punch(sr, body[0], body[1], 0.6, 0.18, 2.4, 0.04), 0, 1.0)            # 아주 낮은 충격
    mix_into(s, sub(sr, subf[0], subf[1], 0.8, 0.3, 100), 0, 0.9)
    mix_into(s, flesh(sr, rng, 300, 0.12, 0.03, 0.8), 0, 0.8)
    mix_into(s, cracks(sr, rng, 5, 0.0, 0.02, (800, 2000), 6), 0, 0.5)
    mix_into(s, wet(sr, rng, 0.22, 420, 24.0, 1.8), sec(sr, 0.01), 0.5)
    s = softclip(s, 2.0)
    s = reverb(s, sr, size=1.4, decay=0.6, wet=0.22, damp=0.75)                        # 어둡고 넓은 방 — 꼬리는 저역만
    s = lowpass(s, sr, 3200)
    ring = mul(tone(sr, 0.95, 1880, 1860), env_adsr(sr, 0.95, 0.08, 0.0, 1.0, 0.7))     # 귀가 먹먹한 '삐' — 정적의 느낌
    mix_into(s, ring, sec(sr, 0.14), 0.012)
    return s


@sfx21('execute_hit', 'player:execute', "P21 새 — 처형 일격(무기별 마무리의 결정타 순간 — 무기 소리·사망 변형 소리 위). 0 s 아주 낮은 충격(70→30 Hz, 0.6 s) + 아래 무게(48→26 Hz) + 살·뼈 + 젖음 → 저역만 남는 넓고 어두운 방 꼬리 + 0.14 s 부터 아주 작은 먹먹한 '삐'(1.9 kHz, 피크 대비 −40 dB) — 순간 다른 소리가 빠진 '정적'(mixing.ducking 처형 규칙과 함께 — 효과음 −9 dB·BGM −6 dB 300 ms). 1.30 s. 슬로 0.3배 120 ms 와 같은 순간. 변주 _v2", 0)
def _execute_hit21(sr, rng):
    return _execute_hit(sr, rng)


@variant21('execute_hit', 2, "처형 일격 변주 2 — 충격 62→28 Hz, 아래 44→24 Hz(더 깊게)")
def _execute_hit_v2(sr, rng):
    return _execute_hit(sr, rng, body=(62, 28), subf=(44, 24))


# ===========================================================================
# 3. 주인공 상흔 — 숯 몸 갈라짐 · 불씨 쉿 (PLAYER_DAMAGED · player:wounded)
# ===========================================================================

def _hero_crack(sr, rng, body=(130, 60), hollow=300, fc=(600, 1800)):
    dur = 0.32
    s = zeros(sec(sr, dur))
    mix_into(s, cracks(sr, rng, 6, 0.0, 0.05, fc, 8, dur=0.15), 0, 0.8)                 # 숯이 갈라지는 굵은 '빠직'
    mix_into(s, punch(sr, body[0], body[1], 0.1, 0.03, 1.4), 0, 0.4)                   # 속 빈 몸통
    mix_into(s, burst(sr, 0.2, rng, fc=hollow, q=4.0, tau=0.05), 0, 0.35)               # 탄 나무 속 울림
    mix_into(s, lowpass(gravel(sr, rng, 0.3, 8, 0.03, 0.26, 0.15), sr, 3000), 0)         # 재가 부스러져 흘러내림
    return lowpass(softclip(s, 1.5), sr, 4500)


@sfx21('hero_crack', 'PLAYER_DAMAGED{guarded:false}', "P21 새 — 숯 몸 갈라짐(주인공 피격마다 hit_player 위 층 — 숯빛 망령은 살이 아니라 숯). 0~50 ms 숯이 갈라지는 굵은 '빠직' 여섯(0.6~1.8 kHz, 거칠게) + 속 빈 몸통(130→60 Hz) + 탄 나무 속 울림(300 Hz) → 재가 부스러져 흘러내림. 0.32 s. 상처 단계가 오를 때(player:wounded{stage 상승})는 재생 속도 0.85 로 한 번 더. 변주 _v2·_v3", 0, category='combat')
def _hero_crack21(sr, rng):
    return _hero_crack(sr, rng)


@variant21('hero_crack', 2, "갈라짐 변주 2 — 몸통 120→55 Hz, 속 울림 260 Hz")
def _hero_crack_v2(sr, rng):
    return _hero_crack(sr, rng, body=(120, 55), hollow=260, fc=(550, 1600))


@variant21('hero_crack', 3, "갈라짐 변주 3 — 몸통 140→64 Hz, 속 울림 340 Hz, 더 잘게")
def _hero_crack_v3(sr, rng):
    return _hero_crack(sr, rng, body=(140, 64), hollow=340, fc=(700, 2000))


def _ember_hiss(sr, rng, fc=2800, dur=0.7):
    s = zeros(sec(sr, dur))
    h = svf(noise(sr, dur, rng), sr, fc, 0.8, 'band')
    mix_into(s, mul(h, env_adsr(sr, dur, 0.02, 0.0, 1.0, dur * 0.85, curve=1.8)), 0, 0.55)   # 불씨가 새는 '쉬이'
    mix_into(s, lowpass(crackle(sr, rng, dur * 0.8, 9, 0.35), sr, 4000), 0)                 # 불씨 톡톡
    w = svf(noise(sr, 0.18, rng), sr, 400, 0.7, 'low')
    mix_into(s, mul(w, env_adsr(sr, 0.18, 0.02, 0.0, 1.0, 0.14)), 0, 0.35)                  # 불씨가 확 일어남 '훅'
    return lowpass(s, sr, 6000)


@sfx21('hero_ember_hiss', 'PLAYER_DAMAGED{woundStage:2+}', "P21 새 — 불씨 쉿(상처 2단 이상 — HP ≤ 50% — 에서 맞을 때마다 hero_crack 위, 상처 단계가 2·3 으로 오를 때 한 번). 0 s 불씨가 확 일어나는 낮은 '훅' + 갈라진 틈으로 불씨가 새는 '쉬이'(2.8 kHz 대역, 0.6 s 에 걸쳐 잦아듦) + 불씨 톡톡. 0.70 s. 귀가 따갑지 않게 6 kHz 위 없음·작게. 조건 woundStage 는 제안(UiSnapshot.player.wound.stage 와 같은 값). 변주 _v2", -5, category='combat')
def _hero_ember_hiss21(sr, rng):
    return _ember_hiss(sr, rng)


@variant21('hero_ember_hiss', 2, "불씨 쉿 변주 2 — 2.4 kHz, 0.8 s")
def _hero_ember_hiss_v2(sr, rng):
    return _ember_hiss(sr, rng, fc=2400, dur=0.8)


# ===========================================================================
# 4. 저HP 심장 박동 (player:low-hp — 루프)
# ===========================================================================

@sfx21('heartbeat_loop', 'player:low-hp{on:true}', "P21 새 — 저HP 심장 박동 루프(HP ≤ 25% 동안 — on:true 에서 400 ms 페이드인, on:false 에서 600 ms 페이드아웃). 88 BPM 네 박(2.73 s 루프): 박마다 '쿵-쿵'(62→38 · 56→36 Hz, 160 Hz 아래) + 피가 귀에서 밀려가는 낮은 '쉬익'(120 Hz 아래, 박 뒤에 부풂). 넷째 박은 조금 약하게(불규칙한 심장). 위치 없음(2D). 권장 재생 속도: ratio 0.25 → 1.0, 0.10 이하 → 1.15(가빠짐 — 0.25~0.10 사이는 선형)", -4, loop=True, category='combat')
def _heartbeat_loop(sr, rng):
    beat = 60.0 / 88.0
    n = sec(sr, beat * 4)
    s = zeros(n)
    for k in range(4):
        t = sec(sr, 0.03 + k * beat)
        g = 0.82 if k == 3 else 1.0
        mix_into(s, lowpass(thud(sr, 0.2, 62, 38, 0.055), sr, 160), t, g, wrap=True)
        mix_into(s, lowpass(thud(sr, 0.18, 56, 36, 0.05), sr, 160), t + sec(sr, 0.17), 0.65 * g, wrap=True)
        rush = svf(noise(sr, 0.45, rng), sr, 120, 0.7, 'low')
        mix_into(s, mul(rush, env_adsr(sr, 0.45, 0.12, 0.0, 1.0, 0.3)), t + sec(sr, 0.05), 0.22 * g, wrap=True)
    return s


# ===========================================================================
# 5. 적 신음 (enemy:wounded — 숨 · '끙', 목소리 없음)
# ===========================================================================

def _groan1(sr, rng, f1=(420, 330), f2=(950, 820), d=0.42):
    s = zeros(sec(sr, d + 0.2))
    mix_into(s, breath(sr, rng, 0.09, (820, 700), (1350, 1250), rough=0.3, a=0.01), 0, 0.35)     # 숨을 '헙' 들이킴
    mix_into(s, grunt(sr, rng, d, f1, f2, rough=0.6, chest=1.2), sec(sr, 0.08), 0.9)              # 이를 악문 '끙'
    return lowpass(s, sr, 3500)


@sfx21('enemy_groan_1', 'enemy:wounded{stage:1}', "P21 새 — 적 신음 1단(HP ≤ 66% — 처음 크게 다침). 목소리 아닌 숨: 숨을 '헙' 들이킴(0.09 s) → 이를 악문 낮은 '끙'(포먼트 420·950 Hz 노이즈 + 가슴 저역, 거칠게 떨림). 0.62 s. 위치 감쇠 권장, 같은 적 한 번(단계가 바뀔 때만). 변주 _v2", -5)
def _enemy_groan_1(sr, rng):
    return _groan1(sr, rng)


@variant21('enemy_groan_1', 2, "신음 1단 변주 2 — 포먼트 380·880 Hz(더 낮은 몸), 0.48 s")
def _enemy_groan_1_v2(sr, rng):
    return _groan1(sr, rng, f1=(380, 300), f2=(880, 760), d=0.48)


def _groan2(sr, rng, f1=(560, 380), gaps=(0.0, 0.42, 0.78), gurgle=340):
    dur = 1.05
    s = zeros(sec(sr, dur))
    for k, t in enumerate(gaps):
        d = 0.32 - 0.06 * k
        b = breath(sr, rng, d, f1, (1050, 880), rough=0.7, a=0.015, chest=1.0)                     # 거칠게 끊기는 '크흐…'
        mix_into(s, b, sec(sr, t), 0.85 * (0.75 ** k))
        mix_into(s, wet(sr, rng, d * 0.8, gurgle, 18.0, 2.5), sec(sr, t + 0.03), 0.3 * (0.75 ** k))  # 목에 고인 피 그르렁
    return lowpass(s, sr, 3200)


@sfx21('enemy_groan_2', 'enemy:wounded{stage:2}', "P21 새 — 적 신음 2단(HP ≤ 33% — 절뚝임과 함께). 목소리 아닌 숨: 거칠게 끊기는 젖은 숨 '크흐… 흐… 흐'(셋, 점점 약하게 — 0·0.42·0.78 s) + 목에 고인 피가 그르렁(340 Hz 젖은 떨림). 1.05 s. 위치 감쇠 권장, 같은 적 한 번. 변주 _v2", -3)
def _enemy_groan_2(sr, rng):
    return _groan2(sr, rng)


@variant21('enemy_groan_2', 2, "신음 2단 변주 2 — 숨 둘(0·0.5 s), 그르렁 300 Hz")
def _enemy_groan_2_v2(sr, rng):
    return _groan2(sr, rng, f1=(520, 350), gaps=(0.0, 0.5), gurgle=300)
