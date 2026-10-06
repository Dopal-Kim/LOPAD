# -*- coding: utf-8 -*-
"""
61라운드 단계 6 (P14) — 수련장 BGM `bgm/training` (44.1 kHz 스테레오, 72 s 루프). manifest `bgmByState.training`.

build.py 가 bgm_floor1 다음에 import 한다(BGM 시드 = 5000 + 등록 순서 → 기존 11곡 불변).
1층 곡(f1_jan)과 **같은 악기 결**(콘트라베이스 피치카토 · 손풍금 · 바이올린 · 류트 · 손북 · A1 드론 · 바람)을 쓰되
긴장을 낮춘 고요한 연습 곡: A 단조 3/4 90 BPM(마디 2 s × 36 = 72 s). 잔 거리 주제를 느리게, 취하지 않은 손으로
(아래에서 미끄러져 드는 음을 줄이고 끝이 처지는 음 없음) — 서사 '이름이 번지기 전, 손이 기억하는 곳'(설계 P14 §1).
삼전음·타악 몰아치기 없음. 루프 규칙은 bgm_floor1 과 같다(wrap 섞기 · 정수 주기 재료 · 덧댄 필터/리버브).
"""
from build import *  # noqa: F401,F403
from build import bgm, BGM  # noqa: F401
from bgm_floor1 import (SR2, Bus, reverb2, svf_loop, lp_loop, fiddle, reed, bass_pluck, frame_drum,  # noqa: F401
                        bar_notes, JAN_MEL, _out)

# (류트·손풍금 화음, 베이스 근음, 5음) — A 단조, 이끔음 E 는 7화음 대신 E 장3화음으로 부드럽게
CH_TR = {'Am': ([57, 60, 64], 45, 52), 'E': ([56, 59, 64], 40, 47), 'Dm': ([57, 62, 65], 38, 45),
         'F': ([57, 60, 65], 41, 48), 'C': ([55, 60, 64], 48, 43)}
TR_A = ['Am', 'Am', 'F', 'F', 'Dm', 'Dm', 'E', 'E']                                     # 0~7   류트 · 바람
TR_B = ['Am', 'Am', 'E', 'E', 'Am', 'Am', 'Dm', 'Dm', 'Dm', 'Am', 'E', 'Am', 'F', 'Dm', 'E', 'E']   # 8~23 주제
TR_C = ['F', 'F', 'C', 'C', 'Dm', 'Dm', 'E', 'E']                                     # 24~31 손풍금 지속 · 낮은 현
TR_D = ['Am', 'Am', 'E', 'E']                                                          # 32~35 비움 → 처음으로
TR_PROG = TR_A + TR_B + TR_C + TR_D
TR_LOW = [(24, 57, 2), (26, 55, 2), (28, 53, 2), (30, 56, 1), (31, 59, 1)]             # C 구간 낮은 현 (마디, midi, 마디 수)


@bgm('training', "수련장(61-6 P14, bgmByState.training). 72 s 루프(36마디), 44.1 kHz 스테레오, A 단조 3/4 90 BPM. 1층 잔 거리와 같은 악기 결을 고요하게: 류트 8분음 분산화음 + 콘트라베이스 1박 + 아주 작은 손북 + 손풍금 2박 한 번, 잔 거리 바이올린 주제를 느리고 맑게(미끄러짐 작게·처지는 음 없음), C 구간 손풍금 긴 화음 + 낮은 현 대선율, 끝 4마디는 류트만 남아 처음으로. 바닥에 A1 드론·좌우 바람, 마디 0·24 에 먼 종(A4) 한 번. 삼전음·몰아치기 없음(긴장 낮게). 권장 음량 +1.8 dB = RMS 약 -23 dBFS(벽 밖과 같은 조용한 층, 전투 곡보다 2 dB 작게)", 1.8, sr=SR2)
def _bgm_training(sr, rng):
    bpm = 90.0
    beat = 60.0 / bpm
    bar = beat * 3
    bars = len(TR_PROG)
    n = sec(sr, bar * bars)
    bus = Bus(n)
    jit = lambda: rng.uniform(-0.004, 0.006)  # noqa: E731  아주 작은 흔들림(취하지 않음)
    for b in range(bars):
        t0 = b * bar
        chord, root, fifth = CH_TR[TR_PROG[b]]
        sect = 0 if b < 8 else 1 if b < 24 else 2 if b < 32 else 3
        # 콘트라베이스 1박 — A·D 는 근음만, B·C 는 근음·5음 번갈아
        m = root if (sect in (0, 3) or b % 2 == 0) else fifth
        bus.put(bass_pluck(sr, 1.4, midi(m), rng), t0 + jit(), sr, 0.42 if sect in (1, 2) else 0.34)
        # 류트 8분음 분산화음(D 는 한 옥타브 위에서 성기게)
        pat = [0, 1, 2, 1, 2, 1]
        for k in range(6):
            if sect == 3 and k % 2:
                continue
            mm = chord[pat[k]] + (12 if sect == 3 else 0)
            p = mul(pluck(sr, 0.9, midi(mm) * (1 + rng.uniform(-0.003, 0.003)), rng, damp=0.994, bright=0.45),
                    env_exp(sr, 0.9, 0.3))
            bus.put(lowpass(p, sr, 2400), t0 + k * 0.5 * beat + jit(), sr, (0.1 if k % 2 == 0 else 0.07), -0.5,
                    width=0.006)
        # 손북: B·C 의 1박만 아주 작게
        if sect in (1, 2):
            bus.put(frame_drum(sr, rng, 1.0, 120, 70), t0, sr, 0.22, 0.05)
        # 손풍금: B 는 2박 한 번 짧게(왈츠의 흔적), C 는 2마디 긴 화음(느린 바람통 떨림)
        if sect == 1:
            for mm in chord:
                bus.put(reed(sr, 0.36, midi(mm) * 0.9995, fc=1100), t0 + 1.0 * beat + jit(), sr, 0.05, -0.3, width=0.008)
        elif sect == 2 and b % 2 == 0:
            for mm in chord:
                r = reed(sr, bar * 2 + 0.1, midi(mm) * 0.9995, fc=1000)
                r = mul(r, [0.8 + 0.2 * math.sin(TAU * 4.0 * i / sr) for i in range(len(r))])
                r = mul(r, env_adsr(sr, bar * 2 + 0.1, 0.6, 0.0, 1.0, 0.8))
                bus.put(r, t0, sr, 0.055, -0.3, width=0.01)

    # 바이올린 — 잔 거리 주제를 느리고 맑게(미끄러짐 작게, 처지는 음 없음). notes = [(시각 s, midi, 길이 s)]
    def play(notes, g, pan, octave=0, scoop=(0.15, 0.35), trem=0.0):
        for t, m, d in notes:
            f = midi(m + octave) * 2 ** (rng.uniform(-0.05, 0.05) / 12.0)
            fd = fiddle(sr, d * 0.96 + 0.06, f, rng, vib=0.005, scoop=rng.uniform(*scoop), trem=trem, bend=0.0,
                        bright=0.8)
            bus.put(fd, t + rng.uniform(0.0, 0.012), sr, g, pan, width=0.006)
    theme = bar_notes([(b, JAN_MEL[b]) for b in range(16)], bar, beat)
    play([(8 * bar + t, m, d) for t, m, d in theme], 0.15, 0.3)
    play([(7 * bar + 2 * beat, 71, beat)], 0.11, 0.3)                                         # A → B 못갖춘마디
    play([(b * bar, m, d * bar) for b, m, d in TR_LOW], 0.1, 0.2, scoop=(0.05, 0.15))      # C 낮은 현 대선율
    play([(32 * bar, 76, 2 * beat), (32 * bar + 2 * beat, 72, beat), (33 * bar, 69, 3 * beat)], 0.08, 0.35)   # D 주제 첫 조각, 멀리
    # 먼 종 A4 — 처음과 C 구간 시작(과제 종 training_task 와 같은 A)
    for t0, g in ((0.0, 0.07), (24 * bar, 0.06)):
        bus.put(bell(sr, 3.5, 440.0, rng, tau=1.3), t0, sr, g, -0.2, width=0.01)
    # 바닥: A1 드론(아주 낮게) + 좌우 따로 부는 약한 바람(3·5 주기 — 루프 정수 주기)
    L = bar * bars
    bus.layer(lp_loop(tone_loop(sr, n, 55.0, 'saw'), sr, 110), None, 0.055)
    for ch, shift in ((0, 0.0), (1, 0.37)):
        gs = [0.5 + a + c for a, c in zip(lfo_loop(sr, n, 3 / L, 0.3, 0.0, shift), lfo_loop(sr, n, 5 / L, 0.15, 0.0, 0.5 + shift))]
        w = svf_loop(noise_loop(sr, n, rng), sr, [250 + 400 * max(0.0, g) for g in gs], 0.7, 'low')
        tgt = bus.L if ch == 0 else bus.R
        for i in range(n):
            tgt[i] += w[i] * max(0.0, gs[i]) * 0.12
    return _out(reverb2(bus, sr, size=1.2, decay=0.72, wet=0.28))


BGM['training']['state'] = 'training'   # manifest bgmByState.training (층 곡이 아니라 상태 곡)
