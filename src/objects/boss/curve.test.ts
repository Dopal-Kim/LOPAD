import { describe, expect, it } from 'vitest';
import { cumulative, curvedDashPath, pointAlong, traceBounces, wobblyLine } from './curve';
import { cellsAlong, linked, rectGap, spreadDelays } from '../../systems/hazards/liquorNet';
import { tiltAt } from '../../systems/boss/tiltMath';
import { rotationCover } from '../../systems/lighting/lightMath';
import { parseBossQuery } from '../../debug/bossQuery';

describe('휘는 돌진 경로 (Q9)', () => {
  it('끝점은 목표 방향 lengthPx, 가운데가 옆으로 휜다 (sign 으로 반대쪽)', () => {
    const a = curvedDashPath({ x: 0, y: 0 }, { x: 100, y: 0 }, 200, 0.3, 1, 20);
    expect(a).toHaveLength(21);
    expect(a[20].x).toBeCloseTo(200);
    expect(a[20].y).toBeCloseTo(0);
    const b = curvedDashPath({ x: 0, y: 0 }, { x: 100, y: 0 }, 200, 0.3, -1, 20);
    expect(Math.sign(a[10].y)).toBe(-Math.sign(b[10].y));
    expect(Math.abs(a[10].y)).toBeCloseTo(30); // 베지어 가운데 = 조절점 편차의 절반
  });
  it('꺾은선 위 거리', () => {
    const pts = [
      { x: 0, y: 0 },
      { x: 10, y: 0 },
      { x: 10, y: 10 },
    ];
    const acc = cumulative(pts);
    expect(acc).toEqual([0, 10, 20]);
    expect(pointAlong(pts, acc, 15)).toEqual({ x: 10, y: 5 });
    expect(pointAlong(pts, acc, 99)).toEqual({ x: 10, y: 10 });
  });
  it('술 뿌리기 물결: 시작점에서 진행 방향으로 lengthPx', () => {
    const w = wobblyLine({ x: 0, y: 0 }, 1, 0, 90, 10, 18);
    expect(w[0].x).toBeCloseTo(0);
    expect(w[0].y).toBeCloseTo(0);
    expect(w[18].x).toBeCloseTo(90);
  });
});

describe('술통 튕김 경로 (Q3)', () => {
  // 100×60 방 (밖 = 막힘)
  const blocked = (x: number, y: number) => x < 0 || x > 100 || y < 0 || y > 60;
  it('벽에 bounces 번 튕기고 다음 벽에서 멈춘다', () => {
    const t = traceBounces({ x: 50, y: 30 }, 1, 0, 2, 10000, 4, blocked);
    expect(t.bounces).toBe(2);
    expect(t.hitWall).toBe(true);
    expect(t.points.length).toBe(4);
    expect(t.points[1].x).toBeGreaterThan(90);
    expect(t.points[2].x).toBeLessThan(10);
  });
  it('대각선: 축별 반사', () => {
    const t = traceBounces({ x: 50, y: 30 }, 1, 1, 1, 10000, 2, blocked);
    expect(t.points[1].y).toBeGreaterThan(50);
    expect(t.points[2].y).toBeLessThan(t.points[1].y);
  });
  it('maxPx 에서 멈춤', () => {
    const t = traceBounces({ x: 10, y: 30 }, 1, 0, 3, 20, 2, blocked);
    expect(t.hitWall).toBe(false);
    expect(t.points[t.points.length - 1].x).toBeCloseTo(30);
  });
});

describe('술 웅덩이 연결망·번짐 (Q3)', () => {
  const cell = (tx: number, ty: number) => ({ x: tx * 16, y: ty * 16, w: 16, h: 16 });
  it('틈 계산·연결', () => {
    expect(rectGap(cell(0, 0), cell(1, 0))).toBe(0);
    expect(rectGap(cell(0, 0), cell(2, 0))).toBe(16);
    expect(linked(cell(0, 0), cell(1, 1), 0)).toBe(true);
    expect(linked(cell(0, 0), cell(2, 0), 4)).toBe(false);
  });
  it('불은 연결된 칸을 따라 칸마다 늦게 (끊긴 칸은 안 탄다)', () => {
    const cells = [cell(0, 0), cell(1, 0), cell(2, 0), cell(5, 0)];
    const d = spreadDelays(cells, 0, 2, 120);
    expect([...d.entries()]).toEqual([
      [0, 0],
      [1, 120],
      [2, 240],
    ]);
  });
  it('꺾은선 → 칸 (중복 없이)', () => {
    const c = cellsAlong(
      [
        { x: 8, y: 8 },
        { x: 56, y: 8 },
      ],
      8,
      16,
    );
    expect(c).toEqual([
      { tx: 0, ty: 0 },
      { tx: 1, ty: 0 },
      { tx: 2, ty: 0 },
      { tx: 3, ty: 0 },
    ]);
  });
});

describe('세상이 돈다 (Q7)', () => {
  const P = { durationMs: 6000, tiltDeg: 8, periodMs: 2000, rampMs: 600 };
  it('±8° 안, 시작·끝은 0, 주기 2초', () => {
    expect(tiltAt(0, P)).toBe(0);
    expect(tiltAt(6000, P)).toBe(0);
    expect(tiltAt(1500, P)).toBeCloseTo(-8);
    for (let t = 0; t < 6000; t += 37) expect(Math.abs(tiltAt(t, P))).toBeLessThanOrEqual(8 + 1e-9);
  });
  it('라이트맵 덮개 배율: 0° = 1, 8° 에서 16:9 화면은 약 1.24', () => {
    expect(rotationCover(960, 540, 0)).toBe(1);
    expect(rotationCover(960, 540, (8 * Math.PI) / 180)).toBeCloseTo(1.237, 2);
  });
});

describe('보스 확인 주소 옵션', () => {
  it('?boss · ?bossPhase · ?bossPattern', () => {
    expect(parseBossQuery('')).toEqual({ jump: false, phase: null, patterns: null });
    expect(parseBossQuery('?boss')).toEqual({ jump: true, phase: null, patterns: null });
    expect(parseBossQuery('?bossPhase=3&bossPattern=drink,nope,spin')).toEqual({
      jump: true,
      phase: 3,
      patterns: ['drink', 'spin'],
    });
  });
});

describe('보스 판정 크기 = 그림 크기 비례 (Q13~Q16)', () => {
  it('시트가 있으면 프레임 월드 크기 × 비율, 없으면 data size', async () => {
    const { bossBodySize } = await import('./bodySize');
    expect(bossBodySize([40, 40], { w: 1, h: 0.6 }, { frameWidth: 128, frameHeight: 192, scale: 0.25 })).toEqual([
      32, 29,
    ]);
    expect(bossBodySize([40, 40], { w: 1, h: 0.6 }, { frameWidth: 192, frameHeight: 240, scale: 0.25 })).toEqual([
      48, 36,
    ]);
    expect(bossBodySize([40, 40], undefined, { frameWidth: 192, frameHeight: 240, scale: 0.25 })).toEqual([40, 40]);
    expect(bossBodySize([40, 40], { w: 1, h: 0.6 }, null)).toEqual([40, 40]);
  });
});
