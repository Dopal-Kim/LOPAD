#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LOPAD 음향 파트 — 절차적 합성 빌드 스크립트 (단일 소스)

  python3 parts/sound/work/build.py            # 전부 재생성 (sfx + bgm + manifest)
  python3 parts/sound/work/build.py sfx        # 효과음만
  python3 parts/sound/work/build.py bgm        # BGM 만
  python3 parts/sound/work/build.py verify     # 생성된 파일 검증 표 출력

의존성: 파이썬 표준 라이브러리만 (wave, struct/array, math, random, json).
외부 라이브러리·네트워크 다운로드 없음. 결과는 결정적(고정 시드)이다.

출력:
  assets/audio/sfx/<이름>.wav   44.1 kHz / 16 bit / mono, 피크 -6 dBFS
  assets/audio/bgm/<이름>.wav   22.05 kHz / 16 bit / mono, 피크 -6 dBFS, 루프 가능
  assets/audio/manifest.json    시스템 파트가 읽을 목록(계약 초안)
"""
import array
import json
import math
import os
import random
import sys
import wave

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
SFX_DIR = os.path.join(ROOT, 'assets', 'audio', 'sfx')
BGM_DIR = os.path.join(ROOT, 'assets', 'audio', 'bgm')
MANIFEST = os.path.join(ROOT, 'assets', 'audio', 'manifest.json')

SR_SFX = 44100
SR_BGM = 22050
PEAK_DBFS = -6.0
PEAK = 10 ** (PEAK_DBFS / 20)  # 0.501

TAU = 2 * math.pi

# ---------------------------------------------------------------------------
# 기본 DSP 유틸 (버퍼 = float 리스트)
# ---------------------------------------------------------------------------

def zeros(n):
    return [0.0] * n


def sec(sr, t):
    return int(round(sr * t))


def mix_into(buf, seg, start, gain=1.0, wrap=False):
    """seg 를 buf[start:] 에 더한다. wrap=True 면 끝을 넘는 부분을 앞으로 감는다(루프)."""
    n = len(buf)
    if n == 0:
        return
    start = int(start)
    if not wrap:
        end = min(n, start + len(seg))
        for i in range(max(0, start), end):
            buf[i] += seg[i - start] * gain
        return
    for i, v in enumerate(seg):
        buf[(start + i) % n] += v * gain


def mul(seg, env):
    return [a * b for a, b in zip(seg, env)]


def scale(seg, g):
    return [a * g for a in seg]


def add(a, b):
    n = max(len(a), len(b))
    out = zeros(n)
    for i, v in enumerate(a):
        out[i] += v
    for i, v in enumerate(b):
        out[i] += v
    return out


def concat(*segs):
    out = []
    for s in segs:
        out.extend(s)
    return out


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)


# --- 오실레이터 -------------------------------------------------------------

def _wave_fn(kind):
    if kind == 'sine':
        return lambda p: math.sin(TAU * p)
    if kind == 'tri':
        return lambda p: 4.0 * abs(p - math.floor(p + 0.5)) - 1.0
    if kind == 'saw':
        return lambda p: 2.0 * (p - math.floor(p + 0.5))
    if kind == 'square':
        return lambda p: 1.0 if (p - math.floor(p)) < 0.5 else -1.0
    if kind == 'pulse':
        return lambda p: 1.0 if (p - math.floor(p)) < 0.25 else -1.0
    raise ValueError(kind)


def tone(sr, dur, f0, f1=None, kind='sine', phase=0.0, curve='exp'):
    """f0→f1 로 글라이드하는 단일 오실레이터. f1 이 None 이면 고정."""
    n = sec(sr, dur)
    fn = _wave_fn(kind)
    out = zeros(n)
    p = phase
    if f1 is None or f1 == f0:
        inc = f0 / sr
        for i in range(n):
            out[i] = fn(p)
            p += inc
        return out
    if curve == 'exp' and f0 > 0 and f1 > 0:
        ratio = math.log(f1 / f0)
        for i in range(n):
            f = f0 * math.exp(ratio * i / n)
            out[i] = fn(p)
            p += f / sr
    else:
        for i in range(n):
            f = f0 + (f1 - f0) * i / n
            out[i] = fn(p)
            p += f / sr
    return out


def tone_loop(sr, n, f, kind='sine', phase=0.0):
    """루프 길이 n 샘플에 정수 주기가 들어가도록 주파수를 미세 보정한 고정 톤."""
    cycles = max(1, round(f * n / sr))
    fq = cycles * sr / n
    fn = _wave_fn(kind)
    inc = fq / sr
    out = zeros(n)
    p = phase
    for i in range(n):
        out[i] = fn(p)
        p += inc
    return out


def lfo_loop(sr, n, f, depth=1.0, offset=0.0, phase=0.0):
    """루프 길이에 정수 주기로 맞춘 사인 LFO (offset + depth*sin)."""
    cycles = max(1, round(f * n / sr))
    inc = cycles / n
    out = zeros(n)
    p = phase
    for i in range(n):
        out[i] = offset + depth * math.sin(TAU * p)
        p += inc
    return out


def noise(sr, dur, rng):
    n = sec(sr, dur)
    u = rng.uniform
    return [u(-1.0, 1.0) for _ in range(n)]


def loopify(seg, n, sr, xf=0.05):
    """seg(길이 >= n + xf) 의 꼬리를 머리에 크로스페이드해 길이 n 의 루프를 만든다."""
    x = min(sec(sr, xf), len(seg) - n)
    out = seg[:n]
    for i in range(x):
        g = i / x
        out[i] = seg[i] * g + seg[n + i] * (1 - g)
    return out


def wrap2(fn, seg):
    """루프 재료용 필터 적용: seg 를 두 번 이어 처리하고 뒷절반을 취해 필터 상태가 경계에서 이어지게 한다."""
    return fn(seg + seg)[len(seg):]


def noise_loop(sr, n, rng, xf=0.05):
    """루프 길이 n 샘플에 이어지는 백색 노이즈 (끝↔처음 크로스페이드)."""
    raw = [rng.uniform(-1.0, 1.0) for _ in range(n + sec(sr, xf))]
    return loopify(raw, n, sr, xf)


def additive(sr, dur, f, partials, detune=0.0, vib_hz=0.0, vib_depth=0.0):
    """partials = [(배음비, 진폭), ...]. detune 은 비율(0.002 = 0.2%) 로 둘째 음원을 겹친다."""
    n = sec(sr, dur)
    out = zeros(n)
    sets = [(f, 1.0)]
    if detune:
        sets = [(f * (1 - detune), 0.5), (f * (1 + detune), 0.5)]
    for base, g in sets:
        for ratio, amp in partials:
            fq = base * ratio
            p = 0.0
            if vib_hz:
                for i in range(n):
                    fv = fq * (1 + vib_depth * math.sin(TAU * vib_hz * i / sr))
                    out[i] += amp * g * math.sin(TAU * p)
                    p += fv / sr
            else:
                inc = fq / sr
                for i in range(n):
                    out[i] += amp * g * math.sin(TAU * p)
                    p += inc
    return out


def pluck(sr, dur, f, rng, damp=0.996, bright=1.0):
    """Karplus-Strong 현 (류트·활시위). bright<1 이면 초기 노이즈를 저역통과."""
    n = sec(sr, dur)
    N = max(2, int(sr / f))
    buf = [rng.uniform(-1, 1) for _ in range(N)]
    if bright < 1.0:
        y = 0.0
        for i in range(N):
            y += bright * (buf[i] - y)
            buf[i] = y
    out = zeros(n)
    i = 0
    for k in range(n):
        v = buf[i]
        nxt = buf[(i + 1) % N]
        buf[i] = damp * 0.5 * (v + nxt)
        out[k] = v
        i += 1
        if i == N:
            i = 0
    return out


# --- 엔벌로프 ---------------------------------------------------------------

def env_exp(sr, dur, tau, start=1.0):
    n = sec(sr, dur)
    k = math.exp(-1.0 / (tau * sr))
    out = zeros(n)
    v = start
    for i in range(n):
        out[i] = v
        v *= k
    return out


def env_adsr(sr, dur, a, d, s, r, curve=1.0):
    n = sec(sr, dur)
    na, nd, nr = sec(sr, a), sec(sr, d), sec(sr, r)
    ns = max(0, n - na - nd - nr)
    out = zeros(n)
    i = 0
    for k in range(na):
        if i >= n:
            break
        out[i] = (k / max(1, na)) ** curve
        i += 1
    for k in range(nd):
        if i >= n:
            break
        out[i] = 1.0 + (s - 1.0) * (k / max(1, nd))
        i += 1
    for k in range(ns):
        if i >= n:
            break
        out[i] = s
        i += 1
    lvl = out[i - 1] if i > 0 else s
    for k in range(nr):
        if i >= n:
            break
        out[i] = lvl * (1.0 - k / max(1, nr))
        i += 1
    return out


def env_lin(sr, dur, a, r):
    """선형 어택·릴리즈, 중간은 1.0."""
    return env_adsr(sr, dur, a, 0.0, 1.0, r)


def fade_edges(seg, sr, t=0.004):
    n = min(len(seg) // 2, sec(sr, t))
    for i in range(n):
        g = i / n
        seg[i] *= g
        seg[-1 - i] *= g
    return seg


# --- 필터 -------------------------------------------------------------------

def lowpass(seg, sr, fc):
    """1차 저역통과. fc 가 리스트면 샘플별 컷오프."""
    out = zeros(len(seg))
    y = 0.0
    if isinstance(fc, (int, float)):
        a = 1.0 - math.exp(-TAU * fc / sr)
        for i, x in enumerate(seg):
            y += a * (x - y)
            out[i] = y
    else:
        e = math.exp
        for i, x in enumerate(seg):
            a = 1.0 - e(-TAU * fc[i] / sr)
            y += a * (x - y)
            out[i] = y
    return out


def highpass(seg, sr, fc):
    lp = lowpass(seg, sr, fc)
    return [x - l for x, l in zip(seg, lp)]


def svf(seg, sr, fc, q=1.0, mode='band'):
    """RBJ 바이쿼드 필터 (어떤 컷오프에서도 안정). fc 는 상수 또는 샘플별 리스트.
    mode: low/band/high. band 는 공진 이득 = Q (skirt 일정형)."""
    n = len(seg)
    out = zeros(n)
    Q = max(0.3, q)
    hi = 0.45 * sr
    cos, sin, pi = math.cos, math.sin, math.pi

    def coef(f):
        f = min(max(10.0, f), hi)
        w0 = TAU * f / sr
        c = cos(w0)
        sn = sin(w0)
        alpha = sn / (2 * Q)
        a0 = 1 + alpha
        if mode == 'low':
            b0 = (1 - c) / 2
            b1 = 1 - c
            b2 = b0
        elif mode == 'high':
            b0 = (1 + c) / 2
            b1 = -(1 + c)
            b2 = b0
        else:
            b0 = sn / 2
            b1 = 0.0
            b2 = -sn / 2
        return b0 / a0, b1 / a0, b2 / a0, (-2 * c) / a0, (1 - alpha) / a0

    x1 = x2 = y1 = y2 = 0.0
    if isinstance(fc, (int, float)):
        b0, b1, b2, a1, a2 = coef(fc)
        for i in range(n):
            x = seg[i]
            y = b0 * x + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
            x2, x1 = x1, x
            y2, y1 = y1, y
            out[i] = y
        return out
    for i in range(n):
        b0, b1, b2, a1, a2 = coef(fc[i])
        x = seg[i]
        y = b0 * x + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
        x2, x1 = x1, x
        y2, y1 = y1, y
        out[i] = y
    return out


def sweep(sr, n, f0, f1, curve='exp'):
    """샘플별 컷오프 배열."""
    if curve == 'exp':
        r = math.log(f1 / f0)
        return [f0 * math.exp(r * i / n) for i in range(n)]
    return [f0 + (f1 - f0) * i / n for i in range(n)]


def softclip(seg, drive=1.0):
    th = math.tanh
    return [th(x * drive) for x in seg]


# --- 공간계 (딜레이 합산 리버브) --------------------------------------------

def _comb(seg, delay, fb, damp=0.2):
    n = len(seg)
    out = zeros(n)
    buf = zeros(delay)
    idx = 0
    store = 0.0
    for i in range(n):
        y = buf[idx]
        store = y * (1 - damp) + store * damp
        buf[idx] = seg[i] + store * fb
        idx += 1
        if idx == delay:
            idx = 0
        out[i] = y
    return out


def _allpass(seg, delay, g=0.5):
    n = len(seg)
    out = zeros(n)
    buf = zeros(delay)
    idx = 0
    for i in range(n):
        b = buf[idx]
        x = seg[i]
        y = -x + b
        buf[idx] = x + b * g
        idx += 1
        if idx == delay:
            idx = 0
        out[i] = y
    return out


def reverb(seg, sr, size=1.0, decay=0.75, wet=0.3, damp=0.3, loop=False, predelay=0.0):
    """Schroeder 식 리버브(병렬 콤 4 + 직렬 올패스 2). loop=True 면 꼬리를 앞으로 감는다."""
    src = seg + seg if loop else seg
    n = len(src)
    if predelay > 0:
        pd = sec(sr, predelay)
        src = zeros(pd) + src[:-pd] if pd < n else src
    combs = [0.0297, 0.0371, 0.0411, 0.0437]
    acc = zeros(n)
    for c in combs:
        d = max(2, int(c * size * sr))
        o = _comb(src, d, decay, damp)
        for i in range(n):
            acc[i] += o[i]
    acc = _allpass(acc, max(2, int(0.005 * sr)))
    acc = _allpass(acc, max(2, int(0.0017 * sr)))
    g = wet * 0.25
    out = [x * (1 - wet * 0.5) + a * g for x, a in zip(src, acc)]
    if loop:
        return out[len(seg):]
    return out


def echo(seg, sr, time, fb=0.4, wet=0.3, loop=False, lp=3000):
    src = seg + seg if loop else seg
    n = len(src)
    d = sec(sr, time)
    out = list(src)
    a = 1.0 - math.exp(-TAU * lp / sr)
    y = 0.0
    for i in range(d, n):
        y += a * (out[i - d] - y)
        out[i] += y * fb
    out = [s * (1 - wet) + (o - s) * wet for s, o in zip(src, out)]
    if loop:
        return out[len(seg):]
    return out


def tail(seg, sr, t):
    """뒤에 무음 t 초를 붙인다 (리버브 꼬리용)."""
    return seg + zeros(sec(sr, t))


# --- 출력 -------------------------------------------------------------------

def normalize(seg, peak=PEAK):
    m = max(abs(x) for x in seg) if seg else 0.0
    if m <= 1e-9:
        return seg
    g = peak / m
    return [x * g for x in seg]


def dc_remove(seg):
    if not seg:
        return seg
    m = sum(seg) / len(seg)
    return [x - m for x in seg]


def write_wav(path, seg, sr):
    seg = normalize(dc_remove(seg))
    ints = array.array('h', [int(max(-32767, min(32767, round(x * 32767)))) for x in seg])
    if sys.byteorder == 'big':
        ints.byteswap()
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(ints.tobytes())
    return len(seg) / sr


# ---------------------------------------------------------------------------
# 악기 (재료별 질감 프리셋)
# ---------------------------------------------------------------------------

def thud(sr, dur=0.18, f0=140, f1=50, tau=0.06):
    """목재·몸통 둔탁음: 피치 하강 사인."""
    return mul(tone(sr, dur, f0, f1), env_exp(sr, dur, tau))


def metal(sr, dur, base, rng, partials=None, tau=0.25, jitter=0.01):
    """강철 울림: 비조화 배음 합."""
    if partials is None:
        partials = [(1.0, 1.0), (1.47, 0.6), (2.09, 0.5), (2.56, 0.35), (3.73, 0.2), (5.11, 0.12)]
    n = sec(sr, dur)
    out = zeros(n)
    for ratio, amp in partials:
        f = base * ratio * (1 + rng.uniform(-jitter, jitter))
        e = env_exp(sr, dur, tau * (1.0 / math.sqrt(ratio)))
        p = 0.0
        inc = f / sr
        for i in range(n):
            out[i] += amp * e[i] * math.sin(TAU * p)
            p += inc
    return out


def burst(sr, dur, rng, fc=3000, q=0.8, tau=0.03, mode='band'):
    """노이즈 버스트 + 필터 + 지수 감쇠 (화약·타격)."""
    nz = noise(sr, dur, rng)
    nz = svf(nz, sr, fc, q, mode)
    return mul(nz, env_exp(sr, dur, tau))


def whoosh(sr, dur, rng, f0, f1, q=1.2, a=0.3, r=0.5):
    """공기 가르는 소리: 밴드패스 스윕 노이즈."""
    n = sec(sr, dur)
    nz = noise(sr, dur, rng)
    nz = svf(nz, sr, sweep(sr, n, f0, f1), q, 'band')
    return mul(nz, env_adsr(sr, dur, dur * a, 0.0, 1.0, dur * r))


def click(sr, rng, dur=0.004, fc=4000):
    return burst(sr, dur, rng, fc=fc, q=0.5, tau=0.0015)


def kick(sr, dur=0.35, f0=130, f1=42, tau=0.09, click_g=0.3, rng=None):
    k = thud(sr, dur, f0, f1, tau)
    if rng is not None and click_g > 0:
        mix_into(k, click(sr, rng, 0.003, 2500), 0, click_g)
    return k


def snare(sr, rng, dur=0.18, tone_g=0.4):
    nz = burst(sr, dur, rng, fc=1800, q=0.6, tau=0.045, mode='high')
    t = mul(tone(sr, dur, 220, 160), env_exp(sr, dur, 0.03))
    mix_into(nz, t, 0, tone_g)
    return nz


def handdrum(sr, rng, dur=0.25, f0=180, f1=95, slap=0.3):
    d = thud(sr, dur, f0, f1, 0.07)
    mix_into(d, burst(sr, 0.05, rng, fc=1200, q=0.7, tau=0.012), 0, slap)
    return d


def bell(sr, dur, f, rng, tau=0.9):
    return metal(sr, dur, f, rng,
                 partials=[(1.0, 1.0), (2.0, 0.45), (2.76, 0.4), (4.07, 0.2), (5.4, 0.12)],
                 tau=tau, jitter=0.002)


def organ(sr, dur, f, detune=0.0025):
    return additive(sr, dur, f,
                    [(1, 1.0), (2, 0.55), (3, 0.3), (4, 0.22), (6, 0.1), (8, 0.06)],
                    detune=detune)


def flute(sr, dur, f):
    return additive(sr, dur, f, [(1, 1.0), (2, 0.25), (3, 0.08)],
                    vib_hz=4.6, vib_depth=0.004)


def horn(sr, dur, f, fc=900):
    s = tone(sr, dur, f, kind='saw')
    s2 = tone(sr, dur, f * 1.003, kind='saw')
    s = add(s, s2)
    return lowpass(s, sr, fc)


# ---------------------------------------------------------------------------
# 효과음 정의
# 각 함수는 (buf, sr, loop) 를 돌려준다.
# ---------------------------------------------------------------------------

SFX = {}


def sfx(name, trigger, note, gain_db=0.0, loop=False, category='combat'):
    def deco(fn):
        SFX[name] = dict(fn=fn, trigger=trigger, note=note, gain_db=gain_db, loop=loop, category=category)
        return fn
    return deco


# --- 무기 ---------------------------------------------------------------------

@sfx('swing_katana', 'PLAYER_ATTACK{weapon:katana}', '사무라이 칼 휘두름. 얇고 빠른 강철 바람', -2)
def _swing_katana(sr, rng):
    w = whoosh(sr, 0.17, rng, 5200, 1400, q=1.6, a=0.15, r=0.55)
    mix_into(w, metal(sr, 0.12, 2400, rng, tau=0.05, jitter=0.02), sec(sr, 0.02), 0.12)
    return tail(w, sr, 0.03)


@sfx('swing_greatsword', 'PLAYER_ATTACK{weapon:greatsword}', '대검 휘두름. 무겁고 낮은 바람, 끝에 둔탁한 무게', -1)
def _swing_greatsword(sr, rng):
    w = whoosh(sr, 0.34, rng, 900, 180, q=1.0, a=0.35, r=0.45)
    mix_into(w, thud(sr, 0.18, 110, 45, 0.06), sec(sr, 0.2), 0.7)
    mix_into(w, burst(sr, 0.1, rng, fc=600, q=0.7, tau=0.03, mode='low'), sec(sr, 0.21), 0.5)
    return tail(w, sr, 0.05)


@sfx('swing_dagger', 'PLAYER_ATTACK{weapon:dagger}', '단검. 아주 짧고 높은 스침', -3)
def _swing_dagger(sr, rng):
    w = whoosh(sr, 0.09, rng, 7000, 2500, q=1.8, a=0.1, r=0.5)
    mix_into(w, click(sr, rng, 0.003, 6000), 0, 0.4)
    return tail(w, sr, 0.02)


@sfx('bow_shot', 'PLAYER_ATTACK{weapon:bow}', '활 발사. 시위 튕김 + 화살 바람', -2)
def _bow_shot(sr, rng):
    s = pluck(sr, 0.25, 190, rng, damp=0.985, bright=0.7)
    s = mul(s, env_exp(sr, 0.25, 0.08))
    mix_into(s, whoosh(sr, 0.14, rng, 2500, 6000, q=1.2, a=0.2, r=0.6), sec(sr, 0.01), 0.35)
    mix_into(s, thud(sr, 0.08, 220, 120, 0.02), 0, 0.5)
    return tail(s, sr, 0.05)


@sfx('bow_aimed', 'PLAYER_SECONDARY{kind:aimedshot,phase:release}', '조준 사격 발사. 깊은 시위 + 꿰뚫는 바람', -1)
def _bow_aimed(sr, rng):
    s = pluck(sr, 0.4, 110, rng, damp=0.99, bright=0.6)
    s = mul(s, env_exp(sr, 0.4, 0.12))
    mix_into(s, whoosh(sr, 0.3, rng, 1800, 7000, q=1.0, a=0.1, r=0.7), sec(sr, 0.01), 0.5)
    mix_into(s, thud(sr, 0.12, 180, 70, 0.03), 0, 0.7)
    return tail(s, sr, 0.08)


@sfx('bow_draw', 'PLAYER_SECONDARY{kind:aimedshot,phase:start}', '조준 사격 시위 당기기(600ms 차지에 맞춤). 삐걱이는 나무·현', -8)
def _bow_draw(sr, rng):
    n = sec(sr, 0.6)
    s = tone(sr, 0.6, 70, 95, kind='saw')
    s = svf(s, sr, sweep(sr, n, 400, 1200), 2.0, 'band')
    s = mul(s, env_adsr(sr, 0.6, 0.1, 0.0, 1.0, 0.08))
    nz = noise(sr, 0.6, rng)
    nz = svf(nz, sr, 2200, 1.0, 'band')
    trem = [0.5 + 0.5 * math.sin(TAU * 28 * i / sr) for i in range(n)]
    nz = mul(mul(nz, trem), env_adsr(sr, 0.6, 0.1, 0.0, 1.0, 0.08))
    mix_into(s, nz, 0, 0.35)
    return s


# --- 타격 ---------------------------------------------------------------------

@sfx('hit_enemy', 'ENEMY_DAMAGED', '적 피격. 날이 박히는 짧은 타격 + 몸통 둔탁음', 0)
def _hit_enemy(sr, rng):
    h = burst(sr, 0.12, rng, fc=2200, q=0.7, tau=0.02)
    mix_into(h, thud(sr, 0.14, 160, 60, 0.04), 0, 0.9)
    mix_into(h, burst(sr, 0.06, rng, fc=500, q=0.6, tau=0.015, mode='low'), sec(sr, 0.005), 0.6)
    return tail(h, sr, 0.03)


@sfx('hit_enemy_crit', 'ENEMY_DAMAGED{crit:true}', '급소 적중. 피격음 위에 밝은 강철 울림', 0)
def _hit_enemy_crit(sr, rng):
    h = _hit_enemy(sr, rng)
    mix_into(h, metal(sr, 0.3, 1800, rng, tau=0.08), sec(sr, 0.005), 0.5)
    return tail(h, sr, 0.1)


@sfx('hit_player', 'PLAYER_DAMAGED', '주인공 피격. 무거운 충격 + 갑옷 쇳소리 + 저역 울림', 0)
def _hit_player(sr, rng):
    h = thud(sr, 0.3, 120, 38, 0.08)
    mix_into(h, burst(sr, 0.1, rng, fc=900, q=0.7, tau=0.025), 0, 0.8)
    mix_into(h, metal(sr, 0.25, 900, rng, tau=0.06, jitter=0.03), sec(sr, 0.004), 0.35)
    h = softclip(h, 1.6)
    return tail(h, sr, 0.05)


@sfx('parry', 'PARRY_SUCCESS', '패링 성공. 강철이 맞부딪히는 밝은 울림(오래 남는다)', 0)
def _parry(sr, rng):
    p = metal(sr, 0.6, 1500, rng, tau=0.22, jitter=0.015)
    mix_into(p, metal(sr, 0.5, 2600, rng, tau=0.12, jitter=0.02), 0, 0.5)
    mix_into(p, click(sr, rng, 0.005, 5000), 0, 1.2)
    mix_into(p, burst(sr, 0.08, rng, fc=3500, q=0.5, tau=0.012), 0, 0.6)
    p = reverb(p, sr, size=0.6, decay=0.6, wet=0.25)
    return p


@sfx('guard_hold', 'PLAYER_SECONDARY{kind:guard,phase:hold}', '가드 유지 루프. 낮은 긴장 울림 + 강철 떨림(누르는 동안 반복)', -10, loop=True)
def _guard_hold(sr, rng):
    dur = 0.6
    n = sec(sr, dur)
    g = wrap2(lambda x: lowpass(x, sr, 140), tone_loop(sr, n, 62, 'saw'))
    rum = wrap2(lambda x: svf(x, sr, 220, 0.9, 'low'), noise_loop(sr, n, rng))
    trem = lfo_loop(sr, n, 10.0, 0.4, 0.6)
    rum = mul(rum, trem)
    mix_into(g, rum, 0, 0.9)
    hum = tone_loop(sr, n, 1240, 'sine')
    hum = mul(hum, lfo_loop(sr, n, 6.7, 0.5, 0.5, 0.25))
    mix_into(g, hum, 0, 0.05)
    return g


@sfx('guard_push', 'PLAYER_SECONDARY{kind:guard,phase:release}', '가드 해제 밀치기. 낮은 폭발적 압력 + 바람', 0)
def _guard_push(sr, rng):
    p = thud(sr, 0.4, 95, 28, 0.1)
    mix_into(p, whoosh(sr, 0.3, rng, 300, 1500, q=0.8, a=0.05, r=0.7), 0, 0.8)
    mix_into(p, burst(sr, 0.12, rng, fc=700, q=0.6, tau=0.03, mode='low'), 0, 0.8)
    p = softclip(p, 1.5)
    return tail(p, sr, 0.08)


@sfx('shadowstep', 'PLAYER_SECONDARY{kind:shadowstep}', '그림자 걸음. 숨 빨려드는 역방향 바람 + 낮은 음이 꺼진다', -2)
def _shadowstep(sr, rng):
    n = sec(sr, 0.32)
    nz = noise(sr, 0.32, rng)
    nz = svf(nz, sr, sweep(sr, n, 600, 4500), 1.5, 'band')
    env = [((i / n) ** 2.2) if i < n * 0.8 else max(0.0, 1 - (i - n * 0.8) / (n * 0.2)) for i in range(n)]
    nz = mul(nz, env)
    t = mul(tone(sr, 0.32, 240, 60), env_adsr(sr, 0.32, 0.15, 0.0, 1.0, 0.12))
    mix_into(nz, t, 0, 0.5)
    mix_into(nz, click(sr, rng, 0.004, 3000), sec(sr, 0.26), 0.5)
    return reverb(tail(nz, sr, 0.1), sr, size=0.5, decay=0.5, wet=0.2)


@sfx('dash', 'PLAYER_DASH', '대쉬. 짧은 상승 바람 + 발 디딤', -3)
def _dash(sr, rng):
    w = whoosh(sr, 0.2, rng, 700, 3200, q=1.1, a=0.2, r=0.5)
    mix_into(w, thud(sr, 0.06, 150, 80, 0.015), 0, 0.5)
    return tail(w, sr, 0.03)


# --- 획득·소모 ------------------------------------------------------------------

@sfx('pickup_gold', 'GOLD_CHANGED{delta>0}', '동전 획득. 작은 금속 두 번 울림', -4, category='pickup')
def _pickup_gold(sr, rng):
    c = metal(sr, 0.22, 2900, rng, partials=[(1, 1), (1.9, 0.5), (3.4, 0.25)], tau=0.05, jitter=0.01)
    c2 = metal(sr, 0.2, 3700, rng, partials=[(1, 1), (1.9, 0.5), (3.4, 0.25)], tau=0.045, jitter=0.01)
    mix_into(c, c2, sec(sr, 0.07), 0.8)
    mix_into(c, click(sr, rng, 0.002, 7000), 0, 0.4)
    return tail(c, sr, 0.05)


@sfx('pickup_potion', 'ITEM_PICKUP{item:potion}', '물약 획득. 유리병 맑은 울림 + 액체 흔들림', -4, category='pickup')
def _pickup_potion(sr, rng):
    g = metal(sr, 0.3, 2100, rng, partials=[(1, 1), (2.4, 0.4), (3.9, 0.15)], tau=0.08, jitter=0.003)
    liq = mul(tone(sr, 0.12, 500, 900), env_exp(sr, 0.12, 0.03))
    mix_into(g, liq, sec(sr, 0.06), 0.3)
    mix_into(g, click(sr, rng, 0.002, 5000), 0, 0.5)
    return tail(g, sr, 0.05)


@sfx('potion_use', 'PLAYER_HEALED', '물약 마심. 병 뚜껑, 꿀꺽 두 번, 짧은 숨', -3, category='pickup')
def _potion_use(sr, rng):
    s = zeros(sec(sr, 0.5))
    mix_into(s, click(sr, rng, 0.004, 3500), 0, 0.7)
    for k, t0 in enumerate([0.1, 0.24]):
        gulp = mul(tone(sr, 0.1, 180 + 40 * k, 420 + 60 * k), env_adsr(sr, 0.1, 0.02, 0.0, 1.0, 0.05))
        gulp = lowpass(gulp, sr, 900)
        mix_into(s, gulp, sec(sr, t0), 0.9)
    breath = mul(svf(noise(sr, 0.14, rng), sr, 1800, 0.6, 'band'), env_adsr(sr, 0.14, 0.03, 0, 1, 0.08))
    mix_into(s, breath, sec(sr, 0.36), 0.25)
    return s


@sfx('shop_buy', 'SHOP_PURCHASE', '상점 구매. 동전 몇 개 떨어지고 나무 좌판 두드림', -4, category='pickup')
def _shop_buy(sr, rng):
    s = zeros(sec(sr, 0.45))
    for k, t0 in enumerate([0.0, 0.05, 0.12]):
        c = metal(sr, 0.2, 2600 + 500 * k, rng, partials=[(1, 1), (1.9, 0.5), (3.4, 0.25)], tau=0.04, jitter=0.01)
        mix_into(s, c, sec(sr, t0), 0.7)
    mix_into(s, thud(sr, 0.12, 300, 140, 0.02), sec(sr, 0.22), 0.8)
    mix_into(s, burst(sr, 0.05, rng, fc=1500, q=0.7, tau=0.01), sec(sr, 0.22), 0.4)
    return s


# --- 맵·문 -------------------------------------------------------------------------

@sfx('door_close', 'ROOM_ENTERED{type:trial}', '시련 방 문 잠김. 두꺼운 나무 문 + 쇠 걸쇠', -1, category='world')
def _door_close(sr, rng):
    d = thud(sr, 0.3, 95, 40, 0.07)
    mix_into(d, burst(sr, 0.15, rng, fc=400, q=0.6, tau=0.04, mode='low'), 0, 1.0)
    mix_into(d, metal(sr, 0.25, 1300, rng, tau=0.05, jitter=0.02), sec(sr, 0.09), 0.35)
    mix_into(d, click(sr, rng, 0.005, 2500), sec(sr, 0.09), 0.8)
    return reverb(tail(d, sr, 0.15), sr, size=0.8, decay=0.6, wet=0.2)


@sfx('door_open', 'ROOM_CLEARED', '방 클리어, 문 열림. 걸쇠 풀림 + 나무 삐걱', -3, category='world')
def _door_open(sr, rng):
    n = sec(sr, 0.5)
    s = zeros(n + sec(sr, 0.2))
    mix_into(s, click(sr, rng, 0.006, 2200), 0, 0.9)
    mix_into(s, metal(sr, 0.2, 1100, rng, tau=0.04, jitter=0.02), 0, 0.3)
    creak = tone(sr, 0.4, 85, 130, kind='saw')
    creak = svf(creak, sr, sweep(sr, sec(sr, 0.4), 500, 1600), 2.5, 'band')
    creak = mul(creak, env_adsr(sr, 0.4, 0.08, 0.0, 1.0, 0.15))
    mix_into(s, creak, sec(sr, 0.08), 0.6)
    return reverb(s, sr, size=0.7, decay=0.5, wet=0.15)


@sfx('boss_unlock', 'STORY{kind:notice,bossUnlocked}', '본영 문 열림. 쇠사슬 세 번 + 무거운 울림', 0, category='world')
def _boss_unlock(sr, rng):
    s = zeros(sec(sr, 1.2))
    for k, t0 in enumerate([0.0, 0.18, 0.4]):
        m = metal(sr, 0.5, 700 + 90 * k, rng, tau=0.12, jitter=0.03)
        mix_into(s, m, sec(sr, t0), 0.7)
        mix_into(s, burst(sr, 0.06, rng, fc=2500, q=0.5, tau=0.01), sec(sr, t0), 0.6)
    mix_into(s, thud(sr, 0.6, 80, 30, 0.18), sec(sr, 0.62), 1.3)
    mix_into(s, burst(sr, 0.3, rng, fc=300, q=0.6, tau=0.08, mode='low'), sec(sr, 0.62), 1.0)
    return reverb(s, sr, size=1.2, decay=0.75, wet=0.3)


@sfx('exit_open', 'STORY{kind:notice,exitOpened}', '오르는 길 열림. 돌이 미끄러지는 긴 마찰 + 낮게 울리는 종', -1, category='world')
def _exit_open(sr, rng):
    n = sec(sr, 0.9)
    s = noise(sr, 0.9, rng)
    s = svf(s, sr, sweep(sr, n, 250, 900), 0.8, 'low')
    s = mul(s, env_adsr(sr, 0.9, 0.2, 0.0, 1.0, 0.35))
    s = tail(s, sr, 0.5)
    mix_into(s, thud(sr, 0.4, 70, 40, 0.1), sec(sr, 0.75), 0.9)
    mix_into(s, bell(sr, 0.8, 330, rng, tau=0.4), sec(sr, 0.8), 0.25)
    return reverb(s, sr, size=1.1, decay=0.7, wet=0.3)


@sfx('level_enter', 'STAGE_STARTED', '층 진입. 멀리서 북 한 번, 바람, 낮은 드론이 잠깐 부푼다', -2, category='world')
def _level_enter(sr, rng):
    dur = 1.8
    n = sec(sr, dur)
    s = zeros(n)
    wind = svf(noise(sr, dur, rng), sr, 500, 0.7, 'low')
    wind = mul(wind, env_adsr(sr, dur, 0.5, 0.0, 1.0, 1.0))
    mix_into(s, wind, 0, 0.5)
    dr = lowpass(tone(sr, dur, 55, kind='saw'), sr, 180)
    dr = mul(dr, env_adsr(sr, dur, 0.4, 0.0, 1.0, 1.0))
    mix_into(s, dr, 0, 0.6)
    k = lowpass(kick(sr, 0.5, 100, 36, 0.14), sr, 300)
    mix_into(s, k, sec(sr, 0.25), 1.2)
    return reverb(s, sr, size=1.4, decay=0.8, wet=0.4)


@sfx('save', 'STORY{kind:notice,saved}', '기록 저장. 깃펜이 종이를 긁는 짧은 소리 두 번', -8, category='ui')
def _save(sr, rng):
    s = zeros(sec(sr, 0.55))
    for t0, d in [(0.0, 0.18), (0.24, 0.22)]:
        n = sec(sr, d)
        sc = svf(noise(sr, d, rng), sr, sweep(sr, n, 3000, 5500), 1.5, 'band')
        trem = [0.6 + 0.4 * math.sin(TAU * 40 * i / sr) for i in range(n)]
        sc = mul(mul(sc, trem), env_adsr(sr, d, 0.02, 0.0, 1.0, 0.05))
        mix_into(s, sc, sec(sr, t0), 1.0)
    return s


# --- UI ----------------------------------------------------------------------------

@sfx('menu_move', 'UI_MENU_MOVE', '메뉴 이동. 나무를 톡 건드리는 작은 소리', -8, category='ui')
def _menu_move(sr, rng):
    s = mul(tone(sr, 0.05, 900, 700), env_exp(sr, 0.05, 0.012))
    mix_into(s, click(sr, rng, 0.003, 3000), 0, 0.6)
    return tail(s, sr, 0.02)


@sfx('menu_select', 'UI_MENU_SELECT', '메뉴 선택. 도장 찍는 둔탁음 + 짧은 쇠 틱', -6, category='ui')
def _menu_select(sr, rng):
    s = thud(sr, 0.12, 260, 120, 0.025)
    mix_into(s, mul(tone(sr, 0.08, 1300), env_exp(sr, 0.08, 0.015)), sec(sr, 0.01), 0.35)
    mix_into(s, click(sr, rng, 0.003, 4000), 0, 0.5)
    return tail(s, sr, 0.03)


@sfx('menu_cancel', 'UI_MENU_CANCEL', '메뉴 닫기/뒤로. 종이 넘기는 짧은 스침', -8, category='ui')
def _menu_cancel(sr, rng):
    n = sec(sr, 0.12)
    s = svf(noise(sr, 0.12, rng), sr, sweep(sr, n, 2500, 900), 0.9, 'band')
    s = mul(s, env_adsr(sr, 0.12, 0.02, 0.0, 1.0, 0.06))
    return tail(s, sr, 0.02)


# --- 성장·연출 ----------------------------------------------------------------------

@sfx('evolve', 'WEAPON_EVOLVED', '개성 변화. 낮게 부푸는 드론 위로 종 같은 상승 아르페지오(이질적·신비)', -1, category='event')
def _evolve(sr, rng):
    dur = 1.6
    s = zeros(sec(sr, dur))
    dr = lowpass(tone(sr, 1.2, 73.4, 110, kind='saw'), sr, 400)
    dr = mul(dr, env_adsr(sr, 1.2, 0.5, 0.0, 1.0, 0.5))
    mix_into(s, dr, 0, 0.5)
    for k, m in enumerate([62, 69, 74, 81, 86]):
        b = bell(sr, 1.0, midi(m), rng, tau=0.35)
        mix_into(s, b, sec(sr, 0.15 + 0.13 * k), 0.5 - 0.04 * k)
    mix_into(s, whoosh(sr, 0.9, rng, 800, 6000, q=0.9, a=0.6, r=0.3), 0, 0.25)
    return reverb(s, sr, size=1.3, decay=0.8, wet=0.4)


@sfx('reinforce', 'WEAPON_REINFORCED', '무기 강화. 모루 위 망치질 한 번 + 쇠 울림', -2, category='event')
def _reinforce(sr, rng):
    s = metal(sr, 0.6, 1050, rng, tau=0.18, jitter=0.01)
    mix_into(s, thud(sr, 0.15, 200, 80, 0.03), 0, 0.9)
    mix_into(s, burst(sr, 0.05, rng, fc=4000, q=0.5, tau=0.008), 0, 0.9)
    return reverb(s, sr, size=0.8, decay=0.6, wet=0.2)


@sfx('fate_decided', 'FATE_DECIDED', '운명(무기) 결정. 일기장 덮는 둔탁음 + 낮은 종 한 번', -2, category='event')
def _fate_decided(sr, rng):
    s = thud(sr, 0.3, 150, 60, 0.06)
    mix_into(s, burst(sr, 0.1, rng, fc=800, q=0.6, tau=0.03, mode='low'), 0, 0.7)
    s = tail(s, sr, 1.0)
    mix_into(s, bell(sr, 1.0, 220, rng, tau=0.5), sec(sr, 0.12), 0.45)
    return reverb(s, sr, size=1.2, decay=0.75, wet=0.35)


@sfx('trial_clear', 'STORY{kind:notice,trialClear}', '시련 끝. 짧은 북 두 번, 낮은 울림', -3, category='event')
def _trial_clear(sr, rng):
    s = zeros(sec(sr, 0.8))
    mix_into(s, lowpass(kick(sr, 0.35, 120, 45, 0.1, rng=rng), sr, 500), 0, 1.0)
    mix_into(s, lowpass(kick(sr, 0.5, 100, 38, 0.14, rng=rng), sr, 500), sec(sr, 0.22), 1.2)
    return reverb(s, sr, size=1.1, decay=0.7, wet=0.3)


# --- 보스 -------------------------------------------------------------------------

@sfx('boss_start', 'BOSS_STARTED', '보스 등장. 큰 북 한 번 + 낮은 쇠 울림 + 서늘한 고음 한 가닥', 0, category='boss')
def _boss_start(sr, rng):
    s = zeros(sec(sr, 1.6))
    mix_into(s, kick(sr, 0.6, 110, 34, 0.18, rng=rng), 0, 1.3)
    mix_into(s, burst(sr, 0.4, rng, fc=250, q=0.6, tau=0.1, mode='low'), 0, 0.9)
    mix_into(s, metal(sr, 1.2, 420, rng, tau=0.4, jitter=0.02), sec(sr, 0.02), 0.5)
    hi = mul(tone(sr, 1.2, 2900, 3100), env_adsr(sr, 1.2, 0.5, 0, 1, 0.6))
    mix_into(s, hi, sec(sr, 0.3), 0.06)
    return reverb(s, sr, size=1.4, decay=0.8, wet=0.35)


@sfx('boss_phase', 'BOSS_PHASE', '보스 국면 전환. 낮은 북 + 불협 쇳소리 부풀기', 0, category='boss')
def _boss_phase(sr, rng):
    s = zeros(sec(sr, 1.3))
    mix_into(s, kick(sr, 0.5, 95, 30, 0.16, rng=rng), 0, 1.3)
    m = metal(sr, 1.1, 310, rng, partials=[(1, 1), (1.41, 0.8), (2.12, 0.6), (2.83, 0.4), (4.24, 0.2)], tau=0.5)
    m = mul(m, env_adsr(sr, 1.1, 0.35, 0.0, 1.0, 0.5))
    mix_into(s, m, sec(sr, 0.05), 0.8)
    mix_into(s, whoosh(sr, 0.8, rng, 300, 2500, q=0.8, a=0.7, r=0.3), 0, 0.35)
    return reverb(s, sr, size=1.3, decay=0.8, wet=0.35)


@sfx('boss_telegraph', 'BOSS_TELEGRAPH{attack:dash}', '보스 돌진 예고(≈650ms). 낮게 울리며 올라가는 으르렁 + 쇠 긁힘', -2, category='boss')
def _boss_telegraph(sr, rng):
    dur = 0.65
    n = sec(sr, dur)
    g = tone(sr, dur, 55, 140, kind='saw')
    g = svf(g, sr, sweep(sr, n, 200, 900), 1.5, 'low')
    g = mul(g, env_adsr(sr, dur, 0.1, 0.0, 1.0, 0.06))
    sc = svf(noise(sr, dur, rng), sr, sweep(sr, n, 1500, 4000), 2.0, 'band')
    sc = mul(sc, env_adsr(sr, dur, 0.3, 0.0, 1.0, 0.1))
    mix_into(g, sc, 0, 0.25)
    return g


@sfx('boss_fan', 'BOSS_ATTACK{attack:fan}', '보스 부채꼴 투사체. 짧은 투척음 연속 3개', -3, category='boss')
def _boss_fan(sr, rng):
    s = zeros(sec(sr, 0.35))
    for k in range(3):
        w = whoosh(sr, 0.12, rng, 1800 + 300 * k, 600, q=1.3, a=0.1, r=0.5)
        mix_into(s, w, sec(sr, 0.055 * k), 0.8)
        mix_into(s, click(sr, rng, 0.003, 3000), sec(sr, 0.055 * k), 0.4)
    return s


@sfx('boss_die', 'BOSS_DIED', '군주 쓰러짐. 긴 낮은 추락음 + 금속 조각 흩어짐 + 정적', 0, category='boss')
def _boss_die(sr, rng):
    s = zeros(sec(sr, 2.2))
    mix_into(s, mul(tone(sr, 1.4, 160, 30), env_adsr(sr, 1.4, 0.02, 0.0, 1.0, 0.9)), 0, 0.8)
    mix_into(s, kick(sr, 0.7, 100, 28, 0.2, rng=rng), sec(sr, 0.35), 1.2)
    mix_into(s, burst(sr, 0.5, rng, fc=300, q=0.6, tau=0.12, mode='low'), sec(sr, 0.35), 1.0)
    for k in range(5):
        t0 = 0.5 + k * 0.11 + rng.uniform(0, 0.03)
        m = metal(sr, 0.4, 1200 + rng.uniform(-300, 500), rng, tau=0.07, jitter=0.02)
        mix_into(s, m, sec(sr, t0), 0.25 - 0.03 * k)
    return reverb(s, sr, size=1.5, decay=0.82, wet=0.4)


# --- 적 ---------------------------------------------------------------------------

@sfx('enemy_death', 'ENEMY_DIED', '일반 적 사망. 짧은 신음 비슷한 노이즈 + 몸이 떨어지는 둔탁음', -2, category='combat')
def _enemy_death(sr, rng):
    s = zeros(sec(sr, 0.45))
    n = sec(sr, 0.18)
    groan = svf(noise(sr, 0.18, rng), sr, sweep(sr, n, 900, 350), 1.8, 'band')
    groan = mul(groan, env_adsr(sr, 0.18, 0.03, 0.0, 1.0, 0.1))
    mix_into(s, groan, 0, 0.6)
    mix_into(s, thud(sr, 0.25, 130, 45, 0.06), sec(sr, 0.16), 1.0)
    mix_into(s, burst(sr, 0.1, rng, fc=500, q=0.6, tau=0.03, mode='low'), sec(sr, 0.16), 0.7)
    return s


@sfx('player_death', 'RUN_ENDED{reason:death}', '주인공 사망. 느리게 꺼지는 저음, 멀어지는 심장 박동 두 번, 바람', 0, category='event')
def _player_death(sr, rng):
    dur = 2.4
    s = zeros(sec(sr, dur))
    fall = mul(tone(sr, 1.6, 110, 32), env_adsr(sr, 1.6, 0.05, 0.0, 1.0, 1.0))
    mix_into(s, lowpass(fall, sr, 400), 0, 0.8)
    for k, t0 in enumerate([0.5, 1.15]):
        mix_into(s, lowpass(kick(sr, 0.4, 90, 40, 0.1), sr, 250), sec(sr, t0), 0.9 - 0.3 * k)
    wind = svf(noise(sr, dur, rng), sr, 400, 0.7, 'low')
    wind = mul(wind, env_adsr(sr, dur, 0.8, 0.0, 1.0, 1.2))
    mix_into(s, wind, 0, 0.35)
    mix_into(s, burst(sr, 0.1, rng, fc=1200, q=0.6, tau=0.03), 0, 0.5)
    return reverb(s, sr, size=1.5, decay=0.85, wet=0.45)


@sfx('charger_telegraph', 'ENEMY_TELEGRAPH{enemy:charger}', '결사병 돌진 예고(600ms). 갑옷 덜그럭 + 빨라지는 발 디딤', -3, category='combat')
def _charger_telegraph(sr, rng):
    dur = 0.6
    s = zeros(sec(sr, dur))
    t = 0.0
    gap = 0.11
    while t < dur - 0.02:
        mix_into(s, thud(sr, 0.05, 220, 120, 0.012), sec(sr, t), 0.8)
        mix_into(s, metal(sr, 0.08, 1900, rng, tau=0.015, jitter=0.05), sec(sr, t), 0.3)
        t += gap
        gap *= 0.82
    rise = mul(tone(sr, dur, 60, 120, kind='saw'), env_adsr(sr, dur, 0.1, 0.0, 1.0, 0.05))
    mix_into(s, lowpass(rise, sr, 300), 0, 0.35)
    return s


@sfx('charger_dash', 'ENEMY_ATTACK{enemy:charger}', '결사병 돌진. 무거운 바람 + 갑옷 소리', -2, category='combat')
def _charger_dash(sr, rng):
    w = whoosh(sr, 0.4, rng, 400, 1200, q=0.9, a=0.15, r=0.5)
    mix_into(w, metal(sr, 0.15, 1500, rng, tau=0.03, jitter=0.05), 0, 0.3)
    mix_into(w, thud(sr, 0.1, 140, 70, 0.03), 0, 0.6)
    return tail(w, sr, 0.03)


@sfx('archer_shot', 'ENEMY_ATTACK{enemy:archer}', '사수 화승총 발사. 날카로운 격발 + 낮은 폭음 + 화약 연기 쉿', -1, category='combat')
def _archer_shot(sr, rng):
    s = zeros(sec(sr, 0.6))
    mix_into(s, burst(sr, 0.03, rng, fc=4500, q=0.4, tau=0.004), 0, 1.3)
    mix_into(s, burst(sr, 0.2, rng, fc=350, q=0.6, tau=0.045, mode='low'), sec(sr, 0.004), 1.4)
    mix_into(s, thud(sr, 0.22, 110, 40, 0.05), sec(sr, 0.004), 1.0)
    hiss = svf(noise(sr, 0.45, rng), sr, 2500, 0.8, 'high')
    hiss = mul(hiss, env_adsr(sr, 0.45, 0.02, 0.0, 1.0, 0.4))
    mix_into(s, hiss, sec(sr, 0.05), 0.18)
    s = softclip(s, 1.4)
    return reverb(s, sr, size=1.0, decay=0.6, wet=0.2)


@sfx('enemy_hurt', 'ENEMY_DAMAGED{aux:true}', '적이 맞고 내는 짧은 숨(피격음과 겹쳐 쓰는 보조음)', -6, category='combat')
def _enemy_hurt(sr, rng):
    n = sec(sr, 0.1)
    g = svf(noise(sr, 0.1, rng), sr, sweep(sr, n, 1200, 700), 2.0, 'band')
    return mul(g, env_adsr(sr, 0.1, 0.01, 0.0, 1.0, 0.06))


# ---------------------------------------------------------------------------
# BGM 정의 — 각 함수는 루프 길이에 맞춘 버퍼를 돌려준다 (22.05 kHz).
# 설계: 모든 음은 wrap=True 로 섞고, 리버브는 loop=True 로 처리해 경계가 이어진다.
# ---------------------------------------------------------------------------

BGM = {}


def bgm(name, note, gain_db=0.0, floors=None):
    def deco(fn):
        BGM[name] = dict(fn=fn, note=note, gain_db=gain_db, floors=floors or [])
        return fn
    return deco


def put(buf, seg, t, sr, g=1.0):
    mix_into(buf, seg, sec(sr, t), g, wrap=True)


@bgm('title', '타이틀. 어둡고 느린 드론, 멀리서 북, 드문 종. A 단조', 1.0)
def _bgm_title(sr, rng):
    L = 32.0
    n = sec(sr, L)
    buf = zeros(n)
    # 드론: A1 saw(LP, 느린 LFO) + E2 sine + A2 sine 희미
    dr = tone_loop(sr, n, 55.0, 'saw')
    fc = lfo_loop(sr, n, 1 / 16.0, 70, 170)
    dr = wrap2(lambda x: lowpass(x, sr, fc + fc), dr)
    mix_into(buf, dr, 0, 0.55)
    mix_into(buf, tone_loop(sr, n, 82.4, 'sine'), 0, 0.12)
    mix_into(buf, mul(tone_loop(sr, n, 110.0, 'tri'), lfo_loop(sr, n, 1 / 8.0, 0.5, 0.5)), 0, 0.08)
    # 바람
    wind = wrap2(lambda x: svf(x, sr, 380, 0.7, 'low'), noise_loop(sr, n, rng))
    wind = mul(wind, lfo_loop(sr, n, 1 / 10.67, 0.45, 0.55, 0.3))
    mix_into(buf, wind, 0, 0.16)
    # 멀리서 북: 4초마다, 세기 약간씩 다르게
    for k in range(8):
        g = 0.9 + 0.25 * (k % 2) + rng.uniform(-0.08, 0.08)
        kd = lowpass(kick(sr, 0.7, 95, 34, 0.2), sr, 260)
        put(buf, kd, 4.0 * k + 0.5, sr, g)
        if k % 4 == 3:
            put(buf, lowpass(kick(sr, 0.5, 90, 36, 0.15), sr, 260), 4.0 * k + 0.5 + 0.38, sr, 0.6)
    # 드문 종
    for t0, m, g in [(6.0, 76, 0.22), (13.5, 72, 0.18), (21.0, 74, 0.2), (28.0, 69, 0.16)]:
        put(buf, bell(sr, 3.0, midi(m), rng, tau=1.2), t0, sr, g)
    # 서늘한 고음 한 가닥 (중반)
    hi = mul(tone(sr, 6.0, 1318, 1322), env_adsr(sr, 6.0, 2.5, 0.0, 1.0, 3.0))
    put(buf, hi, 16.0, sr, 0.025)
    return reverb(buf, sr, size=1.6, decay=0.85, wet=0.45, loop=True)


@bgm('floor_low', '1~2층(술독·도박장). 저음 드론 위에 취한 류트 아르페지오와 손북. A 단조, 96 BPM', -0.5, floors=[1, 2])
def _bgm_floor_low(sr, rng):
    bpm = 96.0
    beat = 60.0 / bpm
    bars = 12
    L = beat * 4 * bars
    n = sec(sr, L)
    buf = zeros(n)
    # 드론 A1 + 희미한 E2
    mix_into(buf, wrap2(lambda x: lowpass(x, sr, 140), tone_loop(sr, n, 55.0, 'saw')), 0, 0.4)
    mix_into(buf, tone_loop(sr, n, 82.4, 'sine'), 0, 0.07)
    # 코드 진행 (12마디)
    prog = [[57, 60, 64], [57, 60, 64], [62, 65, 69], [64, 67, 71],
            [57, 60, 64], [55, 59, 62], [53, 57, 60], [52, 56, 59],
            [57, 60, 64], [62, 65, 69], [52, 56, 59], [57, 60, 64]]
    # 류트 아르페지오: 8분음 스윙, 취한 느낌의 미세 디튠·타이밍 흔들림
    swing = [0.0, 0.56, 1.0, 1.56, 2.0, 2.56, 3.0, 3.56]
    for b in range(bars):
        chord = prog[b]
        order = [0, 1, 2, 1, 0, 2, 1, 2]
        for k, off in enumerate(swing):
            if b % 4 == 3 and k == 7:
                continue
            m = chord[order[k]] + (12 if k in (2, 6) else 0)
            f = midi(m) * (1 + rng.uniform(-0.006, 0.006))
            t0 = (b * 4 + off) * beat + rng.uniform(-0.012, 0.012)
            g = 0.5 if k % 2 == 0 else 0.33
            p = pluck(sr, 1.1, f, rng, damp=0.994, bright=0.55)
            p = mul(p, env_exp(sr, 1.1, 0.35))
            put(buf, p, t0, sr, g)
        # 베이스 류트: 마디 첫 박과 셋째 박
        root = chord[0] - 12
        for off in (0.0, 2.0):
            p = pluck(sr, 1.2, midi(root), rng, damp=0.996, bright=0.4)
            put(buf, mul(p, env_exp(sr, 1.2, 0.5)), (b * 4 + off) * beat, sr, 0.5)
        # 손북: 1박 둔탁, 2.5박·4박 슬랩
        put(buf, handdrum(sr, rng, 0.25, 170, 90, 0.2), b * 4 * beat, sr, 0.8)
        put(buf, handdrum(sr, rng, 0.16, 260, 150, 0.6), (b * 4 + 2.5) * beat, sr, 0.45)
        put(buf, handdrum(sr, rng, 0.16, 240, 140, 0.6), (b * 4 + 3.56) * beat, sr, 0.5)
        if b % 2 == 1:
            put(buf, handdrum(sr, rng, 0.18, 200, 110, 0.3), (b * 4 + 1.56) * beat, sr, 0.3)
    # 술잔 부딪는 소리: 드물게
    for t0 in [7.3, 15.8, 23.1, 27.9]:
        put(buf, metal(sr, 0.4, 2300 + rng.uniform(-200, 300), rng,
                       partials=[(1, 1), (2.4, 0.4), (3.9, 0.15)], tau=0.1, jitter=0.003), t0, sr, 0.12)
    buf = echo(buf, sr, beat * 0.75, fb=0.25, wet=0.18, loop=True, lp=2200)
    return reverb(buf, sr, size=0.9, decay=0.7, wet=0.25, loop=True)


@bgm('floor_mid', '3~5층(야전병원·용병·첩보). 행진 스네어, 낮은 북, 반음 긴장 드론, 뿔나팔 스탭, 멀리 포성. D 단조, 100 BPM', 3.5, floors=[3, 4, 5])
def _bgm_floor_mid(sr, rng):
    bpm = 100.0
    beat = 60.0 / bpm
    bars = 12
    L = beat * 4 * bars
    n = sec(sr, L)
    buf = zeros(n)
    # 드론: D2 + Eb2(반음 긴장, 2마디마다 들락날락)
    d = wrap2(lambda x: lowpass(x, sr, 220), tone_loop(sr, n, 73.4, 'saw'))
    mix_into(buf, d, 0, 0.42)
    eb = wrap2(lambda x: lowpass(x, sr, 200), tone_loop(sr, n, 77.8, 'saw'))
    gate = lfo_loop(sr, n, 1 / (beat * 8), 0.5, 0.5, -0.25)
    gate = [max(0.0, (g - 0.5) * 2) for g in gate]
    mix_into(buf, mul(eb, gate), 0, 0.2)
    mix_into(buf, tone_loop(sr, n, 36.7, 'sine'), 0, 0.12)
    # 행진 스네어 패턴 (마디): 1(강) · 2(16분 두 번) · 3 · 4(3연 롤)
    for b in range(bars):
        base = b * 4 * beat
        put(buf, snare(sr, rng, 0.2, 0.5), base, sr, 0.75)
        put(buf, snare(sr, rng, 0.12, 0.3), base + 1.0 * beat, sr, 0.35)
        put(buf, snare(sr, rng, 0.12, 0.3), base + 1.25 * beat, sr, 0.3)
        put(buf, snare(sr, rng, 0.18, 0.45), base + 2.0 * beat, sr, 0.6)
        for k in range(3):
            put(buf, snare(sr, rng, 0.1, 0.3), base + (3.0 + k / 3.0) * beat, sr, 0.28 + 0.08 * k)
        if b % 4 == 3:
            for k in range(6):
                put(buf, snare(sr, rng, 0.08, 0.25), base + (3.5 + k / 12.0) * beat, sr, 0.22 + 0.05 * k)
        # 낮은 북 1·3박
        put(buf, lowpass(kick(sr, 0.4, 110, 40, 0.1, rng=rng), sr, 350), base, sr, 0.9)
        put(buf, lowpass(kick(sr, 0.35, 105, 42, 0.09, rng=rng), sr, 350), base + 2 * beat, sr, 0.65)
    # 뿔나팔 스탭: 4·8·12마디 (D3 → 두 박 유지), 12마디는 D3+A3+Bb3
    for b, notes in [(3, [50]), (7, [50, 57]), (11, [50, 57, 58])]:
        t0 = (b * 4 + 2.0) * beat
        for m in notes:
            h = mul(horn(sr, 1.8 * beat, midi(m), fc=700), env_adsr(sr, 1.8 * beat, 0.08, 0.3, 0.6, 0.35))
            put(buf, h, t0, sr, 0.22)
    # 멀리서 포성
    for t0 in [(5 * 4 + 1.5) * beat, (10 * 4 + 0.5) * beat]:
        boom = lowpass(kick(sr, 1.0, 80, 28, 0.3), sr, 200)
        mix_into(boom, burst(sr, 0.6, rng, fc=220, q=0.6, tau=0.18, mode='low'), 0, 0.8)
        put(buf, boom, t0, sr, 0.8)
    return reverb(buf, sr, size=1.2, decay=0.72, wet=0.3, loop=True)


@bgm('floor_high', '6~8층(연회·근위·수도). 정적, 오르간 풍 지속 화음, 아주 희미한 고음 반짝임. D 단조', -2.5, floors=[6, 7, 8])
def _bgm_floor_high(sr, rng):
    L = 32.0
    n = sec(sr, L)
    buf = zeros(n)
    chords = [[50, 57, 65], [46, 53, 62], [43, 50, 58], [45, 52, 61]]  # Dm Bb Gm A
    seg = L / len(chords)
    for i, ch in enumerate(chords):
        t0 = i * seg
        for k, m in enumerate(ch):
            o = organ(sr, seg + 1.5, midi(m), detune=0.002 + 0.001 * k)
            o = mul(o, env_adsr(sr, seg + 1.5, 1.6, 0.0, 1.0, 1.5, curve=1.5))
            put(buf, o, t0, sr, 0.22 if k > 0 else 0.3)
        # 저음 페달
        ped = mul(tone(sr, seg + 1.0, midi(ch[0] - 12)), env_adsr(sr, seg + 1.0, 1.0, 0.0, 1.0, 1.0))
        put(buf, ped, t0, sr, 0.18)
    # 느린 윗소리 (오르간 솔로, 한 음씩 멀리)
    melody = [(2.0, 69, 3.5), (9.5, 70, 3.0), (17.0, 67, 3.5), (25.0, 64, 4.0), (29.5, 65, 2.4)]
    for t0, m, d in melody:
        o = organ(sr, d, midi(m), detune=0.0015)
        o = mul(o, env_adsr(sr, d, 0.8, 0.0, 1.0, 1.0, curve=1.5))
        put(buf, o, t0, sr, 0.08)
    # 희미한 고음 반짝임
    shim = mul(tone_loop(sr, n, 2637, 'sine'), lfo_loop(sr, n, 1 / 6.4, 0.5, 0.5))
    mix_into(buf, shim, 0, 0.012)
    air = wrap2(lambda x: svf(x, sr, 3000, 0.5, 'high'), noise_loop(sr, n, rng))
    air = mul(air, lfo_loop(sr, n, 1 / 8.0, 0.4, 0.6, 0.5))
    mix_into(buf, air, 0, 0.02)
    return reverb(buf, sr, size=1.8, decay=0.88, wet=0.5, loop=True)


@bgm('boss', '보스전. 140 BPM, 낮은 북 연타, 톱니 오스티나토(E), 삼전음 스탭, 쇠 타격. E 단조', 1.5)
def _bgm_boss(sr, rng):
    bpm = 140.0
    beat = 60.0 / bpm
    bars = 16
    L = beat * 4 * bars
    n = sec(sr, L)
    buf = zeros(n)
    # 저음 오스티나토 8분음: E2 E2 G2 E2 | E2 E2 F2 E2
    patA = [40, 40, 43, 40, 40, 40, 43, 40]
    patB = [40, 40, 41, 40, 40, 40, 41, 40]
    for b in range(bars):
        pat = patA if (b // 2) % 2 == 0 else patB
        for k, m in enumerate(pat):
            d = beat * 0.5 * 0.9
            s = lowpass(tone(sr, d, midi(m), kind='saw'), sr, 520)
            s = mul(s, env_adsr(sr, d, 0.005, 0.0, 1.0, d * 0.35))
            put(buf, s, (b * 4 + k * 0.5) * beat, sr, 0.45 if k % 2 == 0 else 0.3)
        base = b * 4 * beat
        # 킥: 1, 3, 4.5
        put(buf, kick(sr, 0.3, 140, 42, 0.07, rng=rng), base, sr, 1.0)
        put(buf, kick(sr, 0.3, 140, 42, 0.07, rng=rng), base + 2 * beat, sr, 0.85)
        put(buf, kick(sr, 0.25, 140, 42, 0.06, rng=rng), base + 3.5 * beat, sr, 0.7)
        # 톰 16분 연타 (2박 뒤·4박)
        for k in range(4):
            put(buf, handdrum(sr, rng, 0.15, 150, 85, 0.25), base + (1.0 + k * 0.25) * beat, sr, 0.35 + 0.08 * k)
        put(buf, handdrum(sr, rng, 0.2, 120, 70, 0.3), base + 3.0 * beat, sr, 0.5)
        # 스네어 2·4박
        put(buf, snare(sr, rng, 0.14, 0.3), base + 1 * beat, sr, 0.3)
        put(buf, snare(sr, rng, 0.14, 0.3), base + 3 * beat, sr, 0.3)
        # 삼전음 스탭 2마디마다
        if b % 2 == 1:
            for m in (52, 58):
                h = mul(horn(sr, beat * 1.2, midi(m), fc=1100), env_adsr(sr, beat * 1.2, 0.01, 0.2, 0.5, 0.3))
                put(buf, h, base + 2.5 * beat, sr, 0.2)
        # 8·16마디 쇠 타격
        if b % 8 == 7:
            put(buf, metal(sr, 1.4, 640, rng, tau=0.4, jitter=0.02), base + 3.0 * beat, sr, 0.35)
            for k in range(8):
                put(buf, snare(sr, rng, 0.08, 0.25), base + (2.0 + k / 8.0) * beat, sr, 0.18 + 0.04 * k)
    # 낮은 드론 E1
    mix_into(buf, wrap2(lambda x: lowpass(x, sr, 120), tone_loop(sr, n, 41.2, 'saw')), 0, 0.2)
    return reverb(buf, sr, size=0.9, decay=0.65, wet=0.18, loop=True)


@bgm('emperor', '황제 \'평\'. 조용하고 정연한 단선율(플루트 풍), 희미한 패드, 시계처럼 규칙적인 틱. D 장조, 60 BPM', -3.5)
def _bgm_emperor(sr, rng):
    bpm = 60.0
    beat = 60.0 / bpm
    L = 32.0
    n = sec(sr, L)
    buf = zeros(n)
    # 패드: D3 + A3 (정수 주기)
    mix_into(buf, tone_loop(sr, n, 146.8, 'sine'), 0, 0.1)
    mix_into(buf, tone_loop(sr, n, 220.0, 'sine'), 0, 0.06)
    mix_into(buf, wrap2(lambda x: lowpass(x, sr, 200), tone_loop(sr, n, 73.4, 'tri')), 0, 0.12)
    # 단선율 (2초 단위 16음; 0 = 쉼)
    mel = [74, 76, 78, 81, 83, 81, 78, 76, 74, 71, 69, 71, 74, 76, 74, 0]
    for i, m in enumerate(mel):
        if m == 0:
            continue
        d = 2.0 * 0.95
        f = flute(sr, d, midi(m))
        f = mul(f, env_adsr(sr, d, 0.25, 0.0, 1.0, 0.5, curve=1.3))
        put(buf, f, i * 2.0, sr, 0.2)
    # 규칙적 틱 (매 박, 아주 작게) — 질서
    for b in range(int(L / beat)):
        tk = mul(tone(sr, 0.03, 1800, 1500), env_exp(sr, 0.03, 0.006))
        put(buf, tk, b * beat, sr, 0.05 if b % 4 else 0.08)
    # 아주 낮은 두려움: 16초 주기로 붉게 부푸는 저음 노이즈
    rum = wrap2(lambda x: svf(x, sr, 90, 0.8, 'low'), noise_loop(sr, n, rng))
    rum = mul(rum, [max(0.0, v) ** 2 for v in lfo_loop(sr, n, 1 / 16.0, 1.0, 0.0, -0.25)])
    mix_into(buf, rum, 0, 0.25)
    return reverb(buf, sr, size=1.8, decay=0.88, wet=0.5, loop=True)


# ---------------------------------------------------------------------------
# 빌드 · 검증
# ---------------------------------------------------------------------------

def build_sfx(names=None):
    os.makedirs(SFX_DIR, exist_ok=True)
    out = []
    for i, (name, spec) in enumerate(SFX.items()):
        if names and name not in names:
            continue
        rng = random.Random(1000 + i)
        buf = spec['fn'](SR_SFX, rng)
        if not spec['loop']:
            buf = fade_edges(buf, SR_SFX, 0.002)
        path = os.path.join(SFX_DIR, name + '.wav')
        dur = write_wav(path, buf, SR_SFX)
        out.append((name, path, dur))
        print('  sfx  %-20s %6.3fs' % (name, dur))
    return out


def build_bgm(names=None):
    os.makedirs(BGM_DIR, exist_ok=True)
    out = []
    for i, (name, spec) in enumerate(BGM.items()):
        if names and name not in names:
            continue
        rng = random.Random(5000 + i)
        buf = spec['fn'](SR_BGM, rng)
        path = os.path.join(BGM_DIR, name + '.wav')
        dur = write_wav(path, buf, SR_BGM)
        out.append((name, path, dur))
        print('  bgm  %-20s %6.3fs' % (name, dur))
    return out


def wav_info(path):
    with wave.open(path, 'rb') as w:
        sr = w.getframerate()
        ch = w.getnchannels()
        nf = w.getnframes()
        raw = w.readframes(nf)
    a = array.array('h')
    a.frombytes(raw)
    if sys.byteorder == 'big':
        a.byteswap()
    peak = max(abs(x) for x in a) if len(a) else 0
    clipped = sum(1 for x in a if abs(x) >= 32767)
    seam = abs(a[-1] - a[0]) / 32767.0 if len(a) else 0.0
    step = max((abs(a[i] - a[i - 1]) for i in range(1, len(a))), default=1) / 32767.0
    seam_ratio = seam / step if step else 0.0
    db = 20 * math.log10(peak / 32767.0) if peak else -999
    return dict(sr=sr, ch=ch, frames=nf, dur=nf / sr, peak_db=db, clipped=clipped,
                seam=seam, seam_ratio=seam_ratio, bytes=os.path.getsize(path))


def parse_trigger(t):
    """'EVENT{k:v,flag}' → {event, when}. when 은 조건 문자열 목록(시스템이 해석)."""
    if '{' not in t:
        return dict(event=t, when=[])
    ev, rest = t.split('{', 1)
    conds = [c.strip() for c in rest.rstrip('}').split(',') if c.strip()]
    return dict(event=ev, when=conds)


def write_manifest():
    entries = []
    for name, spec in SFX.items():
        p = os.path.join(SFX_DIR, name + '.wav')
        if not os.path.exists(p):
            continue
        info = wav_info(p)
        entries.append(dict(
            id='sfx/' + name, kind='sfx', category=spec['category'],
            file='assets/audio/sfx/%s.wav' % name,
            sampleRate=info['sr'], channels=info['ch'],
            durationMs=int(round(info['dur'] * 1000)), loop=spec['loop'],
            gainDb=spec['gain_db'], trigger=parse_trigger(spec['trigger']), note=spec['note']))
    for name, spec in BGM.items():
        p = os.path.join(BGM_DIR, name + '.wav')
        if not os.path.exists(p):
            continue
        info = wav_info(p)
        entries.append(dict(
            id='bgm/' + name, kind='bgm', category='bgm',
            file='assets/audio/bgm/%s.wav' % name,
            sampleRate=info['sr'], channels=info['ch'],
            durationMs=int(round(info['dur'] * 1000)), loop=True,
            gainDb=spec['gain_db'], floors=spec['floors'], note=spec['note']))
    manifest = dict(
        version=1,
        generatedBy='parts/sound/work/build.py',
        format=dict(container='wav', bitDepth=16, peakDbfs=PEAK_DBFS,
                    sfxSampleRate=SR_SFX, bgmSampleRate=SR_BGM, channels=1),
        mixing=dict(masterDb=0.0, sfxBusDb=0.0, bgmBusDb=-8.0,
                    bgmCrossfadeMs=1200, bgmBossDuckDb=-3.0,
                    note='gainDb 는 버스 기준 상대값(dB). BGM 의 gainDb 는 곡 간 RMS 를 약 -21 dBFS 로 맞추는 보정값. 같은 효과음 20ms 내 중복 재생은 1회로 묶기 권장.'),
        bgmByFloor={str(f): 'bgm/' + name for name, spec in BGM.items() for f in spec['floors']},
        bgmByState=dict(title='bgm/title', boss='bgm/boss', emperor='bgm/emperor'),
        entries=entries)
    with open(MANIFEST, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print('  manifest %s (%d entries)' % (os.path.relpath(MANIFEST, ROOT), len(entries)))


def verify():
    rows = []
    total = 0
    for d in (SFX_DIR, BGM_DIR):
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if not fn.endswith('.wav'):
                continue
            p = os.path.join(d, fn)
            info = wav_info(p)
            total += info['bytes']
            rows.append((os.path.relpath(p, os.path.join(ROOT, 'assets', 'audio')), info))
    print('| 파일 | SR | ch | 길이(s) | 피크(dBFS) | 클리핑 | 경계차(÷최대인접차) | 크기(KB) |')
    print('|---|---|---|---|---|---|---|---|')
    bad = 0
    for rel, i in rows:
        ok = i['clipped'] == 0 and i['peak_db'] <= -5.9 and i['seam_ratio'] <= 1.0
        if not ok:
            bad += 1
        print('| %s | %d | %d | %.3f | %.2f | %d | %.4f (%.2f) | %.0f |' % (
            rel, i['sr'], i['ch'], i['dur'], i['peak_db'], i['clipped'], i['seam'], i['seam_ratio'], i['bytes'] / 1024))
    print()
    print('파일 %d 개, 총 %.2f MB, 문제 %d 건' % (len(rows), total / 1048576, bad))
    return bad == 0


def main(argv):
    what = argv[1] if len(argv) > 1 else 'all'
    names = set(argv[2:]) if len(argv) > 2 else None
    if what in ('all', 'sfx'):
        print('[sfx] %d 종' % len(SFX))
        build_sfx(names)
    if what in ('all', 'bgm'):
        print('[bgm] %d 곡' % len(BGM))
        build_bgm(names)
    if what in ('all', 'sfx', 'bgm', 'manifest'):
        write_manifest()
    if what in ('all', 'verify'):
        print()
        ok = verify()
        return 0 if ok else 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
