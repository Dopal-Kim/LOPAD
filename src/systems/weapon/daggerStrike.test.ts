/**
 * 61 단계 4 (도영 님 피드백 '단검 공격 판정'): 단검 연격 1~3 의 그림(fx/v3/dagger_combo1~3·accel2·3)과 판정 기하·시각을 고정한다.
 * - 판정 길이·폭 = 아트 thrust(도트 × pixelScale/2) × 주인공 판정 배율, 가속 시트는 그림이 길어진 만큼(ACCEL_REACH_MULTS)
 * - 커서로 적의 그림 몸통을 겨눠도 맞는다 (판정 원점에서 커서로 + 몸통 판정)
 * - 판정 시각 = 이펙트 판정 프레임(impactFrame) 시작 (가속으로 타가 짧아져도)
 * 아트 JSON 은 승인 대장 #8 범위 읽기 (없으면 건너뜀).
 */
import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { WEAPON_FX } from '../../core/Constants';
import { WEAPONS } from '../../data';
import { readSheetJson } from '../sprites/sheetAtlas';
import {
  artScale,
  frameStarts,
  sheetToWorldUnits,
  swingFxDelayMs,
  v3HitLift,
  type SheetJson,
} from '../sprites/spriteDefs';
import { comboShape, shapeHit, shapeHitBody, type HitShape, type HitTarget } from './hitShapes';
import { PLAYER_HIT_ORIGIN_UP_PX, PLAYER_HIT_SCALE } from './playerScale';

const ROOT = resolve(__dirname, '../../../assets/sprites');
const read = (path: string): SheetJson | null => {
  const f = `${ROOT}/${path}.json`;
  return existsSync(f) ? (readSheetJson(JSON.parse(readFileSync(f, 'utf8')))?.json ?? null) : null;
};
const present = existsSync(`${ROOT}/fx/v3/dagger_combo1.json`);

const dagger = WEAPONS.dagger!;
const combo = dagger.combo!;
/** 아트 메모 → 판정 모양 (SwingFx.shape 와 같은 길 — 메모가 있으면 타 크기 배율은 빼고 판정 배율만) */
const shapeOf = (n: number, reach = 1): HitShape => {
  const memo = sheetToWorldUnits(read(`fx/v3/dagger_combo${n}`)!);
  const s = comboShape(combo, PLAYER_HIT_SCALE, memo);
  return s.kind === 'thrust' ? { ...s, length: s.length * reach } : s;
};
/** 징집병(dummy) — 바디 16×16, 그림 몸통 = 피벗 높이 절반 */
const ENEMY = { body: 16 };
const enemyLift = () => v3HitLift(read('enemies/v3/dummy_idle')!, ENEMY.body);
/** 적 발(fx, fy) → 바디 원 (바디 아래 끝 = 발) */
const enemyAt = (fx: number, fy: number): HitTarget => ({ x: fx, y: fy - ENEMY.body / 2, r: ENEMY.body / 2 });
const unit = (x: number, y: number) => {
  const l = Math.hypot(x, y) || 1;
  return { x: x / l, y: y / l };
};

describe.skipIf(!present)('61 단계 4 단검 연격 — 그림과 판정', () => {
  it('판정 길이·폭 = 아트 thrust (1·2타 36·8, 3타 42·10 월드 × 판정 배율 1.25), 시작점 4', () => {
    for (const [n, len, w] of [
      [1, 36, 8],
      [2, 36, 8],
      [3, 42, 10],
    ] as const) {
      const s = shapeOf(n);
      expect(s.kind).toBe('thrust');
      if (s.kind !== 'thrust') continue;
      expect(s.length).toBeCloseTo(len * PLAYER_HIT_SCALE, 5);
      expect(s.width).toBeCloseTo(w * PLAYER_HIT_SCALE, 5);
      expect(s.fromPx).toBeCloseTo(4 * PLAYER_HIT_SCALE, 5);
    }
  });

  it('가속 시트(2·3)의 그림 길이(visualLengthPx − 창끝 12 도트) = 기본 판정 끝 × ACCEL_REACH_MULTS', () => {
    for (const n of [1, 2, 3]) {
      const base = read(`fx/v3/dagger_combo${n}`)!;
      const end = base.thrust!.lengthPx + (base.thrust!.fromPx ?? 0);
      for (const k of [2, 3]) {
        const a = read(`fx/v3/dagger_combo${n}_accel${k}`)!;
        const drawn = (a as { visualLengthPx?: number }).visualLengthPx! - 12;
        expect(Math.abs(end * WEAPON_FX.ACCEL_REACH_MULTS[k - 2]! - drawn), `${n}/${k}`).toBeLessThanOrEqual(2);
        // 판정 모양은 시트마다 같다 (그림만 길어짐 — 시스템이 배율로 늘린다)
        expect(a.thrust).toEqual(base.thrust);
      }
    }
  });

  it('판정 원점 기준으로 같은 배율(도트 × 0.25 × 1.25)이라 그림 끝과 판정 끝이 맞는다 (가속 3단 포함)', () => {
    const base = read('fx/v3/dagger_combo1')!;
    const dot = artScale(base) * PLAYER_HIT_SCALE;
    for (const [reach, vis] of [
      [1, 172],
      [WEAPON_FX.ACCEL_REACH_MULTS[0]!, 188],
      [WEAPON_FX.ACCEL_REACH_MULTS[1]!, 204],
    ] as const) {
      const s = shapeOf(1, reach);
      if (s.kind !== 'thrust') throw new Error('thrust');
      // 판정 끝(시작점 + 길이)은 그림 창끝 − 12 도트 안팎 (창끝 렌즈는 판정 끝 + 12 도트로 그려짐)
      const hitEnd = s.fromPx + s.length;
      expect(Math.abs((vis - 12) * dot - hitEnd)).toBeLessThan(1.5 * dot * 4);
    }
  });

  it('커서로 적 그림 몸통을 겨눠도 맞는다 — 가까이·옆·대각선·위아래 (전: 발에서 잰 방향 + 발밑 바디만 → 헛침)', () => {
    const lift = enemyLift();
    expect(lift).toBeGreaterThan(8);
    const up = PLAYER_HIT_ORIGIN_UP_PX;
    let beforeMiss = 0;
    for (const n of [1, 2, 3])
      for (const dist of [8, 20, 36])
        for (const deg of [0, 45, 90, -45, -90, 135, 180]) {
          const a = (deg * Math.PI) / 180;
          // 주인공 발 (0,0), 적 발 = 거리 dist 방향 deg
          const fx = Math.cos(a) * dist;
          const fy = Math.sin(a) * dist;
          const t = enemyAt(fx, fy);
          // 커서 = 적 그림 몸통 중심 (발 위 피벗 높이 절반)
          const aim = { x: fx, y: fy - (lift + ENEMY.body / 2) };
          const s = shapeOf(n);
          const facing =
            Math.abs(aim.x) >= Math.abs(aim.y + up) ? (aim.x < 0 ? 'left' : 'right') : aim.y + up < 0 ? 'up' : 'down';
          const d = unit(aim.x, aim.y + up);
          expect(shapeHitBody(0, -up, d.x, d.y, s, t, lift, facing), `${n} ${dist} ${deg}`).toBe(true);
          const old = unit(aim.x, aim.y);
          if (!shapeHit(0, -up, old.x, old.y, s, t, facing)) beforeMiss += 1;
        }
    // 같은 표에서 예전 규칙은 여러 칸을 헛쳤다 (헤드리스 허수아비 실측과 같은 경향 — CHANGELOG 61 단계 4)
    expect(beforeMiss).toBeGreaterThan(10);
  });

  it('여러 적: 찌르기 축 위 앞뒤 두 적이 모두 맞는다 · 등 뒤 적은 안 맞는다', () => {
    const lift = enemyLift();
    const up = PLAYER_HIT_ORIGIN_UP_PX;
    const s = shapeOf(3);
    const d = unit(1, 0);
    expect(shapeHitBody(0, -up, d.x, d.y, s, enemyAt(14, 0), lift, 'right')).toBe(true);
    expect(shapeHitBody(0, -up, d.x, d.y, s, enemyAt(40, 0), lift, 'right')).toBe(true);
    expect(shapeHitBody(0, -up, d.x, d.y, s, enemyAt(-24, 0), lift, 'right')).toBe(false);
  });

  it('판정 시각 = 이펙트 impactFrame 시작 (몸 시트 판정 프레임을 타 길이에 맞춘 시각) — 가속 ×1.25 까지 한 프레임(16ms) 안', () => {
    for (const n of [1, 2, 3]) {
      const body = read(`player/v3/player_dagger_combo${n}`)!;
      const fx = read(`fx/v3/dagger_combo${n}`)!;
      const bodyStarts = frameStarts(body);
      const total = bodyStarts[bodyStarts.length - 1]! + (body.frameDurationsMs?.at(-1) ?? 0);
      const lead = frameStarts(fx)[fx.impactFrame as number]!;
      const res = dagger.resource;
      const speeds = res && res.kind === 'heat' ? res.speedMults : [];
      expect(speeds.length).toBeGreaterThan(0);
      for (const speed of [1, ...speeds]) {
        const dur = combo.hits[n - 1]!.durationMs / speed;
        const hitAt = (bodyStarts[body.hitFrames![0]!]! * dur) / total;
        const fxImpactAt = swingFxDelayMs(hitAt, lead) + lead;
        expect(Math.abs(fxImpactAt - hitAt), `${n} ×${speed}`).toBeLessThanOrEqual(16);
      }
    }
  });
});
