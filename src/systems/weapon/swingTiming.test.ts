import { describe, expect, it } from 'vitest';
import {
  frameStarts,
  fxHoldFrame,
  keyedDurations,
  startsOf,
  swingFxDelayMs,
  type SheetJson,
} from '../sprites/spriteDefs';

/** 대검 1타 몸 시트(v3)와 연격 이펙트(v3) 타이밍 — 아트 JSON 값 */
const body = [45, 45, 50, 50, 30, 30, 55, 55, 70, 70, 65, 65];
const fx: SheetJson = {
  image: '',
  action: 'fx',
  frameWidth: 512,
  frameHeight: 512,
  frames: 6,
  directions: ['down'],
  fps: 10,
  frameDurationsMs: [40, 60, 70, 80, 100, 120],
  loop: false,
  pivot: { x: 256, y: 296 },
  impactFrame: 1,
  spawn: 'attack_frame3',
};

describe('55라운드 Q14 ①③ 휘두름 이펙트 타이밍', () => {
  it('정지 프레임: holdFrame → impactFrame', () => {
    expect(fxHoldFrame(fx)).toBe(1);
    expect(fxHoldFrame({ ...fx, holdFrame: 0 })).toBe(0);
    expect(fxHoldFrame({ ...fx, holdFrame: 99 })).toBe(5);
  });

  it('구간별 맞춤 재생에서도 이펙트 판정 프레임 = 몸 판정 프레임 시작 (구 선형 배속 방식은 어긋남)', () => {
    // 몸: 판정 프레임 4 를 hitAtMs 320 에, 전체 900 에 맞춤 (51라운드 Q3 두 구간 맞춤)
    const keyed = keyedDurations(body, 4, 320, 900)!;
    const hitAt = startsOf(keyed)[4];
    expect(hitAt).toBeCloseTo(320);
    const lead = frameStarts(fx)[fxHoldFrame(fx)];
    const delay = swingFxDelayMs(hitAt, lead);
    // 이펙트 f1(판정 백열) 시작 = 몸 판정 시작
    expect(delay + lead).toBeCloseTo(hitAt);
    // 구 방식: fxSpawnAtMs(150) × 선형 배속(900/630) = 214 → 판정 백열이 몸보다 ~66ms 먼저
    const old = 150 * (900 / 630);
    expect(hitAt - (old + lead)).toBeGreaterThan(50);
  });

  it('몸이 이펙트 예비 프레임보다 먼저 치면 즉시', () => {
    expect(swingFxDelayMs(20, 40)).toBe(0);
    expect(swingFxDelayMs(90, 40)).toBe(50);
  });
});
