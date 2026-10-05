/**
 * 앞머리가 나아가는 판정 (Phaser 의존 없음) — 58라운드 Q3 차지 균열(CrackLineStrikes). (56라운드 꽂아내리기 충격파에서 시작 — 58 Q11 삭제)
 * fx 시트 메모 `hitShape.frontPxByFrame`(도트, 프레임마다 앞머리 거리)·`activeFrames`·`frameDurationsMs` → 시간에 따른 앞머리
 * 비율(0..1). 앞머리가 지나간 칸만 맞는다. 메모가 없으면 travelMs 동안 선형.
 */
import type { Pt, HitTarget } from './hitShapes';
import { thrustHit } from './hitShapes';
import { frameStarts, type SheetJson } from '../sprites/spriteDefs';

/** 앞머리 시간표: 시각(ms) → 비율 (끝 = 판정 끝) */
export interface WaveTimeline {
  times: number[];
  ratios: number[];
}

/** 시트 메모에서 시간표 (없으면 선형 0 → travelMs) */
export function waveTimeline(def: SheetJson | null | undefined, travelMs: number): WaveTimeline {
  const hs = (def as { hitShape?: unknown } | null | undefined)?.hitShape as
    { frontPxByFrame?: unknown; activeFrames?: unknown; lengthPx?: unknown } | undefined;
  const fronts = Array.isArray(hs?.frontPxByFrame)
    ? (hs!.frontPxByFrame as unknown[]).filter((v) => typeof v === 'number')
    : [];
  const length =
    typeof hs?.lengthPx === 'number' && hs.lengthPx > 0 ? hs.lengthPx : Math.max(0, ...(fronts as number[]));
  if (!def || fronts.length === 0 || length <= 0) return { times: [0, travelMs], ratios: [0, 1] };
  const active = Array.isArray(hs?.activeFrames) ? (hs!.activeFrames as number[]) : fronts.map((_, i) => i);
  const last = Math.min(fronts.length - 1, Math.max(...active));
  const starts = frameStarts(def);
  const times: number[] = [0];
  const ratios: number[] = [0];
  for (let f = 0; f <= last; f++) {
    // 프레임 f 가 끝날 때 앞머리 = fronts[f]
    const end = starts[f + 1] ?? starts[f] + (def.frameDurationsMs?.[f] ?? 40);
    times.push(end);
    ratios.push(Math.min(1, (fronts[f] as number) / length));
  }
  return { times, ratios };
}

/** 경과 ms 의 앞머리 비율 (구간 선형 보간, 끝 뒤 = 마지막) */
export function waveFrontRatio(tl: WaveTimeline, elapsedMs: number): number {
  const { times, ratios } = tl;
  if (elapsedMs <= times[0]) return ratios[0];
  for (let i = 1; i < times.length; i++) {
    if (elapsedMs <= times[i]) {
      const a = times[i - 1];
      const b = times[i];
      const k = b > a ? (elapsedMs - a) / (b - a) : 1;
      return ratios[i - 1] + (ratios[i] - ratios[i - 1]) * k;
    }
  }
  return ratios[ratios.length - 1];
}

/** 판정 끝 시각 (시간표 마지막) */
export function waveEndMs(tl: WaveTimeline): number {
  return tl.times[tl.times.length - 1] ?? 0;
}

/** 앞머리가 지나간 직사각형(시작 = 꽂힌 자리)에 대상이 걸쳤는가 */
export function waveHit(origin: Pt, dir: Pt, frontPx: number, halfWidthPx: number, t: HitTarget): boolean {
  return frontPx > 0 && thrustHit(origin.x, origin.y, dir.x, dir.y, frontPx, halfWidthPx * 2, t);
}

/**
 * 58라운드 Q3 균열 칸 수 (아트 pickRule): min(차지 단계 최대, 찍은 자리 → 커서 거리 / 칸 반올림(최소 1), 벽까지 / 칸 내림).
 * 0 이면 균열 없음 (바로 앞이 벽)
 */
export function crackTiles(maxTiles: number, cursorAlongPx: number, wallPx: number, tilePx: number): number {
  const t = Math.max(1, tilePx);
  const toCursor = Math.max(1, Math.round(cursorAlongPx / t));
  const toWall = Math.floor(wallPx / t + 1e-6);
  return Math.max(0, Math.min(maxTiles, toCursor, toWall));
}
