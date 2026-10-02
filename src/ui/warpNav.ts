/**
 * 워프 지도(45라운드) 키보드 이동 계산. Phaser 없이 순수 함수로 둔다 (단위 테스트용).
 * 좌표는 격자 칸 단위(방 영역 중심). 방향 키 하나로 그 방향에 있는 가장 가까운 후보를 고른다.
 */

export interface NavNode {
  id: string;
  x: number;
  y: number;
}

/** 방향 벡터 (dx, dy 는 -1·0·1, 한 축만) */
export interface NavDir {
  dx: number;
  dy: number;
}

/** 옆으로 벗어난 거리에 주는 가중치. 클수록 정면에 가까운 방을 고른다 */
const SIDE_WEIGHT = 2;

/**
 * `from` 에서 `dir` 쪽으로 가장 가까운 노드 id. 그 방향에 없으면 null.
 * 점수 = 정면 거리 + 옆 거리 × 2. 정면 거리가 0 이하(같은 줄·반대쪽)는 제외.
 */
export function pickNeighbor(from: { x: number; y: number }, dir: NavDir, nodes: NavNode[], excludeId?: string) {
  let best: string | null = null;
  let bestScore = Infinity;
  for (const n of nodes) {
    if (n.id === excludeId) continue;
    const vx = n.x - from.x;
    const vy = n.y - from.y;
    const along = vx * dir.dx + vy * dir.dy;
    if (along <= 0.01) continue;
    const side = Math.abs(vx * dir.dy - vy * dir.dx);
    const score = along + side * SIDE_WEIGHT;
    if (score < bestScore) {
      bestScore = score;
      best = n.id;
    }
  }
  return best;
}

/** `from` 에 가장 가까운 노드 id (처음 고를 방). 없으면 null */
export function nearest(from: { x: number; y: number }, nodes: NavNode[]): string | null {
  let best: string | null = null;
  let bestD = Infinity;
  for (const n of nodes) {
    const d = (n.x - from.x) ** 2 + (n.y - from.y) ** 2;
    if (d < bestD) {
      bestD = d;
      best = n.id;
    }
  }
  return best;
}

/** 키 이름(KeyboardEvent.key) → 방향. 이동 키가 아니면 null */
export function keyToDir(key: string): NavDir | null {
  switch (key) {
    case 'ArrowUp':
    case 'w':
    case 'W':
      return { dx: 0, dy: -1 };
    case 'ArrowDown':
    case 's':
    case 'S':
      return { dx: 0, dy: 1 };
    case 'ArrowLeft':
    case 'a':
    case 'A':
      return { dx: -1, dy: 0 };
    case 'ArrowRight':
    case 'd':
    case 'D':
      return { dx: 1, dy: 0 };
    default:
      return null;
  }
}
