import type { LayoutParams } from '../../data/types';
import { Rng, hashSeed } from '../rng';
import { planCells } from './layout';
import { rasterize } from './tiles';
import type { FloorLayout } from './types';

export * from './types';
export * from './arena';

const MAX_ATTEMPTS = 100;

/** 시드와 레이아웃 파라미터로 1층을 생성한다. 같은 입력이면 같은 결과. */
export function generateFloor(seed: number | string, P: LayoutParams): FloorLayout {
  const base = hashSeed(seed);
  for (let attempt = 0; attempt < MAX_ATTEMPTS; attempt++) {
    const rng = new Rng((base + attempt * 7919) >>> 0);
    const plan = planCells(rng, P);
    if (!plan) continue;
    try {
      return rasterize(rng, P, plan, base);
    } catch {
      continue;
    }
  }
  throw new Error(`[mapgen] ${MAX_ATTEMPTS}번 시도 후에도 층을 생성하지 못함 (seed=${String(seed)})`);
}
