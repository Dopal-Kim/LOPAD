# -*- coding: utf-8 -*-
"""
61라운드 P11 — 핵심 효과음 20종 품질 패스 + 반복 피로를 줄이는 변주.

build.py 가 sfx_passive 다음(마지막)에 import 한다.

1) 다시 만든 18종(같은 키): `redo()` 로 SFX 표의 같은 키에 함수만 바꿔 끼운다. 파이썬 dict 는 이미 있는 키에
   값을 다시 넣어도 순서가 그대로라 **시드(1000 + 등록 순서)가 바뀌지 않는다** — 다른 소리는 바이트 불변.
   옛 함수(build.py)는 지우지 않는다: `_hit_enemy` 처럼 다른 소리(hit_enemy_crit 옛판 등)가 재료로 부를 수 있고,
   되돌리기도 쉽다.
2) 새 키 2종: `guard_block`(일반 가드로 막음), `combo_finish`(연격 마무리 타격 위에 겹치는 무게).
3) 변주: `<키>_v2`·`_v3`. 같은 합성 뼈대에 매개변수(음높이·대역·타이밍)를 조금씩 달리하고 시드가 달라 노이즈 결도
   다르다. manifest 에서 변주 항목은 trigger = null + `variantOf`, 원본 항목은 `variants`(원본 포함 목록)를 가진다 —
   시스템은 원본 트리거가 오면 목록에서 직전과 다른 하나를 골라 재생한다.

방향(60라운드 Q22 '프라이팬 같다' 피드백 기준):
- 오래 남는 중역(0.7~2 kHz) 비조화 금속 울림을 빼고, 무게는 **피치가 떨어지는 몸통(punch) + 저역**으로,
  날카로움은 **아주 짧은 넓은 대역 순간음(snap) + 날이 지나가는 고역 노이즈(slice)** 로 만든다.
- 금속성이 꼭 필요한 소리(패링·퍼펙트 가드·동전)도 울림을 3 kHz 위로 올리고 감쇠를 0.1 s 안쪽으로 줄인다.
- 짧은 소리는 softclip 으로 밀도를 올려 같은 피크(-6 dBFS)에서 더 크게 들리게 한다.
"""
from build import *  # noqa: F401,F403
from build import SFX, GLASS, gravel, slosh, crackle, sizzle  # noqa: F401

VARIANTS = {}   # 원본 키 → [원본, v2, v3 ...]


def redo(name, note, gain_db=None):
    """이미 등록된 키의 합성 함수·설명을 바꾼다(등록 순서·시드·트리거 유지)."""
    old = SFX[name]

    def deco(fn):
        spec = dict(old)
        spec.update(fn=fn, note=note, redone='61')
        if gain_db is not None:
            spec['gain_db'] = gain_db
        SFX[name] = spec
        return fn
    return deco


def variant(base, k, note):
    """`<base>_v<k>` 변주 등록: 트리거 없음(원본 트리거에서 골라 씀), 음량·분류는 원본과 같다."""
    name = '%s_v%d' % (base, k)
    b = SFX[base]

    def deco(fn):
        sfx(name, None, note, b['gain_db'], category=b['category'])(fn)
        SFX[name]['variant_of'] = base
        VARIANTS.setdefault(base, [base]).append(name)
        return fn
    return deco


# ---------------------------------------------------------------------------
# 재료
# ---------------------------------------------------------------------------

def snap(sr, rng, fc=3500, dur=0.015, tau=0.0025):
    """맞는 순간의 넓은 대역 '딱': 고역통과 노이즈 + 아주 빠른 감쇠(울림 없음)."""
    s = svf(noise(sr, dur, rng), sr, fc, 0.6, 'high')
    return mul(s, env_exp(sr, dur, tau))


def punch(sr, f0, f1, dur, tau, drive=1.4, glide=0.022):
    """몸통 '퍽': 처음 수십 ms 에 f0 → f1 로 급히 떨어지는 사인 + 지수 감쇠 + 살짝 포화."""
    n = sec(sr, dur)
    out = zeros(n)
    p = 0.0
    for i in range(n):
        f = f1 + (f0 - f1) * math.exp(-i / (glide * sr))
        out[i] = math.sin(TAU * p)
        p += f / sr
    out = mul(out, env_exp(sr, dur, tau))
    if drive > 1.0:
        k = 1.0 / math.tanh(drive)
        out = [math.tanh(x * drive) * k for x in out]
    return out


def flesh(sr, rng, fc=650, dur=0.08, tau=0.018, q=0.9):
    """살·천이 눌리는 '퍽'의 노이즈 성분."""
    return burst(sr, dur, rng, fc=fc, q=q, tau=tau, mode='band')


def slice_(sr, rng, f0, f1, dur, q=1.3, a=0.08):
    """날이 지나가는 '샥': 고역 밴드 노이즈 스윕(빠른 어택, 지수에 가까운 꼬리)."""
    n = sec(sr, dur)
    s = svf(noise(sr, dur, rng), sr, sweep(sr, n, f0, f1), q, 'band')
    return mul(s, env_adsr(sr, dur, dur * a, 0.0, 1.0, dur * (1 - a), curve=1.0))


def crunch(seg, hold):
    """샘플 홀드로 거칠게(뼈가 으스러지는 결). hold 샘플마다 값을 붙잡는다."""
    return [seg[i - i % hold] for i in range(len(seg))]


def rustle(sr, rng, dur, fc=1600, rate=35.0, q=0.8):
    """천·가죽 바스락: 밴드 노이즈를 무작위로 떨리는 진폭으로."""
    n = sec(sr, dur)
    s = svf(noise(sr, dur, rng), sr, fc, q, 'band')
    am = lowpass([rng.uniform(0, 1) ** 2 for _ in range(n)], sr, rate)
    am = normalize(am, 1.0)
    return mul(mul(s, am), env_adsr(sr, dur, dur * 0.15, 0.0, 1.0, dur * 0.6))


def sub(sr, f0, f1, dur, tau, fc=180):
    """아래 무게: 아주 낮은 punch 를 저역통과."""
    return lowpass(punch(sr, f0, f1, dur, tau, 1.2, 0.03), sr, fc)


def glint(sr, rng, f, dur, tau, partials=None):
    """짧은 고역 쇳빛(3 kHz 위, 0.1 s 안쪽 감쇠) — 울림이 남지 않게 고역통과."""
    if partials is None:
        partials = [(1.0, 1.0), (1.41, 0.55), (1.93, 0.4), (2.63, 0.22)]
    s = metal(sr, dur, f, rng, partials=partials, tau=tau, jitter=0.015)
    return highpass(s, sr, 2400)


def sparks(sr, rng, dur, count, g=0.3, lo=4500, hi=10000):
    """불똥: 아주 짧은 고역 딸깍을 흩뿌린다."""
    s = zeros(sec(sr, dur))
    for _ in range(count):
        c = burst(sr, 0.006, rng, fc=rng.uniform(lo, hi), q=0.7, tau=rng.uniform(0.0008, 0.0022))
        mix_into(s, c, sec(sr, rng.uniform(0, dur * 0.85)), g * rng.uniform(0.3, 1.0))
    return s


def wood_tok(sr, rng, f=1100, dur=0.05, tau=0.008, g_noise=0.6):
    """나무 '톡': 공진 대역 노이즈 + 짧은 사인 하강."""
    s = mul(svf(noise(sr, dur, rng), sr, f * 1.9, 4.0, 'band'), env_exp(sr, dur, tau * 0.8))
    s = scale(s, g_noise)
    mix_into(s, mul(tone(sr, dur, f, f * 0.82), env_exp(sr, dur, tau)), 0, 1.0)
    return s


# ---------------------------------------------------------------------------
# 1. 적 피격 · 치명 · 처치
# ---------------------------------------------------------------------------

def _hit(sr, rng, body=(230, 85), fl=700, sl=(7000, 2600), wet=0.25, dur=0.2, crack=2600):
    # 노트북 스피커에서도 들리게 무게를 60 Hz 가 아니라 85~250 Hz 몸통과 300 Hz '퍽'에 싣는다
    s = zeros(sec(sr, dur))
    mix_into(s, snap(sr, rng, crack, 0.012, 0.002), 0, 0.9)                        # 맞는 순간 '딱'
    mix_into(s, slice_(sr, rng, sl[0], sl[1], 0.045), 0, 0.42)                       # 날이 지나가는 '샥'
    mix_into(s, punch(sr, body[0], body[1], 0.15, 0.04, 1.6), 0, 1.0)               # 몸통 '퍽'
    mix_into(s, flesh(sr, rng, fl, 0.07, 0.016, 0.9), sec(sr, 0.002), 0.8)           # 살·천
    mix_into(s, flesh(sr, rng, 300, 0.06, 0.02, 0.8), 0, 0.6)                        # 낮은 '퍽'
    mix_into(s, sub(sr, 72, 48, 0.14, 0.045), 0, 0.3)                                # 아래 무게
    w = mul(svf(noise(sr, 0.07, rng), sr, 1300, 1.2, 'band'), env_exp(sr, 0.07, 0.016))
    mix_into(s, w, sec(sr, 0.012), wet)                                              # 젖은 꼬리
    return softclip(s, 2.0)


@redo('hit_enemy', '적 피격(61라운드 품질 패스). 짧은 넓은 대역 \'딱\' + 날이 지나가는 고역 \'샥\' + 피치가 떨어지는 몸통 \'퍽\'(230→85 Hz) + 살·천 노이즈 + 낮은 무게 + 젖은 꼬리. 금속 울림 없음. 변주 v2·v3 와 번갈아. 권장 음량 0 → -3 dB(같은 피크에서 짧은 구간 음량이 약 +7 dB 커져 일부만 되돌림)', -3)
def _hit_enemy61(sr, rng):
    return _hit(sr, rng)


@variant('hit_enemy', 2, '적 피격 변주 2 — 몸통을 조금 낮게(205→76 Hz), 살 대역 600 Hz, 날 6.2k→2.3k')
def _hit_enemy_v2(sr, rng):
    return _hit(sr, rng, body=(205, 76), fl=600, sl=(6200, 2300), wet=0.3, crack=2400)


@variant('hit_enemy', 3, '적 피격 변주 3 — 몸통을 조금 높게(255→94 Hz), 살 대역 780 Hz, 날 7.8k→2.9k, 꼬리 짧게')
def _hit_enemy_v3(sr, rng):
    return _hit(sr, rng, body=(255, 94), fl=780, sl=(7800, 2900), wet=0.2, crack=2900, dur=0.18)


def _crit(sr, rng, body=(200, 62), sl=(10000, 3500), crack_gap=0.011, hold=6):
    dur = 0.36
    s = zeros(sec(sr, dur))
    mix_into(s, snap(sr, rng, 2600, 0.014, 0.0022), 0, 0.85)                        # 뼈가 꺾이는 겹 '딱-딱'
    mix_into(s, snap(sr, rng, 1800, 0.014, 0.003), sec(sr, crack_gap), 0.6)
    mix_into(s, slice_(sr, rng, sl[0], sl[1], 0.06, q=1.0), 0, 0.5)                  # 더 밝게 베는 '샤악'
    mix_into(s, punch(sr, body[0], body[1], 0.24, 0.07, 1.8), 0, 1.0)               # 깊은 몸통
    fl = flesh(sr, rng, 560, 0.09, 0.022, 0.8)
    mix_into(s, crunch(fl, hold), sec(sr, 0.003), 0.7)                               # 으스러지는 결
    mix_into(s, flesh(sr, rng, 280, 0.08, 0.025, 0.8), 0, 0.6)                       # 낮은 '퍽'
    mix_into(s, sub(sr, 64, 42, 0.3, 0.09, 160), 0, 0.5)                             # 아래로 '쿵'
    air = svf(noise(sr, 0.16, rng), sr, 6500, 0.7, 'high')
    mix_into(s, mul(air, env_adsr(sr, 0.16, 0.004, 0.0, 1.0, 0.15)), sec(sr, 0.004), 0.16)  # 번쩍(울림 아닌 공기)
    s = softclip(s, 2.0)
    return reverb(s, sr, size=0.4, decay=0.4, wet=0.1)


@redo('hit_enemy_crit', "급소 적중(61라운드 품질 패스 — 강철 울림 제거). 겹으로 꺾이는 '딱-딱' + 밝게 베는 '샤악' + 깊은 몸통(200→62 Hz) + 으스러지는 살 결(샘플 홀드) + 아래로 떨어지는 '쿵' + 번쩍이는 고역 공기. 작은 방 울림")
def _hit_enemy_crit61(sr, rng):
    return _crit(sr, rng)


@variant('hit_enemy_crit', 2, '급소 적중 변주 2 — 몸통 185→56 Hz, 겹 간격 14 ms, 날 9k→3.2k')
def _hit_enemy_crit_v2(sr, rng):
    return _crit(sr, rng, body=(185, 56), sl=(9000, 3200), crack_gap=0.014, hold=7)


def _death(sr, rng, fall=0.13, bounce=0.27, body=(110, 38), clacks=(0.14, 0.17, 0.22)):
    dur = 0.68
    s = zeros(sec(sr, dur))
    mix_into(s, snap(sr, rng, 2400, 0.012, 0.002), 0, 0.5)
    mix_into(s, punch(sr, 160, 52, 0.12, 0.035, 1.4), 0, 0.6)                        # 마지막 타격의 몸통
    nb = sec(sr, 0.2)
    br = svf(noise(sr, 0.2, rng), sr, sweep(sr, nb, 900, 420), 1.4, 'band')
    mix_into(s, mul(br, env_adsr(sr, 0.2, 0.02, 0.0, 1.0, 0.16)), sec(sr, 0.03), 0.22)  # 숨이 빠짐(노이즈)
    t = sec(sr, fall)
    mix_into(s, punch(sr, body[0], body[1], 0.28, 0.075, 1.6), t, 1.0)              # 몸이 땅에 '쿵'
    mix_into(s, burst(sr, 0.12, rng, fc=380, q=0.6, tau=0.035, mode='low'), t, 0.7)
    mix_into(s, gravel(sr, rng, 0.25, 6, 0.0, 0.18, 0.25), t)                         # 흙·자갈
    for k, tc in enumerate(clacks):                                                    # 장비(나무 자루·가죽) 덜그럭
        mix_into(s, wood_tok(sr, rng, 520 + 140 * k, 0.05, 0.007, 0.8), sec(sr, tc), 0.32 - 0.06 * k)
    mix_into(s, punch(sr, 90, 40, 0.13, 0.03, 1.2), sec(sr, bounce), 0.38)           # 한 번 튐
    dust = svf(noise(sr, 0.35, rng), sr, 600, 0.7, 'low')
    mix_into(s, mul(dust, env_adsr(sr, 0.35, 0.03, 0.0, 1.0, 0.3)), t, 0.18)         # 먼지
    return softclip(s, 1.5)


@redo('enemy_death', "일반 적 처치(61라운드 품질 패스). 마지막 타격 몸통 → 숨이 빠지는 노이즈(목소리 아님) → 0.13 s 몸이 땅에 '쿵' + 흙·자갈 + 장비 덜그럭(나무·가죽) → 한 번 튐 + 먼지. 변주 v2·v3")
def _enemy_death61(sr, rng):
    return _death(sr, rng)


@variant('enemy_death', 2, '처치 변주 2 — 쓰러짐 0.16 s·튐 0.31 s, 몸통 100→36 Hz, 덜그럭 둘')
def _enemy_death_v2(sr, rng):
    return _death(sr, rng, fall=0.16, bounce=0.31, body=(100, 36), clacks=(0.17, 0.235))


@variant('enemy_death', 3, '처치 변주 3 — 쓰러짐 0.11 s·튐 0.24 s, 몸통 120→42 Hz, 덜그럭 셋(빠르게)')
def _enemy_death_v3(sr, rng):
    return _death(sr, rng, fall=0.11, bounce=0.24, body=(120, 42), clacks=(0.12, 0.14, 0.18))


# ---------------------------------------------------------------------------
# 2. 주인공 피격 · 대쉬
# ---------------------------------------------------------------------------

def _player_hit(sr, rng, body=(150, 58), fl=550, recoil=0.11):
    dur = 0.42
    s = zeros(sec(sr, dur))
    mix_into(s, snap(sr, rng, 2000, 0.014, 0.0028), 0, 0.5)                          # 둔한 '딱'
    mix_into(s, punch(sr, body[0], body[1], 0.3, 0.07, 1.8), 0, 1.0)                # 몸에 꽂히는 충격
    mix_into(s, flesh(sr, rng, fl, 0.08, 0.02, 0.8), 0, 0.9)                         # 가죽·천 '퍽'
    mix_into(s, burst(sr, 0.08, rng, fc=900, q=0.6, tau=0.025, mode='low'), 0, 0.5)
    mix_into(s, flesh(sr, rng, 260, 0.09, 0.028, 0.8), 0, 0.7)                       # 몸통 '퍽'(작은 스피커용)
    mix_into(s, sub(sr, 58, 38, 0.28, 0.08, 160), 0, 0.45)                           # 뼈에 울리는 저음
    nb = sec(sr, 0.18)
    br = svf(noise(sr, 0.18, rng), sr, sweep(sr, nb, 900, 450), 1.0, 'band')
    mix_into(s, mul(br, env_adsr(sr, 0.18, 0.01, 0.0, 1.0, 0.14)), sec(sr, 0.02), 0.28)  # 숨 밀림
    nm = sec(sr, 0.26)
    mf = svf(noise(sr, 0.26, rng), sr, sweep(sr, nm, 3200, 260), 0.7, 'low')
    mix_into(s, mul(mf, env_exp(sr, 0.26, 0.06)), 0, 0.3)                            # 귀가 먹먹해지는 하강
    mix_into(s, punch(sr, 82, 40, 0.13, 0.03, 1.2), sec(sr, recoil), 0.35)          # 몸이 밀려 디딤
    return softclip(s, 1.9)


@redo('hit_player', "주인공 피격(60 Q22 재제작 → 61라운드 품질 패스, 금속 울림 없음). 둔한 '딱' + 몸에 꽂히는 충격(150→58 Hz) + 가죽·천 '퍽' + 뼈에 울리는 저음 + 숨 밀림(노이즈) + 귀가 먹먹해지는 고역 하강 + 0.11 s 밀려 디딤. 적 피격보다 낮고 둔해 구별된다. 변주 v2·v3")
def _hit_player61(sr, rng):
    return _player_hit(sr, rng)


@variant('hit_player', 2, '주인공 피격 변주 2 — 몸통 138→54 Hz, 살 500 Hz, 밀림 0.13 s')
def _hit_player_v2(sr, rng):
    return _player_hit(sr, rng, body=(138, 54), fl=500, recoil=0.13)


@variant('hit_player', 3, '주인공 피격 변주 3 — 몸통 165→62 Hz, 살 610 Hz, 밀림 0.095 s')
def _hit_player_v3(sr, rng):
    return _player_hit(sr, rng, body=(165, 62), fl=610, recoil=0.095)


def _dash_core(sr, rng, air=(450, 1700), flutter=30.0, tip=(2500, 4500), land=0.2):
    dur = 0.27
    s = zeros(sec(sr, dur))
    mix_into(s, punch(sr, 140, 70, 0.06, 0.012, 1.2), 0, 0.5)                        # 박차는 발
    mix_into(s, lowpass(burst(sr, 0.05, rng, fc=1800, q=0.6, tau=0.01), sr, 3000), 0, 0.45)  # 흙 긁힘
    mix_into(s, whoosh(sr, 0.22, rng, air[0], air[1], q=0.8, a=0.25, r=0.6), 0, 0.85)  # 몸이 가르는 바람
    mix_into(s, rustle(sr, rng, 0.18, 1400, flutter), sec(sr, 0.02), 0.35)           # 옷자락
    tp = lowpass(whoosh(sr, 0.12, rng, tip[0], tip[1], q=1.0, a=0.3, r=0.6), sr, 6000)
    mix_into(s, tp, sec(sr, 0.04), 0.2)
    mix_into(s, thud(sr, 0.05, 180, 110, 0.01), sec(sr, land), 0.25)                 # 착지 톡
    return s


@redo('dash', '대쉬(61라운드 품질 패스, 60 Q22 음량 -5 dB 유지). 박차는 발 + 흙 긁힘 + 몸이 가르는 부드러운 바람(450→1.7k) + 옷자락 펄럭 + 끝 착지 톡. 날카로운 고역을 줄여 자주 들어도 덜 거슬리게. 변주 v2·v3. 권장 음량 -5 → -3 dB: 파일 자체가 고역을 줄여 약 3 dB 작아졌으므로, 합쳐서 60 Q22 판(-5 dB)보다 약 1 dB 작다', -3)
def _dash61(sr, rng):
    return _dash_core(sr, rng)


@variant('dash', 2, '대쉬 변주 2 — 바람 400→1.5k, 펄럭 24 Hz, 착지 0.21 s')
def _dash_v2(sr, rng):
    return _dash_core(sr, rng, air=(400, 1500), flutter=24.0, tip=(2300, 4000), land=0.21)


@variant('dash', 3, '대쉬 변주 3 — 바람 520→1.9k, 펄럭 38 Hz, 착지 0.19 s')
def _dash_v3(sr, rng):
    return _dash_core(sr, rng, air=(520, 1900), flutter=38.0, tip=(2700, 4900), land=0.19)


# ---------------------------------------------------------------------------
# 3. 가드 · 퍼펙트 가드 · 패링
# ---------------------------------------------------------------------------

def _block(sr, rng, body=(150, 55), steel=2300, grind=3600):
    dur = 0.4
    s = zeros(sec(sr, dur))
    mix_into(s, snap(sr, rng, 2600, 0.014, 0.0022), 0, 0.6)
    mix_into(s, punch(sr, body[0], body[1], 0.2, 0.04, 1.6), 0, 0.9)                 # 팔로 받아내는 충격
    mix_into(s, metal(sr, 0.06, steel, rng, tau=0.012, jitter=0.03), 0, 0.22)         # 날에 닿는 '틱'(울림 없음)
    ng = sec(sr, 0.09)
    gr = svf(noise(sr, 0.09, rng), sr, grind, 1.5, 'band')
    gr = mul(gr, [0.6 + 0.4 * math.sin(TAU * 90 * i / sr) for i in range(ng)])
    mix_into(s, mul(gr, env_adsr(sr, 0.09, 0.003, 0.0, 1.0, 0.08)), sec(sr, 0.004), 0.3)  # 날끼리 긁힘
    mix_into(s, sub(sr, 70, 42, 0.22, 0.06), 0, 0.6)                                  # 밀려나는 무게
    dirt = lowpass(svf(noise(sr, 0.13, rng), sr, 1200, 0.6, 'band'), sr, 1800)
    mix_into(s, mul(dirt, env_adsr(sr, 0.13, 0.01, 0.0, 1.0, 0.1)), sec(sr, 0.04), 0.28)  # 뒤꿈치 밀림
    return softclip(s, 1.6)


@sfx('guard_block', 'PLAYER_DAMAGED{guarded:true}', "61라운드 새 — 일반 가드로 공격을 막음(피해 감소, 퍼펙트 아님). 짧은 '딱' + 팔로 받아내는 둔탁한 충격(150→55 Hz) + 날에 닿는 아주 짧은 '틱'(울림 없음) + 날끼리 긁힘 + 밀려나는 저음 + 뒤꿈치 밀림. 퍼펙트 가드보다 둔하고 짧다", -2)
def _guard_block(sr, rng):
    return _block(sr, rng)


@sfx('combo_finish', 'PLAYER_COMBO_FINISH', "61라운드 새 — 연격 마무리 타(칼 3타·대검 4타·단검 3타)의 첫 적중 1회(PLAYER_COMBO_FINISH{weapon}) 때 그 무기 휘두름·적 피격 위에 겹치는 무게. 공기 터짐 + 깊은 '쿵'(95→34 Hz) + 저역 압력 + 흙 튐 + 짧은 방 울림. 활은 쓰지 않음", -3)
def _combo_finish(sr, rng):
    return _finish(sr, rng)


def _finish(sr, rng, body=(95, 34), press=300):
    dur = 0.5
    s = zeros(sec(sr, dur))
    mix_into(s, snap(sr, rng, 2500, 0.02, 0.004), 0, 1.0)                            # 공기 터짐
    mix_into(s, punch(sr, body[0], body[1], 0.4, 0.1, 1.8), 0, 1.0)                  # 깊은 '쿵'
    pr = lowpass(burst(sr, 0.25, rng, fc=press, q=0.6, tau=0.06, mode='low'), sr, 500)
    mix_into(s, pr, 0, 0.7)                                                           # 저역 압력
    mix_into(s, gravel(sr, rng, 0.2, 5, 0.01, 0.12, 0.22), 0)                         # 흙 튐
    s = softclip(s, 1.7)
    return reverb(s, sr, size=0.5, decay=0.45, wet=0.12)


@variant('guard_block', 2, '가드 막음 변주 2 — 충격 135→50 Hz, 날 틱 2.6 kHz, 긁힘 3.2 kHz')
def _guard_block_v2(sr, rng):
    return _block(sr, rng, body=(135, 50), steel=2600, grind=3200)


@variant('combo_finish', 2, '연격 마무리 변주 2 — 쿵 85→32 Hz, 압력 260 Hz')
def _combo_finish_v2(sr, rng):
    return _finish(sr, rng, body=(85, 32), press=260)


@redo('perfect_guard', "퍼펙트 가드(61라운드 품질 패스 — 880 Hz 종 울림 제거). 충격이 흡수되는 깊은 '훔'(100→40 Hz) + 날카로운 '딱' + 위로 번뜩이는 '키잉' 스침(5→9 kHz) + 3.5 kHz 위의 짧은 쇳빛 + 불똥 + 희미한 고역 잔광. 'PERFECT GUARD' 문구와 같은 프레임")
def _perfect_guard61(sr, rng):
    dur = 0.85
    s = zeros(sec(sr, dur))
    mix_into(s, sub(sr, 100, 40, 0.32, 0.08, 300), 0, 0.85)                          # 흡수된 충격
    mix_into(s, snap(sr, rng, 5000, 0.012, 0.002), 0, 0.6)
    mix_into(s, slice_(sr, rng, 5000, 9000, 0.08, q=1.4, a=0.15), sec(sr, 0.004), 0.45)  # 번뜩 '키잉'
    mix_into(s, glint(sr, rng, 3520, 0.45, 0.1), sec(sr, 0.002), 0.45)              # 높은 쇳빛(짧게)
    mix_into(s, sparks(sr, rng, 0.3, 11, 0.35), sec(sr, 0.01))
    whump = lowpass(burst(sr, 0.15, rng, fc=380, q=0.6, tau=0.035, mode='low'), sr, 500)
    mix_into(s, whump, 0, 0.5)                                                        # 공기 압력
    ns = sec(sr, 0.6)
    sh = svf(noise(sr, 0.6, rng), sr, 8500, 2.0, 'band')
    mix_into(s, mul(sh, env_adsr(sr, 0.6, 0.03, 0.0, 1.0, 0.55)), sec(sr, 0.02), 0.07)  # 잔광
    s = softclip(s, 1.4)
    return reverb(tail(s, sr, 0.02), sr, size=0.6, decay=0.55, wet=0.2)


def _parry_core(sr, rng, clash=2900, scrape=(3500, 8000), body=(140, 65)):
    dur = 0.55
    s = zeros(sec(sr, dur))
    mix_into(s, snap(sr, rng, 4000, 0.012, 0.0018), 0, 0.6)                          # 맞부딪힘 '창'
    mix_into(s, punch(sr, body[0], body[1], 0.12, 0.03, 1.4), 0, 0.75)               # 손에 오는 충격
    mix_into(s, flesh(sr, rng, 420, 0.05, 0.012, 0.8), 0, 0.4)
    mix_into(s, glint(sr, rng, clash, 0.3, 0.07,
                      [(1.0, 1.0), (1.37, 0.6), (1.93, 0.45), (2.61, 0.3), (3.4, 0.15)]), 0, 0.6)  # 짧은 쇳소리
    mix_into(s, slice_(sr, rng, scrape[0], scrape[1], 0.09, q=1.3, a=0.1), sec(sr, 0.003), 0.65)  # 날이 미끄러짐
    mix_into(s, sparks(sr, rng, 0.25, 10, 0.35), sec(sr, 0.008))                     # 불똥
    s = highpass(softclip(s, 2.2), sr, 90)
    return reverb(tail(s, sr, 0.02), sr, size=0.5, decay=0.5, wet=0.18)


@redo('parry', "패링 성공(61라운드 품질 패스 — 1.5 kHz 대 오래 남던 울림 제거). 맞부딪히는 날카로운 '창' + 손에 오는 충격 + 2.9 kHz 위 짧은 쇳소리(0.07 s 감쇠) + 날이 미끄러지는 상승 스침 + 불똥. 변주 v2")
def _parry61(sr, rng):
    return _parry_core(sr, rng)


@variant('parry', 2, '패링 변주 2 — 쇳소리 3.3 kHz, 스침 3.8→8.8 kHz, 충격 150→70 Hz')
def _parry_v2(sr, rng):
    return _parry_core(sr, rng, clash=3300, scrape=(3800, 8800), body=(150, 70))


@redo('parry_perfect', "칼 패링 성공 강조(61라운드 품질 패스, 기존 parry 위에 겹쳐 재생, 'PARRY' 문구·검기 1단 충전과 같은 프레임). 1.8 kHz 위만: 위로 번뜩이는 '키잉' 스침(4→11 kHz) + 4.2 kHz 짧은 쇳빛 + 불똥 + 딸깍")
def _parry_perfect61(sr, rng):
    dur = 0.6
    s = zeros(sec(sr, dur))
    mix_into(s, glint(sr, rng, 4200, 0.5, 0.12), 0, 0.4)
    mix_into(s, slice_(sr, rng, 4000, 11000, 0.12, q=1.4, a=0.15), sec(sr, 0.005), 0.5)
    mix_into(s, sparks(sr, rng, 0.3, 12, 0.3, 5000, 11000), sec(sr, 0.01))
    mix_into(s, click(sr, rng, 0.003, 7000), 0, 0.9)
    s = highpass(s, sr, 1800)
    return reverb(tail(s, sr, 0.03), sr, size=0.45, decay=0.45, wet=0.18)


# ---------------------------------------------------------------------------
# 4. 무기별 휘두르기
# ---------------------------------------------------------------------------

def _katana(sr, rng, hi=(6200, 2000), lo=(1300, 550), dur=0.19):
    s = zeros(sec(sr, dur + 0.03))
    mix_into(s, whoosh(sr, dur, rng, hi[0], hi[1], q=1.3, a=0.2, r=0.55), 0, 0.7)    # 날이 가르는 고역
    mix_into(s, whoosh(sr, dur, rng, lo[0], lo[1], q=0.8, a=0.25, r=0.5), 0, 0.45)   # 팔·몸의 바람
    mix_into(s, burst(sr, 0.02, rng, fc=9000, q=0.8, tau=0.004), sec(sr, 0.02), 0.25)  # 날 끝 '시'
    return s


@redo('swing_katana', '칼 휘두름(61라운드 품질 패스 — 2.4 kHz 쇳소리 제거). 날이 가르는 고역 바람(6.2k→2k) + 팔·몸의 낮은 바람(1.3k→550) + 날 끝 \'시\'. 변주 v2·v3')
def _swing_katana61(sr, rng):
    return _katana(sr, rng)


@variant('swing_katana', 2, '칼 휘두름 변주 2 — 5.6k→1.8k, 0.2 s')
def _swing_katana_v2(sr, rng):
    return _katana(sr, rng, hi=(5600, 1800), lo=(1200, 500), dur=0.2)


@variant('swing_katana', 3, '칼 휘두름 변주 3 — 6.8k→2.3k, 0.17 s')
def _swing_katana_v3(sr, rng):
    return _katana(sr, rng, hi=(6800, 2300), lo=(1400, 600), dur=0.17)


def _greatsword(sr, rng, lo=250, peak=900, end=220, hum=(75, 48), dur=0.4, plant=0.3):
    n = sec(sr, dur)
    s = zeros(sec(sr, dur + 0.06))
    k = int(n * 0.45)
    fc = [lo * (peak / lo) ** (i / k) if i < k else peak * (end / peak) ** ((i - k) / (n - k)) for i in range(n)]
    air = svf(noise(sr, dur, rng), sr, fc, 0.9, 'band')
    mix_into(s, mul(air, env_adsr(sr, dur, dur * 0.4, 0.0, 1.0, dur * 0.5)), 0, 0.95)  # 무거운 바람(올랐다 내림)
    hm = lowpass(mul(tone(sr, dur, hum[0], hum[1]), env_adsr(sr, dur, dur * 0.35, 0.0, 1.0, dur * 0.5)), sr, 160)
    mix_into(s, hm, 0, 0.5)                                                           # 칼 질량의 낮은 울림
    mix_into(s, rustle(sr, rng, 0.08, 900, 40), 0, 0.2)                               # 가죽 손잡이
    mix_into(s, punch(sr, 110, 45, 0.14, 0.04, 1.3), sec(sr, plant), 0.5)            # 디딤
    mix_into(s, lowpass(burst(sr, 0.05, rng, fc=1200, q=0.6, tau=0.012), sr, 2500), sec(sr, plant), 0.3)
    return s


@redo('swing_greatsword', '대검 휘두름(61라운드 품질 패스). 올랐다 내려가는 무거운 바람(250→900→220 Hz) + 칼 질량의 낮은 울림(75→48 Hz) + 가죽 손잡이 + 끝에 디딤. 변주 v2·v3')
def _swing_greatsword61(sr, rng):
    return _greatsword(sr, rng)


@variant('swing_greatsword', 2, '대검 휘두름 변주 2 — 바람 220→800→200, 0.42 s')
def _swing_greatsword_v2(sr, rng):
    return _greatsword(sr, rng, lo=220, peak=800, end=200, hum=(70, 45), dur=0.42, plant=0.32)


@variant('swing_greatsword', 3, '대검 휘두름 변주 3 — 바람 280→1000→240, 0.38 s')
def _swing_greatsword_v3(sr, rng):
    return _greatsword(sr, rng, lo=280, peak=1000, end=240, hum=(80, 50), dur=0.38, plant=0.28)


def _dagger(sr, rng, hi=(8500, 3200), lo=(2200, 1100), dur=0.09):
    s = zeros(sec(sr, dur + 0.02))
    mix_into(s, whoosh(sr, dur, rng, hi[0], hi[1], q=1.7, a=0.12, r=0.5), 0, 0.8)
    mix_into(s, whoosh(sr, dur * 0.9, rng, lo[0], lo[1], q=0.9, a=0.15, r=0.5), 0, 0.35)
    mix_into(s, snap(sr, rng, 6000, 0.008, 0.0012), 0, 0.3)
    return s


@redo('swing_dagger', "단검 찌르기·스침(61라운드 품질 패스). 아주 짧은 고역 '슉'(8.5k→3.2k) + 손목의 작은 바람 + 끝 '틱'. 변주 v2·v3")
def _swing_dagger61(sr, rng):
    return _dagger(sr, rng)


@variant('swing_dagger', 2, '단검 변주 2 — 7.6k→2.8k, 0.1 s')
def _swing_dagger_v2(sr, rng):
    return _dagger(sr, rng, hi=(7600, 2800), lo=(2000, 1000), dur=0.1)


@variant('swing_dagger', 3, '단검 변주 3 — 9.4k→3.6k, 0.08 s')
def _swing_dagger_v3(sr, rng):
    return _dagger(sr, rng, hi=(9400, 3600), lo=(2400, 1200), dur=0.08)


def _bow(sr, rng, f=165, arrow=(3200, 1500), limb=(320, 150)):
    dur = 0.32
    s = zeros(sec(sr, dur))
    st = pluck(sr, 0.25, f, rng, damp=0.98, bright=0.65)
    mix_into(s, mul(st, env_exp(sr, 0.25, 0.06)), 0, 0.7)                             # 시위 '퉁'
    mix_into(s, punch(sr, limb[0], limb[1], 0.06, 0.015, 1.2), 0, 0.55)              # 활대 '텅'
    mix_into(s, burst(sr, 0.03, rng, fc=1800, q=0.7, tau=0.006), 0, 0.35)            # 팔찌 가죽
    mix_into(s, whoosh(sr, 0.2, rng, arrow[0], arrow[1], q=1.1, a=0.1, r=0.7), sec(sr, 0.012), 0.45)  # 멀어지는 화살
    nf = sec(sr, 0.12)
    fl = svf(noise(sr, 0.12, rng), sr, 2200, 1.0, 'band')
    fl = mul(fl, [0.5 + 0.5 * math.sin(TAU * 120 * i / sr) for i in range(nf)])
    mix_into(s, mul(fl, env_exp(sr, 0.12, 0.04)), sec(sr, 0.015), 0.15)              # 깃 떨림
    return s


@redo('bow_shot', "활 짧게 쏘기(61라운드 품질 패스). 시위 '퉁'(165 Hz, 짧게) + 활대 '텅' + 팔찌 가죽 + 멀어지는 화살 바람(3.2k→1.5k) + 깃 떨림. 변주 v2·v3")
def _bow_shot61(sr, rng):
    return _bow(sr, rng)


@variant('bow_shot', 2, '활 변주 2 — 시위 155 Hz, 화살 3k→1.4k')
def _bow_shot_v2(sr, rng):
    return _bow(sr, rng, f=155, arrow=(3000, 1400), limb=(300, 140))


@variant('bow_shot', 3, '활 변주 3 — 시위 176 Hz, 화살 3.4k→1.6k')
def _bow_shot_v3(sr, rng):
    return _bow(sr, rng, f=176, arrow=(3400, 1600), limb=(340, 160))


# ---------------------------------------------------------------------------
# 5. 획득 · 문 · 메뉴
# ---------------------------------------------------------------------------

COIN = [(1, 1.0), (2.03, 0.5), (3.4, 0.25), (4.6, 0.1)]


def _coins(sr, rng, times, freqs):
    dur = 0.32
    s = zeros(sec(sr, dur))
    for t0, f in zip(times, freqs):
        c = metal(sr, 0.18, f, rng, partials=COIN, tau=0.035, jitter=0.01)
        mix_into(s, highpass(c, sr, 2000), sec(sr, t0), 0.75)                         # 높고 짧은 동전
    mix_into(s, thud(sr, 0.06, 220, 140, 0.012), sec(sr, times[-1] + 0.01), 0.3)      # 주머니 '툭'
    mix_into(s, rustle(sr, rng, 0.08, 1500, 50), sec(sr, times[-1]), 0.2)
    return s


@redo('pickup_gold', '동전 획득(61라운드 품질 패스). 높고 짧은 동전 두 번(3.8k·4.75k, 0.035 s 감쇠) + 주머니에 들어가는 \'툭\'·가죽 스침. 변주 v2·v3(동전 수·음높이 다름)')
def _pickup_gold61(sr, rng):
    return _coins(sr, rng, [0.0, 0.06], [3800, 4750])


@variant('pickup_gold', 2, '동전 변주 2 — 세 번(3.5k·4.2k·5k), 간격 45 ms')
def _pickup_gold_v2(sr, rng):
    return _coins(sr, rng, [0.0, 0.045, 0.09], [3500, 4200, 5000])


@variant('pickup_gold', 3, '동전 변주 3 — 두 번(4.1k·3.6k, 내려감), 간격 70 ms')
def _pickup_gold_v3(sr, rng):
    return _coins(sr, rng, [0.0, 0.07], [4100, 3600])


@redo('pickup_potion', "물약 획득(61라운드 품질 패스). 유리병 짧은 '틱'(2.6 kHz, 울림 짧게) + 병 속 출렁 + 마개 '톡' + 허리춤에 거는 가죽 스침. 권장 음량 -4 → -2 dB(울림을 줄여 짧은 구간 음량이 약 5 dB 작아진 만큼 일부 보정)", -2)
def _pickup_potion61(sr, rng):
    dur = 0.42
    s = zeros(sec(sr, dur))
    g = metal(sr, 0.2, 2600, rng, partials=GLASS, tau=0.04, jitter=0.004)
    mix_into(s, highpass(g, sr, 1500), 0, 0.55)
    mix_into(s, slosh(sr, rng, 0.26, 450, 900), sec(sr, 0.03), 0.5)
    mix_into(s, wood_tok(sr, rng, 700, 0.04, 0.006, 0.5), sec(sr, 0.012), 0.35)
    mix_into(s, rustle(sr, rng, 0.12, 1300, 45), sec(sr, 0.2), 0.25)
    return s


@redo('door_open', "방 클리어 · 문 열림(61라운드 품질 패스, 0.7 → 1.1 s). 나무 빗장 들어 올림 + 쇠 걸쇠 '철컥'(울림 짧게) + 나무 문 삐걱 + 문이 미는 낮은 바람 + 벽에 닿는 '쿵', 돌방 울림")
def _door_open61(sr, rng):
    dur = 0.95
    s = zeros(sec(sr, dur))
    mix_into(s, punch(sr, 160, 90, 0.08, 0.02, 1.2), 0, 0.6)                          # 빗장 들림
    mix_into(s, wood_tok(sr, rng, 640, 0.05, 0.008, 0.7), 0, 0.5)
    mix_into(s, click(sr, rng, 0.006, 2200), sec(sr, 0.1), 0.9)                       # 걸쇠 '철컥'
    mix_into(s, metal(sr, 0.08, 1400, rng, tau=0.015, jitter=0.03), sec(sr, 0.1), 0.25)
    mix_into(s, punch(sr, 200, 120, 0.05, 0.01, 1.1), sec(sr, 0.1), 0.35)
    nc = sec(sr, 0.5)
    creak = tone(sr, 0.5, 80, 125, kind='saw')
    creak = svf(creak, sr, sweep(sr, nc, 480, 1500), 2.5, 'band')
    creak = mul(creak, [0.75 + 0.25 * math.sin(TAU * 17 * i / sr) for i in range(nc)])
    mix_into(s, mul(creak, env_adsr(sr, 0.5, 0.08, 0.0, 1.0, 0.18)), sec(sr, 0.18), 0.5)  # 삐걱
    mix_into(s, whoosh(sr, 0.4, rng, 300, 700, q=0.7, a=0.4, r=0.5), sec(sr, 0.3), 0.3)   # 문이 미는 바람
    mix_into(s, thud(sr, 0.2, 90, 45, 0.05), sec(sr, 0.78), 0.7)                      # 벽에 '쿵'
    mix_into(s, burst(sr, 0.08, rng, fc=500, q=0.6, tau=0.02, mode='low'), sec(sr, 0.78), 0.4)
    return reverb(tail(s, sr, 0.15), sr, size=0.75, decay=0.55, wet=0.17)


def _tok(sr, rng, f):
    # 0.08 s: 0.06 s 로 만들면 ffmpeg 6.1 OGG 디코더가 끝을 128 샘플 잘라 길이 검증에 걸린다(소리는 0.05 s 안에 끝남)
    s = zeros(sec(sr, 0.08))
    mix_into(s, wood_tok(sr, rng, f, 0.045, 0.007, 0.5), 0, 1.0)
    return s


@redo('menu_move', "메뉴 이동(61라운드 품질 패스). 마른 나무 '톡'(1150 Hz, 7 ms 감쇠) — 더 둥글게. 변주 v2(1030 Hz)와 번갈아 쓰면 커서가 걷는 느낌")
def _menu_move61(sr, rng):
    return _tok(sr, rng, 1150)


@variant('menu_move', 2, '메뉴 이동 변주 2 — 1030 Hz')
def _menu_move_v2(sr, rng):
    return _tok(sr, rng, 1030)


@redo('menu_select', "메뉴 선택(61라운드 품질 패스 — 쇠 틱 제거). 도장 '쿵'(220→95 Hz) + 종이 '탁' + 나무 '톡'")
def _menu_select61(sr, rng):
    s = zeros(sec(sr, 0.17))
    mix_into(s, punch(sr, 220, 95, 0.13, 0.025, 1.3), 0, 0.9)
    mix_into(s, burst(sr, 0.03, rng, fc=2200, q=0.7, tau=0.006), 0, 0.5)
    mix_into(s, wood_tok(sr, rng, 700, 0.05, 0.009, 0.5), sec(sr, 0.004), 0.35)
    return s


@redo('menu_cancel', "메뉴 닫기·뒤로(61라운드 품질 패스). 종이를 넘기는 짧은 '사락'(3k→1.2k) + 아래로 놓는 작은 '톡'")
def _menu_cancel61(sr, rng):
    s = zeros(sec(sr, 0.15))
    n = sec(sr, 0.09)
    p = svf(noise(sr, 0.09, rng), sr, sweep(sr, n, 3000, 1200), 1.0, 'band')
    mix_into(s, mul(p, env_adsr(sr, 0.09, 0.015, 0.0, 1.0, 0.06)), 0, 0.8)
    mix_into(s, thud(sr, 0.05, 180, 110, 0.01), sec(sr, 0.075), 0.35)
    return s
