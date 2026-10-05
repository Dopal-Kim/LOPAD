/**
 * 61라운드 P4·P9 로드 범위: `data/stages.json` run.loadFloors — 부팅 때 그림을 올릴 층 수 (1층 한정 작업).
 * 2~8층 데이터(stages·bosses·route)는 지우지 않는다. 범위 밖 층에 가면(디버그 `gotoFloor`·다음 층 전환) 층 타일셋은 플레이스홀더,
 * 보스는 1층 보스 시트 별칭(Preloader BOSS_FALLBACK_SHEET)으로 그대로 동작한다.
 */
import stagesJson from '../../data/stages.json';

interface StagesRaw {
  run: { order: string[]; loadFloors?: number };
  stages: Record<string, { boss: string }>;
}

const RAW = stagesJson as unknown as StagesRaw;

/** 로드할 층 수 (없거나 잘못되면 전체) */
export function loadFloorCount(raw: StagesRaw = RAW): number {
  const n = raw.run.loadFloors;
  const all = raw.run.order.length;
  if (typeof n !== 'number' || !Number.isInteger(n) || n < 1) return all;
  return Math.min(all, n);
}

/** 1부터: 이 층의 그림을 부팅 때 올리는가 */
export function floorLoaded(floor: number, raw: StagesRaw = RAW): boolean {
  return floor >= 1 && floor <= loadFloorCount(raw);
}

/** 로드 범위 안 층들의 보스 id */
export function bossIdsInScope(raw: StagesRaw = RAW): string[] {
  const out = new Set<string>();
  for (const id of raw.run.order.slice(0, loadFloorCount(raw))) {
    const b = raw.stages[id]?.boss;
    if (b) out.add(b);
  }
  return [...out];
}
