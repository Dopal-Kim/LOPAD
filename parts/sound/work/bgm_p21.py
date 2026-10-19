# -*- coding: utf-8 -*-
"""
P21 — 타이틀 곡 `bgm/title_dark` (44.1 kHz 스테레오, 64 s 루프). manifest `bgmByState.title` 를 이 곡으로 바꾼다
(옛 `bgm/title` 은 파일·항목을 남긴 폴백).

build.py 가 bgm_p19 다음(마지막)에 import 한다(BGM 시드 = 5000 + 등록 순서 → 기존 13곡 시드 불변).
근거: decisions/2026-10-19-P21-dark-brutal.md §4 음향 '타이틀 곡 교체(낮은 드론·현·먼 종·비·까마귀)',
contracts/dark-brutal.md §9 `bgm/title_dark`. 타이틀 화면 = 밤·젖은 재·피 묻은 연회장·시체·까마귀(아트 A).

구성(박자 없음, A 프리지아 — 반음 위 B♭ 이 계속 문지름): 바닥 A1 드론(+ B♭1 반음 불협이 루프에 한 번 부풀었다 가라앉음)
· 0~64 s 내내 비(좌우 따로) · 2 s·34 s 먼 종 · 12 s 부터 느린 첼로 두 악구 · 콘트라베이스 긴 음 · 22 s·47 s 먼 까마귀 ·
38 s·58 s 가까운 숨(목소리 없음). 고역은 6 kHz 에서 덮는다(어둡게). 루프 규칙은 bgm_floor1 과 같다.
"""
from build import *  # noqa: F401,F403
from build import bgm, BGM  # noqa: F401
from bgm_floor1 import SR2, Bus, reverb2, svf_loop, lp_loop, _out
from sfx_stage61 import breath


def cello(sr, dur, f, rng, vib=0.004, a=0.9, r=1.6, bright=1.0):
    """느린 활 현(첼로·콘트라베이스): 톱니 두 겹 디튠 + 몸통 공명 셋 + 활 잡음, 느린 어택·긴 릴리즈."""
    n = sec(sr, dur)
    vr = 4.8 + rng.uniform(-0.3, 0.3)
    ph = rng.uniform(0, TAU)
    freqs = [f * (1 + vib * min(1.0, i / (sr * 1.2)) * math.sin(TAU * vr * i / sr + ph)) for i in range(n)]
    osc = tone_f(sr, freqs, 'saw', rng.random())
    osc2 = tone_f(sr, [x * 1.003 for x in freqs], 'saw', rng.random())
    o = [p + 0.7 * q for p, q in zip(osc, osc2)]
    body = scale(svf(o, sr, 230, 1.5, 'band'), 0.7)
    mix_into(body, svf(o, sr, 520, 2.0, 'band'), 0, 0.5)
    mix_into(body, svf(o, sr, 1150, 2.0, 'band'), 0, 0.22 * bright)
    mix_into(body, lowpass(o, sr, 700), 0, 0.35)
    mix_into(body, svf(noise(sr, dur, rng), sr, 1800, 0.8, 'band'), 0, 0.03)   # 활 잡음
    return mul(lowpass(body, sr, 1900), env_adsr(sr, dur, a, 0.0, 1.0, r, curve=1.4))


def crow(sr, rng, f0=640):
    """까마귀 '까악'(성대음 아닌 거친 합성 — 톱니 + 노이즈를 포먼트 둘로, 70 Hz 거칠게 떨림, 끝이 처짐)."""
    d = rng.uniform(0.26, 0.34)
    n = sec(sr, d)
    fr = [f0 * (1.0 + 0.08 * math.sin(math.pi * i / n)) * (1 - 0.18 * (i / n) ** 2) for i in range(n)]
    src = tone_f(sr, fr, 'saw', rng.random())
    mix_into(src, noise(sr, d, rng), 0, 0.5)
    s = scale(svf(src, sr, 1150, 3.0, 'band'), 0.8)
    mix_into(s, svf(src, sr, 1650, 3.5, 'band'), 0, 0.5)
    s = mul(s, [0.55 + 0.45 * math.sin(TAU * 70 * i / sr) for i in range(n)])
    return lowpass(mul(s, env_adsr(sr, d, 0.015, 0.0, 1.0, d * 0.45)), sr, 2600)


@bgm('title_dark', "P21 타이틀(bgmByState.title — 옛 bgm/title 대체). 64 s 루프, 44.1 kHz 스테레오, 박자 없음, A 프리지아. "
     "바닥 A1 톱니 드론(필터가 32 s 주기로 열렸다 닫힘) + E2 · B♭1 반음 불협이 루프에 한 번 부풀었다 가라앉음 · 내내 좌우 따로 내리는 비(빗줄기 + 처마 물방울, 32 s 주기로 세졌다 약해짐) + 낮은 바람 · "
     "2 s · 34 s 먼 종(A2·E3, 저역통과·긴 꼬리) · 12~38 s 첼로 첫 악구(A–B♭–A–G–F–E, 느린 활) · 42~61 s 둘째 악구(C–B♭–A–G♯–A) + 콘트라베이스 긴 음(A1·E1·B♭1·A1) · "
     "22 s 왼쪽 먼 까마귀 셋 · 47 s 오른쪽 더 먼 까마귀 둘 · 38 s 가까운 숨(들이쉼–내쉼) · 58.5 s 떨리는 내쉼(목소리 없음). 6 kHz 위를 덮어 어둡게. "
     "권장 음량 -7.0 dB = 통합 -23.1 LUFS(파일 -16.1 — 드론·현이 빽빽해 RMS 가 큼. 옛 타이틀 -23.2 · 벽 밖 -22.5 와 같은 조용한 층)", -7.0, sr=SR2)
def _bgm_title_dark(sr, rng):
    L = 64.0
    n = sec(sr, L)
    bus = Bus(n)
    # 드론: A1 톱니(필터 32 s 주기) + E2 사인 + B♭1 반음 불협(루프에 한 번 부풂)
    fc = lfo_loop(sr, n, 2 / L, 60, 150)
    bus.layer(svf_loop(tone_loop(sr, n, 55.0, 'saw'), sr, [x + 30 for x in fc], 0.8, 'low'), None, 0.42)
    bus.layer(tone_loop(sr, n, 82.41, 'sine'), None, 0.08)
    rub = lp_loop(tone_loop(sr, n, 58.27, 'saw'), sr, 110)
    sw = lfo_loop(sr, n, 1 / L, 0.5, 0.5, 0.75)           # 0 s 최저 → 32 s 최고
    bus.layer([a * max(0.0, w) ** 1.5 for a, w in zip(rub, sw)], None, 0.2)
    # 비: 좌우 따로(빗줄기 = 밴드 노이즈, 32 s 주기 세기) + 처마 물방울
    for ch, shift in ((0, 0.0), (1, 0.41)):
        amt = lfo_loop(sr, n, 2 / L, 0.25, 0.75, shift)
        rn = svf_loop(noise_loop(sr, n, rng), sr, 2200, 0.5, 'band')
        rn = svf_loop(rn, sr, 380, 0.7, 'high')
        tgt = bus.L if ch == 0 else bus.R
        for i in range(n):
            tgt[i] += rn[i] * amt[i] * 0.09
    for _ in range(int(L * 9)):
        t = rng.uniform(0, L)
        dr = burst(sr, 0.02, rng, fc=rng.uniform(1400, 3800), q=1.4, tau=rng.uniform(0.001, 0.003))
        bus.put(dr, t, sr, rng.uniform(0.02, 0.07), rng.uniform(-0.9, 0.9))
    for t in (5.3, 9.1, 17.8, 26.4, 31.0, 40.7, 51.2, 55.9, 61.5):          # 처마에서 떨어지는 굵은 물방울
        bus.put(lowpass(mul(tone(sr, 0.05, 700, 1100), env_exp(sr, 0.05, 0.012)), sr, 2500), t, sr, 0.05, rng.uniform(-0.6, 0.6))
    wind = svf_loop(noise_loop(sr, n, rng), sr, 260, 0.7, 'low')
    bus.layer(mul(wind, lfo_loop(sr, n, 3 / L, 0.4, 0.6, 0.2)), None, 0.1)
    # 먼 종
    for t0, f, g, pan in ((2.0, 110.0, 0.2, 0.35), (2.02, 164.81, 0.08, 0.35), (34.0, 110.0, 0.17, -0.3), (34.02, 164.81, 0.07, -0.3)):
        bus.put(lowpass(bell(sr, 7.0, f, rng, tau=2.2), sr, 1400), t0, sr, g, pan, width=0.012)
    # 첼로 두 악구 + 콘트라베이스 긴 음
    for t0, m, d in ((12, 45, 4.2), (16, 46, 3.2), (19, 45, 5.0), (24.5, 43, 3.0), (27.5, 41, 3.5), (31.5, 40, 6.5),
                     (42, 48, 3.2), (45, 46, 3.2), (48, 45, 4.0), (52, 44, 3.2), (55, 45, 6.0)):
        bus.put(cello(sr, d + 1.6, midi(m) * 2 ** (rng.uniform(-0.04, 0.04) / 12), rng), t0, sr, 0.16, -0.25, width=0.008)
    for t0, m, d in ((8, 33, 10), (31.5, 28, 8), (44, 34, 6), (52, 33, 11)):
        bus.put(cello(sr, d, midi(m), rng, vib=0.002, a=2.0, r=3.0, bright=0.4), t0, sr, 0.14, 0.2, width=0.01)
    # 까마귀(멀리)
    for t0, cnt, pan, g, f0 in ((22.0, 3, -0.65, 0.07, 640), (47.0, 2, 0.7, 0.045, 600)):
        for k in range(cnt):
            bus.put(crow(sr, rng, f0 * rng.uniform(0.95, 1.05)), t0 + k * rng.uniform(0.42, 0.55), sr, g, pan)
    # 숨(가까이, 목소리 없음): 들이쉼–내쉼, 끝 무렵 떨리는 내쉼
    bus.put(breath(sr, rng, 1.1, (900, 760), (1500, 1350), rough=0.25, a=0.5, r=0.5), 38.0, sr, 0.05, 0.05)
    bus.put(breath(sr, rng, 1.8, (620, 420), (1100, 950), rough=0.45, a=0.08, chest=0.4), 39.3, sr, 0.06, 0.05)
    bus.put(breath(sr, rng, 2.0, (560, 400), (1050, 900), rough=0.75, a=0.1, chest=0.5), 58.5, sr, 0.05, -0.05)
    out = reverb2(bus, sr, size=1.6, decay=0.85, wet=0.4, damp=0.6)
    out.L = lp_loop(out.L, sr, 6000)
    out.R = lp_loop(out.R, sr, 6000)
    return _out(out)


BGM['title_dark']['state'] = 'title'   # manifest bgmByState.title (옛 bgm/title 은 폴백으로 남김)
BGM['title']['note'] = '[폴백 — P21 bgm/title_dark 로 대체] ' + BGM['title']['note']
