#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LOPAD 음향 파트 — 절차적 합성 빌드 스크립트 (단일 소스)

  python3 parts/sound/work/build.py            # 전부 재생성 (합성 → 인코딩 → 매니페스트 → 검증)
  python3 parts/sound/work/build.py sfx        # 효과음만 (+인코딩·매니페스트)
  python3 parts/sound/work/build.py bgm        # BGM 만 (+인코딩·매니페스트)
  python3 parts/sound/work/build.py sfx parry  # 특정 소리만
  python3 parts/sound/work/build.py encode     # 작업 캐시 WAV → OGG·M4A 만 다시 (+매니페스트)
  python3 parts/sound/work/build.py manifest   # 매니페스트만 (+들어보기 목록)
  python3 parts/sound/work/build.py listen     # 들어보기 목록(parts/sound/work/listen_index.json)만
  python3 parts/sound/work/build.py verify     # 검증 표 출력 (WAV 원본 + OGG·M4A 디코드 대조)

의존성: 합성은 파이썬 표준 라이브러리만 (wave, struct/array, math, random, json).
인코딩은 ffmpeg(libvorbis·aac). 외부 파이썬 라이브러리·네트워크 없음. 결과는 결정적(고정 시드·bitexact).

출력:
  parts/sound/work/wav/{sfx,bgm}/<이름>.wav   합성 원본(작업 캐시, git 제외 — 이 스크립트로 재생성)
                                              SFX 44.1 kHz / BGM 22.05 kHz, 16 bit, mono, 피크 -6 dBFS
  assets/audio/{sfx,bgm}/<이름>.ogg           배포 1순위 Ogg Vorbis (57라운드 Q17)
  assets/audio/{sfx,bgm}/<이름>.m4a           배포 2순위 AAC-LC (Ogg 미지원 브라우저 대비)
  assets/audio/manifest.json                  시스템 파트가 읽을 목록(계약 sound-assets.md)
  parts/sound/work/listen_index.json          청취 검수(들어보기) 페이지용 목록 — 분류·한 줄 설명·트리거·경로
효과음 정의: 이 파일(1~5x라운드) + sfx_bundle2.py · sfx_branch2.py · sfx_passive.py(60라운드, 이 순서로 등록).
인코딩 규칙·검증 지표는 encode.py 참고.
"""
import array
import json
import math
import os
import random
import sys
import wave

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import encode  # noqa: E402  (배포 형식 인코딩·검증)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
# 합성 WAV = 작업 캐시(저장소·빌드 결과에 넣지 않음), 배포 파일 = OGG·M4A
WAV_DIR = os.path.join(ROOT, 'parts', 'sound', 'work', 'wav')
SFX_WAV_DIR = os.path.join(WAV_DIR, 'sfx')
BGM_WAV_DIR = os.path.join(WAV_DIR, 'bgm')
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


@sfx('hit_player', 'PLAYER_DAMAGED', '주인공 피격(60라운드 Q22 재제작 — 쇳소리 울림 제거). 몸에 꽂히는 둔탁한 충격 + 가죽·천이 눌리는 짧은 퍽 + 뼈에 울리는 낮은 쿵 + 숨이 밀려 나가는 짧은 바람(노이즈, 목소리 아님)', 0)
def _hit_player(sr, rng):
    # Q22 '너무 팅팅거린다, 프라이팬 같다' → 울리는 금속(metal 900 Hz)을 빼고 몸통·가죽·숨으로만
    h = thud(sr, 0.3, 105, 36, 0.07)
    mix_into(h, burst(sr, 0.07, rng, fc=650, q=0.6, tau=0.018, mode='low'), 0, 0.9)  # 가죽·천 눌림 '퍽'
    mix_into(h, burst(sr, 0.03, rng, fc=1600, q=0.7, tau=0.007), 0, 0.45)  # 맞는 순간의 짧은 타격 머리
    mix_into(h, lowpass(thud(sr, 0.2, 70, 34, 0.06), sr, 220), sec(sr, 0.01), 0.7)  # 뼈에 울리는 저음
    n = sec(sr, 0.16)
    hf = svf(noise(sr, 0.16, rng), sr, sweep(sr, n, 900, 500), 1.0, 'band')
    mix_into(h, mul(hf, env_adsr(sr, 0.16, 0.01, 0.0, 1.0, 0.12)), sec(sr, 0.02), 0.3)  # 숨 밀림
    h = softclip(h, 1.8)
    return tail(h, sr, 0.04)


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


@sfx('dash', 'PLAYER_DASH', '대쉬. 짧은 상승 바람 + 발 디딤(60라운드 Q22: 권장 음량 -3 → -5 dB, 파일은 그대로)', -5)
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


@sfx('potion_use', 'PLAYER_HEALED{source:potion}', '물약 마심. 병 뚜껑, 꿀꺽 두 번, 짧은 숨', -3, category='pickup')
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


# --- 1층 보스 '만취' 새 패턴 (54라운드) ----------------------------------------------
# 반드시 기존 효과음 뒤에 둔다: 시드가 SFX 순서(1000 + i)라 앞에 끼우면 기존 파일이 바뀐다.
# 목소리 금지 원칙(sound-design 1장)에 따라 '크아' 숨도 포먼트 필터 노이즈로만 만든다.

GLASS = [(1, 1.0), (2.4, 0.4), (3.9, 0.15), (5.3, 0.08)]


def tone_f(sr, freqs, kind='sine', phase=0.0):
    """샘플별 주파수 배열을 따라가는 오실레이터(울렁임·흔들림용)."""
    fn = _wave_fn(kind)
    out = zeros(len(freqs))
    p = phase
    for i, f in enumerate(freqs):
        out[i] = fn(p)
        p += f / sr
    return out


def gulp(sr, rng, f0=110, f1=260, dur=0.16):
    """꿀꺽 한 번: 목 넘김 둔탁음 + 낮게 올라가는 액체 톤 + 젖은 딸깍."""
    g = mul(tone(sr, dur, f0, f1), env_adsr(sr, dur, 0.02, 0.0, 1.0, dur * 0.55))
    g = lowpass(g, sr, 700)
    mix_into(g, thud(sr, 0.08, 95, 50, 0.02), 0, 0.7)
    mix_into(g, lowpass(click(sr, rng, 0.004, 1400), sr, 2000), sec(sr, dur * 0.5), 0.5)
    return g


def droplets(sr, rng, dur, count, t0, t1, f_lo=500, f_hi=1500, g=0.3):
    """물방울·거품 블립: 짧게 올라가는 사인을 무작위 시각에 흩뿌린다."""
    s = zeros(sec(sr, dur))
    for _ in range(count):
        f = rng.uniform(f_lo, f_hi)
        d = rng.uniform(0.02, 0.045)
        b = mul(tone(sr, d, f, f * rng.uniform(1.3, 1.8)), env_exp(sr, d, d * 0.35))
        mix_into(s, b, sec(sr, rng.uniform(t0, t1)), g * rng.uniform(0.4, 1.0))
    return s


def slosh(sr, rng, dur, fc0=450, fc1=900):
    """잔·통 안의 액체 출렁임: 흔들리는 밴드 노이즈 + 거품 몇 개."""
    n = sec(sr, dur)
    s = svf(noise(sr, dur, rng), sr, sweep(sr, n, fc0, fc1), 1.6, 'band')
    am = lowpass([rng.uniform(-1, 1) for _ in range(n)], sr, 12)
    am = normalize(am, 1.0)
    s = mul(s, [0.55 + 0.45 * a for a in am])
    s = mul(s, env_adsr(sr, dur, dur * 0.2, 0.0, 1.0, dur * 0.5))
    mix_into(s, droplets(sr, rng, dur, 4, 0.0, dur * 0.7, 350, 800, 0.25), 0)
    return s


def kha(sr, rng, dur=0.7, rough=0.3):
    """'크아' 숨 — 성대음 없이 노이즈만: 목 'ㅋ' 버스트 + 'ㅏ' 포먼트(F1 하강) + 거친 진폭 떨림."""
    n = sec(sr, dur)
    s = zeros(n)
    mix_into(s, burst(sr, 0.035, rng, fc=2800, q=1.0, tau=0.008), 0, 0.8)
    src = noise(sr, dur, rng)
    f1 = svf(src, sr, sweep(sr, n, 820, 560), 5.0, 'band')
    f2 = svf(src, sr, sweep(sr, n, 1250, 1050), 6.0, 'band')
    f3 = svf(src, sr, 2600, 4.0, 'band')
    a = [x * 0.22 + y * 0.12 + z * 0.05 for x, y, z in zip(f1, f2, f3)]
    jit = normalize(lowpass([rng.uniform(-1, 1) for _ in range(n)], sr, 45), 1.0)
    a = mul(a, [1.0 - rough + rough * j for j in jit])
    a = mul(a, env_adsr(sr, dur, 0.035, 0.12, 0.6, dur * 0.6, curve=0.6))
    mix_into(s, a, sec(sr, 0.02), 3.0)
    chest = svf(noise(sr, dur * 0.6, rng), sr, 160, 0.8, 'low')
    chest = mul(chest, env_adsr(sr, dur * 0.6, 0.03, 0.0, 1.0, dur * 0.4))
    mix_into(s, chest, sec(sr, 0.02), 1.0)
    return s


def crackle(sr, rng, dur, count, g=0.4, wrap=False):
    """불 타닥: 짧은 고역 딸깍 + 가끔 낮은 톡."""
    s = zeros(sec(sr, dur))
    for _ in range(count):
        t = rng.uniform(0, dur)
        c = burst(sr, 0.008, rng, fc=rng.uniform(1800, 5200), q=0.6, tau=rng.uniform(0.0015, 0.004))
        mix_into(s, c, sec(sr, t), g * rng.uniform(0.3, 1.0), wrap=wrap)
        if rng.random() < 0.2:
            mix_into(s, thud(sr, 0.03, 260, 140, 0.008), sec(sr, t), g * 0.4, wrap=wrap)
    return s


@sfx('boss1_drink_lift', 'BOSS_TELEGRAPH{boss:1,attack:drink,phase:lift}', "만취 큰 잔 들기. 옷 스침 + 유리잔 부딪힘 + 잔 속 술 출렁", -3, category='boss')
def _boss1_drink_lift(sr, rng):
    s = zeros(sec(sr, 0.5))
    mix_into(s, whoosh(sr, 0.3, rng, 400, 1200, q=0.8, a=0.4, r=0.5), 0, 0.3)
    mix_into(s, metal(sr, 0.25, 1500, rng, partials=GLASS, tau=0.06, jitter=0.004), sec(sr, 0.06), 0.35)
    mix_into(s, click(sr, rng, 0.003, 4500), sec(sr, 0.06), 0.4)
    mix_into(s, slosh(sr, rng, 0.38), sec(sr, 0.1), 0.7)
    return s


@sfx('boss1_drink_gulp', 'BOSS_ATTACK{boss:1,attack:drink,phase:gulp}', "만취 꿀꺽꿀꺽 루프(2.0s, 마시는 2초 동안). 0.4초 간격 꿀꺽 5번 + 술 흐름 + 잔 속 거품. 잔이 깨지면 즉시 정지", -4, loop=True, category='boss')
def _boss1_drink_gulp(sr, rng):
    dur = 2.0
    n = sec(sr, dur)
    s = wrap2(lambda x: svf(x, sr, 520, 0.9, 'band'), noise_loop(sr, n, rng))
    s = mul(s, lfo_loop(sr, n, 2.5, 0.35, 0.45))
    s = scale(s, 0.28)
    for k in range(5):
        t0 = 0.05 + 0.4 * k + rng.uniform(-0.015, 0.015)
        f0 = 105 + rng.uniform(-8, 8)
        mix_into(s, gulp(sr, rng, f0, f0 * 2.35, 0.17), sec(sr, t0), 0.9, wrap=True)
        bub = mul(tone(sr, 0.045, 320, 560), env_exp(sr, 0.045, 0.014))
        mix_into(s, bub, sec(sr, t0 + 0.22), 0.18, wrap=True)
    return s


@sfx('boss1_drink_finish', 'BOSS_ATTACK{boss:1,attack:drink,phase:finish}', "만취 다 마심. '크아' 숨(노이즈 포먼트, 목소리 아님) + 잔 내려놓는 '탁'", -2, category='boss')
def _boss1_drink_finish(sr, rng):
    s = zeros(sec(sr, 1.0))
    mix_into(s, kha(sr, rng, 0.7, 0.3), 0, 1.0)
    mix_into(s, thud(sr, 0.12, 320, 160, 0.025), sec(sr, 0.72), 0.35)
    mix_into(s, metal(sr, 0.15, 1400, rng, partials=GLASS, tau=0.03, jitter=0.004), sec(sr, 0.72), 0.12)
    return reverb(s, sr, size=0.7, decay=0.5, wet=0.15)


@sfx('boss1_cup_shatter', 'BOSS_ATTACK{boss:1,attack:drink,phase:broken}', "약점 적중: 큰 잔 깨짐 + 술을 뒤집어씀(첨벙 + 물방울). 3초 경직 시작", 0, category='boss')
def _boss1_cup_shatter(sr, rng):
    s = zeros(sec(sr, 1.2))
    mix_into(s, burst(sr, 0.04, rng, fc=4200, q=0.5, tau=0.006), 0, 1.2)
    mix_into(s, thud(sr, 0.1, 420, 200, 0.02), 0, 0.5)
    for k in range(14):
        t0 = rng.expovariate(1 / 0.08)
        if t0 > 0.4:
            t0 = rng.uniform(0.0, 0.4)
        sh = metal(sr, 0.18, rng.uniform(2500, 6500), rng, partials=GLASS, tau=rng.uniform(0.025, 0.06), jitter=0.01)
        mix_into(s, sh, sec(sr, t0), 0.35 * (1 - 0.04 * k))
    n = sec(sr, 0.8)
    sp = svf(noise(sr, 0.8, rng), sr, sweep(sr, n, 3000, 600), 0.7, 'low')
    sp = mul(sp, env_adsr(sr, 0.8, 0.01, 0.1, 0.5, 0.6))
    mix_into(s, sp, sec(sr, 0.04), 0.7)
    mix_into(s, burst(sr, 0.06, rng, fc=900, q=0.7, tau=0.02), sec(sr, 0.05), 0.6)
    mix_into(s, droplets(sr, rng, 1.0, 12, 0.15, 0.9, 600, 1600, 0.3), 0)
    return reverb(s, sr, size=0.7, decay=0.5, wet=0.15)


@sfx('boss1_spin_start', 'BOSS_ATTACK{boss:1,attack:spin,phase:start}', "'세상이 돈다' 시작. 2초 주기로 울렁이며 내려가는 저음 스윕 + 소용돌이 바람 + 희미한 이질 고음", -2, category='boss')
def _boss1_spin_start(sr, rng):
    dur = 2.0
    n = sec(sr, dur)
    s = zeros(n)
    wob = [math.sin(TAU * 0.5 * i / sr) for i in range(n)]
    base = sweep(sr, n, 72, 46)
    fa = [b * (1 + 0.06 * w) for b, w in zip(base, wob)]
    fb = [f * 1.03 for f in fa]
    lo = add(tone_f(sr, fa, 'saw'), tone_f(sr, fb, 'saw'))
    cut = [380 + 260 * w for w in wob]
    lo = svf(lo, sr, cut, 1.4, 'low')
    lo = mul(lo, env_adsr(sr, dur, 0.5, 0.0, 1.0, 0.7))
    mix_into(s, lo, 0, 0.6)
    wind = svf(noise(sr, dur, rng), sr, [700 + 450 * w for w in wob], 1.2, 'band')
    wind = mul(wind, env_adsr(sr, dur, 0.6, 0.0, 1.0, 0.8))
    mix_into(s, wind, 0, 0.35)
    hi = tone_f(sr, [2900 * (1 + 0.012 * w) for w in wob])
    mix_into(s, mul(hi, env_adsr(sr, dur, 0.7, 0.0, 1.0, 0.9)), 0, 0.03)
    return reverb(tail(s, sr, 0.2), sr, size=1.2, decay=0.75, wet=0.3)


@sfx('boss1_reel_telegraph', 'BOSS_TELEGRAPH{boss:1,attack:reel}', "3연 취권 돌진 예고(타당 1회, 최단 예고 300ms 에 맞춰 0.30s). 휘청이는 으르렁 + 엇박 발 끌림", -2, category='boss')
def _boss1_reel_telegraph(sr, rng):
    dur = 0.3
    n = sec(sr, dur)
    f = [(60 + 70 * i / n) * (1 + 0.08 * math.sin(TAU * 11 * i / sr)) for i in range(n)]
    g = svf(tone_f(sr, f, 'saw'), sr, sweep(sr, n, 250, 900), 1.4, 'low')
    g = mul(g, env_adsr(sr, dur, 0.04, 0.0, 1.0, 0.05))
    s = scale(g, 0.8)
    for t0, fq in [(0.0, 200), (0.13, 170)]:
        mix_into(s, thud(sr, 0.06, fq, fq * 0.55, 0.015), sec(sr, t0), 0.7)
        sc = mul(svf(noise(sr, 0.08, rng), sr, 1600, 0.8, 'band'), env_adsr(sr, 0.08, 0.01, 0.0, 1.0, 0.05))
        mix_into(s, sc, sec(sr, t0), 0.3)
    return s


@sfx('boss1_reel_dash', 'BOSS_ATTACK{boss:1,attack:reel}', "3연 취권 돌진(타당 1회). 휘는 궤적처럼 흔들리는 무거운 바람 + 쿵 디딤 + 옷 펄럭. 1·2·3타 rate 1.0/1.06/1.12 권장", -2, category='boss')
def _boss1_reel_dash(sr, rng):
    dur = 0.4
    n = sec(sr, dur)
    cut = [380 * math.exp(math.log(1400 / 380) * i / n) * (1 + 0.3 * math.sin(TAU * 7 * i / sr)) for i in range(n)]
    w = svf(noise(sr, dur, rng), sr, cut, 0.9, 'band')
    w = mul(w, env_adsr(sr, dur, 0.06, 0.0, 1.0, 0.2))
    mix_into(w, thud(sr, 0.12, 130, 55, 0.035), 0, 0.9)
    mix_into(w, burst(sr, 0.06, rng, fc=500, q=0.6, tau=0.015, mode='low'), 0, 0.6)
    flap = svf(noise(sr, 0.25, rng), sr, 2200, 0.8, 'band')
    flap = mul(mul(flap, [0.5 + 0.5 * math.sin(TAU * 16 * i / sr) for i in range(sec(sr, 0.25))]),
               env_adsr(sr, 0.25, 0.03, 0.0, 1.0, 0.15))
    mix_into(w, flap, sec(sr, 0.05), 0.2)
    return tail(w, sr, 0.04)


@sfx('boss1_fall', 'BOSS_ATTACK{boss:1,attack:reel,phase:fall}', "3연 돌진 뒤 넘어짐 '쿵'(2초 경직 시작). 큰 몸통 충격 + 한 번 튐 + 잔·소품 굴러감 + 먼지", 0, category='boss')
def _boss1_fall(sr, rng):
    s = zeros(sec(sr, 1.1))
    mix_into(s, kick(sr, 0.6, 90, 30, 0.16, rng=rng), 0, 1.4)
    mix_into(s, burst(sr, 0.3, rng, fc=250, q=0.6, tau=0.08, mode='low'), 0, 1.0)
    mix_into(s, thud(sr, 0.3, 110, 45, 0.06), sec(sr, 0.18), 0.6)
    for k, t0 in enumerate([0.26, 0.35, 0.41, 0.46]):
        mix_into(s, thud(sr, 0.06, 420 - 40 * k, 260, 0.015), sec(sr, t0), 0.3 - 0.05 * k)
    dust = mul(svf(noise(sr, 0.6, rng), sr, 900, 0.7, 'low'), env_adsr(sr, 0.6, 0.05, 0.0, 1.0, 0.45))
    mix_into(s, dust, sec(sr, 0.03), 0.2)
    s = softclip(s, 1.4)
    return reverb(s, sr, size=1.0, decay=0.6, wet=0.22)


@sfx('boss1_barrel_kick', 'BOSS_ATTACK{boss:1,attack:barrel,phase:kick}', "술통 걷어차기. 장화 타격 + 속 빈 나무통 울림 + 쇠테 틱 + 통 속 술 출렁", -1, category='boss')
def _boss1_barrel_kick(sr, rng):
    s = zeros(sec(sr, 0.55))
    mix_into(s, burst(sr, 0.03, rng, fc=1500, q=0.6, tau=0.006), 0, 0.8)
    mix_into(s, thud(sr, 0.25, 160, 110, 0.07), 0, 1.0)
    for fc, g in [(230, 0.9), (520, 0.5)]:
        mix_into(s, burst(sr, 0.3, rng, fc=fc, q=6.0, tau=0.08), 0, g)
    mix_into(s, metal(sr, 0.12, 1100, rng, tau=0.02, jitter=0.03), 0, 0.15)
    mix_into(s, slosh(sr, rng, 0.4, 350, 700), sec(sr, 0.05), 0.4)
    return s


@sfx('boss1_barrel_roll', 'BOSS_ATTACK{boss:1,attack:barrel,phase:roll}', "굴러가는 술통 루프(1.2s). 나무통 덜컹(0.12s 간격) + 낮은 굴림 + 속 술 출렁. 통이 멈추거나 부서지면 정지", -6, loop=True, category='boss')
def _boss1_barrel_roll(sr, rng):
    dur = 1.2
    n = sec(sr, dur)
    rum = wrap2(lambda x: svf(x, sr, 180, 0.8, 'low'), noise_loop(sr, n, rng))
    s = mul(rum, lfo_loop(sr, n, 1 / 0.6, 0.3, 0.7))
    liq = wrap2(lambda x: svf(x, sr, 600, 1.5, 'band'), noise_loop(sr, n, rng))
    mix_into(s, mul(liq, lfo_loop(sr, n, 1 / 0.6, 0.5, 0.5, 0.25)), 0, 0.25)
    for k in range(10):
        accent = 1.0 if k % 5 == 0 else rng.uniform(0.45, 0.7)
        t0 = 0.12 * k + rng.uniform(-0.006, 0.006)
        mix_into(s, thud(sr, 0.06, 150, 95, 0.02), sec(sr, t0), 0.45 * accent, wrap=True)
        mix_into(s, burst(sr, 0.02, rng, fc=1300, q=0.7, tau=0.004), sec(sr, t0), 0.12 * accent, wrap=True)
    return s


@sfx('boss1_barrel_bounce', 'BOSS_ATTACK{boss:1,attack:barrel,phase:bounce}', "술통이 벽·기둥에 튕김. 돌에 부딪히는 나무통 + 속 빈 울림 + 쇠테 덜그럭 + 술 출렁", -2, category='boss')
def _boss1_barrel_bounce(sr, rng):
    s = zeros(sec(sr, 0.5))
    mix_into(s, thud(sr, 0.3, 130, 60, 0.06), 0, 1.2)
    for fc, g in [(210, 0.9), (480, 0.5)]:
        mix_into(s, burst(sr, 0.3, rng, fc=fc, q=6.0, tau=0.07), 0, g)
    mix_into(s, burst(sr, 0.03, rng, fc=2500, q=0.6, tau=0.01), 0, 0.6)
    mix_into(s, burst(sr, 0.1, rng, fc=400, q=0.6, tau=0.025, mode='low'), 0, 0.5)
    mix_into(s, metal(sr, 0.15, 950, rng, tau=0.03, jitter=0.04), sec(sr, 0.01), 0.2)
    mix_into(s, slosh(sr, rng, 0.35, 350, 700), sec(sr, 0.04), 0.35)
    return reverb(s, sr, size=0.8, decay=0.5, wet=0.12)


@sfx('boss1_liquor_splash', 'BOSS_ATTACK{boss:1,attack:fire,phase:splash}', "술 뿌리기 '첨벙'. 휙 던지는 바람 + 바닥에 퍼지는 물소리 + 물방울", -3, category='boss')
def _boss1_liquor_splash(sr, rng):
    s = zeros(sec(sr, 0.7))
    mix_into(s, whoosh(sr, 0.15, rng, 1200, 500, q=1.0, a=0.3, r=0.5), 0, 0.3)
    n = sec(sr, 0.55)
    sp = svf(noise(sr, 0.55, rng), sr, sweep(sr, n, 4000, 700), 0.7, 'low')
    sp = mul(sp, env_adsr(sr, 0.55, 0.005, 0.08, 0.45, 0.4))
    mix_into(s, sp, sec(sr, 0.08), 1.0)
    mix_into(s, burst(sr, 0.05, rng, fc=900, q=0.7, tau=0.02), sec(sr, 0.08), 0.7)
    mix_into(s, droplets(sr, rng, 0.7, 10, 0.14, 0.6, 600, 1600, 0.28), 0)
    return s


@sfx('boss1_torch_throw', 'BOSS_ATTACK{boss:1,attack:fire,phase:throw}', "횃불 던지기. 빙글 도는 불 바람(9Hz 맥동) + 타닥", -3, category='boss')
def _boss1_torch_throw(sr, rng):
    dur = 0.55
    n = sec(sr, dur)
    trem = [0.45 + 0.55 * (0.5 + 0.5 * math.sin(TAU * 9 * i / sr)) for i in range(n)]
    w = svf(noise(sr, dur, rng), sr, sweep(sr, n, 500, 1800), 1.0, 'band')
    w = mul(mul(w, trem), env_adsr(sr, dur, 0.08, 0.0, 1.0, 0.25))
    roar = svf(noise(sr, dur, rng), sr, 300, 0.7, 'low')
    roar = mul(mul(roar, trem), env_adsr(sr, dur, 0.08, 0.0, 1.0, 0.25))
    mix_into(w, roar, 0, 0.6)
    mix_into(w, crackle(sr, rng, dur, 6, 0.4), 0)
    return tail(w, sr, 0.05)


@sfx('boss1_ignite', 'BOSS_ATTACK{boss:1,attack:fire,phase:ignite}', "술 웅덩이 점화 '화르륵'. 낮은 펑 + 치솟는 불길 + 타닥", -1, category='boss')
def _boss1_ignite(sr, rng):
    dur = 1.1
    n = sec(sr, dur)
    s = zeros(n)
    mix_into(s, thud(sr, 0.3, 80, 40, 0.07), 0, 0.8)
    roar = svf(noise(sr, dur, rng), sr, sweep(sr, n, 200, 2500), 0.7, 'low')
    roar = mul(roar, env_adsr(sr, dur, 0.06, 0.15, 0.55, 0.8))
    mix_into(s, roar, 0, 1.0)
    mix_into(s, crackle(sr, rng, 0.9, 16, 0.35), sec(sr, 0.15))
    s = softclip(s, 1.3)
    return reverb(s, sr, size=0.8, decay=0.5, wet=0.15)


@sfx('boss1_fire_loop', 'BOSS_ATTACK{boss:1,attack:fire,phase:burn}', "불 번짐 루프(2.0s). 일렁이는 낮은 불길 + 쉿 + 무작위 타닥. 웅덩이가 꺼지면 정지", -8, loop=True, category='boss')
def _boss1_fire_loop(sr, rng):
    dur = 2.0
    n = sec(sr, dur)
    s = wrap2(lambda x: svf(x, sr, 400, 0.7, 'low'), noise_loop(sr, n, rng))
    flick = [a * b for a, b in zip(lfo_loop(sr, n, 0.5, 0.25, 0.75), lfo_loop(sr, n, 1.5, 0.15, 0.85, 0.3))]
    s = mul(s, flick)
    hiss = wrap2(lambda x: svf(x, sr, 3000, 0.7, 'high'), noise_loop(sr, n, rng))
    mix_into(s, hiss, 0, 0.05)
    mix_into(s, crackle(sr, rng, dur, 22, 0.45, wrap=True), 0)
    return s


@sfx('boss1_candle_topple', 'BOSS_ATTACK{boss:1,attack:darkness,phase:topple}', "촛대 쓰러짐(불 꺼짐). 쇠 촛대 넘어지는 쨍그랑 + 한 번 튐 + 불꽃 '훅' 꺼짐 + 내려앉는 저음", -2, category='boss')
def _boss1_candle_topple(sr, rng):
    s = zeros(sec(sr, 1.0))
    mix_into(s, whoosh(sr, 0.15, rng, 600, 300, q=0.8, a=0.6, r=0.3), 0, 0.2)
    mix_into(s, metal(sr, 0.6, 520, rng, tau=0.15, jitter=0.02), sec(sr, 0.15), 0.7)
    mix_into(s, thud(sr, 0.15, 180, 80, 0.03), sec(sr, 0.15), 0.6)
    mix_into(s, metal(sr, 0.4, 610, rng, tau=0.1, jitter=0.03), sec(sr, 0.32), 0.35)
    mix_into(s, metal(sr, 0.15, 900, rng, tau=0.03, jitter=0.05), sec(sr, 0.42), 0.15)
    n = sec(sr, 0.18)
    puff = svf(noise(sr, 0.18, rng), sr, sweep(sr, n, 800, 300), 0.9, 'band')
    puff = mul(puff, env_adsr(sr, 0.18, 0.01, 0.0, 1.0, 0.14))
    mix_into(s, puff, sec(sr, 0.14), 0.5)
    mix_into(s, mul(tone(sr, 0.6, 120, 60), env_adsr(sr, 0.6, 0.05, 0.0, 1.0, 0.45)), sec(sr, 0.2), 0.2)
    return reverb(s, sr, size=1.0, decay=0.6, wet=0.2)


@sfx('boss1_candle_relight', 'BOSS_ATTACK{boss:1,attack:darkness,phase:relight}', "촛대 다시 켜기(타격·E). 쇠 촛대 틱 + 불꽃이 '화륵' 붙음 + 작은 타닥", -3, category='world')
def _boss1_candle_relight(sr, rng):
    s = zeros(sec(sr, 0.7))
    mix_into(s, metal(sr, 0.1, 2200, rng, tau=0.012, jitter=0.02), 0, 0.3)
    mix_into(s, click(sr, rng, 0.004, 3500), 0, 0.3)
    n = sec(sr, 0.25)
    fw = svf(noise(sr, 0.25, rng), sr, sweep(sr, n, 500, 2500), 0.9, 'band')
    fw = mul(fw, env_adsr(sr, 0.25, 0.12, 0.0, 1.0, 0.1))
    mix_into(s, fw, sec(sr, 0.03), 1.2)
    warm = mul(svf(noise(sr, 0.45, rng), sr, 350, 0.7, 'low'), env_adsr(sr, 0.45, 0.08, 0.0, 1.0, 0.3))
    mix_into(s, warm, sec(sr, 0.12), 0.5)
    mix_into(s, crackle(sr, rng, 0.4, 5, 0.25), sec(sr, 0.22))
    return reverb(s, sr, size=0.7, decay=0.5, wet=0.15)


@sfx('boss1_phase_drink', 'BOSS_PHASE{boss:1}', "만취 페이즈 전환 들이켜기(선택, boss_phase 대신 또는 뒤에). 잔 출렁 + 빠른 꿀꺽 3번 + 큰 '크아' + 낮은 북", 0, category='boss')
def _boss1_phase_drink(sr, rng):
    s = zeros(sec(sr, 1.8))
    mix_into(s, slosh(sr, rng, 0.25), 0, 0.5)
    for k, t0 in enumerate([0.2, 0.42, 0.62]):
        mix_into(s, gulp(sr, rng, 92 + 6 * k, 220 + 15 * k, 0.18), sec(sr, t0), 1.0)
    mix_into(s, kha(sr, rng, 0.9, 0.4), sec(sr, 0.85), 1.3)
    mix_into(s, kick(sr, 0.5, 95, 32, 0.15, rng=rng), sec(sr, 0.85), 0.9)
    return reverb(s, sr, size=1.2, decay=0.7, wet=0.3)


# --- 55라운드: 대검 홀드 차지 · 칼 3타 잔상 베기 ------------------------------------------
# 결정 근거: parts/producer/decisions/2026-10-03-round-55-weapon-fx-overhaul.md Q22·Q24·Q29~Q32.
# 반드시 boss1_* 뒤에 둔다(시드 = 1000 + 등록 순서). 차지 단계 0.4/0.8/1.2 s, 잔상 베기는 본 타격 150 ms 뒤.
# 3단 내려찍기는 충격파 꼬리가 붙어 구조가 달라지므로 재생 속도 변주가 아니라 단계별 파일 3개로 둔다.

AMBER_D = [146.83, 293.66, 440.0, 587.33]  # D3·D4·A4·D5. 차지 단계 1·2·3 = [1]·[2]·[3] (D 단조 BGM 과 어울림), [1] 은 루프 험·3단 아래 옥타브에도 씀


def jing(sr, dur, f, rng, bright=0.0, tau=0.5, bend=0.012):
    """호박빛 '징': 비조화 배음 + 처음 0.12 s 동안 살짝 올라갔다 자리 잡는 음높이(징 특유의 '웅').
    bright(0~1) 가 클수록 윗배음이 커지고 저역통과가 열린다(3단 = 백열)."""
    n = sec(sr, dur)
    parts = [(1.0, 1.0), (2.0, 0.42), (2.76, 0.30), (4.07, 0.16 + 0.25 * bright),
             (5.40, 0.08 + 0.22 * bright), (6.80, 0.15 * bright), (8.20, 0.09 * bright)]
    nb = sec(sr, 0.12)
    bend_env = [1.0 + bend * (math.sin(0.5 * math.pi * min(1.0, i / nb))) for i in range(n)]
    out = zeros(n)
    for ratio, amp in parts:
        if amp <= 0:
            continue
        fr = f * ratio * (1 + rng.uniform(-0.002, 0.002))
        freqs = [fr * b for b in bend_env]
        e = env_exp(sr, dur, tau / math.sqrt(ratio))
        osc = tone_f(sr, freqs, 'sine', rng.random())
        for i in range(n):
            out[i] += amp * e[i] * osc[i]
    out = mul(out, env_adsr(sr, dur, 0.006, 0.0, 1.0, dur * 0.25))
    out = lowpass(out, sr, 2200 + 6000 * bright)
    mix_into(out, thud(sr, 0.06, f * 0.5, f * 0.3, 0.015), 0, 0.35)  # 채가 닿는 둔탁한 머리
    return out


def gravel(sr, rng, dur, count, t0, t1, g=0.3):
    """흩어지는 돌 부스러기: 낮은 대역 짧은 딸깍을 무작위로."""
    s = zeros(sec(sr, dur))
    for _ in range(count):
        c = burst(sr, 0.015, rng, fc=rng.uniform(900, 3200), q=0.8, tau=rng.uniform(0.002, 0.005))
        mix_into(s, c, sec(sr, rng.uniform(t0, t1)), g * rng.uniform(0.3, 1.0))
    return s


def slam_impact(sr, rng, dur, f0, f1, tau, weight):
    """지면 강타: 몸통 저음 + 저역 폭발 + 돌 깨짐 + 칼날 쇳소리. weight 1.0~1.6."""
    s = zeros(sec(sr, dur))
    mix_into(s, thud(sr, min(dur, 0.6), f0, f1, tau), 0, 1.2 * weight)
    mix_into(s, burst(sr, 0.25, rng, fc=380, q=0.6, tau=0.04 * weight, mode='low'), 0, 1.0 * weight)
    mix_into(s, burst(sr, 0.06, rng, fc=1800, q=0.7, tau=0.012), sec(sr, 0.002), 0.55)
    mix_into(s, metal(sr, 0.3, 640, rng, tau=0.07, jitter=0.03), sec(sr, 0.003), 0.28)
    mix_into(s, click(sr, rng, 0.004, 2600), 0, 0.8)
    return s


@sfx('charge_start', 'PLAYER_CHARGE{weapon:greatsword,phase:start}', "대검 홀드 차지 시작(홀드 인식 0.18s 시점). 무거운 칼을 들어 올리는 쇳소리 + 숨처럼 차오르는 노이즈(목소리 아님)", -4)
def _charge_start(sr, rng):
    dur = 0.3
    n = sec(sr, dur)
    s = zeros(n)
    mix_into(s, thud(sr, 0.07, 170, 90, 0.018), 0, 0.5)  # 손잡이 고쳐 쥠
    sc = svf(noise(sr, 0.26, rng), sr, sweep(sr, sec(sr, 0.26), 1600, 4200), 3.0, 'band')
    grind = [0.55 + 0.45 * math.sin(TAU * 34 * i / sr) for i in range(len(sc))]
    sc = mul(mul(sc, grind), env_adsr(sr, 0.26, 0.05, 0.0, 1.0, 0.1))
    mix_into(s, sc, sec(sr, 0.02), 0.45)  # 쇠 긁힘
    mix_into(s, metal(sr, 0.25, 760, rng, tau=0.09, jitter=0.02), sec(sr, 0.03), 0.18)
    br = svf(noise(sr, dur, rng), sr, sweep(sr, n, 420, 1500), 0.8, 'band')
    br = mul(br, [((i / n) ** 2.0) * (1.0 if i < n * 0.86 else max(0.0, (n - i) / (n * 0.14))) for i in range(n)])
    mix_into(s, br, 0, 0.6)  # 숨처럼 차오르는 노이즈
    wt = mul(lowpass(tone(sr, dur, 58, 88, kind='saw'), sr, 260), env_adsr(sr, dur, 0.12, 0.0, 1.0, 0.06))
    mix_into(s, wt, 0, 0.35)  # 들어 올리는 무게
    return s


def _gather(sr, rng, dur, f0, f1, q=1.1):
    """기를 모음: 안으로 빨려드는 공기(노이즈 밴드가 위로 차오름)."""
    n = sec(sr, dur)
    g = svf(noise(sr, dur, rng), sr, sweep(sr, n, f0, f1), q, 'band')
    return mul(g, [((i / n) ** 1.4) * (1.0 if i < n * 0.85 else (n - i) / (n * 0.15)) for i in range(n)])


def _strain(sr, dur, f0, f1, shake, depth):
    """힘을 주는 낮은 압력음: 저역통과 톱니 피치 상승 + shake Hz 떨림(버티는 몸)."""
    n = sec(sr, dur)
    p = lowpass(lowpass(tone(sr, dur, f0, f1, kind='saw'), sr, 260), sr, 400)
    return mul(p, [(1 - depth) + depth * (0.5 + 0.5 * math.sin(TAU * shake * i / sr)) for i in range(n)])


@sfx('charge_stage1', 'PLAYER_CHARGE{weapon:greatsword,phase:stage,stage:1}', "차지 1단(0.4 s, 60라운드 Q22 재제작 — 종소리 없음). 기를 모으는 느낌: 안으로 빨려드는 공기 + 낮게 차오르는 압력(55→70 Hz) + 손잡이 가죽 삐걱", -6)
def _charge_stage1(sr, rng):
    dur = 0.55
    s = zeros(sec(sr, dur))
    mix_into(s, _gather(sr, rng, 0.5, 300, 1300), 0, 0.6)
    mix_into(s, mul(_strain(sr, 0.5, 55, 70, 5.0, 0.2), env_adsr(sr, 0.5, 0.25, 0.0, 1.0, 0.2)), 0, 0.8)
    cr = svf(noise(sr, 0.12, rng), sr, 1100, 3.0, 'band')
    cr = mul(cr, [0.5 + 0.5 * math.sin(TAU * 32 * i / sr) for i in range(len(cr))])
    mix_into(s, mul(cr, env_adsr(sr, 0.12, 0.03, 0.0, 1.0, 0.06)), sec(sr, 0.05), 0.25)  # 가죽 삐걱
    return tail(s, sr, 0.02)


@sfx('charge_stage2', 'PLAYER_CHARGE{weapon:greatsword,phase:stage,stage:2}', "차지 2단(0.8 s, 60라운드 Q22 재제작 — 종소리 없음). 힘을 다해 모으는 느낌: 더 깊고 거세게 빨려드는 공기 + 9 Hz 로 떨리며 올라가는 압력(60→95 Hz) + 쇠가 버티는 낮은 끼익 + 발밑 자갈 떨림", -4)
def _charge_stage2(sr, rng):
    dur = 0.75
    s = zeros(sec(sr, dur))
    mix_into(s, _gather(sr, rng, 0.65, 220, 1800, q=0.9), 0, 0.75)
    mix_into(s, mul(_strain(sr, 0.7, 60, 95, 9.0, 0.45), env_adsr(sr, 0.7, 0.2, 0.0, 1.0, 0.25)), 0, 1.0)
    n = sec(sr, 0.45)
    gr = svf(noise(sr, 0.45, rng), sr, sweep(sr, n, 380, 620), 4.0, 'band')
    gr = mul(gr, [0.4 + 0.6 * abs(math.sin(TAU * 13 * i / sr)) for i in range(n)])
    mix_into(s, mul(gr, env_adsr(sr, 0.45, 0.12, 0.0, 1.0, 0.15)), sec(sr, 0.12), 0.3)  # 쇠가 버티는 끼익
    tr = svf(noise(sr, 0.6, rng), sr, 160, 0.8, 'low')
    tr = mul(tr, [0.5 + 0.5 * math.sin(TAU * 9 * i / sr) for i in range(len(tr))])
    mix_into(s, mul(tr, env_adsr(sr, 0.6, 0.2, 0.0, 1.0, 0.2)), 0, 0.45)  # 땅 떨림
    mix_into(s, gravel(sr, rng, 0.6, 6, 0.15, 0.55, 0.15), 0)
    return softclip(tail(s, sr, 0.02), 1.2)


@sfx('charge_stage3', 'PLAYER_CHARGE{weapon:greatsword,phase:stage,stage:3}', "차지 3단(1.2 s, 최대 · 60라운드 Q22 재제작 — 종소리 없음). 힘을 다 짜내 공격 타이밍을 알림: 파일 0 s 에 또렷한 '척'(쥔 손·갑옷이 조여 붙는 단단한 딸깍 + 짧은 쿵) + 위로 터지는 공기 '파앗' → 12 Hz 로 떨리며 끓어 넘치는 압력(97 Hz) + 잔불 타닥. 0 s 신호가 '지금 놓아라'", -2)
def _charge_stage3(sr, rng):
    dur = 1.0
    s = zeros(sec(sr, dur))
    mix_into(s, click(sr, rng, 0.005, 3200), 0, 1.0)  # 조여 붙는 '척'
    mix_into(s, burst(sr, 0.03, rng, fc=1300, q=0.9, tau=0.006), 0, 0.8)
    mix_into(s, thud(sr, 0.18, 130, 48, 0.035), 0, 1.0)
    mix_into(s, burst(sr, 0.12, rng, fc=350, q=0.6, tau=0.025, mode='low'), 0, 0.6)
    n = sec(sr, 0.18)
    up = svf(noise(sr, 0.18, rng), sr, sweep(sr, n, 1500, 7000), 1.1, 'band')
    mix_into(s, mul(up, env_adsr(sr, 0.18, 0.005, 0.0, 1.0, 0.16)), 0, 0.55)  # '파앗'
    mix_into(s, mul(_strain(sr, 0.85, 97, 92, 12.0, 0.55), env_adsr(sr, 0.85, 0.01, 0.15, 0.6, 0.6)), sec(sr, 0.02), 0.9)
    boil = svf(noise(sr, 0.8, rng), sr, 240, 0.8, 'low')
    boil = mul(boil, [0.45 + 0.55 * math.sin(TAU * 12 * i / sr) for i in range(len(boil))])
    mix_into(s, mul(boil, env_adsr(sr, 0.8, 0.02, 0.1, 0.6, 0.6)), sec(sr, 0.02), 0.5)  # 끓어 넘침
    mix_into(s, crackle(sr, rng, 0.7, 10, 0.3), sec(sr, 0.05))
    s = softclip(s, 1.4)
    return reverb(tail(s, sr, 0.03), sr, size=0.6, decay=0.5, wet=0.12)


@sfx('charge_loop', 'PLAYER_CHARGE{weapon:greatsword,phase:start,until:release}', "차지 유지 루프(1.0s). 낮은 웅웅 + 느린 맥놀이 + 희미한 호박 험. start 에 페이드인 시작, release·피격 취소 시 정지", -12, loop=True)
def _charge_loop(sr, rng):
    dur = 1.0
    n = sec(sr, dur)
    g = wrap2(lambda x: lowpass(x, sr, 170), tone_loop(sr, n, 55, 'saw'))
    sub = mul(tone_loop(sr, n, 110, 'sine'), lfo_loop(sr, n, 2.0, 0.35, 0.65))
    mix_into(g, sub, 0, 0.35)
    beat = tone_loop(sr, n, 113, 'sine')  # 110 과 3 Hz 맥놀이
    mix_into(g, beat, 0, 0.18)
    rum = wrap2(lambda x: svf(x, sr, 200, 0.9, 'low'), noise_loop(sr, n, rng))
    rum = mul(rum, lfo_loop(sr, n, 4.0, 0.3, 0.7))
    mix_into(g, rum, 0, 0.6)
    hum = mul(tone_loop(sr, n, AMBER_D[1], 'sine'), lfo_loop(sr, n, 3.0, 0.5, 0.5, 0.25))
    mix_into(g, hum, 0, 0.05)
    return g


@sfx('charge_slam_lv1', 'PLAYER_CHARGE{weapon:greatsword,phase:release,stage:1}', "차지 1단 내려찍기(판정 프레임에 재생). 지면 강타 + 돌 깨짐 + 칼날 쇳소리", -2)
def _charge_slam_lv1(sr, rng):
    s = slam_impact(sr, rng, 0.55, 125, 36, 0.09, 1.0)
    mix_into(s, gravel(sr, rng, 0.55, 6, 0.04, 0.3, 0.3), 0)
    s = softclip(s, 1.3)
    return reverb(tail(s, sr, 0.05), sr, size=0.6, decay=0.5, wet=0.12)


@sfx('charge_slam_lv2', 'PLAYER_CHARGE{weapon:greatsword,phase:release,stage:2}', "차지 2단 내려찍기. 1단보다 낮고 무거운 강타 + 부스러기 더 많이", -2)
def _charge_slam_lv2(sr, rng):
    s = slam_impact(sr, rng, 0.75, 115, 30, 0.12, 1.3)
    mix_into(s, gravel(sr, rng, 0.75, 10, 0.04, 0.45, 0.32), 0)
    rum = mul(svf(noise(sr, 0.6, rng), sr, 160, 0.8, 'low'), env_exp(sr, 0.6, 0.15))
    mix_into(s, rum, sec(sr, 0.01), 0.7)
    s = softclip(s, 1.5)
    return reverb(tail(s, sr, 0.05), sr, size=0.8, decay=0.55, wet=0.15)


@sfx('charge_slam_lv3', 'PLAYER_CHARGE{weapon:greatsword,phase:release,stage:3}', "차지 3단 내려찍기(막타, 충격파 링). 가장 무거운 강타 + 바깥으로 퍼지는 충격파 꼬리 + 땅울림 + 백열 쇳소리", 0)
def _charge_slam_lv3(sr, rng):
    dur = 1.4
    s = zeros(sec(sr, dur))
    mix_into(s, slam_impact(sr, rng, 0.8, 105, 26, 0.15, 1.6), 0)
    sub = mul(tone(sr, 1.0, 50, 24), env_exp(sr, 1.0, 0.32))
    mix_into(s, sub, sec(sr, 0.01), 0.9)  # 충격파 저음
    wave_ = whoosh(sr, 0.8, rng, 2600, 220, q=0.7, a=0.06, r=0.85)
    mix_into(s, wave_, sec(sr, 0.03), 0.55)  # 퍼져 나가는 링
    rum = mul(svf(noise(sr, 1.1, rng), sr, 140, 0.8, 'low'), env_adsr(sr, 1.1, 0.05, 0.0, 1.0, 0.9))
    mix_into(s, rum, sec(sr, 0.05), 0.8)  # 땅울림
    mix_into(s, gravel(sr, rng, 1.2, 16, 0.05, 0.9, 0.3), 0)
    mix_into(s, metal(sr, 0.7, 1300, rng, tau=0.16, jitter=0.015), sec(sr, 0.004), 0.16)  # 백열 쇳소리
    s = softclip(s, 1.8)
    return reverb(s, sr, size=1.1, decay=0.65, wet=0.25)


@sfx('katana_echo', 'PLAYER_ATTACK{weapon:katana,combo:3,phase:echo}', "[보관 — 60라운드 Q6: 파일·manifest 항목 유지, 시스템 연결 끊음] 칼 3타 잔상 베기(본 타격 150ms 뒤 같은 호, 피해 50%). 같은 호를 다시 긋는 얇고 날카로운 바람 + 짧은 잔향 반복", -4)
def _katana_echo(sr, rng):
    w = whoosh(sr, 0.14, rng, 6800, 2200, q=2.2, a=0.12, r=0.6)
    mix_into(w, metal(sr, 0.1, 3300, rng, tau=0.035, jitter=0.02), sec(sr, 0.015), 0.1)
    w = highpass(w, sr, 1400)
    s = zeros(sec(sr, 0.25))
    for t0, g in [(0.0, 1.0), (0.032, 0.45), (0.064, 0.2)]:  # 잔상처럼 겹치는 짧은 반복
        mix_into(s, w, sec(sr, t0), g)
    return s


# --- 56라운드: 가드·자원 · 칼 일섬/분신/간파/대치 · 대검 새 수단 · 단검 · 활 ------------------------
# 결정 근거: parts/producer/decisions/2026-10-04-round-56-weapon-feedback.md Q2·Q3·Q7~Q9·Q10·Q13~Q20·Q28~Q29·Q40~Q43.
# 반드시 katana_echo 뒤에 둔다(시드 = 1000 + 등록 순서). 기존 75개 파일은 바이트 불변이어야 한다.
# 목소리 금지(sound-design 1장): 그로기 숨 헐떡임도 노이즈 포먼트(kha 방식)로만 만든다.
# 칼 자원(검기)은 '칼날 울림'(얇은 강철, 하모닉에 가까운 배음), 대검 차지의 '징'(비조화 징)과 구분한다.
# 음높이는 D 단조 축(D·A)에 둔다 — 차지 '징'(D4·A4·D5)·BGM 과 부딪치지 않게.

BLADE = [(1.0, 1.0), (2.0, 0.35), (2.98, 0.22), (4.1, 0.12), (5.6, 0.06)]


def blade_ring(sr, dur, f, rng, bright=0.0, tau=0.3, vib=0.0):
    """칼날 울림 '시잉': 위로 긁는 짧은 쇠 스침 + 하모닉에 가까운 얇은 배음 울림.
    bright(0~1): 재(어둡게) → 호박 → 백열(윗배음·고역 열림). vib: 미세 떨림 깊이."""
    n = sec(sr, dur)
    out = zeros(n)
    for ratio, amp in BLADE:
        a = amp * (1.0 + 1.5 * bright * (ratio > 2.5))
        fr = f * ratio * (1 + rng.uniform(-0.0015, 0.0015))
        if vib:
            freqs = [fr * (1 + vib * math.sin(TAU * 5.5 * i / sr)) for i in range(n)]
        else:
            freqs = [fr] * n
        osc = tone_f(sr, freqs, 'sine', rng.random())
        e = env_exp(sr, dur, tau / math.sqrt(ratio))
        for i in range(n):
            out[i] += a * e[i] * osc[i]
    out = mul(out, env_adsr(sr, dur, 0.004, 0.0, 1.0, dur * 0.3))
    out = lowpass(out, sr, 2600 + 7000 * bright)
    ns = sec(sr, 0.07)
    sc = svf(noise(sr, 0.07, rng), sr, sweep(sr, ns, 2500, 9000), 2.0, 'band')
    sc = mul(sc, env_adsr(sr, 0.07, 0.03, 0.0, 1.0, 0.04))
    mix_into(out, sc, 0, 0.25 + 0.2 * bright)  # 칼집에서 스치는 '시'
    return out


def tear(sr, dur, rng, f0, f1, rate=70.0, q=1.4):
    """공기 찢김: 아주 빠르게 떨리는(rate Hz) 밴드 스윕 노이즈 — 일반 바람보다 거칠고 찢어진다."""
    n = sec(sr, dur)
    nz = svf(noise(sr, dur, rng), sr, sweep(sr, n, f0, f1), q, 'band')
    jit = [0.5 + 0.5 * math.sin(TAU * rate * i / sr + 1.7 * math.sin(TAU * 9 * i / sr)) for i in range(n)]
    nz = mul(nz, [0.35 + 0.65 * j for j in jit])
    return mul(nz, env_adsr(sr, dur, dur * 0.12, 0.0, 1.0, dur * 0.5))


def sizzle(sr, rng, dur, fc=5200, tau=0.08, q=0.9):
    """지짐: 고역 노이즈 쉿 + 무작위 미세 딸깍(타는 표면)."""
    s = burst(sr, dur, rng, fc=fc, q=q, tau=tau, mode='band')
    mix_into(s, crackle(sr, rng, dur, max(2, int(dur * 40)), 0.35), 0)
    return s


def ash_pop(sr, rng, dur=0.5, f0=150, f1=40, weight=1.0):
    """재 폭발 '펑': 낮은 몸통 + 저역 노이즈 폭발 + 고역 파열 + 쉿 꼬리."""
    s = zeros(sec(sr, dur))
    mix_into(s, thud(sr, min(dur, 0.4), f0, f1, 0.06 * weight), 0, 1.0 * weight)
    mix_into(s, burst(sr, 0.2, rng, fc=420, q=0.6, tau=0.035 * weight, mode='low'), 0, 0.9 * weight)
    mix_into(s, burst(sr, 0.05, rng, fc=3200, q=0.6, tau=0.01), 0, 0.6)
    mix_into(s, click(sr, rng, 0.004, 3500), 0, 0.8)
    hs = mul(svf(noise(sr, dur * 0.8, rng), sr, 4200, 0.7, 'band'), env_adsr(sr, dur * 0.8, 0.02, 0.0, 1.0, dur * 0.7))
    mix_into(s, hs, sec(sr, 0.02), 0.22)
    return s


def heavy_step(sr, rng, g=1.0):
    """무거운 디딤(장화 + 갑옷 덜그럭)."""
    s = thud(sr, 0.12, 120, 55, 0.03)
    mix_into(s, burst(sr, 0.05, rng, fc=900, q=0.7, tau=0.012), 0, 0.5)
    mix_into(s, metal(sr, 0.12, 1100, rng, tau=0.03, jitter=0.05), sec(sr, 0.006), 0.12)
    return scale(s, g)


def arrow_thunk(sr, rng, g=1.0):
    """화살이 흙에 꽂힘: 짧은 톡 + 나무 몸통 떨림."""
    s = burst(sr, 0.03, rng, fc=1800, q=0.8, tau=0.006)
    mix_into(s, thud(sr, 0.08, 260, 150, 0.018), 0, 0.8)
    sh = mul(tone(sr, 0.16, 330, 300, kind='tri'), env_exp(sr, 0.16, 0.035))
    sh = mul(sh, [0.6 + 0.4 * math.sin(TAU * 38 * i / sr) for i in range(len(sh))])
    mix_into(s, lowpass(sh, sr, 1500), sec(sr, 0.006), 0.25)  # 꽂힌 화살대 떨림
    return scale(s, g)


# ---- 가드·자원 ----

@sfx('perfect_guard', 'PERFECT_GUARD', "퍼펙트 가드(가드 누른 직후 0.15s 안 피격 → 피해 0, 튕겨내지 않음). 충격이 흡수되는 짧은 둔탁음 + 맑게 오래 남는 금속 울림(A5·D6). 'PERFECT GUARD' 문구와 같은 프레임", 0)
def _perfect_guard(sr, rng):
    dur = 0.9
    s = zeros(sec(sr, dur))
    mix_into(s, lowpass(thud(sr, 0.12, 140, 70, 0.025), sr, 600), 0, 0.5)  # 흡수된 충격(작게)
    mix_into(s, click(sr, rng, 0.004, 6000), 0, 0.7)
    mix_into(s, bell(sr, 0.85, 880.0, rng, tau=0.55), sec(sr, 0.003), 0.55)
    mix_into(s, bell(sr, 0.7, 1174.66, rng, tau=0.45), sec(sr, 0.003), 0.35)
    sh = mul(tone(sr, 0.6, 4400, 4460), env_adsr(sr, 0.6, 0.02, 0.0, 1.0, 0.5))
    mix_into(s, sh, sec(sr, 0.01), 0.03)  # 맑은 반짝임
    s = highpass(s, sr, 120)
    return reverb(tail(s, sr, 0.05), sr, size=0.7, decay=0.6, wet=0.22)


@sfx('parry_perfect', 'PARRY_SUCCESS{weapon:katana,emphasis:true}', "칼 패링 성공 강조(기존 parry 위에 겹쳐 재생, 'PARRY' 문구·검기 1단 충전과 같은 프레임). 2 kHz 위 대역만: 날카로운 '키잉' + 위로 번뜩이는 스침 + 짧은 울림", -2)
def _parry_perfect(sr, rng):
    dur = 0.75
    s = zeros(sec(sr, dur))
    mix_into(s, blade_ring(sr, 0.7, 1760.0, rng, bright=0.8, tau=0.28), 0, 0.6)
    mix_into(s, metal(sr, 0.4, 3100, rng, tau=0.09, jitter=0.01), 0, 0.3)
    mix_into(s, whoosh(sr, 0.16, rng, 3000, 10000, q=1.6, a=0.15, r=0.7), sec(sr, 0.01), 0.25)
    mix_into(s, click(sr, rng, 0.003, 7000), 0, 0.9)
    s = highpass(s, sr, 1800)
    return reverb(tail(s, sr, 0.04), sr, size=0.5, decay=0.5, wet=0.2)


@sfx('groggy_start', 'GROGGY{phase:start}', "그로기 시작(칼·대검 기력 0, 1.5s). 기운이 빠지는 하강음 + 거친 숨 헐떡임 두 번(노이즈 포먼트, 목소리 아님) + 무릎이 꺾이는 둔탁음 + 갑옷 처짐", -1)
def _groggy_start(sr, rng):
    dur = 1.35
    n = sec(sr, dur)
    s = zeros(n)
    dn = mul(lowpass(tone(sr, 0.7, 220, 70, kind='saw'), sr, 500), env_adsr(sr, 0.7, 0.01, 0.0, 1.0, 0.55))
    mix_into(s, dn, 0, 0.35)  # 기운 빠짐
    mix_into(s, whoosh(sr, 0.45, rng, 2400, 400, q=0.8, a=0.05, r=0.8), 0, 0.3)
    for t0, d, g in [(0.08, 0.32, 1.0), (0.55, 0.42, 0.8)]:  # 헐떡임 두 번(내쉼)
        mix_into(s, kha(sr, rng, d, rough=0.5), sec(sr, t0), 0.55 * g)
    mix_into(s, thud(sr, 0.22, 110, 42, 0.06), sec(sr, 0.18), 0.9)  # 무릎 꺾임
    mix_into(s, metal(sr, 0.3, 700, rng, tau=0.05, jitter=0.06), sec(sr, 0.19), 0.15)
    mix_into(s, burst(sr, 0.12, rng, fc=600, q=0.6, tau=0.03, mode='low'), sec(sr, 0.18), 0.5)
    mix_into(s, metal(sr, 0.2, 1250, rng, tau=0.04, jitter=0.08), sec(sr, 0.36), 0.08)  # 갑옷 처짐
    return tail(s, sr, 0.03)


def _kenki_flame(sr, rng, dur, f0, f1, a):
    n = sec(sr, dur)
    fl = svf(noise(sr, dur, rng), sr, sweep(sr, n, f0, f1), 0.7, 'low')
    return mul(fl, env_adsr(sr, dur, a, dur * 0.2, 0.55, dur * 0.55))


def _kenki(sr, rng, stage):
    """검기 단계(60라운드 Q22 재제작): 1 지글지글 타기 시작 → 2 본격적으로 타오름 → 3 빛남. 울리는 칼날 종소리는 쓰지 않는다."""
    if stage == 1:
        dur = 0.5
        s = zeros(sec(sr, dur))
        mix_into(s, sizzle(sr, rng, 0.45, fc=5200, tau=0.16, q=0.9), 0, 0.7)  # 지글지글
        mix_into(s, crackle(sr, rng, 0.42, 9, 0.35), sec(sr, 0.02))
        n = sec(sr, 0.08)
        sc = svf(noise(sr, 0.08, rng), sr, sweep(sr, n, 2500, 6000), 2.0, 'band')
        mix_into(s, mul(sc, env_adsr(sr, 0.08, 0.02, 0.0, 1.0, 0.05)), 0, 0.3)  # 칼날을 스치는 첫 불씨
        return tail(s, sr, 0.02)
    if stage == 2:
        dur = 0.7
        s = zeros(sec(sr, dur))
        mix_into(s, thud(sr, 0.15, 95, 50, 0.04), 0, 0.5)  # 불이 붙는 '훅'
        mix_into(s, _kenki_flame(sr, rng, 0.62, 260, 2600, 0.05), 0, 1.0)  # 타오름
        mix_into(s, sizzle(sr, rng, 0.5, fc=4600, tau=0.18), sec(sr, 0.04), 0.4)
        mix_into(s, crackle(sr, rng, 0.6, 18, 0.4), sec(sr, 0.03))
        return softclip(tail(s, sr, 0.02), 1.2)
    dur = 0.95
    s = zeros(sec(sr, dur))
    mix_into(s, _kenki_flame(sr, rng, 0.8, 400, 3200, 0.03), 0, 0.6)  # 타오르는 바탕
    n = sec(sr, 0.35)
    gl = svf(noise(sr, 0.35, rng), sr, sweep(sr, n, 3000, 9500), 2.2, 'band')
    mix_into(s, mul(gl, env_adsr(sr, 0.35, 0.12, 0.0, 1.0, 0.2)), 0, 0.5)  # 빛이 번쩍 오름
    m = sec(sr, 0.75)
    sp = svf(noise(sr, 0.75, rng), sr, 7500, 1.5, 'band')
    sp = mul(sp, [0.35 + 0.65 * abs(math.sin(TAU * 17 * i / sr)) * abs(math.sin(TAU * 5.3 * i / sr)) for i in range(m)])
    mix_into(s, mul(sp, env_adsr(sr, 0.75, 0.15, 0.0, 1.0, 0.45)), sec(sr, 0.1), 0.35)  # 반짝임
    for f in (3520.0, 3535.0, 5274.0):  # 맑은 빛 한 겹(종이 아닌 지속 사인, 아주 작게)
        mix_into(s, mul(tone(sr, 0.7, f), env_adsr(sr, 0.7, 0.15, 0.0, 1.0, 0.45)), sec(sr, 0.12), 0.012)
    mix_into(s, crackle(sr, rng, 0.8, 12, 0.3), sec(sr, 0.03))
    return reverb(tail(s, sr, 0.03), sr, size=0.6, decay=0.5, wet=0.18)


@sfx('kenki_stage1', 'WEAPON_GAUGE{stage:1,delta>0}', "검기 1단 도달(재빛 칼날, 60라운드 Q22 재제작). 지글지글 타기 시작: 칼날을 스치는 첫 불씨 + 지짐 쉿 + 잔 타닥", -6)
def _kenki_stage1(sr, rng):
    return _kenki(sr, rng, 1)


@sfx('kenki_stage2', 'WEAPON_GAUGE{stage:2,delta>0}', "검기 2단 도달(호박빛, 60라운드 Q22 재제작). 본격적으로 타오름: 불이 붙는 '훅' + 컷오프가 열리며 치솟는 불길 + 지짐 + 촘촘한 타닥", -5)
def _kenki_stage2(sr, rng):
    return _kenki(sr, rng, 2)


@sfx('kenki_stage3', 'WEAPON_GAUGE{stage:3,delta>0}', "검기 3단 도달(백열, 그림자 분신 준비 · 60라운드 Q22 재제작). 빛남: 타오르는 바탕 위로 번쩍 오르는 고역 + 일렁이는 반짝임 + 아주 작은 맑은 빛 한 겹(A7·E8 근처 지속음, 종 아님) + 타닥, 짧은 울림", -4)
def _kenki_stage3(sr, rng):
    return _kenki(sr, rng, 3)


@sfx('utbun_full', 'UTBUN_CHANGED{full:true}', "울분 가득(대검, 가득 차는 순간 1회만 · 반복음 없음 — 56라운드 Q47). 낮게 끓어오르는 잔불 + 불씨 '훅' 치솟음 + 타닥 + 칼이 달아오르는 쇳소리", -3)
def _utbun_full(sr, rng):
    dur = 1.1
    n = sec(sr, dur)
    s = zeros(n)
    boil = svf(noise(sr, dur, rng), sr, sweep(sr, n, 120, 320), 1.2, 'low')
    am = normalize(lowpass([rng.uniform(-1, 1) for _ in range(n)], sr, 18), 1.0)
    boil = mul(boil, [0.5 + 0.5 * a for a in am])
    boil = mul(boil, env_adsr(sr, dur, 0.35, 0.0, 1.0, 0.45, curve=1.6))
    mix_into(s, boil, 0, 1.0)  # 끓어오름
    fl = svf(noise(sr, 0.6, rng), sr, sweep(sr, sec(sr, 0.6), 250, 2200), 0.9, 'band')
    fl = mul(fl, env_adsr(sr, 0.6, 0.08, 0.0, 1.0, 0.45))
    mix_into(s, fl, sec(sr, 0.3), 0.55)  # 불씨 '훅'
    mix_into(s, thud(sr, 0.25, 90, 45, 0.07), sec(sr, 0.3), 0.6)
    mix_into(s, crackle(sr, rng, 0.9, 18, 0.4), sec(sr, 0.15))
    hot = mul(lowpass(tone(sr, 0.7, 293.66, 296, kind='saw'), sr, 900), env_adsr(sr, 0.7, 0.25, 0.0, 1.0, 0.4))
    mix_into(s, hot, sec(sr, 0.3), 0.12)  # 달아오른 쇠 험(D4)
    return tail(s, sr, 0.03)


@sfx('brand_apply', 'BRAND_CHANGED{delta>0}', "낙인 1스택(단검). 살짝 지지는 '칙' + 작은 틱. 등 뒤 2스택일 때는 같은 소리를 rate 1.1 로 1회 권장", -7)
def _brand_apply(sr, rng):
    s = sizzle(sr, rng, 0.17, fc=5600, tau=0.05, q=1.0)
    mix_into(s, click(sr, rng, 0.003, 4200), 0, 0.6)
    mix_into(s, mul(tone(sr, 0.05, 1900, 1500), env_exp(sr, 0.05, 0.012)), 0, 0.12)
    return tail(s, sr, 0.02)


@sfx('brand_burst', 'BRAND_BURST', "낙인 기폭(그림자 걸음으로 대상 뒤 이동 시 전부 폭발). 숨 들이켜듯 빨려드는 짧은 역바람 → 재 폭발 '펑' + 지지는 꼬리. 파일 0.06s 가 폭발 순간", -1)
def _brand_burst(sr, rng):
    dur = 0.75
    s = zeros(sec(sr, dur))
    pre = mul(svf(noise(sr, 0.06, rng), sr, sweep(sr, sec(sr, 0.06), 900, 5000), 1.4, 'band'),
              [(i / sec(sr, 0.06)) ** 2 for i in range(sec(sr, 0.06))])
    mix_into(s, pre, 0, 0.5)
    t = sec(sr, 0.06)
    mix_into(s, ash_pop(sr, rng, 0.55, 170, 42, 1.0), t, 1.0)
    mix_into(s, sizzle(sr, rng, 0.45, fc=4800, tau=0.12), t + sec(sr, 0.03), 0.35)
    s = softclip(s, 1.3)
    return reverb(tail(s, sr, 0.04), sr, size=0.5, decay=0.45, wet=0.12)


@sfx('overheat_burst', 'OVERHEAT{full:true}', "과열 100% 자동 폭발(단검, 주변 낙인 일괄 폭발 + 식힘). 엇갈린 재 폭발 4번 + 낮은 폭음 + 길게 식는 증기 쉿", 0)
def _overheat_burst(sr, rng):
    dur = 1.5
    n = sec(sr, dur)
    s = zeros(n)
    mix_into(s, ash_pop(sr, rng, 0.8, 120, 30, 1.5), 0, 1.0)
    for t0, f0, g in [(0.05, 190, 0.6), (0.11, 160, 0.55), (0.19, 210, 0.45), (0.26, 175, 0.4)]:
        mix_into(s, ash_pop(sr, rng, 0.4, f0, 50, 0.8), sec(sr, t0), g)
    st = svf(noise(sr, 1.2, rng), sr, sweep(sr, sec(sr, 1.2), 6500, 2500), 0.7, 'band')
    st = mul(st, env_adsr(sr, 1.2, 0.08, 0.0, 1.0, 1.0))
    mix_into(s, st, sec(sr, 0.25), 0.35)  # 식는 증기
    mix_into(s, crackle(sr, rng, 1.1, 20, 0.3), sec(sr, 0.2))
    s = softclip(s, 1.6)
    return reverb(s, sr, size=0.8, decay=0.55, wet=0.15)


@sfx('breath_focus', 'BREATH_FOCUS{phase:start}', "숨(활) 가득 → 감속 정밀 조준 진입. 길게 빨려드는 바람(목소리 아님) + 소리가 먹먹해지며 내려앉는 저음 + 아주 희미한 고음 한 가닥", -3)
def _breath_focus(sr, rng):
    dur = 0.95
    n = sec(sr, dur)
    s = zeros(n)
    nz = svf(noise(sr, 0.45, rng), sr, sweep(sr, sec(sr, 0.45), 500, 3200), 1.2, 'band')
    nz = mul(nz, [((i / sec(sr, 0.45)) ** 1.8) for i in range(sec(sr, 0.45))])
    mix_into(s, nz, 0, 0.6)  # 빨려드는 바람
    lo = mul(tone(sr, 0.6, 110, 46), env_adsr(sr, 0.6, 0.01, 0.0, 1.0, 0.5))
    mix_into(s, lo, sec(sr, 0.42), 0.9)  # 내려앉음(감속)
    mix_into(s, lowpass(burst(sr, 0.2, rng, fc=300, q=0.6, tau=0.05, mode='low'), sr, 400), sec(sr, 0.42), 0.5)
    hi = mul(tone(sr, 0.5, 2349.3, 2349.3), env_adsr(sr, 0.5, 0.15, 0.0, 1.0, 0.3))
    mix_into(s, hi, sec(sr, 0.44), 0.025)  # 집중의 이질 한 가닥(D7)
    return reverb(tail(s, sr, 0.03), sr, size=0.9, decay=0.5, wet=0.18)


# ---- 칼 ----

@sfx('issen_dash', 'PLAYER_SKILL{weapon:katana,move:issen,phase:dash}', "일섬 돌진(앞으로 4칸, 적 관통, 무적). 칼집 딸깍 + 공기를 찢는 아주 빠른 고역 바람 + 발 디딤. 발도 순간 = 0s", -1)
def _issen_dash(sr, rng):
    dur = 0.36
    s = zeros(sec(sr, dur))
    mix_into(s, click(sr, rng, 0.004, 3800), 0, 0.9)  # 코이구치 딸깍
    mix_into(s, thud(sr, 0.06, 160, 90, 0.015), 0, 0.5)  # 디딤
    mix_into(s, tear(sr, 0.28, rng, 1800, 7500, rate=85.0, q=1.6), sec(sr, 0.01), 0.9)
    mix_into(s, whoosh(sr, 0.22, rng, 6500, 2400, q=2.0, a=0.08, r=0.6), sec(sr, 0.03), 0.6)
    mix_into(s, metal(sr, 0.18, 2900, rng, tau=0.05, jitter=0.02), sec(sr, 0.02), 0.12)
    return tail(s, sr, 0.03)


@sfx('issen_burst', 'PLAYER_SKILL{weapon:katana,move:issen,phase:burst}', "일섬 선이 터짐(돌진 후 잠시 뒤, _solo 선 끝 폭발 연출과 같은 프레임). 선을 따라 촘촘히 번지는 날카로운 파열 + 낮은 폭음 + 밝은 칼날 울림", -1)
def _issen_burst(sr, rng):
    dur = 0.8
    s = zeros(sec(sr, dur))
    for k in range(9):  # 선을 따라 번지는 파열(0 → 0.1 s)
        t0 = 0.012 * k
        mix_into(s, burst(sr, 0.04, rng, fc=2600 + 350 * k, q=0.8, tau=0.008), sec(sr, t0), 0.7 - 0.04 * k)
    mix_into(s, thud(sr, 0.35, 130, 40, 0.07), 0, 0.9)
    mix_into(s, burst(sr, 0.2, rng, fc=380, q=0.6, tau=0.04, mode='low'), 0, 0.7)
    mix_into(s, blade_ring(sr, 0.6, 1174.66, rng, bright=0.7, tau=0.22), sec(sr, 0.02), 0.25)
    mix_into(s, whoosh(sr, 0.4, rng, 5000, 1500, q=1.0, a=0.05, r=0.8), sec(sr, 0.01), 0.3)
    s = softclip(s, 1.3)
    return reverb(tail(s, sr, 0.03), sr, size=0.6, decay=0.5, wet=0.15)


@sfx('shadow_clone', 'PLAYER_SKILL{weapon:katana,move:issen,phase:clone}', "그림자 분신 질주(검기 3단 일섬, 일섬 0.2s 뒤 출발 → 0.37s 뒤 도착 베기). 빨려드는 어두운 역바람(이질) + 낮게 겹친 일섬 찢김 + 도착 시 0.37s 에 낮은 베기 '슥'", -2)
def _shadow_clone(sr, rng):
    dur = 0.62
    n = sec(sr, dur)
    s = zeros(n)
    m = sec(sr, 0.37)
    nz = svf(noise(sr, 0.37, rng), sr, sweep(sr, m, 400, 2600), 1.4, 'band')
    nz = mul(nz, [((i / m) ** 1.6) for i in range(m)])
    mix_into(s, nz, 0, 0.55)  # 역바람(어두운 재 실루엣이 달려옴)
    mix_into(s, lowpass(tear(sr, 0.34, rng, 900, 3500, rate=60.0, q=1.3), sr, 3000), sec(sr, 0.03), 0.5)
    lo = mul(tone(sr, 0.37, 70, 140), [((i / m) ** 1.2) for i in range(m)])
    mix_into(s, lo, 0, 0.25)
    cut = whoosh(sr, 0.14, rng, 4200, 1200, q=1.8, a=0.1, r=0.6)
    mix_into(cut, metal(sr, 0.12, 1900, rng, tau=0.04, jitter=0.03), sec(sr, 0.01), 0.15)
    mix_into(s, lowpass(cut, sr, 4500), m, 0.9)  # 도착 베기
    mix_into(s, thud(sr, 0.12, 120, 50, 0.03), m, 0.4)
    return reverb(tail(s, sr, 0.03), sr, size=0.6, decay=0.5, wet=0.22)


@sfx('katana_counter', 'PLAYER_SKILL{weapon:katana,move:counter}', "간파 반격(패링 직후 0.4s 안 좌클릭). 짧게 숨 죽인 정적 뒤 날카롭고 빠른 일격 + 밝은 칼날 울림 + 단단한 적중 머리", -1)
def _katana_counter(sr, rng):
    dur = 0.45
    s = zeros(sec(sr, dur))
    mix_into(s, whoosh(sr, 0.12, rng, 7200, 2000, q=2.0, a=0.1, r=0.5), 0, 0.9)
    mix_into(s, tear(sr, 0.1, rng, 3000, 8000, rate=90.0, q=1.6), 0, 0.4)
    mix_into(s, burst(sr, 0.05, rng, fc=2600, q=0.7, tau=0.01), sec(sr, 0.06), 0.7)
    mix_into(s, thud(sr, 0.1, 170, 70, 0.025), sec(sr, 0.06), 0.6)
    mix_into(s, blade_ring(sr, 0.35, 1174.66, rng, bright=0.6, tau=0.15), sec(sr, 0.06), 0.3)
    return tail(s, sr, 0.02)


@sfx('katana_iai_hold', 'PLAYER_SKILL{weapon:katana,move:iai,phase:hold}', "대치 일격 납도 대치 루프(2.0s, 좌클릭 누르는 동안). 낮게 조여 오는 울림 + 칼집 속 희미한 칼날 험 + 느린 맥박. 아주 작게", -12, loop=True)
def _katana_iai_hold(sr, rng):
    dur = 2.0
    n = sec(sr, dur)
    g = wrap2(lambda x: lowpass(x, sr, 160), tone_loop(sr, n, 73.42, 'saw'))  # D2
    g = mul(g, lfo_loop(sr, n, 0.5, 0.25, 0.75))
    beat = tone_loop(sr, n, 146.83, 'sine')
    mix_into(g, mul(beat, lfo_loop(sr, n, 1.5, 0.5, 0.5)), 0, 0.12)
    hum = mul(tone_loop(sr, n, 1760.0, 'sine'), lfo_loop(sr, n, 0.5, 0.5, 0.5, 0.75))
    mix_into(g, hum, 0, 0.035)  # 칼날 험(A6)
    hum2 = tone_loop(sr, n, 1763.0, 'sine')  # 3 Hz 떨림
    mix_into(g, mul(hum2, lfo_loop(sr, n, 0.5, 0.5, 0.5, 0.75)), 0, 0.02)
    air = wrap2(lambda x: svf(x, sr, 900, 0.7, 'band'), noise_loop(sr, n, rng))
    mix_into(g, mul(air, lfo_loop(sr, n, 0.5, 0.4, 0.6)), 0, 0.08)
    for t0 in (0.0, 1.0):  # 느린 맥박(1 s 간격) — 루프 경계에서 감겨 이어진다
        mix_into(g, lowpass(thud(sr, 0.18, 70, 45, 0.05), sr, 300), sec(sr, t0), 0.35, wrap=True)
    return g


@sfx('katana_iai_release', 'PLAYER_SKILL{weapon:katana,move:iai,phase:release}', "대치 일격 발도(좌클릭 떼는 순간). 코이구치 딸깍 → 30ms 뒤 번개 같은 발도 바람 + 단단한 칼날 울림 + 낮은 무게. 넣기 첫 타 치명과 연결", 0)
def _katana_iai_release(sr, rng):
    dur = 0.65
    s = zeros(sec(sr, dur))
    mix_into(s, click(sr, rng, 0.005, 3200), 0, 1.0)
    mix_into(s, metal(sr, 0.06, 2300, rng, tau=0.012, jitter=0.03), 0, 0.3)
    t = sec(sr, 0.03)
    mix_into(s, tear(sr, 0.2, rng, 2200, 9000, rate=95.0, q=1.8), t, 0.8)
    mix_into(s, whoosh(sr, 0.16, rng, 8000, 2200, q=2.2, a=0.06, r=0.6), t, 0.7)
    mix_into(s, blade_ring(sr, 0.55, 880.0, rng, bright=0.9, tau=0.25), t + sec(sr, 0.02), 0.35)
    mix_into(s, thud(sr, 0.18, 120, 50, 0.04), t, 0.6)
    mix_into(s, burst(sr, 0.12, rng, fc=500, q=0.6, tau=0.025, mode='low'), t, 0.4)
    s = softclip(s, 1.2)
    return reverb(tail(s, sr, 0.03), sr, size=0.55, decay=0.5, wet=0.15)


# ---- 대검 ----

@sfx('gs_plunge', 'PLAYER_CHARGE{weapon:greatsword,phase:release,mode:plunge}', "[보관 — 60라운드 Q6: 파일·manifest 항목 유지, 시스템 연결 끊음] 땅 꽂기(개성 발현 후 차지 = 휘두르지 않고 칼을 땅에 꽂음). 쇠가 흙·돌을 파고드는 '푹' + 무거운 둔탁음 + 칼날 떨림. 파일 0s = 꽂히는 순간, 뒤이어 gs_crack", -1)
def _gs_plunge(sr, rng):
    dur = 0.65
    s = zeros(sec(sr, dur))
    mix_into(s, thud(sr, 0.4, 100, 34, 0.08), 0, 1.3)
    mix_into(s, burst(sr, 0.18, rng, fc=320, q=0.6, tau=0.035, mode='low'), 0, 1.0)
    dig = svf(noise(sr, 0.14, rng), sr, sweep(sr, sec(sr, 0.14), 2400, 700), 1.6, 'band')
    mix_into(s, mul(dig, env_exp(sr, 0.14, 0.04)), 0, 0.6)  # 파고듦
    mix_into(s, gravel(sr, rng, 0.4, 7, 0.02, 0.25, 0.28), 0)
    vib = metal(sr, 0.5, 520, rng, tau=0.14, jitter=0.01)
    vib = mul(vib, [0.6 + 0.4 * math.sin(TAU * 21 * i / sr) for i in range(len(vib))])
    mix_into(s, vib, sec(sr, 0.01), 0.22)  # 꽂힌 칼날 떨림
    s = softclip(s, 1.4)
    return reverb(tail(s, sr, 0.04), sr, size=0.6, decay=0.5, wet=0.12)


@sfx('gs_crack', 'PLAYER_CHARGE{weapon:greatsword,phase:release,mode:plunge,part:crack}', "[보관 — 60라운드 Q6: 파일·manifest 항목 유지, 시스템 연결 끊음] 균열 충격파(꽂은 자리에서 마우스 방향으로 뻗는 균열). 앞으로 달려가는 돌 갈라짐 + 낮은 폭음 + 멀어지는 땅울림. gs_plunge 와 같은 프레임 또는 40ms 뒤", 0)
def _gs_crack(sr, rng):
    dur = 1.0
    n = sec(sr, dur)
    s = zeros(n)
    for k in range(14):  # 앞으로 뻗어 나가는 갈라짐(점점 작고 어둡게)
        t0 = 0.02 + 0.035 * k + rng.uniform(-0.006, 0.006)
        g = 0.75 * (1 - k / 16)
        mix_into(s, burst(sr, 0.05, rng, fc=max(500, 2200 - 110 * k), q=0.9, tau=0.01), sec(sr, t0), g)
        mix_into(s, thud(sr, 0.06, 160 - 4 * k, 70, 0.015), sec(sr, t0), g * 0.4)
    mix_into(s, mul(tone(sr, 0.8, 55, 26), env_exp(sr, 0.8, 0.25)), 0, 0.9)  # 충격파 저음
    rum = mul(svf(noise(sr, 0.9, rng), sr, 150, 0.8, 'low'), env_adsr(sr, 0.9, 0.04, 0.0, 1.0, 0.8))
    mix_into(s, rum, sec(sr, 0.02), 0.8)
    mix_into(s, gravel(sr, rng, 0.9, 12, 0.05, 0.7, 0.25), 0)
    s = softclip(s, 1.5)
    return reverb(s, sr, size=0.9, decay=0.55, wet=0.18)


@sfx('gs_drag', 'PLAYER_ATTACK{weapon:greatsword,combo:3,phase:recover}', "대검 3타 뒤 몸이 끌려감(짧게, 56라운드 Q46: 3타에만). 칼끝이 돌바닥을 긁는 쇳소리 + 자갈 + 미끄러지는 장화", -5)
def _gs_drag(sr, rng):
    dur = 0.36
    n = sec(sr, dur)
    s = zeros(n)
    sc = svf(noise(sr, 0.32, rng), sr, sweep(sr, sec(sr, 0.32), 2800, 1400), 3.0, 'band')
    grind = [0.5 + 0.5 * math.sin(TAU * 27 * i / sr) for i in range(len(sc))]
    sc = mul(mul(sc, grind), env_adsr(sr, 0.32, 0.02, 0.0, 1.0, 0.22))
    mix_into(s, sc, 0, 0.6)  # 칼끝 긁힘
    mix_into(s, metal(sr, 0.25, 980, rng, tau=0.06, jitter=0.04), 0, 0.1)
    sl = mul(svf(noise(sr, 0.28, rng), sr, 500, 0.8, 'low'), env_adsr(sr, 0.28, 0.02, 0.0, 1.0, 0.2))
    mix_into(s, sl, 0, 0.6)  # 장화 미끄러짐
    mix_into(s, gravel(sr, rng, 0.34, 6, 0.01, 0.26, 0.22), 0)
    return tail(s, sr, 0.02)


@sfx('gs_tackle', 'PLAYER_SKILL{weapon:greatsword,move:tackle}', "어깨 태클(대검 대쉬 공격). 무거운 박차기 + 낮은 돌진 바람 + 갑옷 덜그럭 + 어깨 몸통 충돌 '쿵'(0.16s). 적중 시 hit_enemy 를 겹쳐 재생", -1)
def _gs_tackle(sr, rng):
    dur = 0.5
    s = zeros(sec(sr, dur))
    mix_into(s, heavy_step(sr, rng), 0, 0.8)
    mix_into(s, whoosh(sr, 0.22, rng, 400, 1400, q=0.9, a=0.2, r=0.5), 0, 0.7)
    for t0 in (0.03, 0.08, 0.12):
        mix_into(s, metal(sr, 0.08, rng.uniform(900, 1400), rng, tau=0.02, jitter=0.06), sec(sr, t0), 0.12)
    t = sec(sr, 0.16)
    mix_into(s, thud(sr, 0.25, 110, 40, 0.05), t, 1.1)
    mix_into(s, burst(sr, 0.12, rng, fc=700, q=0.6, tau=0.025, mode='low'), t, 0.8)
    mix_into(s, metal(sr, 0.2, 800, rng, tau=0.05, jitter=0.04), t, 0.2)
    s = softclip(s, 1.4)
    return tail(s, sr, 0.02)


@sfx('gs_brace_upswing', 'PLAYER_SKILL{weapon:greatsword,move:brace_upswing}', "버티기 올려베기(가드 중 좌클릭, 맞아도 안 끊김). 발을 박는 디딤 + 쇠 긁으며 들어 올림 → 아래에서 위로 치솟는 무거운 바람. 울분 소모 강화 시 rate 0.92 + utbun_full 의 불씨 겹침 권장", -1)
def _gs_brace_upswing(sr, rng):
    dur = 0.55
    s = zeros(sec(sr, dur))
    mix_into(s, heavy_step(sr, rng), 0, 0.9)
    sc = svf(noise(sr, 0.12, rng), sr, sweep(sr, sec(sr, 0.12), 1200, 3200), 2.5, 'band')
    mix_into(s, mul(sc, env_adsr(sr, 0.12, 0.03, 0.0, 1.0, 0.06)), sec(sr, 0.02), 0.35)
    mix_into(s, whoosh(sr, 0.36, rng, 180, 1300, q=1.0, a=0.45, r=0.4), sec(sr, 0.06), 1.0)
    mix_into(s, mul(lowpass(tone(sr, 0.3, 60, 110, kind='saw'), sr, 300), env_adsr(sr, 0.3, 0.2, 0.0, 1.0, 0.1)), sec(sr, 0.08), 0.35)
    mix_into(s, metal(sr, 0.18, 700, rng, tau=0.05, jitter=0.03), sec(sr, 0.3), 0.12)
    return tail(s, sr, 0.03)


@sfx('gs_leap', 'PLAYER_SKILL{weapon:greatsword,move:leap,phase:takeoff}', "공중제비 도약(차지 중 스페이스, 차지 단계 유지). 무겁게 박차는 디딤 + 갑옷 출렁 + 몸이 도는 바람 2회(공중제비)", -2)
def _gs_leap(sr, rng):
    dur = 0.5
    s = zeros(sec(sr, dur))
    mix_into(s, heavy_step(sr, rng, 1.2), 0, 1.0)
    mix_into(s, burst(sr, 0.1, rng, fc=500, q=0.6, tau=0.025, mode='low'), 0, 0.6)
    mix_into(s, whoosh(sr, 0.2, rng, 500, 1800, q=1.0, a=0.3, r=0.5), sec(sr, 0.03), 0.6)
    mix_into(s, whoosh(sr, 0.2, rng, 700, 2200, q=1.0, a=0.3, r=0.5), sec(sr, 0.2), 0.45)
    for t0 in (0.05, 0.22):
        mix_into(s, metal(sr, 0.1, rng.uniform(1000, 1500), rng, tau=0.025, jitter=0.06), sec(sr, t0), 0.1)
    return tail(s, sr, 0.03)


@sfx('gs_leap_slam', 'PLAYER_SKILL{weapon:greatsword,move:leap,phase:land}', "도약 착지 찍기(판정 프레임 = 0s). 몸무게가 실린 착지 + 지면 강타 + 갑옷 쿵 + 흙먼지. 차지 1단 이상이면 charge_slam_lvN 을 같은 프레임에 겹쳐 재생(0단이면 이것만)", 0)
def _gs_leap_slam(sr, rng):
    dur = 0.9
    s = zeros(sec(sr, dur))
    mix_into(s, slam_impact(sr, rng, 0.6, 115, 32, 0.1, 1.2), 0, 1.0)
    mix_into(s, thud(sr, 0.2, 90, 45, 0.04), sec(sr, 0.03), 0.6)  # 몸이 따라 내려앉음
    mix_into(s, metal(sr, 0.25, 900, rng, tau=0.05, jitter=0.06), sec(sr, 0.03), 0.18)
    dust = mul(svf(noise(sr, 0.6, rng), sr, 1200, 0.6, 'band'), env_adsr(sr, 0.6, 0.03, 0.0, 1.0, 0.5))
    mix_into(s, dust, sec(sr, 0.02), 0.25)
    mix_into(s, gravel(sr, rng, 0.7, 9, 0.03, 0.5, 0.3), 0)
    s = softclip(s, 1.5)
    return reverb(tail(s, sr, 0.03), sr, size=0.7, decay=0.5, wet=0.14)


@sfx('gs_guard_rush', 'PLAYER_SKILL{weapon:greatsword,move:guard_rush}', "막다가 떼면 돌진(퍼펙트 가드 직후 우클릭 떼기, 밀쳐내기 대체). 가드를 풀며 터지는 압력 + 앞으로 밀고 나가는 무거운 바람 + 연속 디딤 + 갑옷", 0)
def _gs_guard_rush(sr, rng):
    dur = 0.6
    s = zeros(sec(sr, dur))
    mix_into(s, thud(sr, 0.3, 100, 32, 0.07), 0, 1.0)
    mix_into(s, burst(sr, 0.12, rng, fc=650, q=0.6, tau=0.03, mode='low'), 0, 0.8)
    mix_into(s, metal(sr, 0.25, 1100, rng, tau=0.06, jitter=0.02), 0, 0.2)
    mix_into(s, whoosh(sr, 0.42, rng, 350, 2000, q=0.9, a=0.15, r=0.6), sec(sr, 0.02), 0.85)
    for k, t0 in enumerate((0.06, 0.15, 0.24)):
        mix_into(s, heavy_step(sr, rng, 0.8 - 0.15 * k), sec(sr, t0), 1.0)
    s = softclip(s, 1.4)
    return tail(s, sr, 0.03)


# ---- 단검 ----

@sfx('dagger_backstab', 'PLAYER_SKILL{weapon:dagger,move:backstab}', "등 뒤 치명 찌르기(그림자 걸음 직후 좌클릭). 짧은 숨 같은 정적 → 깊이 파고드는 찌르기 + 날 박힘 + 밝은 치명 울림. 적중 프레임 = 0.04s", -1)
def _dagger_backstab(sr, rng):
    dur = 0.45
    s = zeros(sec(sr, dur))
    mix_into(s, whoosh(sr, 0.06, rng, 4000, 9000, q=1.8, a=0.5, r=0.3), 0, 0.5)
    t = sec(sr, 0.04)
    pierce = svf(noise(sr, 0.09, rng), sr, sweep(sr, sec(sr, 0.09), 3500, 900), 2.2, 'band')
    mix_into(s, mul(pierce, env_exp(sr, 0.09, 0.025)), t, 0.8)  # 파고듦
    mix_into(s, burst(sr, 0.05, rng, fc=2000, q=0.7, tau=0.01), t, 0.7)
    mix_into(s, thud(sr, 0.12, 150, 55, 0.03), t, 0.8)
    mix_into(s, metal(sr, 0.35, 2200, rng, tau=0.09, jitter=0.01), t, 0.35)  # 치명 울림
    mix_into(s, blade_ring(sr, 0.3, 1760.0, rng, bright=0.5, tau=0.12), t, 0.15)
    return tail(s, sr, 0.03)


def _flurry(sr, rng, f0, f1, fc, body):
    s = whoosh(sr, 0.05, rng, f0, f1, q=1.9, a=0.15, r=0.5)
    mix_into(s, burst(sr, 0.025, rng, fc=fc, q=0.8, tau=0.005), sec(sr, 0.02), 0.6)
    mix_into(s, thud(sr, 0.04, body, body * 0.5, 0.01), sec(sr, 0.02), 0.35)
    mix_into(s, click(sr, rng, 0.002, 6500), 0, 0.3)
    return tail(s, sr, 0.02)


@sfx('dagger_flurry1', 'PLAYER_ATTACK{weapon:dagger,move:flurry,variant:1}', "고속 난타(좌클릭 홀드) 짧은 찌르기 변주 1/4. 찌를 때마다 1~4 중 무작위(직전과 다른 것) + ±3% rate 권장", -5)
def _dagger_flurry1(sr, rng):
    return _flurry(sr, rng, 7500, 3000, 2400, 190)


@sfx('dagger_flurry2', 'PLAYER_ATTACK{weapon:dagger,move:flurry,variant:2}', "고속 난타 변주 2/4(조금 낮고 둔탁)", -5)
def _dagger_flurry2(sr, rng):
    return _flurry(sr, rng, 6200, 2400, 1900, 160)


@sfx('dagger_flurry3', 'PLAYER_ATTACK{weapon:dagger,move:flurry,variant:3}', "고속 난타 변주 3/4(높고 가벼움)", -5)
def _dagger_flurry3(sr, rng):
    return _flurry(sr, rng, 8800, 3600, 3000, 220)


@sfx('dagger_flurry4', 'PLAYER_ATTACK{weapon:dagger,move:flurry,variant:4}', "고속 난타 변주 4/4(짧은 쇠 스침이 섞임)", -5)
def _dagger_flurry4(sr, rng):
    s = _flurry(sr, rng, 7000, 2800, 2600, 180)
    mix_into(s, metal(sr, 0.05, 3400, rng, tau=0.012, jitter=0.03), sec(sr, 0.015), 0.12)
    return s


# ---- 활 ----

@sfx('bow_release_weak', 'PLAYER_SECONDARY{kind:aimedshot,phase:release,power:weak}', "일찍 놓은 약한 화살. 덜 당긴 시위의 둔하고 짧은 '퉁' + 힘없이 흔들리는 바람 + 연기 같은 쉿", -4)
def _bow_release_weak(sr, rng):
    s = pluck(sr, 0.18, 240, rng, damp=0.97, bright=0.45)
    s = mul(s, env_exp(sr, 0.18, 0.04))
    s = lowpass(s, sr, 1600)
    w = whoosh(sr, 0.2, rng, 1500, 2600, q=1.0, a=0.2, r=0.6)
    w = mul(w, [0.6 + 0.4 * math.sin(TAU * 13 * i / sr) for i in range(len(w))])  # 흔들림
    mix_into(s, w, sec(sr, 0.01), 0.3)
    hs = mul(svf(noise(sr, 0.22, rng), sr, 3000, 0.7, 'band'), env_adsr(sr, 0.22, 0.04, 0.0, 1.0, 0.16))
    mix_into(s, hs, sec(sr, 0.04), 0.08)
    mix_into(s, thud(sr, 0.05, 200, 130, 0.012), 0, 0.35)
    return tail(s, sr, 0.03)


@sfx('bow_release_perfect', 'PLAYER_SECONDARY{kind:aimedshot,phase:release,power:perfect}', "완벽 놓기(가득 당긴 직후 0.15s 안). 깊고 단단한 시위 + 맑은 '팅'(A5) + 길게 꿰뚫는 바람 + 짧은 울림. 화살 미소모·숨 회복과 같은 프레임", 0)
def _bow_release_perfect(sr, rng):
    s = pluck(sr, 0.45, 110, rng, damp=0.992, bright=0.7)
    s = mul(s, env_exp(sr, 0.45, 0.13))
    mix_into(s, whoosh(sr, 0.4, rng, 1800, 9000, q=1.1, a=0.08, r=0.75), sec(sr, 0.01), 0.6)
    mix_into(s, thud(sr, 0.14, 190, 70, 0.035), 0, 0.8)
    mix_into(s, bell(sr, 0.55, 880.0, rng, tau=0.35), sec(sr, 0.004), 0.22)
    mix_into(s, click(sr, rng, 0.003, 6500), 0, 0.6)
    return reverb(tail(s, sr, 0.05), sr, size=0.55, decay=0.5, wet=0.15)


@sfx('arrow_rain_launch', 'PLAYER_SKILL{weapon:bow,move:arrow_rain,phase:launch}', "화살비 발사(당긴 채 좌클릭, 하늘로 3발). 빠른 시위 세 번(0/0.06/0.12s) + 하늘로 솟아 멀어지는 바람", -2)
def _arrow_rain_launch(sr, rng):
    dur = 0.75
    s = zeros(sec(sr, dur))
    for k, t0 in enumerate((0.0, 0.06, 0.12)):
        p = mul(pluck(sr, 0.2, 170 + 15 * k, rng, damp=0.985, bright=0.7), env_exp(sr, 0.2, 0.06))
        mix_into(s, p, sec(sr, t0), 0.8)
        mix_into(s, thud(sr, 0.06, 210, 120, 0.015), sec(sr, t0), 0.4)
        mix_into(s, whoosh(sr, 0.18, rng, 2500, 6500, q=1.2, a=0.2, r=0.6), sec(sr, t0 + 0.01), 0.25)
    up = whoosh(sr, 0.55, rng, 3000, 7500, q=1.4, a=0.15, r=0.8)
    mix_into(s, lowpass(up, sr, sweep(sr, len(up), 9000, 2500)), sec(sr, 0.14), 0.3)  # 멀어짐
    return tail(s, sr, 0.03)


@sfx('arrow_rain_impact', 'PLAYER_SKILL{weapon:bow,move:arrow_rain,phase:impact}', "화살비 낙하(커서 원 범위). 짧게 내려꽂히는 휘파람(0~0.1s) → 흙에 꽂히는 '툭' 셋(0.1/0.16/0.23s) + 화살대 떨림. 첫 꽂힘 = 0.1s", -2)
def _arrow_rain_impact(sr, rng):
    dur = 0.6
    s = zeros(sec(sr, dur))
    wh = mul(tone(sr, 0.1, 2600, 1500), env_adsr(sr, 0.1, 0.06, 0.0, 1.0, 0.02))
    mix_into(s, wh, 0, 0.06)  # 내려오는 휘파람
    mix_into(s, whoosh(sr, 0.11, rng, 5000, 2200, q=1.4, a=0.6, r=0.2), 0, 0.3)
    for k, t0 in enumerate((0.1, 0.16, 0.23)):
        mix_into(s, arrow_thunk(sr, rng), sec(sr, t0), 0.9 - 0.12 * k)
    mix_into(s, gravel(sr, rng, 0.5, 5, 0.1, 0.35, 0.2), 0)
    return tail(s, sr, 0.03)


# ---- 활 가득 당김 알림 · 오래 쥐어 흔들림 (56라운드 Q44) ----
# 반드시 arrow_rain_impact 뒤에 둔다(시드 = 1000 + 등록 순서). 기존 109개 파일 바이트 불변.
# bow_draw(0.6 s, 70→95 Hz 톱니 · 400→1200 Hz 밴드 · 28 Hz 삐걱)가 끝나는 지점의 음색을 이어받는다.

@sfx('bow_full_draw', 'PLAYER_SECONDARY{kind:aimedshot,phase:full}', "활 가득 당김 알림(완벽 놓기 창 0.15s 시작 순간, 파일 0ms = 가득 찬 순간). 활대가 멈추는 짧은 나무 '톡' + 딸깍 + 팽팽한 시위 '틱' + 아주 작은 A6 쇠 반짝임", -4)
def _bow_full_draw(sr, rng):
    dur = 0.13
    s = zeros(sec(sr, dur))
    mix_into(s, click(sr, rng, 0.003, 5200), 0, 0.9)  # 딸깍
    mix_into(s, thud(sr, 0.05, 320, 210, 0.01), 0, 0.55)  # 활대 멈춤(나무)
    p = mul(pluck(sr, 0.1, 293.66, rng, damp=0.95, bright=0.8), env_exp(sr, 0.1, 0.018))
    mix_into(s, highpass(p, sr, 500), 0, 0.45)  # 팽팽한 시위 틱(D4)
    mix_into(s, metal(sr, 0.1, 1760, rng, tau=0.02, jitter=0.005), sec(sr, 0.002), 0.12)  # 작은 반짝임(A6)
    return tail(s, sr, 0.02)


@sfx('bow_strain', 'PLAYER_SECONDARY{kind:aimedshot,phase:strain}', "활을 너무 오래 쥐어 조준선이 흔들리는 동안의 루프(1.0s, 이음매 없음). 한계까지 당긴 시위의 떨리는 험(95/98 Hz 맥놀이) + 불규칙하게 떨리는 나무 삐걱 + 드문 작은 삐걱 딸깍. 아주 작게, 흔들림 시작에 페이드인 · 놓으면 즉시 페이드아웃", -10, loop=True)
def _bow_strain(sr, rng):
    dur = 1.0
    n = sec(sr, dur)
    st = add(tone_loop(sr, n, 95, 'saw'), scale(tone_loop(sr, n, 98, 'saw'), 0.7))  # 3 Hz 맥놀이
    st = wrap2(lambda x: svf(x, sr, 1200, 2.0, 'band'), st)
    fl = [a * b for a, b in zip(lfo_loop(sr, n, 7.0, 0.3, 0.7), lfo_loop(sr, n, 11.0, 0.25, 0.75, 0.3))]
    s = scale(mul(st, fl), 0.8)  # 떨리는 시위
    cr = wrap2(lambda x: svf(x, sr, 2200, 1.0, 'band'), noise_loop(sr, n, rng))
    trem = [a * b for a, b in zip(lfo_loop(sr, n, 28.0, 0.5, 0.5), lfo_loop(sr, n, 5.0, 0.4, 0.6, 0.6))]
    mix_into(s, mul(cr, trem), 0, 0.3)  # 나무 삐걱(bow_draw 와 같은 28 Hz)
    for t0, g in [(0.17, 0.5), (0.58, 0.35), (0.83, 0.42)]:  # 드문 삐걱 딸깍 — 경계에서 감긴다
        tk = add(scale(click(sr, rng, 0.003, 3800), 0.6), thud(sr, 0.04, 380, 260, 0.008))
        mix_into(s, tk, sec(sr, t0), 0.3 * g, wrap=True)
    return s


# --- 57·58라운드: 빌드 축(세트·이중 개성·저주·완벽 회피·각성) · 갈래 1단 수단 · 칼 찌르기 · 대검 균열 · 상태 ----------
# 결정 근거: parts/producer/decisions/2026-10-04-round-57-systems-review.md Q22~Q39,
#            2026-10-04-round-58-weapon-feedback2.md Q1·Q3·Q5~Q7·Q11, 설계안 design-2026-10-04-build-axis.md 6.1·-chwigi.md.
# 반드시 bow_strain 뒤에 둔다(시드 = 1000 + 등록 순서). 기존 111개 파일은 바이트 불변이어야 한다.
# 재료 규칙: 세트 = 걸쇠가 맞물리는 강철 + D 단조 종(D5·A5·D6), 저주 = 깃펜·밀랍 도장·쇠사슬 + 삼전음(D–G#),
#            각성 = 개성(evolve)과 같은 '이질'(종 아르페지오·드론) + 무기별 재료 서명. 목소리 없음(숨도 노이즈로만).

def glide_bell(sr, dur, f0, f1, glide, rng, tau=0.6):
    """음높이가 glide 초 동안 f0 → f1 로 미끄러져 자리 잡는 종(이중 개성: 두 음이 하나로 겹침)."""
    n = sec(sr, dur)
    ng = max(1, sec(sr, glide))
    out = zeros(n)
    for ratio, amp in [(1.0, 1.0), (2.0, 0.45), (2.76, 0.35), (4.07, 0.16), (5.4, 0.08)]:
        freqs = [ratio * (f0 + (f1 - f0) * (1 - (1 - min(1.0, i / ng)) ** 2)) for i in range(n)]
        osc = tone_f(sr, freqs, 'sine', rng.random())
        e = env_exp(sr, dur, tau / math.sqrt(ratio))
        for i in range(n):
            out[i] += amp * e[i] * osc[i]
    return mul(out, env_adsr(sr, dur, 0.01, 0.0, 1.0, dur * 0.3))


def latch(sr, rng, g=1.0, heavy=0.0):
    """걸쇠가 맞물리는 '철컥': 딸깍 두 겹 + 짧은 쇠 + (heavy) 낮은 자물쇠 몸통."""
    s = zeros(sec(sr, 0.2))
    mix_into(s, click(sr, rng, 0.004, 5200), 0, 0.9)
    mix_into(s, metal(sr, 0.12, 1650, rng, tau=0.025, jitter=0.03), sec(sr, 0.002), 0.35)
    mix_into(s, click(sr, rng, 0.003, 3400), sec(sr, 0.028), 0.6)
    if heavy:
        mix_into(s, thud(sr, 0.16, 140, 60, 0.035), sec(sr, 0.026), 0.9 * heavy)
        mix_into(s, metal(sr, 0.18, 700, rng, tau=0.05, jitter=0.03), sec(sr, 0.028), 0.3 * heavy)
    return scale(s, g)


def heartbeat(sr, rng, g=1.0):
    """심장 박동 한 번(쿵-쿵): 낮은 몸통 두 번."""
    s = zeros(sec(sr, 0.4))
    mix_into(s, lowpass(thud(sr, 0.18, 68, 40, 0.05), sr, 200), 0, 1.0)
    mix_into(s, lowpass(thud(sr, 0.16, 60, 38, 0.045), sr, 200), sec(sr, 0.16), 0.7)
    return scale(s, g)


def tritone_drone(sr, dur, rng, f=73.42, a=0.3, r=0.5):
    """저주의 낮은 삼전음 드론(D2 + G#2, 톱니 저역통과) — '불협이 몸에 붙는다'."""
    s = add(tone(sr, dur, f, kind='saw'), scale(tone(sr, dur, f * 1.4142, kind='saw'), 0.7))
    s = lowpass(lowpass(s, sr, 320), sr, 320)
    return mul(s, env_adsr(sr, dur, a, 0.0, 1.0, r))


def quill_scratch(sr, rng, d=0.16, f0=3000, f1=5500):
    n = sec(sr, d)
    sc = svf(noise(sr, d, rng), sr, sweep(sr, n, f0, f1), 1.5, 'band')
    trem = [0.6 + 0.4 * math.sin(TAU * 40 * i / sr) for i in range(n)]
    return mul(mul(sc, trem), env_adsr(sr, d, 0.02, 0.0, 1.0, 0.05))


# ---- 빌드 축 ----

def _set_tier(sr, rng, tier):
    dur = [0, 0.7, 0.95, 1.4][tier]
    s = zeros(sec(sr, dur))
    mix_into(s, latch(sr, rng, 1.0, heavy=[0, 0.0, 0.5, 1.0][tier]), 0, 0.8)
    if tier >= 2:
        mix_into(s, latch(sr, rng, 0.7, heavy=0.0), sec(sr, 0.055), 0.6)  # 둘째 걸쇠
    bells = [(587.33, 0.0, 0.5)]  # D5
    if tier >= 2:
        bells.append((880.0, 0.06, 0.38))  # A5
    if tier >= 3:
        bells.append((1174.66, 0.13, 0.3))  # D6
    for f, t0, g in bells:
        mix_into(s, bell(sr, dur - t0 - 0.02, f, rng, tau=0.22 + 0.1 * tier), sec(sr, 0.03 + t0), g)
    if tier == 3:
        mix_into(s, lowpass(kick(sr, 0.5, 110, 40, 0.12, rng=rng), sr, 450), sec(sr, 0.03), 0.8)
        sh = mul(tone(sr, 0.9, 3520, 3560), env_adsr(sr, 0.9, 0.08, 0.0, 1.0, 0.7))
        mix_into(s, sh, sec(sr, 0.15), 0.025)  # 서늘한 한 가닥
        mix_into(s, whoosh(sr, 0.5, rng, 900, 5000, q=0.9, a=0.7, r=0.3), 0, 0.12)
        s = reverb(s, sr, size=0.9, decay=0.65, wet=0.25)
    else:
        s = reverb(s, sr, size=0.6, decay=0.5, wet=0.15)
    return s


@sfx('set_tier1', 'TAG_SET_CHANGED{stage:2,delta>0}', "태그 세트 2단계 켜짐(태그 공용). 걸쇠가 맞물리는 '철컥' + 맑은 종 D5 한 번. 단계가 오를 때만(내려갈 때 없음)", -5, category='event')
def _set_tier1(sr, rng):
    return _set_tier(sr, rng, 1)


@sfx('set_tier2', 'TAG_SET_CHANGED{stage:4,delta>0}', "태그 세트 4단계 켜짐(태그 공용). 걸쇠 두 번 + 종 D5·A5 + 낮은 자물쇠 몸통", -4, category='event')
def _set_tier2(sr, rng):
    return _set_tier(sr, rng, 2)


@sfx('set_tier3', 'TAG_SET_CHANGED{stage:6,delta>0}', "태그 세트 6단계 켜짐(태그 공용, 최대). 무거운 자물쇠 '철컹' + 종 D5·A5·D6 쌓임 + 낮은 북 + 서늘한 고음 한 가닥 + 울림", -2, category='event')
def _set_tier3(sr, rng):
    return _set_tier(sr, rng, 3)


@sfx('dual_trait', 'DUAL_TRAIT_GAINED', "이중 개성 획득(갈래 × 태그). 서로 어긋난 두 종(A4 ±1.5%)이 0.45 s 동안 미끄러져 한 음으로 겹치고, 겹치는 순간 D5 종이 피어남 + 바람. 개성(evolve) 계열 '이질'", -2, category='event')
def _dual_trait(sr, rng):
    dur = 1.5
    s = zeros(sec(sr, dur))
    mix_into(s, glide_bell(sr, 1.4, 440.0 * 0.985, 440.0, 0.45, rng, tau=0.55), 0, 0.42)
    mix_into(s, glide_bell(sr, 1.4, 440.0 * 1.015, 440.0, 0.45, rng, tau=0.55), sec(sr, 0.004), 0.42)
    mix_into(s, bell(sr, 1.0, 587.33, rng, tau=0.45), sec(sr, 0.45), 0.4)  # 겹치는 순간
    mix_into(s, bell(sr, 0.9, 880.0, rng, tau=0.35), sec(sr, 0.5), 0.18)
    mix_into(s, whoosh(sr, 0.55, rng, 600, 4200, q=0.9, a=0.8, r=0.2), 0, 0.18)
    mix_into(s, lowpass(thud(sr, 0.25, 110, 55, 0.06), sr, 400), sec(sr, 0.45), 0.4)
    sh = mul(tone(sr, 0.8, 2637.0, 2650.0), env_adsr(sr, 0.8, 0.1, 0.0, 1.0, 0.6))
    mix_into(s, sh, sec(sr, 0.47), 0.02)
    return reverb(s, sr, size=1.1, decay=0.7, wet=0.32)


@sfx('curse_take', 'CURSE_GAINED', "저주 계약(받음). 깃펜 긁기 → 밀랍 도장 '꾹' + 쇠사슬 감김 3 + 낮은 삼전음(D2–G#2) 드론이 몸에 붙음", -2, category='event')
def _curse_take(sr, rng):
    dur = 1.3
    s = zeros(sec(sr, dur))
    mix_into(s, quill_scratch(sr, rng, 0.16), 0, 0.5)
    t = sec(sr, 0.2)
    mix_into(s, thud(sr, 0.2, 130, 55, 0.04), t, 1.0)  # 도장
    mix_into(s, burst(sr, 0.06, rng, fc=700, q=0.6, tau=0.015, mode='low'), t, 0.6)
    for k, t0 in enumerate((0.28, 0.36, 0.45)):  # 쇠사슬 감김
        mix_into(s, metal(sr, 0.14, 1250 + 160 * k, rng, tau=0.03, jitter=0.05), sec(sr, t0), 0.25)
        mix_into(s, click(sr, rng, 0.003, 4200), sec(sr, t0), 0.35)
    mix_into(s, tritone_drone(sr, 1.0, rng, a=0.25, r=0.55), t, 0.55)
    mix_into(s, lowpass(bell(sr, 0.9, 293.66, rng, tau=0.4), sr, 1200), t, 0.25)
    return reverb(s, sr, size=0.9, decay=0.6, wet=0.22)


@sfx('curse_end', 'CURSE_ENDED', "저주 기간 끝(해제). 족쇄 풀리는 딸깍 + 쇠사슬이 바닥에 떨어짐 + 길게 빠지는 숨(노이즈) + 삼전음이 5도(D–A)로 풀림", -4, category='event')
def _curse_end(sr, rng):
    dur = 1.0
    s = zeros(sec(sr, dur))
    mix_into(s, click(sr, rng, 0.005, 3600), 0, 0.9)
    mix_into(s, metal(sr, 0.18, 1500, rng, tau=0.04, jitter=0.03), 0, 0.35)
    for k, t0 in enumerate((0.07, 0.12, 0.2, 0.26)):  # 바닥에 떨어지는 사슬
        mix_into(s, metal(sr, 0.16, 900 + 140 * k, rng, tau=0.035, jitter=0.06), sec(sr, t0), 0.28 - 0.04 * k)
        mix_into(s, thud(sr, 0.04, 240, 160, 0.01), sec(sr, t0), 0.25)
    n = sec(sr, 0.6)
    ex = svf(noise(sr, 0.6, rng), sr, sweep(sr, n, 1300, 450), 1.2, 'band')
    mix_into(s, mul(ex, env_adsr(sr, 0.6, 0.06, 0.0, 1.0, 0.5)), sec(sr, 0.1), 0.3)  # 빠지는 숨
    tr = tritone_drone(sr, 0.25, rng, a=0.0, r=0.2)
    mix_into(s, tr, 0, 0.35)
    fifth = add(tone(sr, 0.7, 73.42, kind='saw'), scale(tone(sr, 0.7, 110.0, kind='saw'), 0.7))
    fifth = mul(lowpass(lowpass(fifth, sr, 360), sr, 360), env_adsr(sr, 0.7, 0.08, 0.0, 1.0, 0.55))
    mix_into(s, fifth, sec(sr, 0.18), 0.4)  # D–A 로 풀림
    return reverb(s, sr, size=0.8, decay=0.55, wet=0.2)


@sfx('blood_pact', 'CURSE_GAINED{source:bloodPact}', "개성 '피의 계약' 칸 선택(저주 + 이득 1.5배). 날이 손바닥을 긋는 짧은 찢김 → 핏방울 3 + 심장 두 번 + 어두운 D4 종 + 짙은 삼전음 드론. 이때는 curse_take 대신 이것만", -1, category='event')
def _blood_pact(sr, rng):
    dur = 1.8
    s = zeros(sec(sr, dur))
    mix_into(s, tear(sr, 0.12, rng, 3500, 7000, rate=80.0, q=1.6), 0, 0.5)  # 손바닥 긋기
    mix_into(s, metal(sr, 0.1, 2600, rng, tau=0.02, jitter=0.02), 0, 0.12)
    for t0, f in [(0.2, 520), (0.33, 470), (0.47, 560)]:  # 핏방울(낮은 물방울)
        d = mul(tone(sr, 0.04, f, f * 1.5), env_exp(sr, 0.04, 0.012))
        mix_into(s, lowpass(d, sr, 1800), sec(sr, t0), 0.35)
    mix_into(s, heartbeat(sr, rng), sec(sr, 0.3), 0.9)
    mix_into(s, heartbeat(sr, rng), sec(sr, 0.95), 0.75)
    mix_into(s, tritone_drone(sr, 1.5, rng, f=55.0, a=0.35, r=0.7), sec(sr, 0.2), 0.6)
    mix_into(s, lowpass(bell(sr, 1.3, 293.66, rng, tau=0.55), sr, 900), sec(sr, 0.3), 0.35)
    sh = mul(tone(sr, 0.9, 2489.0, 2500.0), env_adsr(sr, 0.9, 0.2, 0.0, 1.0, 0.6))
    mix_into(s, sh, sec(sr, 0.35), 0.015)  # 서늘한 한 가닥(G#7 근처, 삼전음 쪽)
    return reverb(s, sr, size=1.1, decay=0.7, wet=0.28)


@sfx('perfect_evade', 'PERFECT_SUCCESS{kind:perfectEvade}', "완벽 회피(적 공격 판정 직전 0.15 s 안 대쉬·그림자 걸음). 1.2 kHz 위 대역만(대쉬·그림자 걸음과 겹쳐 재생): 스쳐 지나가는 날 바람(가까워졌다 멀어짐) + 맑은 '팅' A6 + D7 반짝임. '완벽 회피' 문구와 같은 프레임", -2)
def _perfect_evade(sr, rng):
    dur = 0.6
    s = zeros(sec(sr, dur))
    n = sec(sr, 0.22)
    nz = svf(noise(sr, 0.22, rng), sr, [1800 * (1 + 2.2 * math.sin(math.pi * i / n)) for i in range(n)], 2.0, 'band')
    nz = mul(nz, [math.sin(math.pi * i / n) ** 2 for i in range(n)])
    mix_into(s, nz, 0, 0.7)  # 스쳐 지나가는 날(도플러처럼 올라갔다 내려감)
    mix_into(s, bell(sr, 0.5, 1760.0, rng, tau=0.2), sec(sr, 0.09), 0.4)  # A6 '팅'
    sh = mul(tone(sr, 0.4, 2349.3, 2360.0), env_adsr(sr, 0.4, 0.02, 0.0, 1.0, 0.35))
    mix_into(s, sh, sec(sr, 0.1), 0.05)  # D7
    mix_into(s, click(sr, rng, 0.003, 7000), sec(sr, 0.09), 0.5)
    s = highpass(highpass(s, sr, 1200), sr, 1200)
    return reverb(tail(s, sr, 0.02), sr, size=0.6, decay=0.5, wet=0.2)


def _awaken_core(sr, rng, dur, peak=0.9):
    """최종 각성 공용 뼈대: 모여드는 바람 + 열리는 D 드론 → peak 에 북 + 종 아르페지오(D4 A4 D5 F5 A5 D6) + 이질 고음."""
    s = zeros(sec(sr, dur))
    m = sec(sr, peak)
    g = svf(noise(sr, peak, rng), sr, sweep(sr, m, 300, 3800), 1.0, 'band')
    mix_into(s, mul(g, [((i / m) ** 2.2) for i in range(m)]), 0, 0.45)  # 모여드는 바람
    dr = add(tone(sr, dur, 36.71, kind='saw'), scale(tone(sr, dur, 73.42 * 1.003, kind='saw'), 0.6))
    nd = sec(sr, dur)
    dr = lowpass(dr, sr, [200 + 700 * min(1.0, i / m) for i in range(nd)])
    dr = mul(dr, env_adsr(sr, dur, peak * 0.8, 0.0, 1.0, dur - peak))
    mix_into(s, dr, 0, 0.4)
    mix_into(s, lowpass(kick(sr, 0.8, 90, 30, 0.2, rng=rng), sr, 380), m, 1.0)
    for k, f in enumerate([293.66, 440.0, 587.33, 698.46, 880.0, 1174.66]):
        mix_into(s, bell(sr, max(0.4, dur - peak - 0.08 * k - 0.05), f, rng, tau=0.4), m + sec(sr, 0.05 + 0.075 * k), 0.34 - 0.03 * k)
    sh = mul(tone(sr, dur - peak, 2936.6, 2950.0), env_adsr(sr, dur - peak, 0.2, 0.0, 1.0, 0.8))
    mix_into(s, sh, m, 0.02)
    return s


@sfx('awaken_katana', 'WEAPON_EVOLVED{kind:awaken,weapon:katana}', "최종 각성 — 칼(만월, 임시 이름). 공용 각성 뼈대(모여드는 바람·D 드론 → 0.9 s 북 + 종 아르페지오) + 달빛 칼날 울림 A5·D6(떨림) + 초승달 베기 '시잉'. 파일 0.9 s = 정점(무기 변형 그림 전환과 같은 프레임 권장)", 0, category='event')
def _awaken_katana(sr, rng):
    dur = 2.6
    s = _awaken_core(sr, rng, dur)
    m = sec(sr, 0.9)
    mix_into(s, tear(sr, 0.25, rng, 2500, 9000, rate=90.0, q=1.8), m - sec(sr, 0.05), 0.5)
    mix_into(s, whoosh(sr, 0.3, rng, 8000, 2000, q=2.0, a=0.1, r=0.7), m, 0.45)
    mix_into(s, blade_ring(sr, 1.5, 880.0, rng, bright=1.0, tau=0.6, vib=0.003), m, 0.4)
    mix_into(s, blade_ring(sr, 1.3, 1174.66, rng, bright=0.8, tau=0.5, vib=0.002), m + sec(sr, 0.08), 0.22)
    return reverb(softclip(s, 1.2), sr, size=1.3, decay=0.78, wet=0.35)


@sfx('awaken_greatsword', 'WEAPON_EVOLVED{kind:awaken,weapon:greatsword}', "최종 각성 — 대검(산붕, 임시 이름). 공용 각성 뼈대 + 0.9 s 산이 무너지는 강타(×1.6) + 오래 굴러 내리는 바위·자갈 + 호박빛 '징' D4·A4. 파일 0.9 s = 정점", 0, category='event')
def _awaken_greatsword(sr, rng):
    dur = 2.6
    s = _awaken_core(sr, rng, dur)
    m = sec(sr, 0.9)
    mix_into(s, slam_impact(sr, rng, 0.8, 100, 26, 0.12, 1.6), m, 0.9)
    rum = mul(svf(noise(sr, 1.6, rng), sr, 140, 0.8, 'low'), env_adsr(sr, 1.6, 0.05, 0.0, 1.0, 1.4))
    mix_into(s, rum, m, 0.9)
    for k in range(18):  # 굴러 내리는 바위
        t0 = 0.9 + 0.05 + rng.uniform(0, 1.2) * (k / 18) ** 0.7
        mix_into(s, thud(sr, 0.08, rng.uniform(120, 200), 60, 0.02), sec(sr, t0), 0.35 * (1 - k / 22))
    mix_into(s, gravel(sr, rng, 1.5, 24, 0.0, 1.3, 0.25), m)
    mix_into(s, jing(sr, 1.4, 293.66, rng, bright=0.4, tau=0.7), m + sec(sr, 0.02), 0.3)
    mix_into(s, jing(sr, 1.2, 440.0, rng, bright=0.6, tau=0.6), m + sec(sr, 0.1), 0.2)
    return reverb(softclip(s, 1.5), sr, size=1.3, decay=0.75, wet=0.3)


@sfx('awaken_dagger', 'WEAPON_EVOLVED{kind:awaken,weapon:dagger}', "최종 각성 — 단검(백귀, 임시 이름). 공용 각성 뼈대 + 엇갈려 빨려드는 어두운 역바람 3겹(그림자 셋) → 0.9 s 부터 세 번 교차 베기 + 재 폭발 작게 셋. 파일 0.9 s = 정점", 0, category='event')
def _awaken_dagger(sr, rng):
    dur = 2.6
    s = _awaken_core(sr, rng, dur)
    m = sec(sr, 0.9)
    for k, (st, f0) in enumerate([(0.45, 350), (0.55, 450), (0.65, 300)]):
        d = 0.9 - st
        nd = sec(sr, d)
        nz = svf(noise(sr, d, rng), sr, sweep(sr, nd, f0, 2400 + 300 * k), 1.4, 'band')
        mix_into(s, mul(nz, [((i / nd) ** 1.6) for i in range(nd)]), sec(sr, st), 0.35)
    for k in range(3):  # 세 번 교차 베기
        t0 = m + sec(sr, 0.06 * k)
        cut = whoosh(sr, 0.12, rng, 7500 - 600 * k, 2200, q=1.9, a=0.1, r=0.6)
        mix_into(s, cut, t0, 0.6)
        mix_into(s, metal(sr, 0.12, 2200 + 300 * k, rng, tau=0.035, jitter=0.03), t0 + sec(sr, 0.01), 0.15)
        mix_into(s, ash_pop(sr, rng, 0.4, 170 - 15 * k, 45, 0.6), t0 + sec(sr, 0.04), 0.35)
    return reverb(softclip(s, 1.3), sr, size=1.2, decay=0.75, wet=0.33)


@sfx('awaken_bow', 'WEAPON_EVOLVED{kind:awaken,weapon:bow}', "최종 각성 — 활(유성, 임시 이름). 깊은 시위 '둥' → 하늘에서 떨어지는 휘파람(0.35~0.9 s) → 0.9 s 유성 낙하 폭음 + 공용 각성 종 + 흩어지는 불티. 파일 0.9 s = 정점", 0, category='event')
def _awaken_bow(sr, rng):
    dur = 2.6
    s = _awaken_core(sr, rng, dur)
    m = sec(sr, 0.9)
    st = pluck(sr, 0.6, 110, rng, damp=0.992, bright=0.6)
    mix_into(s, mul(st, env_exp(sr, 0.6, 0.18)), 0, 0.6)  # 깊은 시위
    d = 0.55
    nd = sec(sr, d)
    wh = mul(tone(sr, d, 3200, 700), [((i / nd) ** 1.4) for i in range(nd)])
    mix_into(s, wh, sec(sr, 0.35), 0.1)  # 떨어지는 휘파람
    fall = svf(noise(sr, d, rng), sr, sweep(sr, nd, 5000, 900), 1.6, 'band')
    mix_into(s, mul(fall, [((i / nd) ** 1.8) for i in range(nd)]), sec(sr, 0.35), 0.4)
    mix_into(s, ash_pop(sr, rng, 0.9, 120, 28, 1.6), m, 0.9)
    mix_into(s, crackle(sr, rng, 1.2, 26, 0.3), m + sec(sr, 0.05))
    return reverb(softclip(s, 1.4), sr, size=1.3, decay=0.78, wet=0.33)


# ---- 칼 갈래 1단: 선풍 회전 베기 · 투구가르기 가드 불가 내려베기 · 3타 찌르기 ----

@sfx('katana_spin_ready', 'PLAYER_SKILL{weapon:katana,move:spin,phase:ready}', "회전 베기 준비 완료(좌클릭 0.4 s 홀드 도달, 반짝임 fx 와 같은 프레임). 칼을 고쳐 쥐는 딸깍 + 짧은 칼날 울림 A5. 투구가르기 0.6 s 도달 알림에도 rate 0.667(→D5) 로 재사용 권장", -6)
def _katana_spin_ready(sr, rng):
    s = zeros(sec(sr, 0.32))
    mix_into(s, click(sr, rng, 0.004, 4200), 0, 0.7)
    mix_into(s, blade_ring(sr, 0.3, 880.0, rng, bright=0.5, tau=0.1), sec(sr, 0.004), 0.5)
    return s


@sfx('katana_spin', 'PLAYER_SKILL{weapon:katana,move:spin,phase:release}', "회전 베기(360°, 반경 2.5칸) 떼는 순간. 발 돌림 스침 → 한 바퀴 도는 칼바람(대역이 올라갔다 내려옴) + 찢김 + 칼날 울림 D5. 검기 소모 2회전은 같은 파일을 0.28 s 뒤 rate 1.05 로 한 번 더", -1)
def _katana_spin(sr, rng):
    dur = 0.5
    s = zeros(sec(sr, dur))
    sc = svf(noise(sr, 0.06, rng), sr, 900, 0.8, 'band')
    mix_into(s, mul(sc, env_exp(sr, 0.06, 0.02)), 0, 0.35)  # 발 돌림
    d = 0.32
    n = sec(sr, d)
    fc = [1400 * (1 + 3.2 * math.sin(math.pi * i / n) ** 1.5) for i in range(n)]
    w = svf(noise(sr, d, rng), sr, fc, 1.7, 'band')
    w = mul(w, [math.sin(math.pi * i / n) ** 0.8 for i in range(n)])
    mix_into(s, w, sec(sr, 0.02), 1.0)  # 한 바퀴 칼바람
    mix_into(s, tear(sr, 0.24, rng, 2600, 6500, rate=75.0, q=1.5), sec(sr, 0.06), 0.35)
    mix_into(s, blade_ring(sr, 0.35, 587.33, rng, bright=0.4, tau=0.12), sec(sr, 0.14), 0.2)
    return tail(s, sr, 0.02)


@sfx('katana_guardbreak_hold', 'PLAYER_SKILL{weapon:katana,move:guardbreak,phase:hold}', "가드 불가 내려베기 홀드 루프(1.0 s, 좌클릭 누르는 동안). 달아오르는 칼: 낮은 D3 웅웅 + 6 Hz 떨리는 칼날 험 A5 + 열기 노이즈 + 잔불 타닥(이음매 없음). 홀드 시작에 150 ms 페이드인, 떼거나 취소하면 60 ms 페이드아웃. 0.6 s 까지 rate 1.0→1.06 올리면 달아오름이 쌓임(선택)", -11, loop=True)
def _katana_guardbreak_hold(sr, rng):
    dur = 1.0
    n = sec(sr, dur)
    # 톱니는 2번 저역통과(고역 잡음이 많으면 AAC 이음매 오차가 커짐), 험은 위상 0.25(이음매에서 기울기 0)
    g = wrap2(lambda x: lowpass(lowpass(x, sr, 260), sr, 600), tone_loop(sr, n, 146.83, 'saw'))  # D3
    g = mul(g, lfo_loop(sr, n, 2.0, 0.2, 0.8))
    hum = add(tone_loop(sr, n, 880.0, 'sine', 0.25), scale(tone_loop(sr, n, 886.0, 'sine', 0.25), 0.6))  # 6 Hz 떨림
    mix_into(g, hum, 0, 0.05)
    heat = wrap2(lambda x: svf(x, sr, 700, 0.8, 'band'), noise_loop(sr, n, rng))
    mix_into(g, mul(heat, lfo_loop(sr, n, 3.0, 0.3, 0.7, 0.2)), 0, 0.35)
    # 타닥은 이음매 ±20 ms 밖에만 둔다(경계에 걸친 딸깍이 AAC 이음매 튐을 키움)
    mix_into(g, fade_edges(crackle(sr, rng, dur - 0.05, 10, 0.35), sr, 0.005), sec(sr, 0.02))
    return g


@sfx('katana_guardbreak', 'PLAYER_SKILL{weapon:katana,move:guardbreak,phase:strike}', "가드 불가 내려베기(정면 쐐기 3칸, 가드·방패 무시). 0~0.1 s 내려오는 무거운 칼바람 → 0.1 s 판정: 방패·갑옷이 쪼개지는 쇳소리 + 둔탁한 강타 + 밝은 칼날 울림 D5. 판정 프레임 100 ms 앞에서 재생", 0)
def _katana_guardbreak(sr, rng):
    dur = 0.75
    s = zeros(sec(sr, dur))
    mix_into(s, whoosh(sr, 0.12, rng, 3200, 600, q=1.4, a=0.3, r=0.2), 0, 0.8)
    t = sec(sr, 0.1)
    mix_into(s, metal(sr, 0.45, 720, rng, tau=0.09, jitter=0.04), t, 0.5)  # 쪼개지는 쇠
    mix_into(s, burst(sr, 0.08, rng, fc=1300, q=0.8, tau=0.018), t, 0.9)
    mix_into(s, thud(sr, 0.3, 115, 38, 0.07), t, 1.1)
    mix_into(s, burst(sr, 0.2, rng, fc=400, q=0.6, tau=0.04, mode='low'), t, 0.7)
    mix_into(s, blade_ring(sr, 0.5, 587.33, rng, bright=0.8, tau=0.2), t + sec(sr, 0.01), 0.28)
    mix_into(s, gravel(sr, rng, 0.3, 5, 0.0, 0.18, 0.2), t)
    s = softclip(s, 1.4)
    return reverb(tail(s, sr, 0.02), sr, size=0.6, decay=0.5, wet=0.12)


@sfx('katana_thrust', 'PLAYER_ATTACK{weapon:katana,combo:3}', "칼 3연격 3타 찌르기(58라운드 Q1, 휘두르지 않고 곧게 뻗음). 반 발 디딤 + 앞으로 곧게 뚫는 좁은 '쉭' + 칼끝 틱. 검기 소모 시 위에 katana_thrust_ki1~3 를 겹침", -2)
def _katana_thrust(sr, rng):
    dur = 0.26
    s = zeros(sec(sr, dur))
    mix_into(s, thud(sr, 0.07, 150, 85, 0.016), 0, 0.5)  # 반 발 디딤
    n = sec(sr, 0.13)
    p = svf(noise(sr, 0.13, rng), sr, sweep(sr, n, 2200, 5200), 2.4, 'band')
    mix_into(s, mul(p, env_adsr(sr, 0.13, 0.02, 0.0, 1.0, 0.09)), sec(sr, 0.01), 1.0)
    mix_into(s, metal(sr, 0.08, 3300, rng, tau=0.02, jitter=0.02), sec(sr, 0.07), 0.12)
    mix_into(s, click(sr, rng, 0.003, 5500), sec(sr, 0.07), 0.4)
    return tail(s, sr, 0.02)


def _thrust_ki(sr, rng, stage):
    f = [0, 440.0, 587.33, 880.0][stage]
    reach = [0, 0.2, 0.24, 0.3][stage]  # 사거리 1.5/1.7/1.9R 에 맞춰 길게
    dur = reach + [0, 0.25, 0.32, 0.45][stage]
    s = zeros(sec(sr, dur))
    mix_into(s, tear(sr, reach, rng, 2000, 6500 + 800 * stage, rate=80.0 + 5 * stage, q=1.7), 0, 0.6)
    mix_into(s, blade_ring(sr, dur - 0.01, f, rng, bright=[0, 0.0, 0.45, 1.0][stage], tau=0.14 + 0.04 * stage, vib=0.001 * stage),
             sec(sr, 0.01), 0.4)
    if stage == 3:
        hi = mul(tone(sr, 0.4, 3520, 3540), env_adsr(sr, 0.4, 0.02, 0.0, 1.0, 0.35))
        mix_into(s, hi, sec(sr, 0.02), 0.03)
        return reverb(tail(s, sr, 0.03), sr, size=0.5, decay=0.5, wet=0.15)
    return tail(s, sr, 0.02)


@sfx('katana_thrust_ki1', 'PLAYER_ATTACK{weapon:katana,combo:3,kenkiStage:1}', "3타 찌르기 검기 1단 소모 겹침(재빛, 사거리 1.5R). 앞으로 뻗는 찢김 + 칼날 울림 A4 — katana_thrust 와 같은 프레임", -5)
def _katana_thrust_ki1(sr, rng):
    return _thrust_ki(sr, rng, 1)


@sfx('katana_thrust_ki2', 'PLAYER_ATTACK{weapon:katana,combo:3,kenkiStage:2}', "3타 찌르기 검기 2단 소모 겹침(호박빛, 1.7R). 더 길게 뻗는 찢김 + 칼날 울림 D5", -4)
def _katana_thrust_ki2(sr, rng):
    return _thrust_ki(sr, rng, 2)


@sfx('katana_thrust_ki3', 'PLAYER_ATTACK{weapon:katana,combo:3,kenkiStage:3}', "3타 찌르기 검기 3단 소모 겹침(백열, 1.9R). 가장 길고 밝은 찢김 + 칼날 울림 A5 + 백열 고음 + 짧은 울림", -3)
def _katana_thrust_ki3(sr, rng):
    return _thrust_ki(sr, rng, 3)


# ---- 대검: 휘둘러 내리찍기 균열(58 Q3) · 중압 원형 진동 · 파쇄 탄 소멸 ----

def _crack_line(sr, rng, tiles):
    step = 0.06  # 칸당 진행 시간(제안) — 시스템 균열 속도·아트 t1~t5 와 맞춰 조정
    run = step * tiles
    dur = run + 0.55
    n = sec(sr, dur)
    s = zeros(n)
    k_all = tiles * 3
    for k in range(k_all):  # 칸마다 갈라짐 3번, 멀어질수록 어둡고 작게
        t0 = 0.01 + run * k / k_all + rng.uniform(-0.004, 0.004)
        g = 0.75 * (1 - 0.45 * k / k_all)
        mix_into(s, burst(sr, 0.045, rng, fc=max(600, 2300 - 1400 * k / k_all), q=0.9, tau=0.009), sec(sr, t0), g)
        mix_into(s, thud(sr, 0.05, 165 - 40 * k / k_all, 75, 0.013), sec(sr, t0), g * 0.35)
    mix_into(s, burst(sr, 0.12, rng, fc=900, q=0.7, tau=0.025), sec(sr, run), 0.55)  # 끝 '툭' 터짐
    mix_into(s, thud(sr, 0.18, 120, 45, 0.04), sec(sr, run), 0.5)
    rum = mul(svf(noise(sr, dur, rng), sr, 160, 0.8, 'low'), env_adsr(sr, dur, run * 0.5, 0.0, 1.0, 0.5))
    mix_into(s, rum, 0, 0.55)
    mix_into(s, gravel(sr, rng, dur, 4 + 2 * tiles, 0.02, run + 0.2, 0.22), 0)
    s = softclip(s, 1.4)
    return reverb(s, sr, size=0.8, decay=0.5, wet=0.15)


@sfx('gs_crack_line_lv1', 'PLAYER_CHARGE{weapon:greatsword,phase:release,stage:1,part:crack}', "휘둘러 내리찍기 균열 진행(차지 1단, 3칸). 찍은 자리에서 커서 쪽으로 달려가는 갈라짐(칸당 0.06 s, 멀어질수록 어둡게) + 끝 '툭' + 땅울림. charge_slam_lv1 과 같은 판정 프레임에 겹침. 커서·벽이 가까워 짧게 끝나면 그 시점에 80 ms 페이드아웃", -1)
def _gs_crack_line_lv1(sr, rng):
    return _crack_line(sr, rng, 3)


@sfx('gs_crack_line_lv2', 'PLAYER_CHARGE{weapon:greatsword,phase:release,stage:2,part:crack}', "균열 진행(차지 2단, 4칸). 1단과 같은 재료, 0.24 s 동안 달려감", -1)
def _gs_crack_line_lv2(sr, rng):
    return _crack_line(sr, rng, 4)


@sfx('gs_crack_line_lv3', 'PLAYER_CHARGE{weapon:greatsword,phase:release,stage:3,part:crack}', "균열 진행(차지 3단, 5칸). 0.30 s 동안 달려감, 가장 길다", 0)
def _gs_crack_line_lv3(sr, rng):
    return _crack_line(sr, rng, 5)


@sfx('gs_quake_ring', 'PLAYER_CHARGE{weapon:greatsword,phase:release,branch:giant,part:quake}', "중압(대검 1단 B) 원형 진동 — 기본 균열 대신(찍은 자리 중심). 땅이 12 Hz 로 떨리는 낮은 진동 + 안으로 빨려드는 바람(적을 끌어당김) → 0.32 s 끌려온 적이 짓눌리는 '쿵'(경직) + 자갈. charge_slam_lvN 과 같은 프레임에 겹침, 반경(단계)에 따라 gain +0/+1.5/+3 dB 권장", 0)
def _gs_quake_ring(sr, rng):
    dur = 1.0
    n = sec(sr, dur)
    s = zeros(n)
    vib = mul(tone(sr, 0.8, 48, 34), [0.55 + 0.45 * math.sin(TAU * 12 * i / sr) for i in range(sec(sr, 0.8))])
    mix_into(s, mul(vib, env_adsr(sr, 0.8, 0.02, 0.0, 1.0, 0.5)), 0, 1.0)  # 떨리는 땅
    gr = svf(noise(sr, 0.8, rng), sr, 260, 0.8, 'low')
    gr = mul(gr, [0.5 + 0.5 * math.sin(TAU * 12 * i / sr + 0.8) for i in range(sec(sr, 0.8))])
    mix_into(s, mul(gr, env_adsr(sr, 0.8, 0.02, 0.0, 1.0, 0.5)), 0, 0.6)
    m = sec(sr, 0.32)
    suck = svf(noise(sr, 0.32, rng), sr, sweep(sr, m, 2400, 350), 1.3, 'band')
    mix_into(s, mul(suck, [((i / m) ** 1.5) for i in range(m)]), 0, 0.45)  # 안으로 빨려듦
    mix_into(s, thud(sr, 0.3, 105, 36, 0.07), m, 1.0)  # 짓눌림
    mix_into(s, burst(sr, 0.15, rng, fc=500, q=0.6, tau=0.03, mode='low'), m, 0.6)
    mix_into(s, gravel(sr, rng, 0.6, 10, 0.0, 0.45, 0.22), sec(sr, 0.02))
    s = softclip(s, 1.5)
    return reverb(s, sr, size=0.8, decay=0.5, wet=0.15)


@sfx('gs_shatter_snuff', 'PLAYER_SKILL{weapon:greatsword,move:crack,phase:snuff}', "파쇄(대검 1단 A) 균열이 적 투사체를 소멸. 짧게 으스러지는 '빠직'(돌·나무·쇠 파편) + 작은 먼지 '푹'. 투사체마다(20 ms 규칙으로 동시 다발은 1회)", -4)
def _gs_shatter_snuff(sr, rng):
    s = zeros(sec(sr, 0.25))
    mix_into(s, burst(sr, 0.03, rng, fc=2600, q=0.8, tau=0.006), 0, 0.9)
    mix_into(s, metal(sr, 0.08, 1450, rng, tau=0.02, jitter=0.06), sec(sr, 0.003), 0.25)
    mix_into(s, gravel(sr, rng, 0.12, 5, 0.0, 0.06, 0.4), 0)
    mix_into(s, burst(sr, 0.12, rng, fc=500, q=0.6, tau=0.03, mode='low'), sec(sr, 0.01), 0.4)
    return tail(s, sr, 0.02)


# ---- 단검 갈래 1단: 질풍 부채꼴 투척 · 쌍격 분신 교차 베기 ----

@sfx('dagger_fan_throw', 'PLAYER_SKILL{weapon:dagger,move:fan_throw}', "질풍(단검 1단 B) 부채꼴 투척(대쉬 직후 0.3 s 안 좌클릭, 3자루 30°). 손목 딸깍 + 25 ms 간격으로 날아가는 높은 바람 셋(음높이 조금씩 다름) + 칼날 틱", -2)
def _dagger_fan_throw(sr, rng):
    s = zeros(sec(sr, 0.32))
    mix_into(s, click(sr, rng, 0.003, 4800), 0, 0.6)
    for k, (f0, f1) in enumerate([(7200, 3000), (8000, 3400), (6600, 2700)]):
        t0 = sec(sr, 0.025 * k)
        mix_into(s, whoosh(sr, 0.16, rng, f0, f1, q=2.0, a=0.08, r=0.7), t0, 0.6)
        mix_into(s, metal(sr, 0.05, 3600 + 300 * k, rng, tau=0.012, jitter=0.03), t0, 0.08)
    return tail(s, sr, 0.02)


@sfx('dagger_cross_clone', 'PLAYER_SKILL{weapon:dagger,move:cross_clone}', "쌍격(단검 1단 A) 그림자 분신 교차 베기 — 낙인 기폭 때 분신이 반대편에서. 0.16 s 빨려드는 어두운 역바람(분신 나타남, 이질) → 0.16 s·0.19 s 엇갈린 두 베기(X) + 쇠 틱 + 낮은 몸통. brand_burst 와 같은 프레임에 겹침", -2)
def _dagger_cross_clone(sr, rng):
    dur = 0.6
    s = zeros(sec(sr, dur))
    m = sec(sr, 0.16)
    nz = svf(noise(sr, 0.16, rng), sr, sweep(sr, m, 350, 2600), 1.4, 'band')
    mix_into(s, mul(nz, [((i / m) ** 1.6) for i in range(m)]), 0, 0.5)
    for k, (f0, f1) in enumerate([(7000, 2200), (5600, 1700)]):
        t0 = m + sec(sr, 0.03 * k)
        mix_into(s, whoosh(sr, 0.13, rng, f0, f1, q=1.9, a=0.1, r=0.6), t0, 0.75)
        mix_into(s, metal(sr, 0.1, 2400 - 400 * k, rng, tau=0.03, jitter=0.03), t0 + sec(sr, 0.01), 0.15)
    mix_into(s, thud(sr, 0.12, 130, 55, 0.03), m + sec(sr, 0.03), 0.45)
    return reverb(tail(s, sr, 0.02), sr, size=0.6, decay=0.5, wet=0.2)


# ---- 활 갈래 1단: 속사 연사 · 저격 관통 화살 ----

def _rapid(sr, rng, f, fc):
    s = mul(pluck(sr, 0.11, f, rng, damp=0.97, bright=0.75), env_exp(sr, 0.11, 0.03))
    mix_into(s, whoosh(sr, 0.08, rng, 2800, fc, q=1.3, a=0.15, r=0.6), sec(sr, 0.005), 0.3)
    mix_into(s, thud(sr, 0.04, 240, 140, 0.01), 0, 0.4)
    mix_into(s, click(sr, rng, 0.003, 5000), 0, 0.3)
    return tail(s, sr, 0.02)


@sfx('bow_rapid1', 'PLAYER_ATTACK{weapon:bow,move:rapid,variant:1}', "속사(활 1단 A) 연사 한 발 — 변주 1/3. 초당 5발에 맞춘 짧은 시위 '틱' + 짧은 화살 바람(0.13 s, bow_shot 의 1/2 길이). 발마다 1~3 중 직전과 다른 것 + ±3% rate", -4)
def _bow_rapid1(sr, rng):
    return _rapid(sr, rng, 220.0, 6200)


@sfx('bow_rapid2', 'PLAYER_ATTACK{weapon:bow,move:rapid,variant:2}', "속사 연사 변주 2/3(조금 낮고 둔함)", -4)
def _bow_rapid2(sr, rng):
    return _rapid(sr, rng, 196.0, 5200)


@sfx('bow_rapid3', 'PLAYER_ATTACK{weapon:bow,move:rapid,variant:3}', "속사 연사 변주 3/3(조금 높고 가벼움)", -4)
def _bow_rapid3(sr, rng):
    return _rapid(sr, rng, 247.0, 7000)


@sfx('bow_pierce', 'PLAYER_SKILL{weapon:bow,move:pierce,phase:pass}', "저격(활 1단 B) 관통 화살이 적을 뚫고 지나감(적마다, 최대 3). 날이 박혔다 빠지는 '퍽' + 계속 뻗어 나가는 높은 바람. 적중 피격음(hit_enemy)과 겹침", -3)
def _bow_pierce(sr, rng):
    s = zeros(sec(sr, 0.24))
    mix_into(s, burst(sr, 0.03, rng, fc=1700, q=0.8, tau=0.006), 0, 0.9)
    mix_into(s, thud(sr, 0.06, 200, 110, 0.014), 0, 0.6)
    mix_into(s, whoosh(sr, 0.18, rng, 3800, 7500, q=1.4, a=0.05, r=0.8), sec(sr, 0.012), 0.6)
    mix_into(s, metal(sr, 0.06, 3100, rng, tau=0.015, jitter=0.03), sec(sr, 0.004), 0.1)
    return tail(s, sr, 0.02)


# ---- 상태 ----

@sfx('mark_stack', 'MARK_CHANGED{delta>0}', "공용 표식 1 쌓임(표식 세트 2, 같은 적 3타마다, 최대 3). 붉은 분필 긋는 짧은 '슥' + 나무 틱. 단검 낙인(brand_apply, 지짐)과 구분. 표식 2·3 에서 rate 1.06·1.12 권장", -8)
def _mark_stack(sr, rng):
    s = zeros(sec(sr, 0.16))
    mix_into(s, quill_scratch(sr, rng, 0.07, 2600, 4200), 0, 0.7)
    mix_into(s, thud(sr, 0.04, 420, 300, 0.008), sec(sr, 0.05), 0.5)
    mix_into(s, metal(sr, 0.06, 2200, rng, tau=0.012, jitter=0.02), sec(sr, 0.05), 0.1)
    return tail(s, sr, 0.02)


@sfx('boil_burst', 'STATUS_BURST{kind:boil}', "끓음 폭발(상흔 세트 4: 출혈 + 화상이 함께 걸린 적의 남은 지속 피해가 즉시 터짐, 반경 1.5칸). 0.14 s 빨라지는 거품 끓음 → 젖은 재 폭발 '퍽' + 핏방울·지짐. 파일 0.14 s = 폭발", -2)
def _boil_burst(sr, rng):
    dur = 0.8
    s = zeros(sec(sr, dur))
    for k in range(12):  # 빨라지는 끓음
        t0 = 0.14 * (1 - (1 - k / 12) ** 0.6)
        d = mul(tone(sr, 0.03, rng.uniform(180, 420), rng.uniform(500, 800)), env_exp(sr, 0.03, 0.01))
        mix_into(s, lowpass(d, sr, 1500), sec(sr, t0), 0.25 + 0.03 * k)
    t = sec(sr, 0.14)
    mix_into(s, ash_pop(sr, rng, 0.5, 160, 45, 1.0), t, 0.9)
    mix_into(s, droplets(sr, rng, 0.4, 8, 0.02, 0.3, 600, 1600, 0.3), t)
    mix_into(s, sizzle(sr, rng, 0.4, fc=4400, tau=0.1), t + sec(sr, 0.02), 0.3)
    s = softclip(s, 1.3)
    return reverb(tail(s, sr, 0.02), sr, size=0.5, decay=0.45, wet=0.12)


@sfx('stillness', 'SET_EFFECT{tag:insight,effect:stillness}', "정적(간파 세트 6: 완벽 성공 3회마다 1 s 동안 적·탄 40% 감속). 짧게 빨려드는 숨(노이즈) → 0.12 s 맑은 '틱' + 유리처럼 얼어붙는 A5·D6 + 먹먹하게 내려앉는 저음. 활 숨(breath_focus)보다 짧고 차갑다", -3)
def _stillness(sr, rng):
    dur = 1.1
    s = zeros(sec(sr, dur))
    m = sec(sr, 0.12)
    nz = svf(noise(sr, 0.12, rng), sr, sweep(sr, m, 1200, 5200), 1.3, 'band')
    mix_into(s, mul(nz, [((i / m) ** 2) for i in range(m)]), 0, 0.5)
    mix_into(s, click(sr, rng, 0.004, 6500), m, 0.8)
    for f, g, tr in [(880.0, 0.3, 5.0), (1174.66, 0.22, 3.7)]:
        b = bell(sr, 0.95, f, rng, tau=0.5)
        b = mul(b, [0.75 + 0.25 * math.sin(TAU * tr * i / sr) for i in range(len(b))])
        mix_into(s, b, m, g)
    lo = mul(tone(sr, 0.7, 92, 40), env_adsr(sr, 0.7, 0.01, 0.0, 1.0, 0.6))
    mix_into(s, lowpass(lo, sr, 300), m, 0.8)
    return reverb(s, sr, size=1.0, decay=0.6, wet=0.25)


@sfx('drunk_ignite', 'POOL_IGNITED', "술 웅덩이 점화(술불, 취기). 작은 '훅' + 낮은 펑 + 빠르게 번지는 불길 + 타닥 — 보스 boss1_ignite(1.1 s)보다 짧고 가볍다(여러 웅덩이 연쇄 대비). 번질 때마다 80~150 ms 시차 권장, 타는 동안은 boss1_fire_loop 1개 재사용", -3)
def _drunk_ignite(sr, rng):
    dur = 0.6
    n = sec(sr, dur)
    s = zeros(n)
    mix_into(s, thud(sr, 0.2, 95, 45, 0.045), 0, 0.7)
    roar = svf(noise(sr, dur, rng), sr, sweep(sr, n, 300, 2400), 0.7, 'low')
    mix_into(s, mul(roar, env_adsr(sr, dur, 0.03, 0.1, 0.45, 0.42)), 0, 0.9)
    mix_into(s, crackle(sr, rng, 0.5, 9, 0.35), sec(sr, 0.06))
    s = softclip(s, 1.2)
    return tail(s, sr, 0.02)


@sfx('drunk_sway', 'DRUNK_SWAY', "취기 휘청(취기 세트 4 '취보': 취기 중 첫 피격 1회 피해 0·0.4 s 무적·반 칸 비틀 미끄러짐). 7 Hz 로 일렁이는 바람 + 장화 미끄러짐 + 몸 안 술 출렁 + 작은 잔 '팅'. 피격음 대신 재생", -3)
def _drunk_sway(sr, rng):
    dur = 0.45
    n = sec(sr, dur)
    s = zeros(n)
    fc = [900 * (1 + 0.6 * math.sin(TAU * 7 * i / sr)) for i in range(n)]
    w = svf(noise(sr, dur, rng), sr, fc, 1.2, 'band')
    mix_into(s, mul(w, env_adsr(sr, dur, 0.05, 0.0, 1.0, 0.3)), 0, 0.7)
    sl = svf(noise(sr, 0.18, rng), sr, 800, 0.8, 'band')
    mix_into(s, mul(sl, env_adsr(sr, 0.18, 0.02, 0.0, 1.0, 0.12)), sec(sr, 0.04), 0.4)  # 장화 미끄러짐
    mix_into(s, gravel(sr, rng, 0.2, 3, 0.0, 0.15, 0.2), sec(sr, 0.04))
    mix_into(s, slosh(sr, rng, 0.3, 380, 700), sec(sr, 0.02), 0.45)
    gl = metal(sr, 0.25, 2100, rng, partials=GLASS, tau=0.06, jitter=0.01)
    mix_into(s, gl, sec(sr, 0.03), 0.12)
    return tail(s, sr, 0.02)


@sfx('endure_trigger', 'ENDURE_TRIGGERED', "버팀 발동(버팀 세트 4 위기 무적·세트 6 HP 0 버팀·패시브 '마지막 잔'). 무거운 심장 박동 두 번 + 발을 박는 강철 버팀 + 차오르는 숨(노이즈, 목소리 아님) + 낮은 D2. 무적 시작 프레임", -1)
def _endure_trigger(sr, rng):
    dur = 1.0
    s = zeros(sec(sr, dur))
    mix_into(s, heartbeat(sr, rng, 1.0), 0, 1.0)
    mix_into(s, heavy_step(sr, rng, 1.0), sec(sr, 0.02), 0.6)
    mix_into(s, metal(sr, 0.35, 520, rng, tau=0.08, jitter=0.03), sec(sr, 0.03), 0.3)
    n = sec(sr, 0.5)
    br = svf(noise(sr, 0.5, rng), sr, sweep(sr, n, 400, 1500), 1.1, 'band')
    mix_into(s, mul(br, [((i / n) ** 1.3) * (1 if i < n * 0.85 else (n - i) / (n * 0.15)) for i in range(n)]), sec(sr, 0.3), 0.3)
    d2 = lowpass(tone(sr, 0.8, 73.42, kind='saw'), sr, 260)
    mix_into(s, mul(d2, env_adsr(sr, 0.8, 0.1, 0.0, 1.0, 0.5)), sec(sr, 0.1), 0.4)
    s = softclip(s, 1.3)
    return reverb(tail(s, sr, 0.02), sr, size=0.7, decay=0.5, wet=0.15)


# --- 60라운드: 2차 묶음 · 2단 갈래 16종 · 패시브 — 별도 모듈(CLAUDE.md 6-1 분리) ----------------------
# 등록 순서 = 아래 import 순서(시드 = 1000 + 등록 순서). 기존 148개는 바이트 불변이어야 하므로 이 줄 위에는
# 효과음을 더 넣지 않는다. 새 효과음은 마지막 모듈(sfx_passive.py) 끝 — 또는 그 뒤 새 모듈 — 에만 추가한다.
# 모듈은 `from build import *` 로 이 파일의 DSP 유틸을 쓴다: 스크립트로 실행될 때(__main__)도 같은 모듈 객체를
# 쓰도록 'build' 이름을 먼저 걸어 둔다(두 번 실행되어 SFX 표가 갈라지는 것을 막음).
sys.modules.setdefault('build', sys.modules[__name__])
import sfx_bundle2  # noqa: E402,F401  2차 묶음 25 (엘리트·성소·등급·리롤·소모품·이벤트·숨은 노드·지도 정보·파훼·증류 화로)
import sfx_branch2  # noqa: E402,F401  2단 갈래 16종 → 32 파일
import sfx_passive  # noqa: E402,F401  패시브 9종 → 10 파일
import listen_index  # noqa: E402  들어보기 페이지용 목록(listen_index.json)


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
    os.makedirs(SFX_WAV_DIR, exist_ok=True)
    out = []
    for i, (name, spec) in enumerate(SFX.items()):
        if names and name not in names:
            continue
        rng = random.Random(1000 + i)
        buf = spec['fn'](SR_SFX, rng)
        if not spec['loop']:
            buf = fade_edges(buf, SR_SFX, 0.002)
        path = os.path.join(SFX_WAV_DIR, name + '.wav')
        dur = write_wav(path, buf, SR_SFX)
        out.append((name, path, dur))
        print('  sfx  %-20s %6.3fs' % (name, dur))
    return out


def build_bgm(names=None):
    os.makedirs(BGM_WAV_DIR, exist_ok=True)
    out = []
    for i, (name, spec) in enumerate(BGM.items()):
        if names and name not in names:
            continue
        rng = random.Random(5000 + i)
        buf = spec['fn'](SR_BGM, rng)
        path = os.path.join(BGM_WAV_DIR, name + '.wav')
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


def _items(kind=None, names=None):
    """(kind, name, 캐시 WAV 경로, 배포 폴더, loop) 목록 — 등록 순서."""
    out = []
    if kind in (None, 'sfx'):
        for name, spec in SFX.items():
            if not names or name in names:
                out.append(('sfx', name, os.path.join(SFX_WAV_DIR, name + '.wav'), SFX_DIR, spec['loop']))
    if kind in (None, 'bgm'):
        for name, spec in BGM.items():
            if not names or name in names:
                out.append(('bgm', name, os.path.join(BGM_WAV_DIR, name + '.wav'), BGM_DIR, True))
    return out


def _need_cache(items):
    missing = [os.path.relpath(w, ROOT) for _, _, w, _, _ in items if not os.path.exists(w)]
    if missing:
        sys.exit('작업 캐시 WAV 가 없습니다(%d개, 예: %s). 먼저 `python3 parts/sound/work/build.py` 로 합성하세요.'
                 % (len(missing), missing[0]))


def encode_all(kind=None, names=None):
    items = _items(kind, names)
    _need_cache(items)
    for k, name, wav_path, out_dir, loop in items:
        encode.encode_file(k, wav_path, out_dir, loop)
        print('  enc  %-20s ogg %6.1f KB  m4a %6.1f KB%s' % (
            name, os.path.getsize(os.path.join(out_dir, name + '.ogg')) / 1024,
            os.path.getsize(os.path.join(out_dir, name + '.m4a')) / 1024, '  (loop)' if loop else ''))


def _asset_path(kind, name, fmt):
    return 'assets/audio/%s/%s.%s' % (kind, name, fmt)


def write_manifest():
    items = _items()
    _need_cache(items)
    entries = []
    for kind, name, wav_path, out_dir, loop in items:
        info = wav_info(wav_path)
        files = [_asset_path(kind, name, fmt) for fmt in encode.FORMATS]
        e = dict(id='%s/%s' % (kind, name), kind=kind)
        e['category'] = SFX[name]['category'] if kind == 'sfx' else 'bgm'
        e['file'] = files[0]
        e['files'] = files
        e['sampleRate'] = info['sr']
        e['channels'] = info['ch']
        e['samples'] = info['frames']
        e['durationMs'] = int(round(info['dur'] * 1000))
        e['loop'] = loop
        if loop:
            e['loopStartSample'] = 0
            e['loopEndSample'] = info['frames']
        if kind == 'sfx':
            spec = SFX[name]
            e['gainDb'] = spec['gain_db']
            e['trigger'] = parse_trigger(spec['trigger'])
        else:
            spec = BGM[name]
            e['gainDb'] = spec['gain_db']
            e['floors'] = spec['floors']
        e['note'] = spec['note']
        entries.append(e)
    prof = encode.PROFILE
    manifest = dict(
        version=1,
        generatedBy='parts/sound/work/build.py',
        format=dict(
            container='ogg', codec='vorbis', mime=encode.MIME['ogg'],
            alternates=[dict(container='m4a', codec='aac-lc', mime=encode.MIME['m4a'])],
            filesNote='file = 1순위(Ogg Vorbis) 경로. files = 같은 소리의 형식별 경로, 선호 순서(ogg → m4a). '
                      '재생 가능한 첫 항목을 쓴다 — Phaser this.load.audio(id, files) 에 그대로 넘기면 된다.',
            loopNote='loop 항목의 이음매 구간은 [loopStartSample, loopEndSample) = 파일 전체 [0, samples). '
                     '디코더가 끝 패딩을 남겨 버퍼가 samples 보다 길면 AudioBufferSourceNode.loopEnd = '
                     'loopEndSample / sampleRate 로 지정한다(M4A 를 쓰는 브라우저 대비).',
            encode=dict(bgm=dict(oggQuality=prof['bgm']['ogg_q'], m4aKbps=prof['bgm']['m4a_kbps']),
                        sfx=dict(oggQuality=prof['sfx']['ogg_q'], m4aKbps=prof['sfx']['m4a_kbps'])),
            source=dict(container='wav', dir='parts/sound/work/wav/',
                        note='합성 원본. 배포·저장소에 넣지 않으며 build.py 로 바이트 단위 재생성(결정적).'),
            bitDepth=16, peakDbfs=PEAK_DBFS,
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


def _fmt_seam(v):
    return '-' if v is None else '%.2f (%.0f dB)' % v


def verify():
    """WAV 원본(피크·클리핑·경계) + OGG·M4A 디코드 대조(길이·정렬·피크·루프 이음매)."""
    items = _items()
    _need_cache(items)
    print('| 파일 | SR | 샘플 | 길이(s) | 루프 | WAV 피크 | WAV 경계비 | OGG KB | OGG 길이차 ff/vf | OGG 피크 | OGG 이음매 '
          '| M4A KB | M4A elst | M4A 끝패딩 | M4A 피크 | M4A 이음매 | 판정 |')
    print('<!-- 이음매 = 튐 비율(디코드 이음매 한 칸 ÷ 안쪽 인접 변화 99.9 백분위, ≤1 통과) (원본 대비 이음매 오차 dBFS) -->')
    print('|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|')
    tot = dict(wav=0, ogg=0, m4a=0)
    by_kind = {}
    bad_total = 0
    for kind, name, wav_path, out_dir, loop in items:
        wi = wav_info(wav_path)
        bad = []
        if not (wi['clipped'] == 0 and wi['peak_db'] <= -5.9 and wi['seam_ratio'] <= 1.0):
            bad.append('wav')
        enc = {fmt: os.path.join(out_dir, '%s.%s' % (name, fmt)) for fmt in encode.FORMATS}
        if not all(os.path.exists(p) for p in enc.values()):
            bad.append('인코딩 없음')
            r = None
        else:
            r, b2 = encode.check_encoded(kind, wav_path, enc, loop)
            bad += b2
        tot['wav'] += wi['bytes']
        k = by_kind.setdefault(kind, dict(n=0, wav=0, ogg=0, m4a=0))
        k['n'] += 1
        k['wav'] += wi['bytes']
        if r:
            tot['ogg'] += r['ogg_kb'] * 1024
            tot['m4a'] += r['m4a_kb'] * 1024
            k['ogg'] += r['ogg_kb'] * 1024
            k['m4a'] += r['m4a_kb'] * 1024
            vf = 'n/a' if r['ogg_vf'] is None else '%+d' % r['ogg_vf']
            print('| %s/%s | %d | %d | %.3f | %s | %.2f | %.2f | %.1f | %+d/%s | %.2f | %s | %.1f | %s | %+d | %.2f | %s | %s |' % (
                kind, name, wi['sr'], wi['frames'], wi['dur'], '루프' if loop else '', wi['peak_db'], wi['seam_ratio'],
                r['ogg_kb'], r['ogg_ff'], vf, r['ogg_peak'], _fmt_seam(r['ogg_seam']),
                r['m4a_kb'], 'ok' if r['m4a_elst'] == wi['frames'] else r['m4a_elst'], r['m4a_tail'],
                r['m4a_peak'], _fmt_seam(r['m4a_seam']), 'OK' if not bad else ', '.join(bad)))
        else:
            print('| %s/%s | %d | %d | %.3f | %s | %.2f | %.2f | - | - | - | - | - | - | - | - | - | %s |' % (
                kind, name, wi['sr'], wi['frames'], wi['dur'], '루프' if loop else '', wi['peak_db'], wi['seam_ratio'],
                ', '.join(bad)))
        if bad:
            bad_total += 1
    print()
    mb = 1048576.0
    for kind, k in by_kind.items():
        print('%s %d개: WAV %.2f MB → OGG %.2f MB (%.1f%%), M4A %.2f MB (%.1f%%)' % (
            kind, k['n'], k['wav'] / mb, k['ogg'] / mb, 100 * k['ogg'] / k['wav'], k['m4a'] / mb, 100 * k['m4a'] / k['wav']))
    print('전체 %d개: WAV %.2f MB → 배포(OGG+M4A) %.2f MB, 브라우저 1곳이 받는 양 OGG %.2f MB / M4A %.2f MB, 문제 %d 건' % (
        len(items), tot['wav'] / mb, (tot['ogg'] + tot['m4a']) / mb, tot['ogg'] / mb, tot['m4a'] / mb, bad_total))
    if not encode._vorbisfile():
        print('(libvorbisfile 없음 — OGG 참조 디코더 대조 생략)')
    return bad_total == 0


def main(argv):
    what = argv[1] if len(argv) > 1 else 'all'
    names = set(argv[2:]) if len(argv) > 2 else None
    if what in ('all', 'sfx'):
        print('[sfx] %d 종' % len(SFX))
        build_sfx(names)
    if what in ('all', 'bgm'):
        print('[bgm] %d 곡' % len(BGM))
        build_bgm(names)
    if what in ('all', 'sfx', 'bgm', 'encode'):
        kind = what if what in ('sfx', 'bgm') else None
        print('[encode] ogg q%s/%s · m4a %s/%s kbps (bgm/sfx)' % (
            encode.PROFILE['bgm']['ogg_q'], encode.PROFILE['sfx']['ogg_q'],
            encode.PROFILE['bgm']['m4a_kbps'], encode.PROFILE['sfx']['m4a_kbps']))
        encode_all(kind, names)
    if what in ('all', 'sfx', 'bgm', 'encode', 'manifest'):
        write_manifest()
    if what in ('all', 'sfx', 'bgm', 'encode', 'manifest', 'listen'):
        listen_index.write(ROOT, MANIFEST, SFX)
    if what in ('all', 'verify'):
        print()
        ok = verify()
        return 0 if ok else 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
