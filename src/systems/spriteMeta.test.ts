import { describe, expect, it } from 'vitest';
import { SPRITES } from '../core/Constants';
import { overlayDepthAt, type SheetJson } from './spriteDefs';
import {
  anchorOffset,
  bladeAt,
  gripAt,
  handAt,
  overlayPivot,
  scarAt,
  scarFit,
  strideRate,
  strideSpeed,
} from './spriteMeta';

const body = { pivot: { x: 32, y: 92 }, pixelScale: 0.5 } as const;

describe('52라운드 v3 시트 메모 (spriteMeta)', () => {
  it('보폭: stride 도트 → 월드 속도, 실제 속도 비율을 범위로 자른다 (이동 속도는 그대로)', () => {
    // 걷기 36도트(v3 = 월드 9) / 800ms = 월드 11.25/s
    const walk = { stride: { px: 36, cycleMs: 800 }, pixelScale: 0.5 };
    expect(strideSpeed(walk)).toBeCloseTo(11.25);
    expect(strideRate(walk, 11.25)).toBeCloseTo(1);
    expect(strideRate(walk, 16.875)).toBeCloseTo(1.5);
    expect(strideRate(walk, 96)).toBe(SPRITES.STRIDE_RATE_MAX); // 실제 걷기 6타일/s — 상한
    expect(strideRate(walk, 1)).toBe(SPRITES.STRIDE_RATE_MIN);
    expect(strideRate({ pixelScale: 0.5 }, 96)).toBe(1); // stride 없음
    expect(strideRate(walk, 0)).toBe(1);
  });

  it('손·칼 앵커: 열·방향 고르기, gripAnchors 우선 · 없으면 무기 handAnchors 오른손', () => {
    const def = {
      handAnchors: {
        down: [
          { handR: [16, 60], handL: [48, 60] },
          { handR: [18, 58], handL: [46, 58] },
        ],
      },
      gripAnchors: { right: [[70, 90]] },
      bladeLocal: [
        { thetaDeg: null, elevDeg: null },
        { thetaDeg: -30, elevDeg: -6 },
      ],
    } as unknown as SheetJson;
    expect(handAt(def, 'down', 1)?.handR).toEqual([18, 58]);
    expect(handAt(def, 'down', 9)?.handR).toEqual([18, 58]); // 열 넘침 → 마지막
    expect(handAt(def, 'up', 0)).toBeNull();
    expect(gripAt(def, 'right', 0)).toEqual([70, 90]);
    expect(gripAt(def, 'down', 0)).toEqual([16, 60]);
    expect(bladeAt(def, 0)).toBeNull(); // 칼집 안
    expect(bladeAt(def, 1)).toEqual({ thetaDeg: -30, elevDeg: -6 });
    // v3 도트 → 월드: (16-32, 60-92) × 0.25
    expect(anchorOffset(body, [16, 60])).toEqual({ x: -4, y: -8 });
  });

  it('무기 오버레이 원점 = 몸 피벗 + playerFrameOffset (배율이 같을 때), 아니면 무기 pivot', () => {
    const weapon = { pivot: { x: 64, y: 124 }, pixelScale: 0.5, playerFrameOffset: { x: 32, y: 32 } };
    expect(overlayPivot(weapon, body)).toEqual({ x: 64, y: 124 });
    expect(overlayPivot(weapon, { pivot: { x: 30, y: 90 }, pixelScale: 0.5 })).toEqual({ x: 62, y: 122 });
    expect(overlayPivot(weapon, { pivot: { x: 16, y: 46 }, pixelScale: 1 })).toEqual({ x: 64, y: 124 });
    expect(overlayPivot({ pivot: { x: 24, y: 39 } }, body)).toEqual({ x: 24, y: 39 });
    // 53라운드 대검 확대 틀 248×272: 주인공 v3 96×144 피벗 (48,138) + 오프셋 (73,71) = JSON 피벗 (121,209)
    const greatsword = { pivot: { x: 121, y: 209 }, pixelScale: 0.5, playerFrameOffset: { x: 73, y: 71 } };
    expect(overlayPivot(greatsword, { pivot: { x: 48, y: 138 }, pixelScale: 0.5 })).toEqual({ x: 121, y: 209 });
  });

  it('깊이: occlusionBaked 면 늘 위, depthByFrame 이 depth 보다 우선', () => {
    expect(overlayDepthAt({ depth: { up: 'below' }, occlusionBaked: true }, 'up', 0)).toBe('above');
    expect(overlayDepthAt({ depth: { up: 'above' }, depthByFrame: { up: ['above', 'below'] } }, 'up', 1)).toBe('below');
    expect(overlayDepthAt({ depth: { up: 'below' } }, 'up', 0)).toBe('below');
  });
});

describe('53라운드 Q10 달리기 배속 · Q4 상흔 기준점', () => {
  it('기준 속도를 주면 상한에 걸려도 Shift 달리기는 그만큼 더 빨리 재생', () => {
    const run = { stride: { px: 45, cycleMs: 560 }, pixelScale: 0.5 };
    const base = strideRate(run, 96, 96);
    expect(base).toBe(SPRITES.STRIDE_RATE_MAX);
    expect(strideRate(run, 96 * 1.8, 96)).toBeCloseTo(base * 1.8);
    expect(strideRate(run, 96 * 1.8, 96)).toBeLessThanOrEqual(SPRITES.STRIDE_RATE_MAX * SPRITES.SPRINT_RATE_HEADROOM);
    // 기준 속도가 stride 와 맞으면 평소 1배
    const fit = { stride: { px: 384, cycleMs: 1000 }, pixelScale: 0.5 };
    expect(strideRate(fit, 96, 96)).toBeCloseTo(1);
  });

  it('scarAnchor: 방향 → 열 목록 · 시트 프레임 순서 배열 · visible:false · 형식 틀림', () => {
    const a = { x: 48, y: 50, w: 24, h: 30, rot: 0, visible: true };
    const byDir = {
      frames: 2,
      directions: ['down', 'up', 'left', 'right'],
      scarAnchor: { up: [a, { ...a, x: 50 }], down: [{ ...a, visible: false }] },
    };
    expect(scarAt(byDir, 'up', 1)?.x).toBe(50);
    expect(scarAt(byDir, 'down', 0)?.visible).toBe(false);
    expect(scarAt(byDir, 'left', 0)).toBeNull();
    const flat = { frames: 2, directions: ['down', 'up'], scarAnchor: [null, null, a, { ...a, y: 60 }] };
    expect(scarAt(flat, 'up', 1)?.y).toBe(60);
    expect(scarAt(flat, 'down', 0)).toBeNull();
    expect(scarAt({ frames: 1, directions: ['down'] }, 'down', 0)).toBeNull();
  });

  it('상흔 맞춤: 기준 비율을 지켜 앵커 안에 (남는 쪽 가운데)', () => {
    expect(scarFit({ w: 30, h: 30 }, 2)).toEqual({ w: 30, h: 15 });
    expect(scarFit({ w: 40, h: 20 }, 1)).toEqual({ w: 20, h: 20 });
  });
});
