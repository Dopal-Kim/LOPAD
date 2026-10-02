/**
 * 비전투 이동 (45라운드 Q2 달리기 · Q3 워프) — Phaser 의존 없는 순수 규칙.
 * - 비전투 판정: 방 상태 머신(RoomDirector)에 'active'(시련·보스 진행 중) 방이 하나도 없으면 비전투
 * - 달리기 배율: 목표(1 또는 speedMult)로 가속·감속 시간에 걸쳐 선형 접근
 * - 워프(45라운드 Q3)는 48라운드에 비활성(계약 §10.2) — 실행 경로는 50라운드에 지웠고 거부 사유 형식만 남는다
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
