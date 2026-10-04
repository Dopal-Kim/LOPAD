import { describe, expect, it } from 'vitest';
import { WEAPONS } from '../data';
import {
  arcHit,
  comboRadius,
  hitShapeBounds,
  resolveHitShape,
  ringHit,
  shapeCenterPoint,
  shapeHit,
  shapeOutline,
  type HitShape,
} from './hitShapes';

/** 각도 deg(화면 시계 +), 거리 d 의 점 */
const at = (deg: number, d: number, r = 1) => ({
  x: Math.cos((deg * Math.PI) / 180) * d,
  y: Math.sin((deg * Math.PI) / 180) * d,
  r,
});

describe('55라운드 §17 판정 모양 — arc (내반경·비대칭)', () => {
  it('내반경: 몸 가까이(초승달 안쪽)는 빗나가고 띠 안은 맞는다', () => {
    expect(arcHit(0, 0, 1, 0, 40, 150, at(0, 5, 1), 12)).toBe(false);
    expect(arcHit(0, 0, 1, 0, 40, 150, at(0, 20, 1), 12)).toBe(true);
    expect(arcHit(0, 0, 1, 0, 40, 150, at(0, 11, 2), 12)).toBe(true); // 걸침
    // 내반경 0 은 48라운드 규칙 그대로 (원점과 겹치면 맞음)
    expect(arcHit(0, 0, 1, 0, 40, 150, at(0, 1, 2))).toBe(true);
  });

  it('비대칭 대각 호 (칼 1타 +70→−40): 아래 60° 는 맞고 위 60° 는 빗나감, 왼쪽 조준은 좌우 반전', () => {
    const s = resolveHitShape({ kind: 'arc', fromDeg: 70, toDeg: -40 }, 33);
    expect(s).toMatchObject({ kind: 'arc', radius: 33, arcDeg: 110, centerDeg: 15, fromDeg: 70, toDeg: -40, inner: 0 });
    expect(shapeHit(0, 0, 1, 0, s, at(60, 25), 'right')).toBe(true);
    expect(shapeHit(0, 0, 1, 0, s, at(-60, 25), 'right')).toBe(false);
    // 왼쪽 조준(180°): 반전된 호 = 180−70=110°(아래 왼쪽) ~ 180+40=220°(위 왼쪽)
    expect(shapeHit(0, 0, -1, 0, s, at(120, 25), 'left')).toBe(true);
    expect(shapeHit(0, 0, -1, 0, s, at(240, 25), 'left')).toBe(false);
  });

  it('왼쪽 조준 회전(leftTransform rotate = facing right 로 넘김): 오른쪽 조준의 180° 회전과 같다', () => {
    const s = resolveHitShape({ kind: 'arc', fromDeg: 70, toDeg: -40 }, 33);
    // 오른쪽 조준 +60°(아래) 가 맞으면, 회전한 왼쪽 조준에선 180+60=240°(위 왼쪽) 가 맞는다 (반전이면 120°)
    expect(shapeHit(0, 0, -1, 0, s, at(240, 25), 'right')).toBe(true);
    expect(shapeHit(0, 0, -1, 0, s, at(120, 25), 'right')).toBe(false);
  });

  it('칼 3타 초승달: 반경 ×1.25 · 내반경 0.45 (아트 그림 값)', () => {
    const s = resolveHitShape({ kind: 'arc', fromDeg: 75, toDeg: -75, innerRatio: 0.45, radiusMult: 1.25 }, 33);
    if (s.kind !== 'arc') throw new Error('arc');
    expect(s.radius).toBeCloseTo(41.25);
    expect(s.inner).toBeCloseTo(18.5625);
    expect(s.arcDeg).toBe(150);
    expect(shapeHit(0, 0, 1, 0, s, at(70, 30), 'right')).toBe(true);
    expect(shapeHit(0, 0, 1, 0, s, at(0, 4, 1), 'right')).toBe(false);
  });
});

describe('55라운드 §17 판정 모양 — wedge · rect · ring', () => {
  const R = 51;
  const wedge = resolveHitShape(
    { kind: 'wedge', widthDeg: 40, lengthMult: 1.3, impactCircle: { radiusRatio: 0.35 } },
    R,
  ) as Extract<HitShape, { kind: 'wedge' }>;

  it('쐐기: 폭 40° 안·길이 1.3R 까지, 옆은 빗나감, 끝점 충격원(0.35R)은 쐐기 밖 옆도 맞음', () => {
    expect(wedge.length).toBeCloseTo(66.3);
    expect(wedge.impact!.radius).toBeCloseTo(17.85);
    expect(wedge.impact!.dist).toBeCloseTo(66.3);
    expect(shapeHit(0, 0, 1, 0, wedge, at(10, 40), 'right')).toBe(true);
    expect(shapeHit(0, 0, 1, 0, wedge, at(45, 30), 'right')).toBe(false);
    // 끝점 옆 (쐐기 폭 밖이지만 충격원 안)
    expect(shapeHit(0, 0, 1, 0, wedge, { x: 66, y: 15, r: 2 }, 'right')).toBe(true);
    expect(shapeHit(0, 0, 1, 0, wedge, { x: 66, y: 30, r: 2 }, 'right')).toBe(false);
    expect(shapeCenterPoint(0, 0, 0, 1, wedge, 'down')).toMatchObject({
      x: expect.closeTo(0),
      y: expect.closeTo(66.3),
    });
  });

  it('차지 단계 길이 배율·관성 최대 충격원 배율 (shapeScale)', () => {
    const s = resolveHitShape(
      { kind: 'wedge', widthDeg: 40, lengthMult: 1.3, impactCircle: { radiusRatio: 0.35 } },
      R,
      { lengthMult: 1.8, impactMult: 1.4 },
    ) as Extract<HitShape, { kind: 'wedge' }>;
    expect(s.length).toBeCloseTo(91.8);
    expect(s.impact!.dist).toBeCloseTo(91.8);
    expect(s.impact!.radius).toBeCloseTo(17.85 * 1.4);
  });

  it('rect = 찌르기 (R 배율), ring = 고리 (안쪽 빈 곳은 빗나감)', () => {
    const r = resolveHitShape({ kind: 'rect', lengthMult: 1, widthMult: 0.25, fromMult: 0.1 }, 40);
    expect(r).toMatchObject({ kind: 'thrust', length: 40, width: 10, fromPx: 4, angleDeg: 0 });
    const ring = resolveHitShape({ kind: 'ring', radiusMult: 1, innerRatio: 0.45, atMult: 2 }, 40);
    expect(ring).toMatchObject({ kind: 'ring', radius: 40, dist: 80 });
    expect(shapeHit(0, 0, 1, 0, ring, { x: 80 + 30, y: 0, r: 2 }, 'right')).toBe(true);
    expect(shapeHit(0, 0, 1, 0, ring, { x: 80, y: 0, r: 2 }, 'right')).toBe(false); // 고리 안 빈 곳
    expect(ringHit(0, 0, 10, 5, { x: 0, y: 0, r: 6 })).toBe(true); // 안 반지름까지 걸침
  });

  it('외접 사각형은 모든 윤곽 점을 감싼다 (쐐기 + 충격원)', () => {
    const b = hitShapeBounds(0, 0, 1, 0, wedge, 'right');
    for (const poly of shapeOutline(0, 0, 1, 0, wedge, 'right'))
      for (const p of poly) {
        expect(p.x).toBeGreaterThanOrEqual(b.x - 1e-6);
        expect(p.x).toBeLessThanOrEqual(b.x + b.w + 1e-6);
        expect(p.y).toBeGreaterThanOrEqual(b.y - 1e-6);
        expect(p.y).toBeLessThanOrEqual(b.y + b.h + 1e-6);
      }
    expect(b.x + b.w).toBeCloseTo(66.3 + 17.85, 0);
  });
});

describe('55라운드 데이터 (계약 §17 수치)', () => {
  it('칼 K-A: 1타 +70→−40 · 2타 −70→+40 · 3타 +75→−75 ×1.25 + 150ms 잔상 50%', () => {
    const c = WEAPONS.katana.combo!;
    const R = comboRadius(c, WEAPONS.katana.hitbox);
    expect(R).toBe(33);
    expect(c.hits.map((h) => h.hitShape)).toMatchObject([
      { kind: 'arc', fromDeg: 70, toDeg: -40 },
      { kind: 'arc', fromDeg: -70, toDeg: 40 },
      { kind: 'arc', fromDeg: 75, toDeg: -75, radiusMult: 1.25 },
    ]);
    expect(c.hits[2].heavy).toBe(true);
    expect(c.hits[2].followUps).toMatchObject([{ id: 'echo', delayMs: 150, damageMult: 0.5 }]);
    expect(c.hits[2].hitShape).toMatchObject({ innerRatio: 0.45 });
    expect(c.leftTransform).toBe('rotate');
    // 내딛기 1·2타 4~6 · 3타 14~16
    for (const i of [0, 1]) expect(c.hits[i].step!.px).toBeGreaterThanOrEqual(4);
    for (const i of [0, 1]) expect(c.hits[i].step!.px).toBeLessThanOrEqual(6);
    expect(c.hits[2].step!.px).toBeGreaterThanOrEqual(14);
    expect(c.hits[2].step!.px).toBeLessThanOrEqual(16);
  });

  it('대검 G-C: H1 시계 150° → V 쐐기 40° ×1.3 + 충격원 0.35R → H2 반시계 → V, 순환·관성·차지', () => {
    const c = WEAPONS.greatsword.combo!;
    expect(comboRadius(c, WEAPONS.greatsword.hitbox)).toBe(51);
    expect(c.loop).toBe(true);
    const [h1, v, h2, v2] = c.hits.map((h) => h.hitShape!);
    expect(h1).toMatchObject({ kind: 'arc', fromDeg: -75, toDeg: 75 });
    expect(h2).toMatchObject({ kind: 'arc', fromDeg: 75, toDeg: -75 });
    for (const s of [v, v2])
      expect(s).toMatchObject({ kind: 'wedge', widthDeg: 40, lengthMult: 1.3, impactCircle: { radiusRatio: 0.35 } });
    expect(c.hits.map((h) => Boolean(h.heavy))).toEqual([false, true, false, true]);
    expect(c.hits[1].step!.px).toBe(12);
    expect(c.momentum).toMatchObject({ perHit: 0.05, max: 0.2, idleResetMs: 1000 });
    expect(c.charge!.stages.map((s) => [s.atMs, s.lengthMult])).toEqual([
      [400, 1.3],
      [800, 1.5],
      [1200, 1.8],
    ]);
    expect(c.charge!.stages[2].followUps![0].hitShape!.kind).toBe('ring');
    expect(c.charge!.moveMult).toBe(0.35);
    expect(c.leftTransform).toBe('rotate');
    expect(c.charge!.stages.map((s) => s.impactMult)).toEqual([1.0, 1.15, 1.3]);
    expect(c.momentum!.maxImpactMult).toBe(1.3);
  });

  it('회귀: 단검(찌르기)·활은 타별 모양 없이 기존 규칙', () => {
    expect(WEAPONS.dagger.combo!.hits.every((h) => h.hitShape === undefined && h.art === undefined)).toBe(true);
    expect(WEAPONS.dagger.combo!.loop).toBeUndefined();
    expect(WEAPONS.bow.combo).toBeUndefined();
  });
});
