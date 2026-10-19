import { describe, expect, it } from 'vitest';
import { applyMatrix, gradeMatrix, pulseAt, vignetteAlpha } from './gradeMath';

const lum = ([r, g, b]: readonly number[]) => 0.2126 * r + 0.7152 * g + 0.0722 * b;

describe('P21 색 보정 행렬 (dark-brutal §7 · 아트 A _semantics)', () => {
  it('항등 값이면 색이 그대로', () => {
    const m = gradeMatrix({ saturation: 0, contrast: 0, brightness: 1, shadowTint: 0 });
    const c: [number, number, number] = [0.3, 0.6, 0.9];
    applyMatrix(m, c).forEach((v, i) => expect(v).toBeCloseTo(c[i], 6));
  });

  it('채도 = Phaser saturate 인자 (−1 무채) · 대비 0.5 기준 · 명도 곱 · 틴트 더함', () => {
    const gray = applyMatrix(
      gradeMatrix({ saturation: -1, contrast: 0, brightness: 1, shadowTint: 0 }),
      [0.9, 0.3, 0.3],
    );
    expect(gray[0]).toBeCloseTo(0.5, 6);
    expect(gray[1]).toBeCloseTo(0.5, 6);
    const flat = (c: number) => gradeMatrix({ saturation: 0, contrast: c, brightness: 1, shadowTint: 0 });
    expect(applyMatrix(flat(0.5), [0.5, 0.5, 0.5])[0]).toBeCloseTo(0.5, 6);
    expect(applyMatrix(flat(0.5), [0.7, 0.7, 0.7])[0]).toBeCloseTo(0.8, 6);
    const tinted = applyMatrix(
      gradeMatrix({ saturation: 0, contrast: 0, brightness: 0.5, shadowTint: 0x050609 }),
      [0, 0, 0],
    );
    expect(tinted[2]).toBeCloseTo(9 / 255, 6);
  });

  it('아트 A 1차 값: 어두워지고 채도가 빠진다', () => {
    const m = gradeMatrix({ saturation: -0.42, contrast: 0.04, brightness: 0.95, shadowTint: 0x050609 });
    const warm: [number, number, number] = [0.8, 0.5, 0.25];
    const out = applyMatrix(m, warm);
    expect(lum(out)).toBeLessThan(lum(warm));
    const spread = (c: readonly number[]) => Math.max(...c) - Math.min(...c);
    // 빨강 − 파랑 = 원래 차 × 채도 배율 × 대비 × 명도 + 틴트 차 (5 − 9)/255
    expect(spread(out)).toBeCloseTo(spread(warm) * 0.58 * 1.04 * 0.95 - 4 / 255, 4);
  });

  it('비네트: 반지름 안은 0, 모서리는 strength · 맥박 0.6~1.0', () => {
    expect(vignetteAlpha(0.4, 0.45, 0.3)).toBe(0);
    expect(vignetteAlpha(0.4, 0.45, 1)).toBeCloseTo(0.4, 6);
    for (let t = 0; t < 2000; t += 37) {
      const v = pulseAt(t, 1.2);
      expect(v).toBeGreaterThanOrEqual(0.6 - 1e-9);
      expect(v).toBeLessThanOrEqual(1 + 1e-9);
    }
  });
});
