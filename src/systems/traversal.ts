/**
 * 비전투 이동 (45라운드 Q2 달리기 · Q3 워프) — Phaser 의존 없는 순수 규칙.
 * - 비전투 판정: 방 상태 머신(RoomDirector)에 'active'(시련·보스 진행 중) 방이 하나도 없으면 비전투
 * - 달리기 배율: 목표(1 또는 speedMult)로 가속·감속 시간에 걸쳐 선형 접근
 * - 워프 대상: 방문했고 클리어된 방(시작 방은 처음부터 클리어, 휴식 방은 진입 시 클리어), 현재 방 제외
 * - 워프 착지점: 방 중앙에서 가까운 순으로, 몸이 들어갈 바닥이고 출구·상점 타일에서 떨어진 타일
 */
import type { SprintParams } from '../data/types';

/** 방 진행 상태 (RoomDirector 와 같은 값) */
export type RoomProgress = 'idle' | 'active' | 'cleared';

/** 워프 거부 사유 (계약 `UiWarpDenyReason` 과 같은 값) */
export type WarpDenyReason = 'combat' | 'busy' | 'unknown-room' | 'not-cleared' | 'current-room';

/** 활성 전투 방(시련·보스 진행 중)이 있으면 전투 중 */
export function isInCombat(progress: ReadonlyMap<string, RoomProgress>): boolean {
  for (const s of progress.values()) if (s === 'active') return true;
  return false;
}

/** 이 방이 워프 목적지 조건(방문·클리어·현재 방 아님)을 만족하는지. 전투·연출 여부는 따로 본다 */
export function isWarpTarget(
  roomId: string,
  visited: ReadonlySet<string>,
  progress: ReadonlyMap<string, RoomProgress>,
  currentRoomId: string,
): boolean {
  return roomId !== currentRoomId && visited.has(roomId) && progress.get(roomId) === 'cleared';
}

/** 워프 가능한 방 id 목록 (방 정의 순서 유지) */
export function warpTargets(
  rooms: readonly { id: string }[],
  visited: ReadonlySet<string>,
  progress: ReadonlyMap<string, RoomProgress>,
  currentRoomId: string,
): string[] {
  return rooms.filter((r) => isWarpTarget(r.id, visited, progress, currentRoomId)).map((r) => r.id);
}

/**
 * 워프 요청 판정. `block` 은 씬 상태에서 온 공통 거부 사유(전투·연출·메뉴 등, 없으면 null).
 * 반환 null 이면 허용
 */
export function warpDenyReason(args: {
  roomId: string;
  block: 'combat' | 'busy' | null;
  rooms: readonly { id: string }[];
  visited: ReadonlySet<string>;
  progress: ReadonlyMap<string, RoomProgress>;
  currentRoomId: string;
}): WarpDenyReason | null {
  if (args.block) return args.block;
  if (!args.rooms.some((r) => r.id === args.roomId)) return 'unknown-room';
  if (args.roomId === args.currentRoomId) return 'current-room';
  if (!isWarpTarget(args.roomId, args.visited, args.progress, args.currentRoomId)) return 'not-cleared';
  return null;
}

/**
 * 달리기 배율 한 프레임 진행: current → target 으로 1 ↔ speedMult 구간을 accelMs(올릴 때)·decelMs(내릴 때)에 걸쳐 선형 이동.
 * 시간이 0 이하면 즉시 목표
 */
export function sprintStep(current: number, target: number, deltaMs: number, p: SprintParams): number {
  if (current === target) return current;
  const span = Math.max(0, p.speedMult - 1);
  const up = target > current;
  const ms = up ? p.accelMs : p.decelMs;
  if (ms <= 0 || span === 0) return target;
  const step = (span * Math.max(0, deltaMs)) / ms;
  return up ? Math.min(target, current + step) : Math.max(target, current - step);
}

/**
 * 워프 착지 타일 (타일 좌표). 방 내부 사각형 안에서 중앙에 가까운 순으로 찾는다.
 * 조건: 반경 `bodyTiles`(체비쇼프) 안이 모두 `isFree`, 반경 `hazardTiles` 안에 `isHazard`(출구·상점) 없음.
 * 못 찾으면 null (호출 쪽이 방 중앙으로 대체)
 */
export function findSafeTile(
  interior: { x: number; y: number; w: number; h: number },
  isFree: (tx: number, ty: number) => boolean,
  isHazard: (tx: number, ty: number) => boolean,
  bodyTiles: number,
  hazardTiles: number,
): { tx: number; ty: number } | null {
  const cx = interior.x + (interior.w - 1) / 2;
  const cy = interior.y + (interior.h - 1) / 2;
  const tiles: { tx: number; ty: number; d: number }[] = [];
  for (let ty = interior.y; ty < interior.y + interior.h; ty++)
    for (let tx = interior.x; tx < interior.x + interior.w; tx++)
      tiles.push({ tx, ty, d: (tx - cx) ** 2 + (ty - cy) ** 2 });
  tiles.sort((a, b) => a.d - b.d || a.ty - b.ty || a.tx - b.tx);
  const around = (tx: number, ty: number, r: number, fn: (x: number, y: number) => boolean): boolean => {
    for (let y = ty - r; y <= ty + r; y++) for (let x = tx - r; x <= tx + r; x++) if (fn(x, y)) return true;
    return false;
  };
  for (const t of tiles) {
    if (around(t.tx, t.ty, bodyTiles, (x, y) => !isFree(x, y))) continue;
    if (around(t.tx, t.ty, hazardTiles, isHazard)) continue;
    return { tx: t.tx, ty: t.ty };
  }
  return null;
}
