import type Phaser from 'phaser';

/**
 * 62 루프 3 UI H (점검 P1-N6): 기억 장·소품 고르기의 그림 자리.
 *  - 아트가 만드는 중인 기억 아이콘(`ui_relics/memory_*` — 이름은 아트 보고 뒤 확정)은 시스템이 `iconKey` 로 주면 그것을 쓰고,
 *    주지 않아도 여기 표(`MEMORY_ICON_KEYS`, 기억 id → 텍스처 키)에 적힌 키가 로드돼 있으면 쓴다. 이름이 정해지면 표만 고친다.
 *  - '빈손'(소품 없음)은 검은 네모 대신 흐린 종이 위 빈 손바닥 선 그림 (UI 도형, `drawEmptyHand`).
 */
export const MEMORY_ICON_KEYS: Readonly<Record<string, string>> = {
  // 예: 'shop:ink': 'ui_relics/memory_ink' — 아트 키 확정 뒤 채운다
};
/** '빈손' 그림 키 (아트가 만들면 — 없으면 선 그림) */
export const EMPTY_HAND_ICON_KEY: string | null = null;

/** 그림 키 고르기: 시스템 iconKey → 표의 키 → null. `has` = 텍스처가 로드돼 있는가 */
export function memoryIconKey(
  e: { id?: string; iconKey?: string | null } | null | undefined,
  has: (key: string) => boolean,
): string | null {
  if (e?.iconKey && has(e.iconKey)) return e.iconKey;
  const k = e?.id ? MEMORY_ICON_KEYS[e.id] : undefined;
  return k && has(k) ? k : null;
}

/**
 * 빈 손바닥 실루엣 (칸 21×24, 손가락 넷 + 엄지). 윤곽만 그린다 — `handOutline` 이 칸 목록을 만든다 (순수).
 */
function handFilled(x: number, y: number): boolean {
  // 손바닥 (아래는 둥글게)
  if (y >= 10 && y <= 20 && x >= 5 && x <= 18) return true;
  if (y >= 21 && y <= 23 && x >= 7 && x <= 16) return true;
  // 손가락 (검지·중지·약지·새끼 — 사이 한 칸)
  const fingers: [number, number, number][] = [
    [5, 7, 3],
    [9, 11, 1],
    [13, 15, 2],
    [17, 18, 5],
  ];
  for (const [a, b, top] of fingers) if (x >= a && x <= b && y >= top && y <= 10) return true;
  // 엄지 (왼쪽 위로 비스듬히)
  const thumb: Record<number, [number, number]> = {
    8: [1, 2],
    9: [1, 3],
    10: [1, 4],
    11: [2, 4],
    12: [2, 4],
    13: [3, 4],
    14: [4, 4],
  };
  const t = thumb[y];
  return Boolean(t && x >= t[0] && x <= t[1]);
}

export const HAND_W = 21;
export const HAND_H = 24;

/** 윤곽 칸 (채운 칸 중 상하좌우 이웃이 비어 있는 것) */
export function handOutline(): [number, number][] {
  const out: [number, number][] = [];
  for (let y = 0; y < HAND_H; y++)
    for (let x = 0; x < HAND_W; x++) {
      if (!handFilled(x, y)) continue;
      const edge = !handFilled(x - 1, y) || !handFilled(x + 1, y) || !handFilled(x, y - 1) || !handFilled(x, y + 1);
      if (edge) out.push([x, y]);
    }
  return out;
}

let outlineCache: [number, number][] | null = null;

/** 흐린 종이(size 정사각) 위 가운데에 빈 손바닥 선 그림. (x0, y0) = 칸 왼쪽 위 */
export function drawEmptyHand(
  g: Phaser.GameObjects.Graphics,
  x0: number,
  y0: number,
  size: number,
  paper: number,
  ink: number,
): void {
  g.fillStyle(paper, 1).fillRect(x0, y0, size, size);
  const cell = Math.max(1, Math.floor(size / 32));
  const ox = Math.round(x0 + size / 2 - (HAND_W * cell) / 2);
  const oy = Math.round(y0 + size / 2 - (HAND_H * cell) / 2);
  outlineCache ??= handOutline();
  g.fillStyle(ink, 1);
  for (const [x, y] of outlineCache) g.fillRect(ox + x * cell, oy + y * cell, cell, cell);
}
