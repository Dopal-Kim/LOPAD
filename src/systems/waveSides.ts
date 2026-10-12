/**
 * 62 루프 2 시스템 D (P2-10) 웨이브 진입 방향 섞기 (Phaser 의존 없음 — 테스트): 웨이브마다 들어오는 쪽을 바꾼다.
 * 첫 웨이브는 주인공 반대쪽 한 면, 가운데 웨이브는 면(북·남·동·서)·양옆(flank)을 섞고, 마지막 웨이브는 사방(around).
 * 같은 쪽이 두 번 이어지지 않는다. 자리는 방 안 무작위 점 중 그 쪽에 드는 것 (모자라면 사방 — RoomDirector).
 */
import type { UiWaveSide } from '../contract/ui';

export type WaveSide = UiWaveSide;
const FACES: readonly WaveSide[] = ['north', 'east', 'south', 'west'];

/** 주인공이 방 가운데에서 어느 쪽에 있나 → 그 반대 면 */
export function farFace(
  player: { x: number; y: number },
  center: { x: number; y: number },
  halfW: number,
  halfH: number,
): WaveSide {
  const dx = (player.x - center.x) / Math.max(1, halfW);
  const dy = (player.y - center.y) / Math.max(1, halfH);
  if (Math.abs(dx) >= Math.abs(dy)) return dx >= 0 ? 'west' : 'east';
  return dy >= 0 ? 'north' : 'south';
}

/** 웨이브 index(0부터) 의 쪽. seed = 노드 시드 해시 (같은 노드면 같은 순서) */
export function waveSideFor(index: number, total: number, seed: number, first: WaveSide): WaveSide {
  if (total > 1 && index === total - 1) return 'around';
  if (index === 0) return first;
  const pool: WaveSide[] = [...FACES, 'flank'];
  let prev: WaveSide = first;
  let side: WaveSide = first;
  for (let i = 1; i <= index; i++) {
    const cands = pool.filter((s) => s !== prev);
    side = cands[Math.abs(Math.imul(seed ^ (i * 0x9e3779b1), 0x85ebca6b) >>> 0) % cands.length];
    prev = side;
  }
  return side;
}

/** 점 p 가 그 쪽에 드나 (center = 방 가운데, half = 방 반폭·반높이 px, player = 주인공 — flank 는 주인공 좌우) */
export function inSide(
  side: WaveSide,
  p: { x: number; y: number },
  center: { x: number; y: number },
  halfW: number,
  halfH: number,
  player: { x: number; y: number },
): boolean {
  const T = 0.25;
  switch (side) {
    case 'north':
      return p.y < center.y - halfH * T;
    case 'south':
      return p.y > center.y + halfH * T;
    case 'east':
      return p.x > center.x + halfW * T;
    case 'west':
      return p.x < center.x - halfW * T;
    case 'flank':
      return Math.abs(p.x - player.x) > halfW * 0.6 && Math.abs(p.y - player.y) < halfH * 0.7;
    case 'around':
      return true;
  }
}
