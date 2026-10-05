/**
 * 61라운드 P4·P5 '층 노출' (1층판): 데이터 항목의 `floor` 필드 = 그 항목이 처음 켜지는 층(1부터, 없으면 1).
 * 1층에서 끈 것(패시브 14·태그 4·세트 6단계·저주 4·접두어 3·소모품 2·이벤트 4·숨은 노드·지도 정보·성소·'양' 등급)은
 * 데이터를 지우지 않고 `floor: 2` 로 둔다. 층 null = 제한 없음(무기 시험장). Phaser 의존 없음.
 * (그림 로드 범위 `scope.ts loadFloors` 와는 다른 축 — 이것은 '무엇을 내보이나', 저것은 '무엇을 올리나')
 */
import stagesJson from '../../data/stages.json';

export interface FloorGated {
  /** 처음 켜지는 층 (1부터). 없으면 1 */
  floor?: number;
}

/** 지금 층 (1부터). null = 제한 없음 (시험장·검사) */
export type FloorScope = number | null;

/** 이 층에서 켜졌나 */
export function onFloor(item: FloorGated | null | undefined, floor: FloorScope): boolean {
  if (floor === null) return true;
  return (item?.floor ?? 1) <= floor;
}

/** 이 층에서 켜진 것만 */
export function floorItems<T extends FloorGated>(items: readonly T[], floor: FloorScope): T[] {
  return items.filter((it) => onFloor(it, floor));
}

const ORDER: readonly string[] = (stagesJson as unknown as { run: { order: string[] } }).run.order;

/** 층 id(stage1…) → 층 번호 (1부터, 모르면 1) */
export function floorOfStage(stageId: string): number {
  const i = ORDER.indexOf(stageId);
  return i < 0 ? 1 : i + 1;
}

/** 층별 표(`{ "1": v }`)에서 이 층의 값 (없으면 fallback). 층 null 이면 fallback */
export function byFloor<T>(table: Record<string, T> | undefined, floor: FloorScope, fallback: T): T {
  if (floor === null || !table) return fallback;
  return table[String(floor)] ?? fallback;
}
