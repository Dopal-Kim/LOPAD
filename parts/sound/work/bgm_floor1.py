# -*- coding: utf-8 -*-
"""
61라운드 P11 — 1층 전용 BGM (44.1 kHz 스테레오, 60~120 s 루프).

build.py 가 기존 BGM 6곡(title ~ emperor) 다음에 import 한다(BGM 시드 = 5000 + 등록 순서 → 기존 곡 불변).

  f1_outside   벽 밖(탄생지 · 버려진 길 · 국경 초소)  96 s  — 바람, 먼 포성, 바람에 흔들리는 쇠, 적막
  f1_jan       잔 거리(1층 전투 노드)               96 s  — 3/4 150 BPM, 술집 골목의 비틀린 왈츠(바이올린·손풍금·손북)
  f1_boss_p1   만취 1국면                           72 s  — 6/8(점4분 120), 기본: 베이스 오스티나토·손풍금·바이올린
  f1_boss_p2   만취 2국면                           72 s  — p1 + 타악(큰 북·술통·탬버린·스네어)
  f1_boss_p3   만취 3국면                           72 s  — p2 를 0.5 Hz 로 울렁이게(세상이 돈다) + 왜곡 베이스·삼전음 뿔나팔 + 불길

보스 3국면은 **같은 길이·같은 박자 격자**이고 p1 ⊂ p2 ⊂ p3 로 층을 쌓는다. 시스템은 국면이 바뀌면 지금 재생 위치를
그대로 이어 다음 파일로 교차 페이드하면 '층이 더해지는' 것처럼 들린다(manifest `bgmByFloorState`·`mixing.bgmPhase*`).
세 파일은 같은 이득으로 정규화했다(p1·p2 피크는 -6 dBFS 보다 낮다) — 바뀔 때 바탕 음량이 그대로다.

루프 규칙: 음은 모두 wrap=True 로 섞고(꼬리가 앞으로 감김), 지속 재료는 정수 주기(tone_loop·lfo_loop·noise_loop),
필터·리버브는 루프 끝을 앞에 덧대 상태를 이어 처리한다(`_loopfx`).
"""
import functools

from build import *  # noqa: F401,F403
from build import bgm, GLASS, crackle  # noqa: F401

SR2 = 44100


# ---------------------------------------------------------------------------
# 스테레오 버스
# ---------------------------------------------------------------------------

def _pan(p):
    a = (max(-1.0, min(1.0, p)) + 1.0) * math.pi / 4
    return math.cos(a) * math.sqrt(2.0), math.sin(a) * math.sqrt(2.0)   # 가운데 = 1, 1


class Bus(object):
    """루프 길이 n 의 스테레오 버퍼(L·R 리스트). 모든 put 은 루프로 감긴다."""

    def __init__(self, n):
        self.n = n
        self.L = zeros(n)
        self.R = zeros(n)

    def put(self, seg, t, sr, g=1.0, pan=0.0, width=0.0):
        """seg 를 t 초에. pan(-1~1) 일정 전력, width = 오른쪽만 늦추는 하스 지연(초, 음수면 왼쪽)."""
        gl, gr = _pan(pan)
        s = sec(sr, t)
        dl = sec(sr, -width) if width < 0 else 0
        dr = sec(sr, width) if width > 0 else 0
        mix_into(self.L, seg, s + dl, g * gl, wrap=True)
        mix_into(self.R, seg, s + dr, g * gr, wrap=True)

    def layer(self, segL, segR=None, g=1.0):
        """루프 전체 길이 재료(길이 n)를 더한다."""
        segR = segL if segR is None else segR
        for i in range(self.n):
            self.L[i] += segL[i] * g
            self.R[i] += segR[i] * g

    def add(self, other, g=1.0):
        self.layer(other.L, other.R, g)


def _loopfx(fn, seg, sr, pre):
    """루프 재료에 필터·리버브: 끝 pre 초를 앞에 덧대 상태를 데운 뒤 처리하고 덧댄 부분을 버린다."""
    p = min(len(seg), sec(sr, pre))
    return fn(seg[len(seg) - p:] + seg)[p:]


def _rev_pre(size, decay, sr):
    """콤 필터 꼬리가 -100 dB 밑으로 내려가는 시간(초) — 루프 리버브 덧댐 길이."""
    d = 0.0297 * size
    return min(12.0, max(1.0, d * math.log(1e-5) / math.log(max(1e-3, decay))))


def reverb2(bus, sr, size=1.0, decay=0.75, wet=0.3, damp=0.3, spread=1.071):
    """스테레오 루프 리버브: 오른쪽 콤 지연을 spread 배로 늘려 꼬리를 서로 다르게(넓이)."""
    out = Bus(bus.n)
    pre = _rev_pre(size * spread, decay, sr)
    out.L = _loopfx(lambda x: reverb(x, sr, size, decay, wet, damp), bus.L, sr, pre)
    out.R = _loopfx(lambda x: reverb(x, sr, size * spread, decay, wet, damp), bus.R, sr, pre)
    return out


def svf_loop(seg, sr, fc, q=1.0, mode='low', pre=0.5):
    """루프 재료용 바이쿼드. fc 가 리스트(길이 n, 루프 주기)면 같이 덧댄다."""
    p = sec(sr, pre)
    if isinstance(fc, (int, float)):
        return svf(seg[-p:] + seg, sr, fc, q, mode)[p:]
    return svf(seg[-p:] + seg, sr, fc[-p:] + fc, q, mode)[p:]


def lp_loop(seg, sr, fc, pre=0.5):
    p = sec(sr, pre)
    return lowpass(seg[-p:] + seg, sr, fc)[p:]


# ---------------------------------------------------------------------------
# 악기
# ---------------------------------------------------------------------------

def fiddle(sr, dur, f, rng, vib=0.006, scoop=0.6, trem=0.0, bend=0.0, bright=1.0):
    """비틀린 현(바이올린): 톱니 + 몸통 공명 셋 + 활 잡음. scoop = 반음 단위로 아래에서 미끄러져 들어감,
    bend = 끝 30 % 동안 반음 단위로 처지는 정도(취한 손), trem = 12 Hz 활 떨기 깊이."""
    n = sec(sr, dur)
    ph = rng.uniform(0, TAU)
    vr = 5.4 + rng.uniform(-0.3, 0.3)
    nb = int(n * 0.7)
    freqs = []
    for i in range(n):
        t = i / sr
        ramp = min(1.0, t / 0.25)
        x = 2 ** ((-scoop * math.exp(-t / 0.045)) / 12.0)
        if bend and i > nb:
            x *= 2 ** (-bend * ((i - nb) / max(1, n - nb)) ** 2 / 12.0)
        freqs.append(f * x * (1 + vib * ramp * math.sin(TAU * vr * t + ph)))
    osc = tone_f(sr, freqs, 'saw', rng.random())
    body = scale(svf(osc, sr, 480, 2.0, 'band'), 0.5)
    mix_into(body, svf(osc, sr, 1150, 2.5, 'band'), 0, 0.6)
    mix_into(body, svf(osc, sr, 2700, 2.0, 'band'), 0, 0.35 * bright)
    mix_into(body, lowpass(osc, sr, 900), 0, 0.25)
    mix_into(body, svf(noise(sr, dur, rng), sr, 3200, 0.8, 'band'), 0, 0.05)   # 활 잡음
    env = env_adsr(sr, dur, min(0.06, dur * 0.3), 0.1, 0.85, min(0.09, dur * 0.3))
    if trem:
        env = [e * (1 - trem + trem * abs(math.sin(math.pi * 12 * i / sr))) for i, e in enumerate(env)]
    return mul(body, env)


def reed(sr, dur, f, detune=0.004, fc=1300):
    """손풍금(리드): 펄스 + 사각 두 겹 디튠 → 대역 + 저역통과. 짧은 '빰'."""
    a = tone(sr, dur, f * (1 - detune), kind='pulse')
    b = tone(sr, dur, f * (1 + detune), kind='square')
    s = add(a, scale(b, 0.6))
    s = add(scale(svf(s, sr, fc, 0.8, 'band'), 0.8), scale(lowpass(s, sr, 2400), 0.35))
    return mul(s, env_adsr(sr, dur, 0.012, 0.05, 0.8, min(0.07, dur * 0.4)))


def bass_pluck(sr, dur, f, rng):
    """콘트라베이스 피치카토: 현 + 같은 음 사인."""
    s = mul(pluck(sr, dur, f, rng, damp=0.995, bright=0.45), env_exp(sr, dur, dur * 0.4))
    mix_into(s, mul(tone(sr, dur, f), env_exp(sr, dur, dur * 0.3)), 0, 0.5)
    return lowpass(s, sr, 1200)


def bass_bow(sr, dur, f, cut=(1500, 420), drive=1.0):
    """보스 베이스: 톱니 + 사인, 필터가 빠르게 닫히는 '둥'. drive > 1 이면 포화(3국면 왜곡)."""
    n = sec(sr, dur)
    s = add(tone(sr, dur, f, kind='saw'), scale(tone(sr, dur, f), 0.6))
    fc = [cut[1] + (cut[0] - cut[1]) * math.exp(-i / (0.08 * sr)) for i in range(n)]
    s = svf(s, sr, fc, 0.9, 'low')
    s = mul(s, env_adsr(sr, dur, 0.006, 0.0, 1.0, min(0.05, dur * 0.3)))
    if drive > 1.0:
        k = 1.0 / math.tanh(drive)
        s = [math.tanh(x * drive) * k for x in s]
    return s


def frame_drum(sr, rng, g=1.0, f0=140, f1=78):
    d = thud(sr, 0.3, f0, f1, 0.08)
    mix_into(d, burst(sr, 0.05, rng, fc=900, q=0.7, tau=0.012), 0, 0.25)
    return scale(d, g)


def spoons(sr, rng):
    s = burst(sr, 0.03, rng, fc=2600, q=2.0, tau=0.005)
    mix_into(s, mul(tone(sr, 0.03, 900, 700), env_exp(sr, 0.03, 0.006)), 0, 0.3)
    return s


def tambourine(sr, rng, g=1.0):
    s = burst(sr, 0.12, rng, fc=7000, q=0.7, tau=0.035, mode='high')
    for f in (6100, 7400, 8800):
        mix_into(s, mul(tone(sr, 0.08, f * rng.uniform(0.98, 1.02)), env_exp(sr, 0.08, 0.02)), 0, 0.06)
    return scale(s, g)


def bottle(sr, rng):
    return metal(sr, 0.35, rng.uniform(2300, 3400), rng, partials=GLASS, tau=0.07, jitter=0.004)


def big_drum(sr, rng, g=1.0):
    d = thud(sr, 0.6, 88, 40, 0.18)
    mix_into(d, burst(sr, 0.25, rng, fc=200, q=0.6, tau=0.06, mode='low'), 0, 0.6)
    mix_into(d, burst(sr, 0.02, rng, fc=1500, q=0.6, tau=0.004), 0, 0.25)
    return scale(d, g)


def barrel(sr, rng, g=1.0):
    """술통 '통': 속 빈 나무 공명(230·520 Hz) — 보스 효과음 boss1_barrel_kick 과 같은 재료."""
    d = thud(sr, 0.18, 240, 170, 0.035)
    mix_into(d, mul(svf(noise(sr, 0.18, rng), sr, 520, 5.0, 'band'), env_exp(sr, 0.18, 0.05)), 0, 0.7)
    mix_into(d, burst(sr, 0.02, rng, fc=2000, q=0.8, tau=0.004), 0, 0.2)
    return scale(d, g)


def cannon(sr, rng):
    """먼 포성: 낮은 '쿵' + 저역 폭음 + 언덕에 부딪혀 굴러오는 메아리 셋."""
    dur = 3.2
    s = zeros(sec(sr, dur))
    b = lowpass(kick(sr, 1.4, 72, 26, 0.4), sr, 160)
    mix_into(b, lowpass(burst(sr, 1.2, rng, fc=120, q=0.6, tau=0.45, mode='low'), sr, 220), 0, 1.0)
    mix_into(s, b, 0, 1.0)
    for t0, g, fc in ((0.28, 0.45, 140), (0.61, 0.26, 110), (1.05, 0.13, 90)):
        mix_into(s, lowpass(b, sr, fc), sec(sr, t0), g)
    roll = svf(noise(sr, 2.6, rng), sr, 90, 0.7, 'low')
    mix_into(s, mul(roll, env_adsr(sr, 2.6, 0.2, 0.0, 1.0, 2.2)), sec(sr, 0.15), 0.6)
    return s


def creak(sr, dur, rng):
    """녹슨 간판·쇠고리가 바람에 삐걱."""
    n = sec(sr, dur)
    c = tone(sr, dur, 90 * rng.uniform(0.9, 1.1), 125, kind='saw')
    c = svf(c, sr, sweep(sr, n, 600, 1400), 3.0, 'band')
    return mul(c, env_adsr(sr, dur, dur * 0.3, 0.0, 1.0, dur * 0.5))


def bar_notes(rows, bar_len, beat_len):
    """[(마디, [(박 오프셋, midi, 박 길이)])] → [(시각 s, midi, 길이 s)]."""
    out = []
    for b, row in rows:
        for off, m, d in row:
            out.append((b * bar_len + off * beat_len, m, d * beat_len))
    return out


# ---------------------------------------------------------------------------
# ① 벽 밖 — 바람 · 먼 포성 · 쇠 · 적막
# ---------------------------------------------------------------------------

@bgm('f1_outside', "1층 벽 밖(탄생지·버려진 길·국경 초소). 96 s 루프, 44.1 kHz 스테레오. 좌우가 따로 부는 바람(돌풍 3겹 · 가는 휘파람) + 아주 낮은 A1·E2 드론 + 먼 포성 8번(언덕 메아리) + 바람에 흔들리는 쇠고리·녹슨 삐걱 + 멀리서 류트 네 음 두 번 + 중반의 서늘한 고음 한 가닥. 박자 없음, 비어 있는 시간이 대부분. 권장 음량 +3.5 dB = RMS 약 -23 dBFS(전투 곡보다 2 dB 작게 — 적막)", 3.5, sr=SR2, use=dict(floor=1, state='journey'))
def _bgm_f1_outside(sr, rng):
    L = 96.0
    n = sec(sr, L)
    bus = Bus(n)
    # 돌풍: 5·7·13 주기 사인 합(루프에 정수 주기)
    def gust(shift):
        a = lfo_loop(sr, n, 5 / L, 0.5, 0.0, shift)
        b = lfo_loop(sr, n, 7 / L, 0.3, 0.0, 0.31 + shift)
        c = lfo_loop(sr, n, 13 / L, 0.2, 0.0, 0.67 + shift)
        return [min(1.0, max(0.0, 0.5 + x + y + z)) for x, y, z in zip(a, b, c)]
    for ch, shift in ((0, 0.0), (1, 0.021)):
        gs = gust(shift)
        fc = [220 + 650 * g ** 1.5 for g in gs]
        w = svf_loop(noise_loop(sr, n, rng), sr, fc, 0.7, 'low')
        w = [x * (0.3 + 0.7 * g) for x, g in zip(w, gs)]
        wf = [900 + 700 * g for g in gs]
        wh = svf_loop(noise_loop(sr, n, rng), sr, wf, 8.0, 'band')
        wh = [x * g * g for x, g in zip(wh, gs)]
        tgt = bus.L if ch == 0 else bus.R
        for i in range(n):
            tgt[i] += w[i] * 0.42 + wh[i] * 0.05
    # 드론: A1 톱니(좌우 0.12 % 디튠 → 아주 느린 맥놀이) + E2 사인, 48 s 주기로 부풀었다 가라앉음
    swell = lfo_loop(sr, n, 2 / L, 0.3, 0.7, -0.25)
    dl = lp_loop(tone_loop(sr, n, 55.0 * 0.9988, 'saw'), sr, 160)
    dr = lp_loop(tone_loop(sr, n, 55.0 * 1.0012, 'saw'), sr, 160)
    e2 = tone_loop(sr, n, 82.41, 'sine')
    bus.layer([(a + 0.3 * e) * s for a, e, s in zip(dl, e2, swell)],
              [(b + 0.3 * e) * s for b, e, s in zip(dr, e2, swell)], 0.16)
    rum = svf_loop(noise_loop(sr, n, rng), sr, 70, 0.7, 'low')
    bus.layer(rum, None, 0.12)
    # 먼 포성 (시각, 팬, 세기) — 31.2 는 겹쳐 쏜 두 발
    for t0, p, g in ((6.4, -0.5, 0.8), (19.7, 0.35, 0.55), (31.2, -0.15, 0.9), (31.75, -0.05, 0.5),
                     (49.9, 0.55, 0.7), (63.3, -0.6, 0.6), (77.8, 0.2, 0.85), (88.6, 0.6, 0.45)):
        bus.put(cannon(sr, rng), t0, sr, g * 0.9, p, width=0.012)
    # 바람에 흔들리는 쇠고리(높고 작게 — 중역 울림 없음) · 녹슨 삐걱
    for t0 in (14.2, 14.9, 42.5, 70.3, 71.1):
        m = highpass(metal(sr, 1.4, rng.uniform(2000, 2700), rng, tau=0.3, jitter=0.02), sr, 1500)
        bus.put(m, t0, sr, 0.05, rng.uniform(-0.8, 0.8))
    for t0 in (26.0, 58.4, 84.0):
        bus.put(creak(sr, 0.9, rng), t0, sr, 0.06, rng.uniform(-0.7, 0.7))
    # 멀리서 류트 네 음(1층 잔 거리 선율의 첫 조각 — 기억처럼)
    for t0, m in ((36.0, 57), (36.9, 60), (37.7, 64), (39.2, 59), (80.0, 64), (80.8, 62), (81.7, 60), (83.0, 57)):
        p = mul(pluck(sr, 2.2, midi(m) * (1 + rng.uniform(-0.004, 0.004)), rng, damp=0.996, bright=0.5),
                env_exp(sr, 2.2, 0.7))
        bus.put(lowpass(p, sr, 2000), t0, sr, 0.11, -0.3, width=0.008)
    # 서늘한 고음 한 가닥(이질) — 좌우 2 Hz 차 맥놀이
    hi = env_adsr(sr, 12.0, 5.0, 0.0, 1.0, 6.0)
    bus.put(mul(tone(sr, 12.0, 1318.5), hi), 56.0, sr, 0.014, -0.6)
    bus.put(mul(tone(sr, 12.0, 1320.5), hi), 56.0, sr, 0.014, 0.6)
    return _out(reverb2(bus, sr, size=1.7, decay=0.84, wet=0.4))


# ---------------------------------------------------------------------------
# ② 잔 거리 — 술집 골목의 비틀린 왈츠 (A 단조, 3/4, 150 BPM, 80마디 = 96 s)
# ---------------------------------------------------------------------------

CH_JAN = {'Am': ([57, 60, 64], 45, 52), 'E7': ([56, 59, 62], 40, 47), 'Dm': ([57, 62, 65], 38, 45),
          'F': ([57, 60, 65], 41, 48), 'Bb': ([58, 62, 65], 46, 41)}   # (손풍금 화음, 베이스 근음, 5음)
JAN_THEME = ['Am', 'Am', 'E7', 'E7', 'Am', 'Am', 'Dm', 'Dm', 'Dm', 'Am', 'E7', 'Am', 'F', 'Dm', 'E7', 'E7']
JAN_TENSE = ['Dm', 'Dm', 'Am', 'Am', 'Bb', 'Bb', 'E7', 'E7', 'Dm', 'Dm', 'Am', 'F', 'Bb', 'E7', 'Am', 'E7']
JAN_BREAK = ['Am'] * 6 + ['Dm', 'Dm'] + ['Am'] * 4 + ['F', 'E7', 'E7', 'E7']
JAN_MEL = [  # 마디별 (박, midi, 박 길이)
    [(0, 76, 2), (2, 72, 1)], [(0, 69, 1.5), (1.5, 71, 0.5), (2, 72, 1)], [(0, 71, 2), (2, 68, 1)], [(0, 64, 3)],
    [(0, 69, 1), (1, 72, 1), (2, 76, 1)], [(0, 81, 2), (2, 80, 1)], [(0, 77, 1.5), (1.5, 76, 0.5), (2, 74, 1)],
    [(0, 74, 3)],
    [(0, 77, 1), (1, 81, 1), (2, 77, 1)], [(0, 76, 2), (2, 72, 1)], [(0, 74, 1), (1, 71, 1), (2, 68, 1)],
    [(0, 69, 3)],
    [(0, 72, 1), (1, 77, 1), (2, 81, 1)], [(0, 77, 1.5), (1.5, 74, 0.5), (2, 68, 1)],
    [(0, 71, 1), (1, 74, 1), (2, 77, 1)], [(0, 76, 2)],
]
JAN_TENSE_MEL = [(0, 74, 2), (2, 72, 2), (4, 70, 2), (6, 68, 2), (8, 69, 2), (10, 72, 2), (12, 74, 1), (13, 77, 1),
                 (14, 76, 2)]   # (마디, midi, 마디 수) — 활 떨기로 길게


@bgm('f1_jan', "1층 잔 거리(전투 노드). 96 s 루프(80마디), 44.1 kHz 스테레오, A 단조 3/4 150 BPM. 술집 골목의 비틀린 왈츠: 콘트라베이스 1박 + 손풍금 2·3박(빈 왈츠처럼 2박이 살짝 이르고 3박이 늦음), 취한 바이올린 주제(아래에서 미끄러져 들어가는 음, 끝이 처지는 음), 손북·숟가락·탬버린·술병. 구성 A(골목) → B(주제) → C(긴장: 삼전음 드론, 활 떨기, 타악 증가) → B'(주제 + 류트 대선율 + 옥타브 아래 바이올린) → D(쉼·쌓기: 낮은 반복음 → 반음계 상승 + 롤). 권장 음량 +3.5 dB = RMS 약 -21 dBFS", 3.5, floors=[1], sr=SR2, use=dict(floor=1, state='combat'))
def _bgm_f1_jan(sr, rng):
    bpm = 150.0
    beat = 60.0 / bpm
    bar = beat * 3
    bars = 80
    n = sec(sr, bar * bars)
    bus = Bus(n)
    prog = JAN_THEME + JAN_THEME + JAN_TENSE + JAN_THEME + JAN_BREAK
    jit = lambda: rng.uniform(-0.006, 0.009)  # noqa: E731  늦는 쪽으로 기운 흔들림
    for b in range(bars):
        sect = b // 16
        t0 = b * bar
        chord, root, fifth = CH_JAN[prog[b]]
        # 콘트라베이스 1박 (근음·5음 번갈아), D 마지막 2마디는 반음계 상승
        if b in (78, 79):
            for k, m in enumerate((40, 41) if b == 78 else (42, 44)):
                bus.put(bass_pluck(sr, 0.7, midi(m), rng), t0 + k * 1.5 * beat, sr, 0.55)
        else:
            m = root if b % 2 == 0 else fifth
            bus.put(bass_pluck(sr, 1.0, midi(m), rng), t0 + jit(), sr, 0.6)
        # 손풍금
        if sect == 2:      # 긴장: 화음을 길게, 바람통 떨림
            if b % 2 == 0:
                for m in chord:
                    r = reed(sr, bar * 2 + 0.1, midi(m) * 0.9995, fc=1100)
                    r = mul(r, [0.75 + 0.25 * math.sin(TAU * 6.5 * i / sr) for i in range(len(r))])
                    bus.put(r, t0, sr, 0.09, -0.35, width=0.01)
        elif not (sect == 4 and b < 72):
            for off, g in ((1.0 - 0.06, 0.12), (2.0 + 0.03, 0.1)):
                for m in chord:
                    bus.put(reed(sr, 0.28, midi(m) * 0.9995), t0 + off * beat + jit(), sr, g, -0.35, width=0.008)
        # 손북 1박(+ 긴장·B' 에 3박 뒤)
        bus.put(frame_drum(sr, rng), t0, sr, 0.7)
        if sect in (2, 3):
            bus.put(frame_drum(sr, rng, 0.6, 170, 95), t0 + 2.5 * beat, sr, 0.35, 0.15)
        if sect == 4 and b >= 72:      # 쌓기: 8분음 손북이 점점 세게
            for k in range(6):
                bus.put(frame_drum(sr, rng, 1.0, 165, 90), t0 + k * 0.5 * beat, sr, 0.12 + 0.3 * (b - 72) / 8 + 0.02 * k, 0.1)
        # 숟가락 2·3박, 가끔 2박 뒤 유령음
        if sect != 4 or b >= 70:
            for off in (1.0, 2.0):
                bus.put(spoons(sr, rng), t0 + off * beat + jit(), sr, 0.28, 0.45)
            if rng.random() < 0.5:
                bus.put(spoons(sr, rng), t0 + 1.5 * beat + jit(), sr, 0.13, 0.5)
        # 탬버린(긴장·B')
        if sect in (2, 3):
            for k, off in enumerate((1.0, 1.5, 2.0, 2.5)):
                bus.put(tambourine(sr, rng), t0 + off * beat + jit(), sr, 0.12 if k % 2 == 0 else 0.07, -0.45)
        # 술병 부딪힘: 네 마디에 한 번쯤
        if sect in (0, 1, 3) and rng.random() < 0.25:
            bus.put(bottle(sr, rng), t0 + rng.choice((0.5, 1.5, 2.5)) * beat, sr, 0.07, rng.uniform(-0.7, 0.7))
    # 쌓기 끝 스네어 롤(마지막 마디 16분음, 점점 세게)
    for k in range(12):
        bus.put(snare(sr, rng, 0.1, 0.25), 79 * bar + k * 0.25 * beat, sr, 0.08 + 0.022 * k, -0.1)
    # 바이올린
    def play(notes, g, pan, trem=0.0, bend_p=0.25, octave=0):
        for t, m, d in notes:
            f = midi(m + octave) * 2 ** (rng.uniform(-0.12, 0.12) / 12.0)
            bend = rng.uniform(0.3, 0.8) if rng.random() < bend_p else 0.0
            fd = fiddle(sr, d * 0.97 + 0.04, f, rng, scoop=rng.uniform(0.3, 0.9), trem=trem, bend=bend)
            bus.put(fd, t + rng.uniform(0.0, 0.018), sr, g, pan, width=0.006)
    theme = bar_notes([(b, JAN_MEL[b]) for b in range(16)], bar, beat)
    play([(16 * bar + t, m, d) for t, m, d in theme], 0.2, 0.3)
    play([(48 * bar + t, m, d) for t, m, d in theme], 0.2, 0.3)
    play([(48 * bar + t, m, d) for t, m, d in theme], 0.08, -0.2, octave=-12, bend_p=0.0)
    play([(15 * bar + 2 * beat, 71, 1)], 0.16, 0.3)                             # A → B 못갖춘마디
    play([((32 + b) * bar, m, d * 3) for b, m, d in JAN_TENSE_MEL], 0.16, 0.3, trem=0.45, bend_p=0.0)
    low = [[(0, 57, 1), (1, 60, 1), (2, 59, 1)], [(0, 57, 1), (1, 56, 1), (2, 57, 1)]]
    for b in range(64, 80):
        row = low[b % 2]
        play([(b * bar + o * beat, m, d) for o, m, d in row], 0.13, 0.25, bend_p=0.15)
        if b >= 72:
            play([(b * bar + o * beat, m + 12, d) for o, m, d in row], 0.07 + 0.01 * (b - 72), 0.4, bend_p=0.0)
    # 류트 대선율(B'): 8분음 화음 분산
    for b in range(48, 64):
        chord = CH_JAN[prog[b]][0]
        for k in range(6):
            m = chord[[0, 1, 2, 1, 2, 1][k]] + 12
            p = mul(pluck(sr, 0.6, midi(m) * (1 + rng.uniform(-0.004, 0.004)), rng, damp=0.993, bright=0.5),
                    env_exp(sr, 0.6, 0.18))
            bus.put(p, b * bar + k * 0.5 * beat + jit(), sr, 0.1 if k % 2 == 0 else 0.07, -0.55)
    # 바닥 긴장: A1 낮은 드론 + C 구간에만 E♭2(삼전음)가 스며듦
    dr = lp_loop(tone_loop(sr, n, 55.0, 'saw'), sr, 120)
    bus.layer(dr, None, 0.1)
    eb = lp_loop(tone_loop(sr, n, 77.78, 'saw'), sr, 150)
    c0, c1 = sec(sr, 32 * bar), sec(sr, 48 * bar)
    env = [0.0] * n
    for i in range(c0, c1):
        x = (i - c0) / (c1 - c0)
        env[i] = math.sin(math.pi * x) ** 0.7
    bus.layer([a * e for a, e in zip(eb, env)], None, 0.09)
    out = reverb2(bus, sr, size=0.9, decay=0.65, wet=0.22)
    return _out(out)


# ---------------------------------------------------------------------------
# ③ 만취 보스 — D 단조 6/8(점4분 120), 72마디 = 72 s. 국면마다 층을 쌓는다.
# ---------------------------------------------------------------------------

CH_BOSS = {'Dm': ([62, 65, 69], 38), 'Gm': ([62, 67, 70], 31), 'A7': ([61, 64, 67], 33), 'Bb': ([62, 65, 70], 34),
           'Eb': ([63, 67, 70], 39), 'Cm': ([60, 63, 67], 36), 'D7': ([62, 66, 72], 38), 'C#dim': ([61, 64, 67], 37),
           'C': ([60, 64, 67], 36), 'Bdim': ([59, 62, 65], 35), 'A': ([61, 64, 69], 33)}
BOSS_PROG = (['Dm', 'Dm', 'Dm', 'Eb', 'Dm', 'Dm', 'Dm', 'A7'] +          # A 도입(베이스 동기)
             ['Dm', 'Dm', 'Gm', 'A7', 'Dm', 'Bb', 'A7', 'Dm'] +          # B 주제 1
             ['Gm', 'Gm', 'Cm', 'D7', 'Gm', 'Eb', 'D7', 'Gm'] +          # C 주제 1(4도 위)
             ['Dm', 'C#dim', 'C', 'Bdim', 'Bb', 'A', 'A7', 'A7'] +       # D 세상이 돈다(반음 하강)
             ['Dm', 'Dm', 'Bb', 'A7', 'Dm', 'Dm', 'Eb', 'A7'] +          # E 베이스 + 낮은 뿔나팔
             ['Dm', 'Eb', 'Dm', 'A7', 'Dm', 'Gm', 'A7', 'A7'] +          # F 주제 2(높게)
             ['Dm', 'Dm', 'Dm', 'Dm', 'Dm', 'Dm', 'Eb', 'A7'] +          # G 숨 고르기
             ['Dm', 'Dm', 'Gm', 'A7', 'Dm', 'Bb', 'A7', 'Dm'] +          # H 주제 1
             ['Bb', 'Bb', 'Gm', 'Gm', 'Eb', 'Eb', 'A7', 'A7'])           # I 되돌이
BOSS_T1 = [[(0, 74, 3), (3, 77, 1), (4, 76, 1), (5, 74, 1)], [(0, 81, 3), (3, 79, 1.5), (4.5, 77, 1.5)],
           [(0, 79, 2), (2, 82, 1), (3, 81, 3)], [(0, 76, 3), (3, 73, 3)],
           [(0, 74, 1), (1, 76, 1), (2, 77, 1), (3, 81, 2), (5, 77, 1)], [(0, 82, 3), (3, 81, 1), (4, 79, 2)],
           [(0, 81, 2), (2, 79, 1), (3, 77, 1), (4, 76, 1), (5, 73, 1)], [(0, 74, 6)]]
BOSS_T2 = [[(0, 81, 1), (1, 86, 2), (3, 84, 1), (4, 81, 2)], [(0, 82, 1), (1, 87, 2), (3, 86, 1), (4, 82, 2)],
           [(0, 81, 3), (3, 77, 3)], [(0, 79, 1), (1, 77, 1), (2, 76, 1), (3, 73, 3)],
           [(0, 86, 3), (3, 84, 1.5), (4.5, 82, 1.5)], [(0, 82, 3), (3, 81, 1.5), (4.5, 79, 1.5)],
           [(0, 81, 2), (2, 82, 1), (3, 81, 1), (4, 80, 1), (5, 81, 1)], [(0, 81, 6)]]


@functools.lru_cache(maxsize=2)
def _boss_layers(sr):
    """보스 3국면 공통 재료(한 번만 합성). 자체 시드 — 세 파일이 같은 바탕을 공유해야 하므로 곡별 rng 를 쓰지 않는다."""
    rng = random.Random(7361)
    e = 1.0 / 6.0           # 8분음
    bar = 1.0
    bars = 72
    n = sec(sr, bar * bars)
    base, perc, dist = Bus(n), Bus(n), Bus(n)
    jit = lambda: rng.uniform(-0.004, 0.008)  # noqa: E731
    for b in range(bars):
        t0 = b * bar
        ph = b // 8
        chord, root = CH_BOSS[BOSS_PROG[b]]
        end = b % 8 == 7
        # 베이스 오스티나토: e0 근음 · e2 옥타브 · e3 5음 · e5 반음(b2) 또는 단3
        pat = ((0, 0, 1.7), (2, 12, 0.8), (3, 7, 1.7), (5, 1 if b % 2 else 3, 0.8))
        for k, iv, d in pat:
            if ph == 6 and b < 52 and k in (1, 3):      # G 숨 고르기 앞쪽은 성기게
                continue
            f = midi(root + iv)
            bus_g = 0.42 if k in (0, 2) else 0.3
            base.put(bass_bow(sr, d * e, f), t0 + k * e, sr, bus_g)
            dist.put(lowpass(bass_bow(sr, d * e, f * 2, cut=(2600, 900), drive=5.0), sr, 2200),
                     t0 + k * e, sr, 0.22, 0.0)
        # 손풍금 찌르기 e0·e3 (+ 주제 구간 e5 비틀 찌르기), D 는 떨리는 지속, G 는 쉼
        if ph == 3:
            for m in chord:
                r = reed(sr, bar + 0.05, midi(m), fc=1200)
                r = mul(r, [0.7 + 0.3 * math.sin(TAU * 7.0 * i / sr) for i in range(len(r))])
                base.put(r, t0, sr, 0.07, -0.35, width=0.01)
        elif ph != 6:
            offs = [(0, 0.11), (3, 0.09)] + ([(5, 0.06)] if ph in (1, 2, 5, 7) else [])
            for k, g in offs:
                for m in chord:
                    base.put(reed(sr, 0.2, midi(m)), t0 + k * e + jit(), sr, g, -0.35, width=0.008)
        # 기본 타악(1국면부터): 손북 e0·e3, 숟가락 e2·e5
        base.put(frame_drum(sr, rng, 1.0, 130, 72), t0, sr, 0.6)
        base.put(frame_drum(sr, rng, 0.8, 150, 82), t0 + 3 * e, sr, 0.4)
        if ph != 6:
            for k in (2, 5):
                base.put(spoons(sr, rng), t0 + k * e + jit(), sr, 0.2, 0.45)
        # E 구간 낮은 뿔나팔 (2마디마다 Bb2 → A2)
        if ph == 4 and b % 2 == 1:
            for k, m in ((3, 46), (4.5, 45)):
                h = mul(horn(sr, 1.2 * e * 1.5, midi(m), fc=800), env_adsr(sr, 1.8 * e, 0.02, 0.1, 0.7, 0.1))
                base.put(h, t0 + k * e, sr, 0.16, 0.2)
        # --- 2국면 타악 층 ---
        if ph == 6:          # 숨 고르기: 심장 박동 같은 큰 북만, 뒤쪽 4마디는 스네어가 차오름
            perc.put(big_drum(sr, rng), t0, sr, 0.7)
            perc.put(big_drum(sr, rng, 0.6), t0 + e, sr, 0.4)
            if b >= 52:
                for k in range(12):
                    perc.put(snare(sr, rng, 0.08, 0.25), t0 + k * e / 2, sr, 0.05 + 0.02 * k + 0.04 * (b - 52), 0.1)
        else:
            perc.put(big_drum(sr, rng), t0, sr, 0.85)
            if b % 2:
                perc.put(big_drum(sr, rng, 0.8), t0 + 3 * e, sr, 0.6)
            for k, p in ((1, -0.4), (4, 0.4)):
                perc.put(barrel(sr, rng), t0 + k * e + jit(), sr, 0.42, p)
            for k in range(6):
                perc.put(tambourine(sr, rng), t0 + k * e + jit(), sr, 0.15 if k in (0, 3) else 0.08, -0.5)
            perc.put(snare(sr, rng, 0.16, 0.35), t0 + 3 * e, sr, 0.3, 0.1)
            if end:
                for k in (3, 4, 5):
                    perc.put(big_drum(sr, rng, 0.9), t0 + k * e, sr, 0.5 + 0.12 * (k - 3))
                for k in range(6):
                    perc.put(snare(sr, rng, 0.08, 0.25), t0 + 3 * e + k * e / 2, sr, 0.12 + 0.04 * k, 0.1)
        # --- 3국면 왜곡 층: 삼전음 뿔나팔(D+G#) 2마디마다 e3, 8마디 끝 상승 소음 ---
        if b % 2 == 1 and ph not in (3, 6):
            for m in (50, 56):
                h = horn(sr, 2 * e, midi(m), fc=1500)
                h = softclip(mul(h, env_adsr(sr, 2 * e, 0.01, 0.1, 0.7, 0.08)), 3.0)
                dist.put(h, t0 + 3 * e, sr, 0.16, 0.25 if m == 50 else -0.25)
        if end:
            nr = sec(sr, bar)
            rs = svf(noise(sr, bar, rng), sr, sweep(sr, nr, 400, 3200), 1.5, 'band')
            rs = mul(rs, [(i / nr) ** 2 for i in range(nr)])
            dist.put(rs, t0, sr, 0.18, 0.5 if (b // 8) % 2 else -0.5)
    # 바이올린
    def play(bus, b0, rows, g, transpose=0, trem=0.0):
        for b, row in enumerate(rows):
            for off, m, d in row:
                f = midi(m + transpose) * 2 ** (rng.uniform(-0.1, 0.1) / 12.0)
                bend = rng.uniform(0.3, 0.7) if rng.random() < 0.2 else 0.0
                fd = fiddle(sr, d * e * 0.96 + 0.03, f, rng, vib=0.007, scoop=rng.uniform(0.3, 0.8), trem=trem, bend=bend)
                bus.put(fd, (b0 + b) * bar + off * e + rng.uniform(0, 0.012), sr, g, 0.3, width=0.006)
    play(base, 8, BOSS_T1, 0.2)
    play(base, 16, BOSS_T1, 0.19, transpose=5)
    play(base, 40, BOSS_T2, 0.19)
    play(base, 56, BOSS_T1, 0.2)
    spin = []
    for k in range(6):          # D: 한 마디씩 반음 내려가며 도는 8분음
        r = 74 - k
        spin.append([(j, r + iv, 1) for j, iv in enumerate((0, -1, 0, 3, 2, 0))])
    spin.append([(0, 69, 1), (1, 73, 1), (2, 76, 1), (3, 79, 1), (4, 81, 1), (5, 79, 1)])
    spin.append([(0, 77, 1), (1, 76, 1), (2, 74, 1), (3, 73, 1), (4, 76, 1), (5, 81, 1)])
    play(base, 24, spin, 0.17)
    play(base, 48, [[(0, 69, 6)], [(0, 69, 6)], [], [], [(0, 70, 6)], [(0, 69, 6)], [(0, 70, 6)], [(0, 69, 6)]],
         0.12, trem=0.4)
    play(base, 64, [[(0, 77, 6)], [(0, 77, 6)], [(0, 79, 6)], [(0, 79, 6)], [(0, 82, 6)], [(0, 82, 6)],
                    [(0, 81, 6)], [(0, 81, 3), (3, 73, 3)]], 0.16, trem=0.5)
    # 술병 부딪힘(1국면부터)
    for b in range(0, bars, 3):
        if rng.random() < 0.5:
            base.put(bottle(sr, rng), b * bar + rng.choice((1, 2, 4, 5)) * e, sr, 0.06, rng.uniform(-0.7, 0.7))
    # 낮은 D1 드론
    base.layer(lp_loop(tone_loop(sr, n, 36.71, 'saw'), sr, 90), None, 0.12)
    # 3국면 불길: 0.5 Hz 로 일렁이는 저역 불 + 타닥, 0.25 Hz 로 좌우를 돈다
    fire = Bus(n)
    roar_l = svf_loop(noise_loop(sr, n, rng), sr, 700, 0.7, 'low')
    roar_r = svf_loop(noise_loop(sr, n, rng), sr, 700, 0.7, 'low')
    wob = lfo_loop(sr, n, 0.5, 0.35, 0.65)
    rot = lfo_loop(sr, n, 0.25, 1.0, 0.0)
    fire.layer([x * w * (0.6 + 0.4 * r) for x, w, r in zip(roar_l, wob, rot)],
               [x * w * (0.6 - 0.4 * r) for x, w, r in zip(roar_r, wob, rot)], 0.3)
    cr = crackle(sr, rng, bar * bars, 520, 0.5, wrap=True)
    cr2 = crackle(sr, rng, bar * bars, 520, 0.5, wrap=True)
    fire.layer(cr, cr2, 0.4)
    # 공간
    base = reverb2(base, sr, size=1.0, decay=0.7, wet=0.22)
    perc = reverb2(perc, sr, size=0.8, decay=0.6, wet=0.15)
    dist = reverb2(dist, sr, size=0.9, decay=0.6, wet=0.18)
    p1 = base
    p2 = Bus(n)
    p2.add(base)
    p2.add(perc)
    p3 = _warp(p2, sr, depth=0.0019, rate=0.5)       # ±0.6 % 음높이 울렁임 = '세상이 돈다'(0.5 Hz, 화면 기울기와 같은 주기)
    p3.add(dist)
    p3.add(fire)
    peak = max(max(abs(v) for v in b.L + b.R) for b in (p1, p2, p3))
    return dict(p1=p1, p2=p2, p3=p3, gain=PEAK / peak)


def _warp(bus, sr, depth, rate):
    """루프 안 시간 울렁임: 지연 d(t) = depth·(1 + sin) 로 읽는 위치를 흔든다(선형 보간, 루프 감김).
    오른쪽은 위상 90° 늦춰 좌우가 엇갈리게 돈다."""
    n = bus.n
    out = Bus(n)
    cyc = max(1, round(rate * n / sr))
    for src, dst, ph in ((bus.L, out.L, 0.0), (bus.R, out.R, 0.25)):
        for i in range(n):
            d = depth * sr * (1.0 + math.sin(TAU * (cyc * i / n + ph)))
            x = i - d
            j = math.floor(x)
            fr = x - j
            dst[i] = src[j % n] * (1 - fr) + src[(j + 1) % n] * fr
    return out


def _out(bus, gain=None):
    return (bus.L, bus.R, gain)


_BOSS_NOTE = ("1층 보스 '만취' %d국면. 72 s 루프(72마디), 44.1 kHz 스테레오, D 단조 6/8(점4분 120). 세 국면이 같은 길이·박자 격자·같은 바탕이며 "
              "같은 이득으로 정규화 — 국면이 바뀌면 재생 위치를 이어 교차 페이드. ")


@bgm('f1_boss_p1', _BOSS_NOTE % 1 + "1국면(기본): 비틀거리는 베이스 오스티나토(e0 근음·e2 옥타브·e3 5음·e5 반음) + 손풍금 찌르기 + 손북·숟가락 + 취한 바이올린 주제 둘 + D 구간 반음씩 내려가며 도는 8분음 + 낮은 뿔나팔 + D1 드론. 권장 음량 0 dB(세 국면 공통) — RMS 1국면 -22.8 · 2국면 -21.1 · 3국면 -20.2 dBFS", 0.0, sr=SR2, group='f1_boss', use=dict(floor=1, state='boss', phase=1))
def _bgm_f1_boss_p1(sr, rng):
    m = _boss_layers(sr)
    return _out(m['p1'], m['gain'])


@bgm('f1_boss_p2', _BOSS_NOTE % 2 + "2국면(타악 추가): 1국면 + 큰 북(e0, 홀수 마디 e3) · 술통 '통'(e1·e4, 좌우) · 탬버린 8분음 · 스네어 e3 · 8마디 끝 북·스네어 몰아치기 · 숨 고르기 구간의 심장 박동 북", 0.0, sr=SR2, group='f1_boss', use=dict(floor=1, state='boss', phase=2))
def _bgm_f1_boss_p2(sr, rng):
    m = _boss_layers(sr)
    return _out(m['p2'], m['gain'])


@bgm('f1_boss_p3', _BOSS_NOTE % 3 + "3국면(왜곡·불): 2국면 전체를 0.5 Hz 로 울렁이게(±0.6 % 음높이, 좌우 엇갈림 — '세상이 돈다') + 옥타브 위 왜곡 베이스 + 삼전음 뿔나팔(D+G#) + 8마디 끝 상승 소음 + 좌우를 도는 불길·타닥", 0.0, sr=SR2, group='f1_boss', use=dict(floor=1, state='boss', phase=3))
def _bgm_f1_boss_p3(sr, rng):
    m = _boss_layers(sr)
    return _out(m['p3'], m['gain'])
