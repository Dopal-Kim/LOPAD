# -*- coding: utf-8 -*-
"""
61라운드 단계 2·3 (자율 모드) — 1층 신규 적 2종 · 보스 '만취' 효과음 패스(P6) · 칼 발도 검기 단수 · 가드 다듬기.

build.py 가 sfx_core61 다음(마지막)에 import 한다. 시드 = 1000 + 등록 순서 — 이 모듈은 끝에 붙으므로 기존 소리는
바이트 불변이다. 같은 키를 다시 만드는 것은 `redo()`(dict 의 같은 키에 값만 바꿔 끼움 → 순서·시드 유지).
**새 효과음은 이 파일 끝에만** 추가한다.

방향(61 P11 원칙 그대로): 오래 남는 0.7~2 kHz 금속 울림 금지, 무게 = 피치가 떨어지는 몸통(85~250 Hz) + 300 Hz '퍽',
날카로움 = 짧은 넓은 대역 '딱' + 고역 노이즈. 목소리 없음 — 적의 숨·'끙'도 성대음 없는 노이즈 포먼트로만.
타이밍 기준: 계약 art-assets §23 — 행상 throw 놓음 프레임 5 = 550 ms, 짐꾼 push 놓음 프레임 5 = 530 ms.
"""
from build import *  # noqa: F401,F403
from build import SFX, GLASS, gravel, slosh, crackle, sizzle, droplets, kha, gulp, tear, heartbeat, tone_f  # noqa: F401
from sfx_core61 import snap, punch, flesh, slice_, crunch, rustle, sub, glint, sparks, wood_tok  # noqa: F401
from sfx_bundle2 import flame, glass_shards  # noqa: F401

ROUND = '61-2'   # listen_index 의 round 값(61라운드 단계 2·3)


def redo(name, note, gain_db=None, trigger=None, round_=ROUND):
    """이미 등록된 키의 합성 함수·설명(·트리거·음량)을 바꾼다. 등록 순서·시드는 그대로. round_ = listen_index 의 round 값."""
    old = SFX[name]

    def deco(fn):
        spec = dict(old)
        spec.update(fn=fn, note=note, redone=round_, origin_module=old.get('origin_module', old['fn'].__module__))
        if gain_db is not None:
            spec['gain_db'] = gain_db
        if trigger is not None:
            spec['trigger'] = trigger
        SFX[name] = spec
        return fn
    return deco


def archive(name, reason):
    """보관: 오디오·시드 그대로, note 앞에 [보관 …] 표시(시스템 연결 끊음). listen_index.ARCHIVED 에도 적는다."""
    SFX[name] = dict(SFX[name], note='[보관 — %s] %s' % (reason, SFX[name]['note']), archived=ROUND)


# ===========================================================================
# 재료
# ===========================================================================

def breath(sr, rng, dur, f1=(700, 480), f2=(1250, 1050), rough=0.35, a=0.02, curve=0.7, chest=0.0, r=None):
    """숨(성대음 없는 노이즈 포먼트): F1·F2 밴드 + 거친 진폭 떨림. chest > 0 이면 가슴 저역 노이즈. r = 릴리즈(기본 0.7 × 길이)."""
    n = sec(sr, dur)
    src = noise(sr, dur, rng)
    x = svf(src, sr, sweep(sr, n, f1[0], f1[1]), 4.0, 'band')
    y = svf(src, sr, sweep(sr, n, f2[0], f2[1]), 5.0, 'band')
    s = [p * 0.6 + q * 0.3 for p, q in zip(x, y)]
    jit = normalize(lowpass([rng.uniform(-1, 1) for _ in range(n)], sr, 40), 1.0)
    s = mul(s, [1 - rough + rough * j for j in jit])
    if chest:
        c = svf(noise(sr, dur, rng), sr, 170, 0.8, 'low')
        mix_into(s, c, 0, chest)
    return mul(s, env_adsr(sr, dur, a, 0.0, 1.0, dur * 0.7 if r is None else r, curve=curve))


def grunt(sr, rng, dur, f1=(420, 340), f2=(980, 860), rough=0.55, chest=1.4, a=0.012):
    """'끙'(성대음 없음): 'ㅡ' 쪽 낮은 포먼트 노이즈 + 가슴 저역 + 거친 떨림. 짐꾼처럼 큰 몸."""
    return breath(sr, rng, dur, f1, f2, rough, a, 0.6, chest)


def scuff(sr, rng, dur, fc=1100, g=1.0):
    """발·몸이 흙을 긁음."""
    d = lowpass(svf(noise(sr, dur, rng), sr, fc, 0.6, 'band'), sr, fc * 1.8)
    return scale(mul(d, env_adsr(sr, dur, dur * 0.15, 0.0, 1.0, dur * 0.7)), g)


def creak(sr, rng, dur, f0=80, f1=110, band=(450, 1100), trem=13.0, q=2.5):
    """나무·가죽 삐걱: 톱니 → 움직이는 밴드 + 떨림."""
    n = sec(sr, dur)
    c = svf(tone(sr, dur, f0, f1, kind='saw'), sr, sweep(sr, n, band[0], band[1]), q, 'band')
    c = mul(c, [0.7 + 0.3 * math.sin(TAU * trem * i / sr) for i in range(n)])
    return mul(c, env_adsr(sr, dur, dur * 0.2, 0.0, 1.0, dur * 0.4))


def body_fall(sr, rng, f=(110, 38), dur=0.32, tau=0.08, g=1.0, dirt=6):
    """몸이 땅에 '쿵' + 흙·자갈 + 먼지."""
    s = zeros(sec(sr, max(dur, 0.4)))
    mix_into(s, punch(sr, f[0], f[1], dur, tau, 1.6), 0, 1.0 * g)
    mix_into(s, burst(sr, 0.12, rng, fc=380, q=0.6, tau=0.035, mode='low'), 0, 0.7 * g)
    mix_into(s, gravel(sr, rng, 0.3, dirt, 0.0, 0.2, 0.25 * g), 0)
    dust = mul(svf(noise(sr, 0.35, rng), sr, 600, 0.7, 'low'), env_adsr(sr, 0.35, 0.03, 0.0, 1.0, 0.3))
    mix_into(s, dust, 0, 0.18 * g)
    return s


def barrel_body(sr, rng, dur=0.3, f=(220, 500), tau=0.07, q=6.0):
    """속 빈 나무통 공명(두 대역)."""
    s = zeros(sec(sr, dur))
    for fc, gg in ((f[0], 0.9), (f[1], 0.5)):
        mix_into(s, burst(sr, dur, rng, fc=fc, q=q, tau=tau), 0, gg)
    return s


def hoop_clunk(sr, rng, f=480, dur=0.12, tau=0.018):
    """쇠테 '덜컥': 낮고 짧게(1.8 kHz 저역통과 — 울림이 남지 않게)."""
    return lowpass(metal(sr, dur, f, rng, tau=tau, jitter=0.04), sr, 1800)


def staves(sr, rng, dur, count, t0, t1, g=0.35, lo=380, hi=900):
    """판자 쪼개짐: 짧은 나무 크랙 + 나무 톡 여럿."""
    s = zeros(sec(sr, dur))
    for _ in range(count):
        t = sec(sr, rng.uniform(t0, t1))
        k = rng.uniform(0.5, 1.0)
        mix_into(s, snap(sr, rng, rng.uniform(1500, 3200), 0.012, rng.uniform(0.0015, 0.003)), t, g * k)
        mix_into(s, wood_tok(sr, rng, rng.uniform(lo, hi), 0.06, rng.uniform(0.006, 0.012), 0.7), t, g * 0.8 * k)
    return s


def gush(sr, rng, dur=0.7, f=(3500, 500), g=1.0):
    """술이 한꺼번에 쏟아짐: 열렸다 닫히는 저역 노이즈 + 둔탁한 물 몸통 + 물방울."""
    n = sec(sr, dur)
    s = zeros(n)
    sp = svf(noise(sr, dur, rng), sr, sweep(sr, n, f[0], f[1]), 0.7, 'low')
    mix_into(s, mul(sp, env_adsr(sr, dur, 0.006, 0.08, 0.45, dur * 0.65)), 0, 1.0 * g)
    mix_into(s, burst(sr, 0.06, rng, fc=900, q=0.7, tau=0.02), 0, 0.6 * g)
    mix_into(s, thud(sr, 0.15, 160, 80, 0.035), 0, 0.4 * g)
    mix_into(s, droplets(sr, rng, dur, 10, dur * 0.15, dur * 0.85, 600, 1600, 0.25 * g), 0)
    return s


def glugs(sr, rng, times, f0=300, f1=520, g=0.3):
    """병·통이 비며 나는 '꿀렁'(공기 방울)."""
    s = zeros(sec(sr, max(times) + 0.08))
    for t in times:
        d = rng.uniform(0.04, 0.06)
        b = mul(tone(sr, d, f0 * rng.uniform(0.9, 1.1), f1 * rng.uniform(0.9, 1.1)), env_exp(sr, d, d * 0.4))
        mix_into(s, lowpass(b, sr, 1400), sec(sr, t), g)
    return s


def roll(sr, rng, dur, fc=800, am=12.0, g=1.0):
    """작은 잔·병이 구름: 밴드 노이즈 + 회전 떨림, 점점 느리고 작게."""
    n = sec(sr, dur)
    r = svf(noise(sr, dur, rng), sr, fc, 2.0, 'band')
    ph = 0.0
    out = zeros(n)
    for i in range(n):
        f = am * (1 - 0.6 * i / n)
        ph += f / sr
        out[i] = r[i] * (0.35 + 0.65 * abs(math.sin(math.pi * ph)))
    return scale(mul(out, env_adsr(sr, dur, 0.02, 0.0, 1.0, dur * 0.8)), g)


def woozy(sr, dur, f0, f1, rng, depth=0.06, det=1.03, cut=(380, 260), a=0.5, r=0.7):
    """'세상이 돈다' 울렁임: 0.5 Hz(주기 2 s, 화면 기울기와 같음)로 흔들리며 내려가는 톱니 두 겹(맥놀이) + 소용돌이 바람."""
    n = sec(sr, dur)
    wob = [math.sin(TAU * 0.5 * i / sr) for i in range(n)]
    base = sweep(sr, n, f0, f1)
    fa = [b * (1 + depth * w) for b, w in zip(base, wob)]
    lo = add(tone_f(sr, fa, 'saw'), tone_f(sr, [f * det for f in fa], 'saw'))
    lo = svf(lo, sr, [cut[0] + cut[1] * w for w in wob], 1.4, 'low')
    s = scale(mul(lo, env_adsr(sr, dur, a, 0.0, 1.0, r)), 0.6)
    wind = svf(noise(sr, dur, rng), sr, [650 + 400 * w for w in wob], 1.2, 'band')
    mix_into(s, mul(wind, env_adsr(sr, dur, a + 0.1, 0.0, 1.0, r + 0.1)), 0, 0.3)
    return s


def table_slam(sr, rng, g=1.0):
    """큰 잔·주먹을 나무 탁자에 '탁!': 몸통 + 나무 톡 + 탁자 공명 + 잔들 덜그럭."""
    s = zeros(sec(sr, 0.45))
    mix_into(s, snap(sr, rng, 2200, 0.016, 0.003), 0, 0.9 * g)
    mix_into(s, punch(sr, 230, 95, 0.18, 0.04, 1.8), 0, 1.0 * g)
    mix_into(s, wood_tok(sr, rng, 520, 0.08, 0.012, 0.8), 0, 0.7 * g)
    mix_into(s, barrel_body(sr, rng, 0.3, (160, 340), 0.06, 5.0), 0, 0.5 * g)
    for k, t in enumerate((0.04, 0.08, 0.13)):
        mix_into(s, wood_tok(sr, rng, 900 + 180 * k, 0.04, 0.006, 0.6), sec(sr, t), (0.25 - 0.05 * k) * g)
    return s


# ===========================================================================
# 1. 신규 적 — 독주 행상(peddler)
#    throw: 등불로 심지에 불 → 프레임 5(550 ms) 손에서 놓음 → fire_bottle_thrown → fire_bottle_burst → fire_pool
# ===========================================================================

@sfx('peddler_wick', 'ENEMY_TELEGRAPH{kind:throw}', "61-2 새 — 독주 행상 투척 예고(throw 시작 = 프레임 0, 놓음 550 ms 까지). 등불 갓이 '톡' → 0.12 s 심지가 등불에 닿아 불붙는 '푸슉' → 놓는 순간(0.55 s)까지 점점 커지는 심지 지글거림·타닥 + 0.3 s 부터 팔을 젖히는 옷 바람 + 병 속 술 출렁. 소리가 커지다 끊기는 곳 = 병이 날아가는 순간(피하기 신호)", -3)
def _peddler_wick(sr, rng):
    dur = 0.6
    rel = 0.55
    s = zeros(sec(sr, dur))
    mix_into(s, wood_tok(sr, rng, 1250, 0.04, 0.006, 0.5), 0, 0.35)                     # 등불 갓 '톡'
    mix_into(s, rustle(sr, rng, 0.12, 1500, 40), 0, 0.2)
    t = 0.12
    mix_into(s, flame(sr, rng, 0.22, 450, 3200, a=0.015), sec(sr, t), 0.55)               # 불붙는 '푸슉'
    mix_into(s, snap(sr, rng, 5200, 0.01, 0.0015), sec(sr, t), 0.35)
    nw = sec(sr, rel - t)
    hs = svf(noise(sr, rel - t, rng), sr, sweep(sr, nw, 3800, 6800), 1.0, 'band')
    ramp = [0.25 + 0.75 * (i / nw) ** 1.6 for i in range(nw)]                             # 놓을 때까지 커짐
    mix_into(s, mul(hs, ramp), sec(sr, t), 0.4)
    cr = crackle(sr, rng, rel - t, 14, 0.35)
    mix_into(s, mul(cr, ramp), sec(sr, t), 1.0)
    mix_into(s, whoosh(sr, 0.25, rng, 450, 1300, q=0.8, a=0.85, r=0.1), sec(sr, 0.3), 0.45)  # 팔을 젖힘
    mix_into(s, slosh(sr, rng, 0.32, 380, 760), sec(sr, 0.14), 0.25)                     # 병 속 술
    # 놓는 순간 뚝 끊기도록 0.55 s 뒤를 빠르게 줄인다
    n0, n1 = sec(sr, rel), sec(sr, rel + 0.03)
    for i in range(n0, len(s)):
        s[i] *= max(0.0, 1.0 - (i - n0) / (n1 - n0))
    return s


@sfx('peddler_throw', 'ENEMY_ATTACK{kind:throw,phase:throw}', "61-2 새 — 독주 행상 병 놓음(throw 프레임 5 = 550 ms, fire_bottle_thrown 이 생기는 프레임). 짧게 내뱉는 숨 + 팔 휘두르는 '휙'(1.6k→500) + 빙글 도는 병(9 Hz) + 심지 불이 펄럭이며 멀어짐. 착탄은 bottle_burst 재사용(같은 그림·같은 불 웅덩이) — 시스템 트리거 ENEMY_ATTACK{kind:throw,phase:burst} → sfx/bottle_burst(시스템 audioMap), 웅덩이는 boss1_fire_loop", -3)
def _peddler_throw(sr, rng):
    dur = 0.52
    n = sec(sr, dur)
    s = zeros(n)
    mix_into(s, breath(sr, rng, 0.12, (820, 600), (1400, 1150), 0.3, 0.004), 0, 0.35)      # '흡' 숨(노이즈)
    mix_into(s, whoosh(sr, 0.17, rng, 1600, 500, q=1.1, a=0.18, r=0.6), 0, 0.85)          # 팔 '휙'
    mix_into(s, rustle(sr, rng, 0.12, 1700, 45), 0, 0.25)
    sp = svf(noise(sr, 0.42, rng), sr, sweep(sr, sec(sr, 0.42), 1100, 700), 1.2, 'band')
    sp = mul(sp, [0.35 + 0.65 * abs(math.sin(math.pi * 9 * i / sr)) for i in range(len(sp))])
    mix_into(s, mul(sp, env_adsr(sr, 0.42, 0.04, 0.0, 1.0, 0.35)), sec(sr, 0.06), 0.45)  # 도는 병
    fl = svf(noise(sr, 0.42, rng), sr, sweep(sr, sec(sr, 0.42), 1500, 600), 0.7, 'low')
    fl = mul(fl, [0.3 + 0.7 * abs(math.sin(math.pi * 9 * i / sr + 0.7)) for i in range(len(fl))])
    mix_into(s, mul(fl, env_adsr(sr, 0.42, 0.02, 0.0, 1.0, 0.38)), sec(sr, 0.06), 0.45)  # 펄럭이는 심지 불(멀어짐)
    mix_into(s, crackle(sr, rng, 0.3, 5, 0.25), sec(sr, 0.08))
    return s


@sfx('peddler_hurt', 'ENEMY_DAMAGED{enemy:peddler,aux:true}', "61-2 새 — 독주 행상 피격 몸짓(목소리 없음, hurt 4프레임 · 번쩍 프레임 0). 짧게 들이켜는 '흑' 숨(노이즈) + 등짐 속 술병끼리 부딪는 아주 짧은 '짤그락'(3 kHz 위, 20 ms 감쇠) + 병 속 출렁 + 옷 스침. hit_enemy 위에 겹침(이 적에게는 enemy_hurt 대신)", -5)
def _peddler_hurt(sr, rng):
    dur = 0.28
    s = zeros(sec(sr, dur))
    mix_into(s, breath(sr, rng, 0.11, (880, 640), (1500, 1250), 0.3, 0.004, 1.0), 0, 0.7)
    for t, f in ((0.012, 3300), (0.034, 4100), (0.062, 3700)):
        g = metal(sr, 0.06, f, rng, partials=GLASS, tau=rng.uniform(0.012, 0.02), jitter=0.01)
        mix_into(s, highpass(g, sr, 2600), sec(sr, t), 0.22)
    mix_into(s, slosh(sr, rng, 0.2, 420, 820), sec(sr, 0.02), 0.3)
    mix_into(s, rustle(sr, rng, 0.12, 1400, 45), 0, 0.3)
    return s


@sfx('peddler_death', 'ENEMY_DIED{enemy:peddler}', "61-2 새 — 독주 행상 쓰러짐(목소리 없음, death 10프레임). 마지막 숨이 빠짐(노이즈) + 비틀 발 끌림 → 0.18 s 몸이 '쿵' + 등짐 술병들이 깨지는 '와장창'(짧은 유리 조각) + 쏟아지는 술 '꿀렁꿀렁' → 병 하나가 데구루루 굴러가다 멈춤. enemy_death 대신(엘리트면 elite_die 위에 겹침)", -2)
def _peddler_death(sr, rng):
    dur = 1.0
    s = zeros(sec(sr, dur))
    mix_into(s, breath(sr, rng, 0.32, (760, 430), (1300, 1000), 0.45, 0.01, 0.9, 0.6), 0, 0.55)   # 숨 빠짐
    mix_into(s, scuff(sr, rng, 0.14, 1000), sec(sr, 0.04), 0.35)                          # 비틀
    t = sec(sr, 0.18)
    mix_into(s, body_fall(sr, rng, (125, 42), 0.28, 0.07, 1.0, 6), t, 1.0)                # '쿵'
    mix_into(s, burst(sr, 0.03, rng, fc=3500, q=0.8, tau=0.006), t, 0.5)
    mix_into(s, glass_shards(sr, rng, 0.35, 8, 0.0, 0.16, 2500, 5600, 0.2), t)            # 등짐 병 깨짐(짧게)
    mix_into(s, gush(sr, rng, 0.45, (2600, 500), 0.55), t + sec(sr, 0.02), 1.0)            # 술 쏟아짐
    mix_into(s, glugs(sr, rng, (0.0, 0.11, 0.24), 290, 500, 0.3), sec(sr, 0.36), 1.0)
    mix_into(s, punch(sr, 90, 40, 0.12, 0.03, 1.2), sec(sr, 0.33), 0.3)                   # 한 번 튐
    mix_into(s, roll(sr, rng, 0.45, 850, 13.0, 0.3), sec(sr, 0.42), 1.0)                  # 병 하나 굴러감
    mix_into(s, wood_tok(sr, rng, 1500, 0.03, 0.004, 0.5), sec(sr, 0.88), 0.15)          # 멈춤
    return softclip(s, 1.3)


# ===========================================================================
# 2. 신규 적 — 술통 짐꾼(porter)
#    push: 프레임 5(530 ms) 술통 놓음 → porter_rolling_barrel(60 ms × 8 = 0.48 s 한 바퀴) →
#    되치기 = porter_rolling_barrel_returned / 벽·단단한 구조물 → porter_barrel_break(8프레임) → pool_liquor
# ===========================================================================

@sfx('porter_windup', 'ENEMY_TELEGRAPH{kind:roll}', "61-2 새 — 술통 짐꾼 밀기 예고(push 시작 = 프레임 0, 놓음 530 ms 까지). 발을 디디는 '쿵' + 어깨를 통에 대는 나무 '톡' → 0.08 s 부터 커지는 '끄응' 힘주는 숨(노이즈, 목소리 아님) + 통이 눌려 삐걱 + 발이 흙에 밀림 + 통 속 술 출렁. 0.53 s 에 끊김 = 통이 굴러 나오는 순간", -3)
def _porter_windup(sr, rng):
    dur = 0.58
    rel = 0.53
    s = zeros(sec(sr, dur))
    mix_into(s, punch(sr, 150, 65, 0.1, 0.025, 1.4), 0, 0.7)                             # 디딤
    mix_into(s, scuff(sr, rng, 0.14, 1200), 0, 0.4)
    mix_into(s, wood_tok(sr, rng, 300, 0.07, 0.012, 0.8), sec(sr, 0.05), 0.5)            # 어깨가 통에
    mix_into(s, barrel_body(sr, rng, 0.2, (220, 500), 0.05), sec(sr, 0.05), 0.25)
    g = grunt(sr, rng, rel - 0.08, (400, 360), (950, 900), 0.55, 1.4, 0.3)                 # '끄응'(커짐)
    mix_into(s, mul(g, [(i / len(g)) ** 0.8 for i in range(len(g))]), sec(sr, 0.08), 0.9)
    mix_into(s, creak(sr, rng, 0.4, 70, 95, (420, 1000), 11.0), sec(sr, 0.13), 0.35)     # 통 삐걱
    mix_into(s, scuff(sr, rng, 0.3, 900, 1.0), sec(sr, 0.22), 0.35)                       # 발 밀림
    mix_into(s, slosh(sr, rng, 0.3, 330, 650), sec(sr, 0.22), 0.3)
    n0, n1 = sec(sr, rel), sec(sr, rel + 0.03)
    for i in range(n0, len(s)):
        s[i] *= max(0.0, 1.0 - (i - n0) / (n1 - n0))
    return s


@sfx('porter_push', 'ENEMY_ATTACK{kind:roll,phase:push}', "61-2 새 — 술통 짐꾼 술통 놓음(push 프레임 5 = 530 ms, porter_rolling_barrel 이 생기는 프레임). 내뱉는 '흡' + 어깨로 밀어내는 둔탁한 '쿵'(140→55 Hz) + 속 빈 통 울림 + 굴러 나가며 빨라지는 덜컹 셋 + 출렁. 이어서 porter_barrel_roll 루프", -1)
def _porter_push(sr, rng):
    dur = 0.5
    s = zeros(sec(sr, dur))
    mix_into(s, breath(sr, rng, 0.13, (560, 420), (1050, 900), 0.45, 0.004, 0.8, 1.0), 0, 0.45)
    mix_into(s, snap(sr, rng, 1800, 0.014, 0.0025), 0, 0.6)
    mix_into(s, punch(sr, 140, 55, 0.25, 0.06, 1.7), 0, 1.0)                             # 밀어내는 '쿵'
    mix_into(s, barrel_body(sr, rng, 0.3, (225, 510), 0.065), 0, 0.6)
    mix_into(s, hoop_clunk(sr, rng, 470), sec(sr, 0.005), 0.15)
    for k, t in enumerate((0.13, 0.23, 0.31)):                                            # 굴러 나감
        mix_into(s, thud(sr, 0.06, 150, 95, 0.02), sec(sr, t), 0.5 - 0.08 * k)
        mix_into(s, burst(sr, 0.02, rng, fc=1300, q=0.7, tau=0.004), sec(sr, t), 0.14)
    mix_into(s, slosh(sr, rng, 0.4, 330, 700), sec(sr, 0.05), 0.35)
    mix_into(s, punch(sr, 110, 48, 0.1, 0.025, 1.2), sec(sr, 0.08), 0.35)                # 앞발 디딤
    return softclip(s, 1.5)


@sfx('porter_barrel_roll', 'ENEMY_ATTACK{kind:roll,phase:push}', "61-2 새 — 짐꾼 술통 굴러가는 루프(0.96 s = 그림 한 바퀴 0.48 s × 2, 60 ms × 8 프레임과 같은 주기). 판자 덜컹 0.12 s 간격(한 바퀴마다 강세) + 낮은 굴림 + 통 속 출렁 + 자갈 바스락. 시작 = porter_push 와 같은 트리거(phase:push, 놓는 순간 함께 재생), 정지 = ENEMY_ATTACK{kind:roll,phase:rollEnd} 에서 80 ms 페이드아웃(멈춤·깨짐 모두). 되치기(phase:return) 뒤에도 끊지 않고 같은 루프. 보스 boss1_barrel_roll 보다 가볍고 빠름", -6, loop=True)
def _porter_barrel_roll(sr, rng):
    dur = 0.96
    n = sec(sr, dur)
    rev = 0.48
    rum = wrap2(lambda x: svf(x, sr, 200, 0.8, 'low'), noise_loop(sr, n, rng))
    s = mul(rum, lfo_loop(sr, n, 1 / rev, 0.3, 0.7))
    liq = wrap2(lambda x: svf(x, sr, 650, 1.5, 'band'), noise_loop(sr, n, rng))
    mix_into(s, mul(liq, lfo_loop(sr, n, 1 / rev, 0.5, 0.5, 0.3)), 0, 0.22)
    for k in range(8):
        accent = 1.0 if k % 4 == 0 else rng.uniform(0.45, 0.7)
        t0 = 0.12 * k + rng.uniform(-0.005, 0.005)
        mix_into(s, thud(sr, 0.05, 165, 105, 0.017), sec(sr, t0), 0.45 * accent, wrap=True)
        mix_into(s, burst(sr, 0.018, rng, fc=1400, q=0.7, tau=0.0035), sec(sr, t0), 0.13 * accent, wrap=True)
    mix_into(s, gravel(sr, rng, dur, 10, 0.0, dur - 0.02, 0.08), 0, wrap=True)
    return s


def _tang(sr, rng, g=1.0):
    """되치기 '탕'(짐꾼·보스 공용 머리): 넓은 '딱' + 단단한 나무 몸통 + 짧게 울리는 속 빈 통 + 쇠테 덜컥."""
    s = zeros(sec(sr, 0.4))
    mix_into(s, snap(sr, rng, 2600, 0.018, 0.0028), 0, 1.0 * g)
    mix_into(s, punch(sr, 270, 115, 0.13, 0.03, 2.0), 0, 0.95 * g)
    mix_into(s, barrel_body(sr, rng, 0.3, (300, 680), 0.085, 8.0), 0, 0.75 * g)
    mix_into(s, hoop_clunk(sr, rng, 560, 0.1, 0.014), sec(sr, 0.003), 0.25 * g)
    mix_into(s, sub(sr, 85, 48, 0.2, 0.05), 0, 0.45 * g)
    return s


@sfx('barrel_return', 'ENEMY_ATTACK{kind:roll,phase:return}', "61-2 새 — 술통 되치기 '탕'(굴러오는 통을 쳐서 되돌린 순간 = porter_rolling_barrel_returned 로 바뀌는 프레임). 넓은 '딱' + 단단한 나무 몸통(270→115 Hz) + 짧게 울리는 속 빈 통(300·680 Hz) + 쇠테 덜컥 + 거꾸로 밀려 나가는 바람(700→2.2k) + 위로 번뜩이는 짧은 공기(울림 없음). **보스 술통 되치기(BOSS_ATTACK{boss:1,attack:barrel,phase:return})에도 같은 id 재사용** — 짐꾼에서 배운 소리 = 보스 파훼 신호", 0)
def _barrel_return(sr, rng):
    dur = 0.55
    s = zeros(sec(sr, dur))
    mix_into(s, _tang(sr, rng), 0, 1.0)
    mix_into(s, whoosh(sr, 0.26, rng, 700, 2200, q=0.9, a=0.12, r=0.7), sec(sr, 0.015), 0.5)  # 되돌아감
    mix_into(s, slice_(sr, rng, 5000, 9500, 0.07, q=1.2, a=0.2), sec(sr, 0.004), 0.28)    # 번뜩(공기)
    mix_into(s, slosh(sr, rng, 0.3, 380, 760), sec(sr, 0.03), 0.3)
    s = softclip(s, 2.0)
    return reverb(tail(s, sr, 0.02), sr, size=0.5, decay=0.45, wet=0.12)


@sfx('porter_barrel_break', 'ENEMY_ATTACK{kind:roll,phase:break}', "61-2 새 — 짐꾼 술통이 벽·단단한 구조물에 깨짐(porter_barrel_break 8프레임 시작). 부딪는 '쾅'(140→45 Hz) + 속 빈 통 마지막 울림 + 판자 쪼개짐 10 + 쇠테 둘이 떨어져 덜컥·굴러감(낮게) + 술이 한꺼번에 쏟아짐 + 나무 조각 흩어짐. 웅덩이가 퍼질 때 porter_liquor_spill", -1)
def _porter_barrel_break(sr, rng):
    dur = 0.95
    s = zeros(sec(sr, dur))
    mix_into(s, snap(sr, rng, 2000, 0.02, 0.003), 0, 0.9)
    mix_into(s, punch(sr, 140, 45, 0.3, 0.07, 1.8), 0, 1.0)
    mix_into(s, barrel_body(sr, rng, 0.25, (210, 480), 0.05), 0, 0.55)
    mix_into(s, staves(sr, rng, 0.3, 10, 0.0, 0.18, 0.4), 0)
    mix_into(s, gush(sr, rng, 0.75, (3500, 450), 1.0), sec(sr, 0.03), 0.9)
    for t, f in ((0.12, 430), (0.3, 520)):
        mix_into(s, hoop_clunk(sr, rng, f, 0.12, 0.02), sec(sr, t), 0.25)
    mix_into(s, roll(sr, rng, 0.4, 600, 10.0, 0.22), sec(sr, 0.34), 1.0)                 # 쇠테 굴러감(낮게)
    for _ in range(6):
        mix_into(s, wood_tok(sr, rng, rng.uniform(600, 1200), 0.04, 0.006, 0.6), sec(sr, rng.uniform(0.2, 0.6)), 0.15)
    s = softclip(s, 1.6)
    return reverb(s, sr, size=0.6, decay=0.45, wet=0.12)


@sfx('porter_liquor_spill', 'ENEMY_ATTACK{kind:roll,phase:spill}', "61-2 새 — 깨진 술통의 술이 바닥에 퍼짐(fx pool_liquor 가 생기는 프레임, break stateHold 뒤). 넓게 번지는 물결 '쏴아'(1.8k→600) + 꿀렁 셋 + 물방울. 불이 닿으면 기존 drunk_ignite(POOL_IGNITED) → boss1_fire_loop", -6)
def _porter_liquor_spill(sr, rng):
    dur = 0.85
    n = sec(sr, dur)
    s = zeros(n)
    w = svf(noise(sr, dur, rng), sr, sweep(sr, n, 1800, 600), 0.8, 'band')
    mix_into(s, mul(w, env_adsr(sr, dur, 0.05, 0.0, 1.0, 0.6)), 0, 0.8)
    lo = svf(noise(sr, dur, rng), sr, 300, 0.7, 'low')
    mix_into(s, mul(lo, env_adsr(sr, dur, 0.04, 0.0, 1.0, 0.55)), 0, 0.5)
    mix_into(s, glugs(sr, rng, (0.05, 0.17, 0.31), 260, 470, 0.3), 0)
    mix_into(s, droplets(sr, rng, dur, 9, 0.1, 0.75, 500, 1400, 0.22), 0)
    return s


@sfx('porter_hurt', 'ENEMY_DAMAGED{enemy:porter,aux:true}', "61-2 새 — 술통 짐꾼 피격 몸짓(목소리 없음, hurt 4프레임). 낮은 '읍' 끙(노이즈 포먼트 + 가슴 저역) + 큰 몸통 '퍽'(110→48 Hz) + 가죽 멜빵 삐걱 + 등 나무틀 '톡'. hit_enemy 위에 겹침(이 적에게는 enemy_hurt 대신)", -4)
def _porter_hurt(sr, rng):
    dur = 0.32
    s = zeros(sec(sr, dur))
    mix_into(s, grunt(sr, rng, 0.18, (380, 330), (900, 820), 0.55, 1.4, 0.006), 0, 0.85)
    mix_into(s, punch(sr, 110, 48, 0.2, 0.05, 1.5), 0, 0.7)
    mix_into(s, flesh(sr, rng, 320, 0.07, 0.02, 0.8), 0, 0.4)
    mix_into(s, creak(sr, rng, 0.1, 90, 110, (650, 900), 18.0), sec(sr, 0.04), 0.25)    # 멜빵
    mix_into(s, wood_tok(sr, rng, 420, 0.05, 0.008, 0.7), sec(sr, 0.03), 0.25)          # 등 나무틀
    return softclip(s, 1.3)


@sfx('porter_death', 'ENEMY_DIED{enemy:porter}', "61-2 새 — 술통 짐꾼 쓰러짐(목소리 없음, death 10프레임). 길게 빠지는 '끄으' 숨(노이즈) → 0.16 s 무릎이 '쿵' → 0.34 s 큰 몸이 '쿠웅'(95→32 Hz) + 흙·자갈 + 등 나무틀·멜빵 덜그럭 + 쇠테 하나 덜컥 → 한 번 튐 + 먼지. enemy_death 대신(엘리트면 elite_die 위에 겹침)", -1)
def _porter_death(sr, rng):
    dur = 1.15
    s = zeros(sec(sr, dur))
    mix_into(s, grunt(sr, rng, 0.45, (440, 300), (980, 800), 0.6, 1.2, 0.02), 0, 0.7)
    mix_into(s, punch(sr, 130, 55, 0.18, 0.045, 1.4), sec(sr, 0.16), 0.6)                # 무릎
    mix_into(s, gravel(sr, rng, 0.2, 4, 0.0, 0.1, 0.2), sec(sr, 0.16))
    t = sec(sr, 0.34)
    mix_into(s, body_fall(sr, rng, (95, 32), 0.4, 0.11, 1.3, 10), t, 1.0)                 # 큰 몸
    for k, tt in enumerate((0.36, 0.41, 0.48)):
        mix_into(s, wood_tok(sr, rng, 380 + 120 * k, 0.06, 0.01, 0.8), sec(sr, tt), 0.3 - 0.05 * k)
    mix_into(s, hoop_clunk(sr, rng, 450, 0.12, 0.02), sec(sr, 0.44), 0.2)
    mix_into(s, punch(sr, 85, 38, 0.15, 0.035, 1.2), sec(sr, 0.55), 0.35)               # 튐
    s = softclip(s, 1.5)
    return reverb(s, sr, size=0.6, decay=0.45, wet=0.1)


# ===========================================================================
# 3. 보스 '만취' 효과음 패스(P6) — 국면 얼큰(100~65%) → 만취(65~30%) → 인사불성(30%~)
# ===========================================================================

def break_sting(sr, rng, s, t, g=1.0):
    """파훼 공통 신호(4종이 같은 뼈대 — '무너뜨렸다'를 귀로 배운다): 넓은 '쾅' 머리 + 깊은 몸통(180→48 Hz) +
    아래로 꺼지는 '부웅'(220→55 Hz, 균형을 잃음) + 0.14 s 몸이 주저앉는 '쿵' + 저역 압력."""
    t = int(t)
    mix_into(s, snap(sr, rng, 3000, 0.02, 0.003), t, 1.0 * g)
    mix_into(s, punch(sr, 180, 48, 0.4, 0.1, 2.0), t, 1.0 * g)
    dn = lowpass(lowpass(tone(sr, 0.45, 220, 55, kind='saw'), sr, 600), sr, 600)
    mix_into(s, mul(dn, env_adsr(sr, 0.45, 0.01, 0.0, 1.0, 0.35)), t + sec(sr, 0.02), 0.5 * g)
    mix_into(s, sub(sr, 72, 34, 0.5, 0.14, 150), t + sec(sr, 0.14), 0.9 * g)
    mix_into(s, punch(sr, 125, 46, 0.26, 0.06, 1.5), t + sec(sr, 0.14), 0.6 * g)
    pr = lowpass(burst(sr, 0.3, rng, fc=300, q=0.6, tau=0.07, mode='low'), sr, 500)
    mix_into(s, pr, t, 0.7 * g)


def winded(sr, rng, g=1.0):
    """보스가 숨이 턱 막혀 내뱉는 낮은 '허억'(노이즈, 목소리 아님)."""
    return scale(breath(sr, rng, 0.45, (620, 420), (1100, 900), 0.5, 0.02, 0.8, 1.2), g)


# ---- 파훼 4종 (ui:boss-break{kind:cup|pillar|cask|stumble}) -------------------------------------------------

@sfx('boss1_break_cup', 'ui:boss-break{kind:cup}', "61-2 새 — 파훼 · 잔 깨짐(한 잔 더 마시는 중 큰 잔 약점 적중 → 경직). 도자기 몸통이 갈라지는 둔탁한 '빡' + 짧은 조각(3 kHz 위, 감쇠 짧게) + 술을 뒤집어쓰는 '촤악' + 물방울 + 파훼 공통 신호(쾅 → 꺼지는 '부웅' → 주저앉는 '쿵') + 0.35 s 사레들린 기침 둘(노이즈). boss1_cup_shatter 를 대신함", 0, category='boss')
def _boss1_break_cup(sr, rng):
    dur = 1.5
    s = zeros(sec(sr, dur))
    mix_into(s, crunch(burst(sr, 0.08, rng, fc=1300, q=0.7, tau=0.02), 7), 0, 0.8)        # 도자기 몸통 '빡'
    mix_into(s, wood_tok(sr, rng, 700, 0.06, 0.01, 0.9), 0, 0.5)
    mix_into(s, glass_shards(sr, rng, 0.4, 11, 0.0, 0.3, 3000, 6500, 0.22), 0)
    break_sting(sr, rng, s, 0)
    mix_into(s, gush(sr, rng, 0.85, (3200, 500), 1.0), sec(sr, 0.02), 0.85)               # 뒤집어씀
    mix_into(s, droplets(sr, rng, 1.3, 14, 0.15, 0.95, 600, 1600, 0.25), 0)
    for t in (0.36, 0.53):                                                                # 기침(노이즈)
        mix_into(s, breath(sr, rng, 0.11, (900, 650), (1500, 1200), 0.5, 0.003, 1.0, 0.8), sec(sr, t), 0.5)
    s = softclip(s, 1.8)
    return reverb(s, sr, size=0.8, decay=0.55, wet=0.16)


@sfx('boss1_break_pillar', 'ui:boss-break{kind:pillar}', "61-2 새 — 파훼 · 기둥 무너짐(돌진하다 기둥에 정면 충돌 → 경직). 머리로 들이받는 큰 '쿵'(120→38 Hz) + 기둥 나무가 쪼개짐 + 파훼 공통 신호 → 0.15~0.6 s 기둥이 기우는 낮은 삐걱 신음 → 0.62 s 무너지는 '와르르'(큰 몸통 + 판자 + 돌 부스러기 18) + 먼지. 돌방 울림", 0, category='boss')
def _boss1_break_pillar(sr, rng):
    dur = 1.9
    n = sec(sr, dur)
    s = zeros(n)
    mix_into(s, punch(sr, 120, 38, 0.45, 0.12, 2.2), 0, 1.0)
    mix_into(s, staves(sr, rng, 0.2, 6, 0.0, 0.08, 0.4, 300, 700), 0)
    break_sting(sr, rng, s, 0, 0.9)
    ng = sec(sr, 0.5)                                                                     # 기우는 신음
    gr = svf(tone(sr, 0.5, 58, 44, kind='saw'), sr, sweep(sr, ng, 320, 180), 3.0, 'band')
    gr = mul(gr, [0.6 + 0.4 * math.sin(TAU * 4 * i / sr) for i in range(ng)])
    mix_into(s, mul(gr, env_adsr(sr, 0.5, 0.25, 0.0, 1.0, 0.08)), sec(sr, 0.14), 0.5)
    mix_into(s, creak(sr, rng, 0.42, 60, 75, (300, 650), 7.0, 3.0), sec(sr, 0.18), 0.3)
    t = sec(sr, 0.62)                                                                     # 무너짐
    mix_into(s, punch(sr, 90, 30, 0.55, 0.15, 2.0), t, 1.0)
    mix_into(s, burst(sr, 0.4, rng, fc=250, q=0.6, tau=0.1, mode='low'), t, 0.9)
    mix_into(s, staves(sr, rng, 0.35, 8, 0.0, 0.22, 0.32, 300, 800), t)
    mix_into(s, gravel(sr, rng, 0.8, 18, 0.0, 0.6, 0.3), t)
    for _ in range(5):
        mix_into(s, wood_tok(sr, rng, rng.uniform(450, 900), 0.05, 0.008, 0.6), t + sec(sr, rng.uniform(0.25, 0.65)), 0.18)
    dust = mul(svf(noise(sr, 1.1, rng), sr, 900, 0.7, 'low'), env_adsr(sr, 1.1, 0.05, 0.0, 1.0, 0.9))
    mix_into(s, dust, t, 0.25)
    s = softclip(s, 1.7)
    return reverb(s, sr, size=1.1, decay=0.62, wet=0.2)


@sfx('boss1_break_barrel', 'ui:boss-break{kind:cask}', "61-2 새 — 파훼 · 술통 되치기(되돌린 술통이 만취에게 박혀 터짐 → 경직). 통이 몸에 박히는 '콰직'(판자 9 + 속 빈 통 마지막 울림 + 쇠테 덜컥 둘) + 술이 한꺼번에 터져 뒤집어씀 + 파훼 공통 신호 + 0.3 s 숨이 턱 막힌 '허억'(노이즈). 되치기 순간의 '탕'은 barrel_return(짐꾼과 같은 소리)", 0, category='boss')
def _boss1_break_barrel(sr, rng):
    dur = 1.5
    s = zeros(sec(sr, dur))
    mix_into(s, snap(sr, rng, 2400, 0.02, 0.003), 0, 0.8)
    mix_into(s, barrel_body(sr, rng, 0.3, (215, 490), 0.06), 0, 0.7)
    mix_into(s, staves(sr, rng, 0.3, 9, 0.0, 0.15, 0.42), 0)
    for t, f in ((0.08, 450), (0.22, 540)):
        mix_into(s, hoop_clunk(sr, rng, f, 0.12, 0.02), sec(sr, t), 0.22)
    break_sting(sr, rng, s, 0)
    mix_into(s, gush(sr, rng, 0.85, (3600, 450), 1.0), sec(sr, 0.02), 0.95)
    mix_into(s, winded(sr, rng), sec(sr, 0.3), 0.6)
    s = softclip(s, 1.8)
    return reverb(s, sr, size=0.8, decay=0.55, wet=0.15)


@sfx('boss1_break_reel', 'ui:boss-break{kind:stumble}', "61-2 새 — 파훼 · 취권 꺾임(3연 취권 돌진을 받아쳐 꺾음 → 경직). 받아치는 '딱' + 채찍 같은 '샥' → 몸이 비틀려 도는 바람(7 Hz 로 휘며 내려감) + 파훼 공통 신호 → 0.32 s 크게 나뒹구는 '쿵'(boss1_fall 보다 큼) + 바닥 잔·소품 튐 + 먼지. 파훼로 인정된 넘어짐이면 boss1_fall 대신. 시스템 내부 이름 reel → UI 이벤트 kind stumble", 0, category='boss')
def _boss1_break_reel(sr, rng):
    dur = 1.6
    s = zeros(sec(sr, dur))
    mix_into(s, snap(sr, rng, 3200, 0.016, 0.0022), 0, 0.9)
    mix_into(s, slice_(sr, rng, 6500, 2000, 0.08, q=1.1), 0, 0.5)
    nw = sec(sr, 0.36)
    cut = [1400 * (350 / 1400) ** (i / nw) * (1 + 0.3 * math.sin(TAU * 7 * i / sr)) for i in range(nw)]
    w = mul(svf(noise(sr, 0.36, rng), sr, cut, 0.9, 'band'), env_adsr(sr, 0.36, 0.03, 0.0, 1.0, 0.2))
    mix_into(s, w, sec(sr, 0.02), 0.7)                                                    # 비틀려 도는 몸
    break_sting(sr, rng, s, 0, 0.85)
    t = sec(sr, 0.32)
    mix_into(s, kick(sr, 0.7, 90, 30, 0.2, rng=rng), t, 1.3)                              # 나뒹굶
    mix_into(s, burst(sr, 0.35, rng, fc=250, q=0.6, tau=0.09, mode='low'), t, 1.0)
    mix_into(s, punch(sr, 110, 45, 0.3, 0.06, 1.4), t + sec(sr, 0.17), 0.5)
    for k, tt in enumerate((0.4, 0.47, 0.53, 0.6)):
        mix_into(s, wood_tok(sr, rng, 800 - 60 * k, 0.05, 0.008, 0.6), sec(sr, tt), 0.3 - 0.05 * k)
    dust = mul(svf(noise(sr, 0.7, rng), sr, 900, 0.7, 'low'), env_adsr(sr, 0.7, 0.05, 0.0, 1.0, 0.55))
    mix_into(s, dust, t, 0.22)
    s = softclip(s, 1.7)
    return reverb(s, sr, size=1.0, decay=0.6, wet=0.2)


# ---- 결정타 · 쓰러짐 · 등장 ---------------------------------------------------------

@redo('break_finisher', "결정타(61-2 다시 만듦 — 크고 묵직하게, 쇠·징·종 울림 제거). 0.08 s 빨려드는 역바람 → 일격: 겹으로 터지는 '딱-딱' + 날이 파고드는 '샥' + 아주 깊은 몸통(150→32 Hz) + 큰 북 '둥'(75→30 Hz) + 0.9 s 이어지는 낮은 울림(D2→A1, 무게만) + 저역 압력 + 흙·돌 튐 + 번쩍이는 고역 공기 → 0.3 s 두 번째 낮은 '둥'. 큰 돌방 울림. 파일 0.08 s = 일격. 마지막 일격으로 쓰러지면 boss1_die 와 같은 프레임에 겹침(boss1_die 앞 0.3 s 는 일부러 조용함)")
def _break_finisher61(sr, rng):
    dur = 2.1
    s = zeros(sec(sr, dur))
    m = sec(sr, 0.08)
    pre = svf(noise(sr, 0.08, rng), sr, sweep(sr, m, 700, 5000), 1.4, 'band')
    mix_into(s, mul(pre, [(i / m) ** 2 for i in range(m)]), 0, 0.6)
    mix_into(s, snap(sr, rng, 2600, 0.02, 0.003), m, 1.0)
    mix_into(s, snap(sr, rng, 1600, 0.02, 0.004), m + sec(sr, 0.012), 0.7)
    mix_into(s, slice_(sr, rng, 9000, 3000, 0.08, q=1.0), m, 0.45)
    mix_into(s, punch(sr, 150, 32, 0.6, 0.16, 2.4), m, 1.0)
    mix_into(s, kick(sr, 0.9, 75, 30, 0.26, rng=rng), m, 1.0)
    boom = lowpass(lowpass(add(tone(sr, 1.4, 73.4, 55.0), scale(tone(sr, 1.4, 110.0, 82.4, kind='tri'), 0.35)), sr, 260), sr, 260)
    mix_into(s, mul(boom, env_exp(sr, 1.4, 0.45)), m, 0.55)                               # 이어지는 낮은 울림
    mix_into(s, lowpass(burst(sr, 0.45, rng, fc=220, q=0.6, tau=0.12, mode='low'), sr, 450), m, 0.9)
    mix_into(s, crunch(flesh(sr, rng, 520, 0.1, 0.025, 0.8), 6), m, 0.5)
    mix_into(s, gravel(sr, rng, 0.6, 14, 0.0, 0.35, 0.3), m)
    air = svf(noise(sr, 0.25, rng), sr, 6500, 0.7, 'high')
    mix_into(s, mul(air, env_adsr(sr, 0.25, 0.004, 0.0, 1.0, 0.24)), m, 0.2)
    mix_into(s, kick(sr, 0.7, 62, 28, 0.22, rng=rng), m + sec(sr, 0.3), 0.6)              # 두 번째 '둥'
    s = softclip(s, 2.0)
    return reverb(s, sr, size=1.4, decay=0.78, wet=0.3)


@sfx('boss1_die', 'BOSS_DIED{boss:1}', "61-2 새 — 만취 쓰러짐(1층 보스 처치 연출, boss_die 대신). 처음 0.3 s 는 결정타가 들리게 조용히 낮게 앓는 숨(노이즈) → 0.35 s 무거운 비틀 걸음 + 마루 삐걱 → 0.6 s 손에서 큰 잔이 미끄러져 '톡'·데굴 → 0.75 s 무릎 '쿵' → 1.05 s 큰 몸이 탁자를 쓸며 넘어지는 '쿠웅'(85→28 Hz) + 판자·소품 덜그럭 + 쏟아지는 술 꿀렁 + 먼지 → 1.6 s 마지막 긴 숨 → 낮은 울림이 꺼지며 정적. 돌방 울림", 0, category='boss')
def _boss1_die(sr, rng):
    dur = 3.3
    s = zeros(sec(sr, dur))
    mix_into(s, breath(sr, rng, 0.9, (700, 420), (1200, 950), 0.5, 0.15, 0.8, 1.0), sec(sr, 0.05), 0.45)
    mix_into(s, punch(sr, 100, 40, 0.18, 0.045, 1.4), sec(sr, 0.35), 0.7)                  # 비틀 걸음
    mix_into(s, creak(sr, rng, 0.25, 65, 80, (350, 700), 9.0), sec(sr, 0.37), 0.25)
    mix_into(s, wood_tok(sr, rng, 650, 0.06, 0.01, 0.8), sec(sr, 0.6), 0.4)               # 잔이 미끄러짐
    mix_into(s, roll(sr, rng, 0.55, 750, 12.0, 0.3), sec(sr, 0.63), 1.0)
    mix_into(s, punch(sr, 120, 48, 0.25, 0.06, 1.5), sec(sr, 0.75), 0.8)                 # 무릎
    t = sec(sr, 1.05)
    mix_into(s, kick(sr, 0.9, 85, 28, 0.24, rng=rng), t, 1.5)                             # 큰 몸
    mix_into(s, burst(sr, 0.5, rng, fc=220, q=0.6, tau=0.12, mode='low'), t, 1.1)
    mix_into(s, punch(sr, 140, 50, 0.3, 0.07, 1.6), t, 0.6)
    mix_into(s, staves(sr, rng, 0.3, 6, 0.0, 0.2, 0.3, 350, 800), t)                      # 탁자 쓸림
    for _ in range(8):
        mix_into(s, wood_tok(sr, rng, rng.uniform(500, 1200), 0.05, 0.007, 0.6), t + sec(sr, rng.uniform(0.08, 0.6)), 0.16)
    mix_into(s, glugs(sr, rng, (0.0, 0.13, 0.28), 260, 450, 0.3), t + sec(sr, 0.3))
    mix_into(s, gravel(sr, rng, 0.9, 14, 0.0, 0.6, 0.25), t)
    dust = mul(svf(noise(sr, 1.0, rng), sr, 800, 0.7, 'low'), env_adsr(sr, 1.0, 0.05, 0.0, 1.0, 0.85))
    mix_into(s, dust, t, 0.22)
    mix_into(s, breath(sr, rng, 0.8, (560, 380), (1000, 820), 0.4, 0.1, 1.0, 0.8), sec(sr, 1.6), 0.4)  # 마지막 숨
    dr = lowpass(add(tone(sr, 1.6, 73.4), scale(tone(sr, 1.6, 110.0), 0.4)), sr, 300)
    mix_into(s, mul(dr, env_adsr(sr, 1.6, 0.3, 0.0, 1.0, 1.2)), sec(sr, 1.3), 0.18)       # 정적으로 꺼짐
    s = softclip(s, 1.5)
    return reverb(s, sr, size=1.4, decay=0.78, wet=0.32)


@sfx('boss1_entrance', 'boss:intro', "61-2 새 — 만취 등장(1층 보스 등장 연출 boss:intro, boss_start 대신 — 1층 BGM 인트로 역할. 보스 1국면 곡은 boss:fight 부터 권장). 큰 잔을 탁자에 내리치는 '탁!' + 잔들 덜그럭 + 큰 북 '둥' → 울렁이며 깔리는 낮은 불협(D2·G#2 톱니, 0.5 Hz 맥놀이) → 0.55·1.15 s 무거운 걸음 둘 + 마루 삐걱 → 1.4 s 크게 내뱉는 '크아'(노이즈) → 1.6 s 등불이 확 살아나는 '화륵'. 돌방 울림", 0, category='boss')
def _boss1_entrance(sr, rng):
    dur = 2.7
    s = zeros(sec(sr, dur))
    mix_into(s, table_slam(sr, rng), 0, 1.0)
    mix_into(s, slosh(sr, rng, 0.35, 380, 760), sec(sr, 0.02), 0.4)
    mix_into(s, kick(sr, 0.7, 85, 30, 0.22, rng=rng), sec(sr, 0.03), 1.1)
    n = sec(sr, 2.6)
    wob = [math.sin(TAU * 0.5 * i / sr) for i in range(n)]
    dr = add(tone_f(sr, [73.42 * (1 + 0.012 * w) for w in wob], 'saw'),
             scale(tone_f(sr, [103.83 * (1 - 0.012 * w) for w in wob], 'saw'), 0.7))
    dr = lowpass(lowpass(dr, sr, 300), sr, 300)
    mix_into(s, mul(dr, env_adsr(sr, 2.6, 0.9, 0.0, 1.0, 1.0)), sec(sr, 0.05), 0.4)       # 낮은 불협
    for t in (0.55, 1.15):
        mix_into(s, punch(sr, 105, 40, 0.22, 0.055, 1.6), sec(sr, t), 0.75)               # 걸음
        mix_into(s, creak(sr, rng, 0.2, 62, 78, (330, 650), 9.0), sec(sr, t + 0.02), 0.2)
    mix_into(s, kha(sr, rng, 0.9, 0.45), sec(sr, 1.4), 1.1)                               # '크아'
    mix_into(s, flame(sr, rng, 0.7, 300, 2200, a=0.05), sec(sr, 1.6), 0.6)                # 등불 '화륵'
    mix_into(s, crackle(sr, rng, 0.8, 10, 0.25), sec(sr, 1.7))
    s = softclip(s, 1.4)
    return reverb(s, sr, size=1.3, decay=0.75, wet=0.3)


# ---- 국면 전환 (BOSS_PHASE{boss:1,phase}) ---------------------------------------------

@redo('boss1_phase_drink', "만취 국면 전환 1→2(얼큰 → 만취, 61-2 다시 만듦 — 트리거를 phase:2 로 좁힘). 잔 들어 출렁 → 0.15 s 꿀꺽 셋(더 낮고 굵게) → 0.85 s 큰 '크아'(노이즈) + 큰 북 '둥' + 1.25 s 두 번째 '둥' → 0.85~2.6 s '세상이 돈다' 울렁임(0.5 Hz = 화면 기울기 2 s, 내려가는 톱니 두 겹 + 소용돌이 바람). 기울기 설정이 꺼져도 소리는 그대로(멀미 설정은 그림만)",
      trigger='BOSS_PHASE{boss:1,phase:2}')
def _boss1_phase_drink61(sr, rng):
    dur = 2.7
    s = zeros(sec(sr, dur))
    mix_into(s, slosh(sr, rng, 0.3, 350, 700), 0, 0.5)
    for k, t0 in enumerate((0.15, 0.36, 0.56)):
        mix_into(s, gulp(sr, rng, 84 + 6 * k, 200 + 14 * k, 0.19), sec(sr, t0), 1.0)
    t = sec(sr, 0.85)
    mix_into(s, kha(sr, rng, 0.9, 0.45), t, 1.2)
    mix_into(s, kick(sr, 0.6, 90, 30, 0.18, rng=rng), t, 1.0)
    mix_into(s, kick(sr, 0.5, 72, 28, 0.16, rng=rng), sec(sr, 1.25), 0.7)
    mix_into(s, woozy(sr, 1.8, 70, 48, rng), t, 0.9)
    s = softclip(s, 1.3)
    return reverb(s, sr, size=1.2, decay=0.72, wet=0.28)


@sfx('boss1_phase_blackout', 'BOSS_PHASE{boss:1,phase:3}', "61-2 새 — 만취 국면 전환 2→3(만취 → 인사불성). 술단지째 들이붓는 꿀꺽 다섯(빠르게) + 흘러넘치는 술 → 0.9 s 단지를 내던지는 '휙' → 1.1 s 바닥에 깨지는 '와장창'(도자기, 짧게) + 가장 깊은 '크아아'(노이즈) + 무거운 심장 셋(점점 크게) → 1.0~3.0 s 더 깊고 느린 울렁임(52→38 Hz). 등불 끄기는 이어지는 boss1_candle_topple(3국면 진입 확정 패턴)", 0, category='boss')
def _boss1_phase_blackout(sr, rng):
    dur = 3.1
    s = zeros(sec(sr, dur))
    mix_into(s, slosh(sr, rng, 0.25, 320, 650), 0, 0.4)
    for k, t0 in enumerate((0.1, 0.24, 0.37, 0.5, 0.63)):
        mix_into(s, gulp(sr, rng, 78 + 4 * k, 185 + 10 * k, 0.15), sec(sr, t0), 0.95)
    pour = svf(noise(sr, 0.7, rng), sr, 600, 1.0, 'band')
    mix_into(s, mul(pour, env_adsr(sr, 0.7, 0.1, 0.0, 1.0, 0.3)), sec(sr, 0.1), 0.25)    # 흘러넘침
    mix_into(s, whoosh(sr, 0.2, rng, 1300, 450, q=1.0, a=0.2, r=0.6), sec(sr, 0.9), 0.5)
    t = sec(sr, 1.1)
    mix_into(s, crunch(burst(sr, 0.08, rng, fc=1200, q=0.7, tau=0.02), 7), t, 0.7)        # 단지 깨짐
    mix_into(s, wood_tok(sr, rng, 560, 0.07, 0.012, 0.9), t, 0.5)
    mix_into(s, glass_shards(sr, rng, 0.35, 8, 0.0, 0.25, 2800, 6000, 0.18), t)
    mix_into(s, kha(sr, rng, 1.2, 0.55), sec(sr, 1.0), 1.3)                               # '크아아'
    mix_into(s, kick(sr, 0.7, 80, 28, 0.2, rng=rng), sec(sr, 1.0), 1.0)
    for k, tb in enumerate((1.3, 1.9, 2.5)):
        mix_into(s, heartbeat(sr, rng, 0.6 + 0.2 * k), sec(sr, tb), 1.0)                   # 심장(점점 크게)
    mix_into(s, woozy(sr, 2.0, 52, 38, rng, depth=0.08, det=1.04, cut=(320, 200), a=0.4, r=0.8), sec(sr, 1.0), 1.0)
    s = softclip(s, 1.4)
    return reverb(s, sr, size=1.4, decay=0.78, wet=0.32)


@redo('boss1_spin_start', "'세상이 돈다'(61-2 다시 만듦 — 희미한 2.9 kHz 이질 고음 제거). 2 s 주기로 울렁이며 내려가는 저음 톱니 두 겹 + 소용돌이 바람 + 0.3·1.3 s 휘청이는 발 끌림. 국면 전환 소리(boss1_phase_drink·boss1_phase_blackout)에 같은 울렁임이 들어 있으므로, 시스템이 국면 전환과 별도로 '세상이 돈다'를 쓸 때만")
def _boss1_spin_start61(sr, rng):
    dur = 2.2
    s = zeros(sec(sr, dur))
    mix_into(s, woozy(sr, 2.0, 72, 46, rng), 0, 1.0)
    for t in (0.3, 1.3):
        mix_into(s, punch(sr, 140, 70, 0.08, 0.02, 1.2), sec(sr, t), 0.35)
        mix_into(s, scuff(sr, rng, 0.16, 1100), sec(sr, t), 0.3)
    return reverb(s, sr, size=1.2, decay=0.75, wet=0.3)


# ---- 등불 꺼짐 · 다시 켜짐 (3국면 진입 확정 1회 + 이후 패턴) ---------------------------

@redo('boss1_candle_topple', "등불 꺼짐(61-2 다시 만듦 — 520 Hz 쇠 촛대 '쨍그랑' 제거). 크게 휘두르는 팔 바람 → 0.12 s 등잔이 엎어지는 둔탁한 '톡' + 기름 찰랑 → 0.18·0.32·0.44·0.54 s 방 안 등불이 차례로 꺼지는 '훅' 넷(점점 작게) → 깔려 내려가는 어둠의 저음(110→45 Hz) + 서늘한 바람결. 돌방 울림. 권장 음량 -2 → 0 dB(화면이 어두워지는 큰 사건)", 0)
def _boss1_candle_topple61(sr, rng):
    dur = 1.7
    s = zeros(sec(sr, dur))
    mix_into(s, whoosh(sr, 0.28, rng, 650, 220, q=0.8, a=0.3, r=0.6), 0, 0.5)
    mix_into(s, wood_tok(sr, rng, 560, 0.07, 0.012, 0.8), sec(sr, 0.12), 0.55)           # 등잔 엎어짐
    mix_into(s, punch(sr, 180, 90, 0.1, 0.025, 1.3), sec(sr, 0.12), 0.4)
    mix_into(s, slosh(sr, rng, 0.2, 450, 900), sec(sr, 0.13), 0.25)                      # 기름
    for k, t in enumerate((0.18, 0.32, 0.44, 0.54)):                                     # 꺼짐 '훅'
        m = sec(sr, 0.14)
        pf = svf(noise(sr, 0.14, rng), sr, sweep(sr, m, 950 - 60 * k, 260), 0.9, 'band')
        mix_into(s, mul(pf, env_adsr(sr, 0.14, 0.008, 0.0, 1.0, 0.12)), sec(sr, t), 0.95 - 0.12 * k)
        mix_into(s, crackle(sr, rng, 0.06, 2, 0.2), sec(sr, t))
    dk = mul(lowpass(tone(sr, 1.1, 110, 45), sr, 300), env_adsr(sr, 1.1, 0.15, 0.0, 1.0, 0.8))
    mix_into(s, dk, sec(sr, 0.5), 0.12)                                                  # 어둠
    cold = svf(noise(sr, 1.0, rng), sr, 2600, 0.7, 'band')
    mix_into(s, mul(cold, env_adsr(sr, 1.0, 0.3, 0.0, 1.0, 0.65)), sec(sr, 0.55), 0.07)
    return reverb(s, sr, size=1.1, decay=0.65, wet=0.24)


@redo('boss1_candle_relight', "등불 다시 켜짐(61-2 다시 만듦 — 2.2 kHz 쇠 틱 제거, 타격·E). 심지에 닿는 작은 '톡' + 긁힘 → 0.03 s 불이 붙는 '화륵'(350→2.8k) + 따뜻하게 부푸는 저역 + 작은 타닥. 안심되는 소리")
def _boss1_candle_relight61(sr, rng):
    dur = 0.85
    s = zeros(sec(sr, dur))
    mix_into(s, wood_tok(sr, rng, 1350, 0.03, 0.004, 0.5), 0, 0.35)
    mix_into(s, burst(sr, 0.02, rng, fc=4200, q=0.7, tau=0.004), 0, 0.3)
    mix_into(s, flame(sr, rng, 0.38, 350, 2800, a=0.07), sec(sr, 0.03), 1.1)
    mix_into(s, thud(sr, 0.2, 120, 70, 0.05), sec(sr, 0.04), 0.35)
    warm = mul(svf(noise(sr, 0.55, rng), sr, 340, 0.7, 'low'), env_adsr(sr, 0.55, 0.12, 0.0, 1.0, 0.35))
    mix_into(s, warm, sec(sr, 0.1), 0.55)
    mix_into(s, crackle(sr, rng, 0.5, 6, 0.22), sec(sr, 0.2))
    return reverb(s, sr, size=0.7, decay=0.5, wet=0.14)


# ---- 잔 마시기 · 술통 (금속 울림 다시) -----------------------------------------------

@redo('boss1_drink_lift', "만취 큰 잔 들기(한 잔 더 예고, 61-2 다시 만듦 — 1.5 kHz 유리 울림 제거). 팔을 드는 옷 바람 + 탁자에서 잔이 끌리는 '드륵' + 도자기 '톡'(짧게) + 무겁게 출렁이는 술 + 0.1~0.5 s 낮게 올라가는 기대음(80→130 Hz, 예고). 이 소리가 들리면 잔을 노린다. 권장 음량 -3 → -2 dB(예고 우선순위 4)", -2)
def _boss1_drink_lift61(sr, rng):
    dur = 0.55
    s = zeros(sec(sr, dur))
    mix_into(s, whoosh(sr, 0.32, rng, 300, 950, q=0.8, a=0.45, r=0.45), 0, 0.35)
    ns = sec(sr, 0.12)
    dr = svf(noise(sr, 0.12, rng), sr, 900, 1.5, 'band')
    dr = mul(dr, [0.5 + 0.5 * math.sin(TAU * 32 * i / sr) for i in range(ns)])
    mix_into(s, mul(dr, env_adsr(sr, 0.12, 0.01, 0.0, 1.0, 0.08)), 0, 0.4)                 # 끌림
    mix_into(s, wood_tok(sr, rng, 720, 0.05, 0.008, 0.8), sec(sr, 0.08), 0.5)            # 도자기 '톡'
    mix_into(s, slosh(sr, rng, 0.42, 320, 680), sec(sr, 0.1), 0.85)
    up = mul(lowpass(tone(sr, 0.42, 80, 130, kind='saw'), sr, 380), env_adsr(sr, 0.42, 0.3, 0.0, 1.0, 0.08))
    mix_into(s, up, sec(sr, 0.1), 0.35)
    return softclip(s, 1.4)


@redo('boss1_drink_finish', "만취 다 마심(61-2 다시 만듦 — 유리 틱 제거). '크아' 숨(노이즈 포먼트, 목소리 아님) + 0.72 s 큰 잔을 탁자에 내려놓는 '탁!'(나무 몸통 + 잔들 덜그럭)")
def _boss1_drink_finish61(sr, rng):
    s = zeros(sec(sr, 1.15))
    mix_into(s, kha(sr, rng, 0.7, 0.3), 0, 1.0)
    mix_into(s, table_slam(sr, rng, 0.8), sec(sr, 0.72), 0.55)
    return reverb(s, sr, size=0.7, decay=0.5, wet=0.15)


@redo('boss1_barrel_kick', "술통 걷어차기(61-2 다시 만듦 — 쇠테 울림을 낮고 짧게). 장화가 통을 차는 '퍽'(160→75 Hz) + 속 빈 통 울림 + 쇠테 덜컥 + 출렁 → 0.18·0.3 s 굴러 나가는 덜컹 둘. 짐꾼 porter_push 와 같은 재료를 더 크게")
def _boss1_barrel_kick61(sr, rng):
    dur = 0.6
    s = zeros(sec(sr, dur))
    mix_into(s, snap(sr, rng, 1500, 0.016, 0.003), 0, 0.8)
    mix_into(s, punch(sr, 160, 75, 0.25, 0.06, 1.7), 0, 1.0)
    mix_into(s, barrel_body(sr, rng, 0.3, (225, 510), 0.075), 0, 0.7)
    mix_into(s, hoop_clunk(sr, rng, 470), sec(sr, 0.004), 0.22)
    mix_into(s, slosh(sr, rng, 0.42, 330, 680), sec(sr, 0.05), 0.4)
    for k, t in enumerate((0.18, 0.3)):
        mix_into(s, thud(sr, 0.06, 150, 95, 0.02), sec(sr, t), 0.45 - 0.1 * k)
        mix_into(s, burst(sr, 0.02, rng, fc=1300, q=0.7, tau=0.004), sec(sr, t), 0.13)
    return softclip(s, 1.5)


@redo('boss1_barrel_bounce', "술통이 벽·기둥에 튕김(61-2 다시 만듦 — 950 Hz 쇠 울림 제거). 돌에 부딪는 '쿵'(130→55 Hz) + 넓은 '딱' + 속 빈 통 울림 + 쇠테 덜컥(낮게) + 출렁. 되치기 '탕'(barrel_return)보다 둔하다 — 벽에 맞은 것과 쳐낸 것을 구별")
def _boss1_barrel_bounce61(sr, rng):
    dur = 0.55
    s = zeros(sec(sr, dur))
    mix_into(s, punch(sr, 130, 55, 0.3, 0.065, 1.6), 0, 1.0)
    mix_into(s, snap(sr, rng, 2300, 0.016, 0.003), 0, 0.55)
    mix_into(s, barrel_body(sr, rng, 0.3, (210, 480), 0.07), 0, 0.75)
    mix_into(s, burst(sr, 0.1, rng, fc=400, q=0.6, tau=0.025, mode='low'), 0, 0.5)
    mix_into(s, hoop_clunk(sr, rng, 430, 0.12, 0.02), sec(sr, 0.01), 0.22)
    mix_into(s, slosh(sr, rng, 0.35, 330, 680), sec(sr, 0.04), 0.35)
    s = softclip(s, 1.4)
    return reverb(s, sr, size=0.8, decay=0.5, wet=0.12)


# ---- 1국면 패턴: 돌진(기둥 파훼의 출발) · 내리찍기 ----------------------------------

@sfx('boss1_dash_telegraph', 'BOSS_TELEGRAPH{boss:1,attack:dash}', "61-2 새 — 만취 돌진 예고(≈650 ms, 기둥 파훼의 출발 — boss_telegraph 대신, 쇠 긁힘 제거). 바닥을 구르는 무거운 발 둘(0·0.25 s) + 흙 긁기 + 0.45 s 콧김 '흥'(노이즈) + 낮게 올라가는 으르렁(55→120 Hz 톱니, 컷오프가 열림)", -2, category='boss')
def _boss1_dash_telegraph(sr, rng):
    dur = 0.65
    n = sec(sr, dur)
    s = zeros(n)
    g = svf(tone(sr, dur, 55, 120, kind='saw'), sr, sweep(sr, n, 200, 850), 1.4, 'low')
    mix_into(s, mul(g, env_adsr(sr, dur, 0.12, 0.0, 1.0, 0.06)), 0, 0.55)
    for k, t in enumerate((0.0, 0.25)):
        mix_into(s, punch(sr, 120, 48, 0.16, 0.04, 1.6), sec(sr, t), 0.8)
        mix_into(s, scuff(sr, rng, 0.18, 1100), sec(sr, t + 0.02), 0.45)
    mix_into(s, breath(sr, rng, 0.12, (1100, 900), (1900, 1700), 0.3, 0.004, 1.0), sec(sr, 0.45), 0.4)  # 콧김
    return s


@sfx('boss1_dash', 'BOSS_ATTACK{boss:1,attack:dash}', "61-2 새 — 만취 돌진(직선, 기둥에 부딪히면 boss1_break_pillar). 무거운 바람(300→1.1k) + 빠른 쿵쿵 걸음 넷 + 배 속 술 출렁 + 옷 펄럭", -1, category='boss')
def _boss1_dash(sr, rng):
    dur = 0.6
    s = zeros(sec(sr, dur))
    mix_into(s, whoosh(sr, 0.5, rng, 300, 1100, q=0.8, a=0.15, r=0.5), 0, 0.8)
    for k, t in enumerate((0.0, 0.11, 0.22, 0.33)):
        mix_into(s, punch(sr, 125, 50, 0.13, 0.03, 1.5), sec(sr, t), 0.7 - 0.08 * k)
        mix_into(s, burst(sr, 0.04, rng, fc=900, q=0.7, tau=0.01), sec(sr, t), 0.25)
    mix_into(s, slosh(sr, rng, 0.45, 300, 600), sec(sr, 0.05), 0.3)
    mix_into(s, rustle(sr, rng, 0.4, 1800, 18), sec(sr, 0.05), 0.25)
    return softclip(s, 1.3)


@sfx('boss1_slam_telegraph', 'BOSS_TELEGRAPH{boss:1,attack:slam}', "61-2 새 — 만취 내리찍기 예고(두 팔을 머리 위로). 위로 올라가는 옷 바람(300→1.4k) + 힘주어 들이쉬는 숨(노이즈) + 낮게 차오르는 압력(70→110 Hz)", -2, category='boss')
def _boss1_slam_telegraph(sr, rng):
    dur = 0.5
    s = zeros(sec(sr, dur))
    mix_into(s, whoosh(sr, 0.45, rng, 300, 1400, q=0.8, a=0.8, r=0.15), 0, 0.55)
    br = breath(sr, rng, 0.4, (500, 760), (1000, 1300), 0.3, 0.26, 1.4, 0.0, 0.12)   # 들이쉼(커졌다 짧게 닫힘)
    mix_into(s, br, sec(sr, 0.04), 0.45)
    up = mul(lowpass(tone(sr, 0.45, 70, 110, kind='saw'), sr, 350), env_adsr(sr, 0.45, 0.35, 0.0, 1.0, 0.05))
    mix_into(s, up, 0, 0.4)
    return s


@sfx('boss1_slam', 'BOSS_ATTACK{boss:1,attack:slam}', "61-2 새 — 만취 내리찍기 착지(바닥 강타). 넓은 '쾅' + 깊은 몸통(110→32 Hz) + 저역 압력 + 마룻장 쪼개짐 + 흙·돌 튐 + 0.12~0.3 s 바닥의 잔·소품이 튀어 덜그럭 + 먼지. 돌방 울림", 0, category='boss')
def _boss1_slam(sr, rng):
    dur = 1.0
    s = zeros(sec(sr, dur))
    mix_into(s, snap(sr, rng, 1800, 0.02, 0.0035), 0, 0.9)
    mix_into(s, punch(sr, 110, 32, 0.5, 0.13, 2.0), 0, 1.0)
    mix_into(s, lowpass(burst(sr, 0.35, rng, fc=260, q=0.6, tau=0.08, mode='low'), sr, 500), 0, 0.9)
    mix_into(s, staves(sr, rng, 0.2, 5, 0.0, 0.06, 0.3, 300, 700), 0)
    mix_into(s, gravel(sr, rng, 0.5, 14, 0.0, 0.3, 0.3), 0)
    for k, t in enumerate((0.12, 0.17, 0.24, 0.3)):
        mix_into(s, wood_tok(sr, rng, 900 - 70 * k, 0.04, 0.006, 0.6), sec(sr, t), 0.25 - 0.04 * k)
    dust = mul(svf(noise(sr, 0.6, rng), sr, 800, 0.7, 'low'), env_adsr(sr, 0.6, 0.04, 0.0, 1.0, 0.5))
    mix_into(s, dust, 0, 0.2)
    s = softclip(s, 1.7)
    return reverb(s, sr, size=1.0, decay=0.6, wet=0.2)


archive('boss1_cup_shatter', '61-2: 파훼 · 잔 깨짐은 boss1_break_cup(ui:boss-break{kind:cup})으로 대체, 시스템 연결 끊음')


# ===========================================================================
# 4. 칼 발도 — 소모한 검기 단수(kenkiStage)별 무게. katana_iai_release(0단) 대신 재생
#    색은 검기 단계음과 같다: 1 재(지글) · 2 호박(타오름) · 3 백열(빛남) · 4 불꽃 맺힘(명경) · 5 빛 고리 다섯(명경)
# ===========================================================================

def _iai_ki(sr, rng, st):
    dur = (0.62, 0.74, 0.88, 1.02, 1.2)[st - 1]
    s = zeros(sec(sr, dur))
    mix_into(s, snap(sr, rng, 5200, 0.01, 0.0015), 0, 0.8)                                # 코이구치 딸깍
    mix_into(s, wood_tok(sr, rng, 1500, 0.03, 0.004, 0.5), 0, 0.3)
    t = sec(sr, 0.03)
    mix_into(s, tear(sr, 0.18 + 0.03 * st, rng, 2300 - 150 * st, 9000, rate=95.0, q=1.8), t, 0.75)
    mix_into(s, slice_(sr, rng, 9000, 2600, 0.06 + 0.01 * st, q=1.2), t, 0.5)
    mix_into(s, whoosh(sr, 0.2 + 0.04 * st, rng, 1200 - 110 * st, 320 - 25 * st, q=0.8, a=0.15, r=0.6), t, 0.3 + 0.1 * st)
    mix_into(s, punch(sr, 175 - 12 * st, 72 - 6 * st, 0.2 + 0.06 * st, 0.04 + 0.015 * st, 1.4 + 0.15 * st), t, 0.45 + 0.12 * st)
    mix_into(s, sub(sr, 76 - 4 * st, 42 - 2 * st, 0.25 + 0.08 * st, 0.06 + 0.025 * st, 170), t, 0.2 + 0.14 * st)
    pr = lowpass(burst(sr, 0.1 + 0.04 * st, rng, fc=380, q=0.6, tau=0.02 + 0.012 * st, mode='low'), sr, 600)
    mix_into(s, pr, t, 0.3 + 0.12 * st)
    mix_into(s, glint(sr, rng, 3700 + 150 * st, 0.25, 0.05 + 0.008 * st), t + sec(sr, 0.015), 0.22)  # 짧은 쇳빛
    if st == 1:                                                                           # 재: 지글
        mix_into(s, sizzle(sr, rng, 0.32, fc=5200, tau=0.12), t + sec(sr, 0.05), 0.35)
        mix_into(s, crackle(sr, rng, 0.3, 6, 0.25), t + sec(sr, 0.05))
    if st >= 2:                                                                           # 호박: 타오름
        mix_into(s, thud(sr, 0.15, 95, 50, 0.04), t + sec(sr, 0.02), 0.4)
        mix_into(s, flame(sr, rng, 0.35 + 0.05 * st, 250, 2400 + 300 * st, a=0.02), t + sec(sr, 0.02), 0.45 + 0.05 * st)
        mix_into(s, crackle(sr, rng, 0.4, 6 + 3 * st, 0.28), t + sec(sr, 0.04))
    if st >= 3:                                                                           # 백열: 빛남
        ab = svf(noise(sr, 0.4, rng), sr, 7200, 0.8, 'band')
        mix_into(s, mul(ab, env_adsr(sr, 0.4, 0.004, 0.0, 1.0, 0.36)), t + sec(sr, 0.01), 0.28)
        mix_into(s, sparks(sr, rng, 0.4, 8 + 3 * st, 0.3), t + sec(sr, 0.02))
        mix_into(s, kick(sr, 0.5, 80 - 4 * st, 32, 0.12 + 0.02 * st, rng=rng), t, 0.3 + 0.12 * (st - 2))
    if st == 4:                                                                           # 명경 4: 불꽃 맺힘 맥동
        nh = sec(sr, 0.55)
        sh = add(svf(noise(sr, 0.55, rng), sr, 8200, 6.0, 'band'), svf(noise(sr, 0.55, rng), sr, 10500, 6.0, 'band'))
        sh = mul(sh, [0.45 + 0.55 * (0.5 + 0.5 * math.sin(TAU * 6.0 * i / sr)) for i in range(nh)])
        mix_into(s, mul(sh, env_adsr(sr, 0.55, 0.02, 0.0, 1.0, 0.45)), t + sec(sr, 0.08), 0.12)
    if st == 5:                                                                           # 명경 5: 빛 고리 다섯 + 화악
        for k in range(5):
            mix_into(s, glint(sr, rng, 4200 + 450 * k, 0.12, 0.03), t + sec(sr, 0.07 + 0.045 * k), 0.2)
        mix_into(s, flame(sr, rng, 0.35, 600, 5500, a=0.01), t + sec(sr, 0.3), 0.45)
        mix_into(s, sparks(sr, rng, 0.3, 12, 0.3, 5000, 11000), t + sec(sr, 0.3))
    s = softclip(s, 1.3 + 0.15 * st)
    return reverb(tail(s, sr, 0.03), sr, size=0.5 + 0.08 * st, decay=0.45 + 0.04 * st, wet=0.12 + 0.03 * st)


@sfx('katana_iai_ki1', 'PLAYER_SKILL{weapon:katana,move:iai,phase:release,kenkiStage:1}', "61-2 새 — 칼 발도 · 검기 1단 소모(재빛). 딸깍 → 30 ms 발도 찢김 + 날 '샥' + 몸통 '퍽'(163→66 Hz) + 짧은 쇳빛(3.9 kHz, 울림 없음) + 칼날에 남는 지글거림. katana_iai_release(0단) 대신 재생 — 단수가 오를수록 낮고 무겁고 길다", -1)
def _katana_iai_ki1(sr, rng):
    return _iai_ki(sr, rng, 1)


@sfx('katana_iai_ki2', 'PLAYER_SKILL{weapon:katana,move:iai,phase:release,kenkiStage:2}', "61-2 새 — 칼 발도 · 검기 2단 소모(호박빛). 1단 위에 불이 붙는 '훅' + 치솟는 불길 + 타닥, 몸통 151→60 Hz 로 더 깊게. katana_iai_release 대신", -0.5)
def _katana_iai_ki2(sr, rng):
    return _iai_ki(sr, rng, 2)


@sfx('katana_iai_ki3', 'PLAYER_SKILL{weapon:katana,move:iai,phase:release,kenkiStage:3}', "61-2 새 — 칼 발도 · 검기 3단 소모(백열 — 기본 상한). 2단 위에 번쩍 오르는 고역 공기 + 불똥 + 큰 북 같은 아래 무게(68→32 Hz), 몸통 139→54 Hz. katana_iai_release 대신", 0)
def _katana_iai_ki3(sr, rng):
    return _iai_ki(sr, rng, 3)


@sfx('katana_iai_ki4', 'PLAYER_SKILL{weapon:katana,move:iai,phase:release,kenkiStage:4}', "61-2 새 — 칼 발도 · 검기 4단 소모(명경 전용). 3단 위에 불꽃이 맺혀 6 Hz 로 맥동하는 고역 반짝임(8.2k·10.5k), 아래 무게 더 크게. katana_iai_release 대신", 0)
def _katana_iai_ki4(sr, rng):
    return _iai_ki(sr, rng, 4)


@sfx('katana_iai_ki5', 'PLAYER_SKILL{weapon:katana,move:iai,phase:release,kenkiStage:5}', "61-2 새 — 칼 발도 · 검기 5단 소모(명경 최대). 3단 위에 빛 고리 다섯(45 ms 간격, 점점 높게, 3 kHz 위·짧게) → 0.33 s 백열 '화악' + 불똥, 가장 낮고 무겁고 긴 무게와 울림. katana_iai_release 대신", 0)
def _katana_iai_ki5(sr, rng):
    return _iai_ki(sr, rng, 5)


# ===========================================================================
# 5. 가드 다듬기 (P1 4동사 확정: 우 = 가드 — 칼·대검. 대검은 떼면 밀쳐내기)
# ===========================================================================

@redo('guard_hold', "가드 유지 루프(61-2 다시 만듦 — 1.24 kHz 쇠 험 제거, 0.6 → 1.2 s). 낮게 버티는 압력(0.83 Hz 숨 쉬듯) + 손잡이 가죽이 이따금 삐걱(셋) + 아주 작은 날 떨림(4.5 kHz 위, 7.5 Hz). 우클릭 누르는 동안(칼·대검 공통, 그로기 중 가드도). 시작 120 ms 페이드인, 떼면 80 ms 페이드아웃", -10)
def _guard_hold61(sr, rng):
    dur = 1.2
    n = sec(sr, dur)
    pr = wrap2(lambda x: svf(x, sr, 170, 0.8, 'low'), noise_loop(sr, n, rng))
    s = mul(pr, lfo_loop(sr, n, 1 / dur, 0.3, 0.7))                                       # 숨 쉬듯 버팀
    lo = wrap2(lambda x: lowpass(x, sr, 120), tone_loop(sr, n, 58, 'saw'))
    mix_into(s, mul(lo, lfo_loop(sr, n, 2 / dur, 0.2, 0.8, 0.25)), 0, 0.35)
    for t in (0.17, 0.58, 0.93):                                                          # 가죽 삐걱
        c = creak(sr, rng, 0.09, 88, 104, (800, 1100), 26.0, 3.0)
        mix_into(s, c, sec(sr, t + rng.uniform(-0.02, 0.02)), 0.12, wrap=True)
    sh = wrap2(lambda x: svf(x, sr, 4800, 6.0, 'band'), noise_loop(sr, n, rng))
    mix_into(s, mul(sh, lfo_loop(sr, n, 7.5, 0.5, 0.5)), 0, 0.05)                         # 날 떨림
    return s


@redo('guard_push', "대검 가드 떼기 = 밀쳐내기(61-2 다시 만듦, 4동사 — 대검만, 퍼펙트 직후 떼기는 gs_guard_rush). 짧게 내뱉는 숨(노이즈) + 칼 넓은 면이 공기를 미는 '훅'(250→900→300 Hz) + 0.06 s 넓적한 '퍽'(120→50 Hz, 저역 압력) + 가죽·갑옷 덜그럭 + 0.18 s 디딤 + 흙 긁힘. 적에게 닿으면 hit_enemy 를 겹침",
      trigger='PLAYER_SECONDARY{kind:guard,phase:release,weapon:greatsword}')
def _guard_push61(sr, rng):
    dur = 0.5
    s = zeros(sec(sr, dur))
    mix_into(s, breath(sr, rng, 0.12, (620, 480), (1100, 950), 0.4, 0.004, 0.8, 0.8), 0, 0.35)
    nw = sec(sr, 0.28)
    k = int(nw * 0.4)
    fc = [250 * (900 / 250) ** (i / k) if i < k else 900 * (300 / 900) ** ((i - k) / (nw - k)) for i in range(nw)]
    air = svf(noise(sr, 0.28, rng), sr, fc, 0.9, 'band')
    mix_into(s, mul(air, env_adsr(sr, 0.28, 0.08, 0.0, 1.0, 0.16)), 0, 0.8)               # 넓은 면 '훅'
    mix_into(s, punch(sr, 120, 50, 0.25, 0.06, 1.6), sec(sr, 0.06), 0.8)                 # 넓적한 '퍽'
    mix_into(s, lowpass(burst(sr, 0.15, rng, fc=350, q=0.6, tau=0.035, mode='low'), sr, 500), sec(sr, 0.06), 0.7)
    mix_into(s, rustle(sr, rng, 0.14, 900, 40), 0, 0.3)
    mix_into(s, punch(sr, 110, 45, 0.12, 0.03, 1.2), sec(sr, 0.18), 0.45)               # 디딤
    mix_into(s, scuff(sr, rng, 0.14, 1200), sec(sr, 0.18), 0.3)
    return softclip(s, 1.5)


@sfx('guard_block_heavy', 'PLAYER_DAMAGED{guarded:true,weapon:greatsword}', "61-2 새 — 대검 일반 가드로 막음(넓은 칼 면을 방패처럼). guard_block(칼) 보다 무겁고 넓다: '딱' + 칼 면으로 받는 큰 충격(120→44 Hz) + 넓적한 저역 '훔' + 날 틱(2.6 kHz, 10 ms 감쇠) + 짧은 긁힘 + 0.05~0.25 s 뒤로 밀리는 발·흙. 대검이면 guard_block 대신", -1)
def _guard_block_heavy(sr, rng):
    dur = 0.5
    s = zeros(sec(sr, dur))
    mix_into(s, snap(sr, rng, 2200, 0.016, 0.0025), 0, 0.6)
    mix_into(s, punch(sr, 120, 44, 0.28, 0.07, 1.8), 0, 1.0)
    mix_into(s, lowpass(burst(sr, 0.18, rng, fc=300, q=0.6, tau=0.04, mode='low'), sr, 450), 0, 0.8)
    mix_into(s, metal(sr, 0.05, 2600, rng, tau=0.01, jitter=0.03), 0, 0.18)
    ng = sec(sr, 0.12)
    gr = svf(noise(sr, 0.12, rng), sr, 2800, 1.5, 'band')
    gr = mul(gr, [0.6 + 0.4 * math.sin(TAU * 70 * i / sr) for i in range(ng)])
    mix_into(s, mul(gr, env_adsr(sr, 0.12, 0.003, 0.0, 1.0, 0.1)), sec(sr, 0.004), 0.22)
    mix_into(s, sub(sr, 62, 36, 0.3, 0.08), 0, 0.6)
    mix_into(s, scuff(sr, rng, 0.2, 1100), sec(sr, 0.05), 0.4)
    mix_into(s, punch(sr, 100, 45, 0.1, 0.025, 1.2), sec(sr, 0.2), 0.3)
    return softclip(s, 1.7)


# ===========================================================================
# 6. 61라운드 단계 4 — 새 보스 내부 이벤트 BOSS_ACTION(introRoar·cupStruck·pillarCrack·flameSnuff) · 화살비 타이밍
#    (데모 버전 6 피드백 배분 '새 보스 동작 소리 → 음향'. 시스템 EventBus `BOSS_ACTION {id, action, index?}`.
#     트리거 표기는 이 파일의 보스 관례(`EVENT{boss:1,키:값}`) — 조건 키 action·index 는 payload 필드 그대로.)
#    **이 절 아래에만 새 효과음을 붙인다**(시드 = 1000 + 등록 순서 — 위 소리는 바이트 불변).
# ===========================================================================

ROUND4 = '61-4'   # listen_index 의 round 값(61라운드 단계 4)


def sfx4(name, trigger, note, gain_db=0.0, loop=False, category='combat'):
    """sfx() + round 표시(61-4)."""
    def deco(fn):
        sfx(name, trigger, note, gain_db, loop=loop, category=category)(fn)
        SFX[name]['round'] = ROUND4
        return fn
    return deco


def variant4(base, k, note):
    """sfx_core61.variant() + round 표시(61-4)."""
    from sfx_core61 import variant

    def deco(fn):
        variant(base, k, note)(fn)
        SFX['%s_v%d' % (base, k)]['round'] = ROUND4
        return fn
    return deco


# ---- 등장 포효 (BOSS_ACTION introRoar — 등장 연출 roarAtMs 3.8 s, 이름 카드 ui:boss-roar 와 같은 순간) ----------

@sfx4('boss1_intro_roar', 'BOSS_ACTION{boss:1,action:introRoar}', "61-4 새 — 만취 등장 포효(등장 연출의 포효 프레임 = 보스 이름 카드가 뜨는 순간, 등장 시작 3.8 s). boss1_entrance(0 s, 2.7 s — 탁자 '탁!'·걸음·'크아')와 겹치지 않고 그 뒤에 온다: 가슴을 부풀린 디딤 '쿵'(105→36 Hz) + 아래 무게 → 0.02~0.9 s 짧고 굵은 포효(노이즈 포먼트 'ㅇ워아' F1 380→760→480 Hz, 목소리 아님) + 31 Hz 로 긁는 거친 떨림 + 가슴 저역 + 48 Hz 낮은 으르렁 + 0.25 s 부터 커지는 4 Hz 취기 흔들림(혀 꼬인 끝 처짐) + 배 속 술 출렁 → 0.95 s 작은 딸꾹. 돌방 울림. 이름 카드와 함께 화면의 한 방(우선순위 4 — 다른 효과음 −6 dB·BGM −3 dB 덕킹)", 0, category='boss')
def _boss1_intro_roar(sr, rng):
    dur = 1.25
    s = zeros(sec(sr, dur))
    mix_into(s, punch(sr, 105, 36, 0.42, 0.1, 2.0), 0, 0.85)                              # 디딤 '쿵'
    mix_into(s, sub(sr, 60, 34, 0.5, 0.15), 0, 0.6)
    mix_into(s, lowpass(burst(sr, 0.25, rng, fc=280, q=0.6, tau=0.06, mode='low'), sr, 450), 0, 0.5)
    rd = 0.9
    n = sec(sr, rd)
    t0 = sec(sr, 0.02)
    f1, f2 = [], []
    for i in range(n):                                                                    # 'ㅇ워아' → 처짐
        t = i / sr
        if t < 0.18:
            u = t / 0.18
            a, b = 380 + 380 * u, 880 + 370 * u
        else:
            u = min(1.0, (t - 0.18) / 0.72)
            a, b = 760 - 280 * u, 1250 - 300 * u
        w = 1 + 0.07 * min(1.0, max(0.0, (t - 0.25) / 0.3)) * math.sin(TAU * 4.2 * t)      # 취기 흔들림
        f1.append(a * w)
        f2.append(b * w)
    src = noise(sr, rd, rng)
    v = [x * 0.6 + y * 0.32 + z * 0.1 for x, y, z in zip(svf(src, sr, f1, 4.5, 'band'), svf(src, sr, f2, 5.5, 'band'),
                                                           svf(src, sr, 2500, 4.0, 'band'))]
    growl = [0.45 + 0.55 * (0.5 + 0.5 * math.sin(TAU * 31 * i / sr + 1.3 * math.sin(TAU * 7 * i / sr))) for i in range(n)]
    jit = normalize(lowpass([rng.uniform(-1, 1) for _ in range(n)], sr, 40), 1.0)
    v = mul(mul(v, growl), [0.75 + 0.25 * j for j in jit])
    chest = mul(svf(noise(sr, rd, rng), sr, 210, 0.8, 'low'), growl)
    mix_into(v, chest, 0, 1.1)
    rum = lowpass(lowpass(tone_f(sr, [48 * (1 + 0.04 * math.sin(TAU * 4.2 * i / sr)) for i in range(n)], 'saw'), sr, 170), sr, 170)
    mix_into(v, mul(rum, growl), 0, 0.55)
    v = mul(v, env_adsr(sr, rd, 0.06, 0.1, 0.8, 0.38, curve=0.7))
    mix_into(s, softclip(v, 2.4), t0, 1.0)
    mix_into(s, slosh(sr, rng, 0.35, 320, 650), sec(sr, 0.1), 0.22)                      # 배 속 출렁
    hc = sec(sr, 0.95)                                                                    # 작은 딸꾹
    mix_into(s, burst(sr, 0.02, rng, fc=2400, q=1.0, tau=0.004), hc, 0.3)
    mix_into(s, breath(sr, rng, 0.07, (560, 480), (1050, 980), 0.4, 0.004, 1.0, 0.6, 0.05), hc, 0.3)
    s = softclip(s, 1.4)
    return reverb(s, sr, size=1.3, decay=0.72, wet=0.26)


# ---- 잔 맞힘 · 안 깨짐 (BOSS_ACTION cupStruck — 3국면은 2타째에 깨짐 → 그때는 ui:boss-break{kind:cup}) ---------

@sfx4('boss1_cup_struck', 'BOSS_ACTION{boss:1,action:cupStruck}', "61-4 새 — 약점 잔을 맞혔으나 아직 안 깨짐(3국면 1타째 등). 맞는 순간 짧은 '딱' + 잔 몸통 '톡' → 맑은 '팅'(2.95 kHz 종 배음, 0.11 s 감쇠 — 0.7~2 kHz 오래 남는 울림 없음) + 6 Hz 로 흔들리는 맥놀이(잔이 흔들림) + 짧은 술 출렁 + 물방울 몇. 깨질 때의 boss1_break_cup(둔탁한 '빡'·뒤집어씀)과 반대로 가볍고 맑다 = '금은 갔지만 아직'. 우선순위 3", -2, category='boss')
def _boss1_cup_struck(sr, rng):
    dur = 0.62
    s = zeros(sec(sr, dur))
    mix_into(s, snap(sr, rng, 3200, 0.012, 0.002), 0, 0.5)
    mix_into(s, wood_tok(sr, rng, 1500, 0.04, 0.005, 0.7), 0, 0.3)
    mix_into(s, punch(sr, 260, 140, 0.06, 0.015, 1.3), 0, 0.25)
    pt = [(1.0, 1.0), (2.01, 0.35), (2.76, 0.25), (4.07, 0.12)]
    mix_into(s, highpass(metal(sr, 0.5, 2950, rng, partials=pt, tau=0.11, jitter=0.002), sr, 2000), 0, 0.55)
    mix_into(s, highpass(metal(sr, 0.5, 2956, rng, partials=pt[:2], tau=0.13, jitter=0.0), sr, 2000), 0, 0.28)
    mix_into(s, slosh(sr, rng, 0.32, 500, 1000), sec(sr, 0.015), 0.45)
    mix_into(s, droplets(sr, rng, 0.4, 4, 0.05, 0.3, 700, 1500, 0.12), 0)
    return reverb(s, sr, size=0.6, decay=0.45, wet=0.12)


# ---- 기둥 균열 (BOSS_ACTION pillarCrack, index = 새 단 1~3 — 3단에서 멈춤, 무너지지 않음) ---------------------

def _pillar_crack(sr, rng, st):
    """돌기둥에 금이 감: 단이 오를수록 길고 낮고 깊다. 돌진 충돌(ui:boss-break{kind:pillar} 의 큰 '쿵')과 같은 프레임에
    겹칠 수 있으므로 몸통은 가볍게 두고 '돌이 갈라지는' 결(중고역 지직·쩌억·부스러기)에 무게를 둔다."""
    dur = (0.5, 0.75, 1.05)[st - 1]
    s = zeros(sec(sr, dur))
    mix_into(s, snap(sr, rng, 2600, 0.014, 0.0025), 0, 0.8)                               # 'ㅉ'
    mix_into(s, crunch(burst(sr, 0.05 + 0.02 * st, rng, fc=1400 - 250 * st, q=0.8, tau=0.012 + 0.006 * st), 5 + 2 * st), 0, 0.8)
    spread = 0.1 + 0.12 * st                                                              # 번지는 잔금
    times = sorted(rng.uniform(0.02, 0.02 + spread) for _ in range(4 + 5 * st))
    for k, t in enumerate(times):
        u = k / max(1, len(times) - 1)
        fc = 3200 * (1 - u) + (1100 - 150 * st) * u
        c = crunch(burst(sr, 0.014, rng, fc=fc, q=0.9, tau=rng.uniform(0.002, 0.005)), 3)
        mix_into(s, c, sec(sr, t), (0.55 - 0.25 * u) * rng.uniform(0.6, 1.0))
    mix_into(s, punch(sr, 190 - 35 * st, 80 - 12 * st, 0.12 + 0.06 * st, 0.03 + 0.015 * st, 1.6), 0, 0.3 + 0.12 * st)
    if st >= 2:                                                                           # '쩌억'
        mix_into(s, tear(sr, 0.18 * st, rng, 900, 350, rate=38.0, q=1.2), sec(sr, 0.04), 0.3 + 0.08 * st)
    if st >= 3:                                                                           # 깊은 돌 신음
        gn = sec(sr, 0.45)
        gr = svf(tone(sr, 0.45, 70, 48, kind='saw'), sr, sweep(sr, gn, 260, 160), 2.0, 'band')
        mix_into(s, mul(gr, env_adsr(sr, 0.45, 0.12, 0.0, 1.0, 0.3)), sec(sr, 0.08), 0.45)
        mix_into(s, sub(sr, 64, 34, 0.5, 0.15), sec(sr, 0.03), 0.5)
    mix_into(s, gravel(sr, rng, dur, 3 + 5 * st, 0.05, 0.25 + 0.2 * st, 0.18 + 0.04 * st), 0)  # 부스러기
    if st >= 2:
        dust = mul(svf(noise(sr, 0.3 * st, rng), sr, 900, 0.7, 'low'), env_adsr(sr, 0.3 * st, 0.04, 0.0, 1.0, 0.25 * st))
        mix_into(s, dust, sec(sr, 0.05), 0.1 * st)
    s = softclip(s, 1.5)
    return reverb(s, sr, size=0.9 + 0.15 * st, decay=0.55 + 0.05 * st, wet=0.15 + 0.03 * st)


@sfx4('boss1_pillar_crack1', 'BOSS_ACTION{boss:1,action:pillarCrack,index:1}', "61-4 새 — 기둥 균열 1단(가는 금). 돌이 '짝' 갈라지는 짧은 소리 + 위로 번지는 잔금 지직 9(고역 → 중역) + 가벼운 돌 몸통(155→68 Hz) + 부스러기 몇. 0.5 s. 돌진 충돌의 ui:boss-break{kind:pillar} 와 같은 프레임에 겹쳐도 되게 몸통은 가볍다", -3, category='boss')
def _boss1_pillar_crack1(sr, rng):
    return _pillar_crack(sr, rng, 1)


@sfx4('boss1_pillar_crack2', 'BOSS_ACTION{boss:1,action:pillarCrack,index:2}', "61-4 새 — 기둥 균열 2단(벌어짐). 1단보다 낮고 길게: '짝' + 잔금 14 + 0.04 s 부터 '쩌억' 찢기는 돌(900→350 Hz, 38 Hz 거친 떨림) + 돌 몸통(120→56 Hz) + 부스러기·먼지. 0.75 s", -2, category='boss')
def _boss1_pillar_crack2(sr, rng):
    return _pillar_crack(sr, rng, 2)


@sfx4('boss1_pillar_crack3', 'BOSS_ACTION{boss:1,action:pillarCrack,index:3}', "61-4 새 — 기둥 균열 3단(깊은 금 — 여기서 멈춤, 무너지지 않음). 2단 위에 기둥 속에서 울리는 깊은 돌 신음(70→48 Hz 톱니, 260→160 Hz 대역) + 아래 무게(64→34 Hz) + 더 많은 부스러기·먼지, '쩌억' 더 길게. 1.05 s", -1, category='boss')
def _boss1_pillar_crack3(sr, rng):
    return _pillar_crack(sr, rng, 3)


# ---- 촛불 하나 꺼짐 (BOSS_ACTION flameSnuff — 처치 연출 snuffAtMs 부터 먼 촛대 순으로 60·90·75 ms 간격) ----------

def _snuff(sr, rng, fc=1000, puff=0.07):
    """불꽃 하나가 '훅' 꺼짐 + 가는 연기. 여러 개가 60~90 ms 간격으로 겹치므로 머리는 짧고 또렷하게, 꼬리(연기)는 아주
    작게, 울림 거의 없음 — 겹쳐도 '훅·훅·훅' 이 하나씩 들리게."""
    dur = 0.34
    s = zeros(sec(sr, dur))
    m = sec(sr, puff)
    pf = svf(noise(sr, puff, rng), sr, sweep(sr, m, fc * 1.3, fc * 0.45), 0.9, 'band')
    mix_into(s, mul(pf, env_adsr(sr, puff, 0.004, 0.0, 1.0, puff * 0.85)), 0, 1.0)    # '훅'
    mix_into(s, thud(sr, 0.04, 160, 90, 0.012), 0, 0.15)                                 # 공기가 꺼지는 작은 몸통
    mix_into(s, crackle(sr, rng, 0.08, 2, 0.12), sec(sr, 0.01))                            # 심지 마지막 지직
    sm = svf(noise(sr, 0.28, rng), sr, 2200, 0.5, 'band')                                  # 연기
    am = normalize(lowpass([rng.uniform(0, 1) for _ in range(len(sm))], sr, 18), 1.0)
    sm = mul(mul(sm, [0.5 + 0.5 * a for a in am]), env_adsr(sr, 0.28, 0.03, 0.0, 1.0, 0.24))
    mix_into(s, sm, sec(sr, 0.03), 0.13)
    return reverb(s, sr, size=0.4, decay=0.35, wet=0.06)


@sfx4('boss1_flame_snuff', 'BOSS_ACTION{boss:1,action:flameSnuff}', "61-4 새 — 촛불 하나 꺼짐(보스 처치 연출: snuffAtMs 2.3 s 부터 방 촛대를 먼 순서로 60·90·75 ms 간격, fx boss1_flame_snuff 와 함께). 아주 짧은 '훅'(1.3k→450 Hz, 70 ms) + 작은 몸통 + 심지 지직 + 가는 연기 쉿(2.2 kHz, 0.28 s, 아주 작게). 울림 거의 없음 — 여러 개가 겹쳐도 하나씩 들리게. 변주 v2·v3 를 번갈아(직전과 다른 것) + 재생 속도 ±3 %. 같은 그룹 동시 4개", -7, category='boss')
def _boss1_flame_snuff(sr, rng):
    return _snuff(sr, rng, 1000, 0.07)


@variant4('boss1_flame_snuff', 2, "촛불 꺼짐 변주 2 — '훅' 조금 낮고 짧게(850 Hz, 60 ms)")
def _boss1_flame_snuff_v2(sr, rng):
    return _snuff(sr, rng, 850, 0.06)


@variant4('boss1_flame_snuff', 3, "촛불 꺼짐 변주 3 — '훅' 조금 높고 길게(1.18 kHz, 80 ms)")
def _boss1_flame_snuff_v3(sr, rng):
    return _snuff(sr, rng, 1180, 0.08)


# ---- 화살비 타이밍 맞춤 (서서 시작 판 arrow_rain_stand: releasesAtMs [240,360,480], 전체 770 ms,
#      firstDropAtMs 690 + 낙하 판정 프레임 120 ms = 첫 꽂힘 810 ms, 낙하 9곳 × 40 ms) ----------------------------
#  시스템: launch = releasesAtMs[0](240 ms)에 1회, impact = 첫 꽂힘 − 100 ms(710 ms)에 1회.

@redo('arrow_rain_launch', "화살비 발사(61-4 다시 만듦 — 서서 시작 판 발사 시각 240·360·480 ms 에 맞춤). 파일 0 = 첫 발사(launch 이벤트 = releasesAtMs[0]). 시위 세 번 0 / 0.12 / 0.24 s(옛 0/0.06/0.12 s 는 발사 간격 120 ms 와 어긋남) + 발마다 하늘로 솟는 짧은 바람 → 0.25~0.47 s 멀어지는 바람(낙하 휘파람이 시작하는 0.47 s = 710 ms 전에 사라짐)", round_=ROUND4)
def _arrow_rain_launch61(sr, rng):
    dur = 0.5
    s = zeros(sec(sr, dur))
    for k, t0 in enumerate((0.0, 0.12, 0.24)):
        p = mul(pluck(sr, 0.2, 170 + 15 * k, rng, damp=0.985, bright=0.7), env_exp(sr, 0.2, 0.06))
        mix_into(s, p, sec(sr, t0), 0.8)
        mix_into(s, thud(sr, 0.06, 210, 120, 0.015), sec(sr, t0), 0.4)
        mix_into(s, whoosh(sr, 0.16, rng, 2500, 6500, q=1.2, a=0.2, r=0.6), sec(sr, t0 + 0.01), 0.25)
    up = whoosh(sr, 0.22, rng, 3000, 7500, q=1.4, a=0.15, r=0.8)
    mix_into(s, lowpass(up, sr, sweep(sr, len(up), 9000, 2500)), sec(sr, 0.25), 0.3)  # 멀어짐
    return tail(s, sr, 0.03)


@redo('arrow_rain_impact', "화살비 낙하(61-4 다시 만듦 — 낙하 9곳 × 40 ms 에 맞춤). 파일 0 = 첫 꽂힘 100 ms 전(impact 이벤트). 0~0.1 s 내려꽂히는 휘파람 + 비 쏟아지는 쉿(0.4 s) → 흙에 꽂히는 '툭' 아홉(0.10 + 0.04 s × k, ±4 ms, 점점 작게 — 옛 셋 0.1/0.16/0.23 s 는 마지막 낙하 0.42 s 까지 못 감) + 화살대 떨림 + 흙 튐", round_=ROUND4)
def _arrow_rain_impact61(sr, rng):
    dur = 0.6
    s = zeros(sec(sr, dur))
    wh = mul(tone(sr, 0.1, 2600, 1500), env_adsr(sr, 0.1, 0.06, 0.0, 1.0, 0.02))
    mix_into(s, wh, 0, 0.06)                                                              # 내려오는 휘파람
    mix_into(s, whoosh(sr, 0.11, rng, 5000, 2200, q=1.4, a=0.6, r=0.2), 0, 0.3)
    mix_into(s, whoosh(sr, 0.4, rng, 4200, 2600, q=0.9, a=0.15, r=0.5), sec(sr, 0.06), 0.1)  # 이어 떨어지는 쉿
    for k in range(9):
        t0 = 0.10 + 0.04 * k + (rng.uniform(-0.004, 0.004) if k else 0.0)
        mix_into(s, arrow_thunk(sr, rng), sec(sr, t0), (0.9 - 0.05 * k) * rng.uniform(0.7, 1.0))
    mix_into(s, gravel(sr, rng, 0.6, 9, 0.1, 0.5, 0.18), 0)
    return tail(s, sr, 0.03)
