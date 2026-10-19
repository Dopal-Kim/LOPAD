# -*- coding: utf-8 -*-
"""
P19 (1-Snd) — 전투 BGM 강도 2단: 1층 전투 곡 `f1_jan` 위에 겹치는 **타악 겹** `f1_jan_perc`.

build.py 가 bgm_training 다음(마지막)에 import 한다(BGM 시드 = 5000 + 등록 순서 → 기존 12곡 불변).
f1_jan 과 **같은 길이·박자 격자**(A 단조 3/4 150 BPM, 80마디 = 96 s, 44.1 kHz 스테레오)라서 시스템은 f1_jan 의
지금 재생 위치에 맞춰 이 파일을 함께 돌리고 음량만 올리고 내린다(manifest `mixing.bgmIntensity`).
구성은 f1_jan 구간(A 0~15 · B 16~31 · C 32~47 · B' 48~63 · D 64~79)을 따라간다: 큰 북 1박 · 술통 '통' 2박 뒤 ·
군북 몰아치기(4마디마다) · B·B' 8분음(P21 부터 탬버린 대신 낮은 손북) · C 구간 스네어 유령음 · D 끝 8마디 쌓기. 화음 악기 없음(곡과 부딪히지 않게).
근거: decisions/2026-10-14-P19-free-combat.md ④H '웨이브 겹침에 맞춰 전투 BGM 강도 2단(적 ≥ 6 이면 타악 층 추가)'.
"""
from build import *  # noqa: F401,F403
from build import bgm  # noqa: F401
from bgm_floor1 import SR2, Bus, reverb2, lp_loop, frame_drum, big_drum, barrel, _out


def _buk(sr, rng, g=1.0, f=(118, 64)):
    """군북 '둥'(효과음 drummer_beat 와 같은 재료 — 깃발 고수 북이 곡 안에서도 들리는 결)."""
    d = thud(sr, 0.36, f[0], f[1], 0.1)
    mix_into(d, burst(sr, 0.04, rng, fc=1100, q=0.7, tau=0.01), 0, 0.35)
    mix_into(d, burst(sr, 0.2, rng, fc=220, q=0.6, tau=0.05, mode='low'), 0, 0.4)
    return scale(d, g)


@bgm('f1_jan_perc', "P19 전투 강도 겹 — 1층 전투 곡 f1_jan 위에 겹치는 타악만의 층(96 s 루프, 80마디, 44.1 kHz 스테레오, 3/4 150 BPM — f1_jan 과 같은 길이·박자 격자). 큰 북 1박 + 술통 '통' 2박 뒤(좌우 번갈아) + 군북 4마디마다 몰아치기 + B·B' 낮은 손북 8분음(P21 — 탬버린 뺌) + C(긴장) 군북 2·3박 · 둔한 스네어 유령음 + D 앞 8마디 비움 → 끝 8마디 군북 8분음 쌓기. 화음 악기 없음. P21: f1_jan 과 같은 어두운 방(넓은 리버브 + 3.6 kHz 위 덮음). 혼자 재생하지 않는다 — f1_jan 재생 위치에 맞춰 함께 돌리고 mixing.bgmIntensity 규칙으로 음량만 올림/내림(살아 있는 적 ≥ 6 → 켬). 권장 음량 -0.8 dB(P21 — 어둡게 다시 뒤 파일 -22.3 LUFS → -23.1, f1_jan -19.1 보다 4 LU 아래. 겹치면 -17.8 LUFS = +1.3 LU)", -0.8, sr=SR2, use=dict(floor=1, state='combatLayer'))
def _bgm_f1_jan_perc(sr, rng):
    beat = 60.0 / 150.0
    bar = beat * 3
    bars = 80
    n = sec(sr, bar * bars)
    bus = Bus(n)
    jit = lambda: rng.uniform(-0.004, 0.006)  # noqa: E731
    for b in range(bars):
        sect = b // 16
        t0 = b * bar
        building = sect == 4 and b >= 72
        resting = sect == 4 and b < 72
        # 큰 북 1박(D 앞 8마디는 두 마디에 한 번)
        if not resting or b % 2 == 0:
            bus.put(big_drum(sr, rng, 1.0), t0 + jit(), sr, 0.5 if not resting else 0.35)
        # 술통 '통' 2박 뒤(좌우 번갈아), B·B' 는 3박에도
        if not resting:
            bus.put(barrel(sr, rng), t0 + 1.5 * beat + jit(), sr, 0.32, 0.4 if b % 2 else -0.4)
            if sect in (1, 3):
                bus.put(barrel(sr, rng, 0.8), t0 + 2.0 * beat + jit(), sr, 0.22, -0.4 if b % 2 else 0.4)
        # B·B' 8분음: P21 — 탬버린 대신 낮은 손북 유령음(고역 줄임)
        if sect in (1, 3):
            for k, off in enumerate((0.5, 1.0, 1.5, 2.0, 2.5)):
                bus.put(frame_drum(sr, rng, 0.5, 150, 85), t0 + off * beat + jit(), sr, 0.07 if k % 2 else 0.045, 0.5)
        # C(긴장): 군북 2·3박 + 스네어 유령음 3박 뒤
        if sect == 2:
            for off in (1.0, 2.0):
                bus.put(_buk(sr, rng, 0.8), t0 + off * beat + jit(), sr, 0.42, -0.15)
            bus.put(lowpass(snare(sr, rng, 0.1, 0.2), sr, 2200), t0 + 2.5 * beat + jit(), sr, 0.07, 0.2)
        # 4마디마다 끝 마디에 군북 몰아치기(8분음 셋, 점점 세게)
        if b % 4 == 3 and not resting and not building:
            for k, off in enumerate((1.0, 1.5, 2.0, 2.5)):
                bus.put(_buk(sr, rng, 0.7 + 0.1 * k, (128 - 4 * k, 66)), t0 + off * beat + jit(), sr, 0.3 + 0.06 * k, 0.15)
        # D 끝 8마디: 군북 8분음 쌓기(점점 세게) — f1_jan 의 손북 쌓기·스네어 롤과 같은 자리
        if building:
            for k in range(6):
                bus.put(_buk(sr, rng, 1.0, (124, 66)), t0 + k * 0.5 * beat + jit(), sr,
                        0.14 + 0.32 * (b - 72) / 8 + 0.02 * k, -0.1)
        # 손북 겹(앞뒤 빈 박을 채움, 아주 작게)
        if sect in (0, 1, 3):
            bus.put(frame_drum(sr, rng, 0.6, 170, 95), t0 + 2.5 * beat + jit(), sr, 0.12, 0.25)
    out = reverb2(bus, sr, size=1.2, decay=0.68, wet=0.26, damp=0.55)   # P21: f1_jan 과 같은 어두운 방
    out.L = lp_loop(out.L, sr, 3600)
    out.R = lp_loop(out.R, sr, 3600)
    return _out(out)
