import Phaser from 'phaser';
import type { UiNodeState, UiNodeType } from '../contract/ui';
import { GlowText } from './glow';
import { ICON, KIT, accentHex } from './kit';
import { routeText, type RouteTextKey } from './text';
import { GRAY, SEPIA, hexToNum } from './theme';

/**
 * 노드 지도 그리기 조각 (48~50라운드 RouteMap 에서 분리, 60라운드 정리). 노드 종류·상태 이름, 키트 글리프 폴백,
 * 픽셀 마름모·고리, 주인공 실루엣. 노드 지도(RouteMap)·HUD 노드 띠(RouteStrip)가 같이 쓴다.
 */

/** 노드 종류 이름 (임시 문구, text.ts ROUTE_TEXT). 상점은 스냅샷 `names.shop` 이 있으면 그 이름 */
const TYPE_KEY: Record<UiNodeType, RouteTextKey> = {
  journey: 'typeJourney',
  battle: 'typeBattle',
  shop: 'typeShop',
  rest: 'typeRest',
  event: 'typeEvent',
  boss: 'typeBoss',
};
export function nodeTypeName(t: UiNodeType, shopName?: string): string {
  if (t === 'shop' && shopName) return shopName;
  return routeText(TYPE_KEY[t]);
}
const STATE_KEY: Record<UiNodeState, RouteTextKey> = {
  current: 'stateCurrent',
  available: 'stateAvailable',
  cleared: 'stateCleared',
  passed: 'statePassed',
  locked: 'stateLocked',
};

/**
 * 아이콘 시트가 없을 때의 글리프 (키트 icons 재사용): 여정 = 시작 방, 전투 = 시련, 쉼터 = 휴식, 본영 = 보스 (8×8 → 2배),
 * 상점 = 전표 아이콘 16×16, 이벤트 = '?' 글자.
 */
const GLYPH: Record<UiNodeType, { frame: string; scale: 1 | 2 } | null> = {
  journey: { frame: ICON.miniStart, scale: 2 },
  battle: { frame: ICON.miniTrial, scale: 2 },
  shop: { frame: ICON.gold, scale: 1 },
  rest: { frame: ICON.miniRest, scale: 2 },
  event: null,
  boss: { frame: ICON.miniBoss, scale: 2 },
};

/** 글리프 16×16 (또는 '?') 하나를 (0,0) 중심으로 만든다 */
export function makeGlyph(scene: Phaser.Scene, type: UiNodeType, stageIndex: number): Phaser.GameObjects.GameObject {
  const gl = GLYPH[type];
  if (gl) {
    return scene.add.image(-8, -8, KIT.icons, gl.frame).setOrigin(0, 0).setScale(gl.scale);
  }
  const q = new GlowText(scene, 0, 0, '?', 'ink_body', { stageIndex });
  q.setPosition(-Math.round(q.displayWidth / 2), -Math.round(q.displayHeight / 2));
  return q;
}

/** 계단식 픽셀 마름모 (반대각선 r, 중심 0,0) 채우기 */
export function pixelDiamond(
  g: Phaser.GameObjects.Graphics,
  r: number,
  color: number,
  alpha = 1,
  cx = 0,
  cy = 0,
): void {
  g.fillStyle(color, alpha);
  for (let dy = -r; dy <= r; dy++) {
    const w = r - Math.abs(dy);
    g.fillRect(cx - w, cy + dy, w * 2 + 1, 1);
  }
}

/** 마름모 테두리 (두께 t) */
export function diamondRing(
  g: Phaser.GameObjects.Graphics,
  r: number,
  t: number,
  color: number,
  alpha = 1,
  cx = 0,
  cy = 0,
): void {
  g.fillStyle(color, alpha);
  for (let dy = -r; dy <= r; dy++) {
    const w = r - Math.abs(dy);
    const inner = r - t - Math.abs(dy);
    if (inner < 0) {
      g.fillRect(cx - w, cy + dy, w * 2 + 1, 1);
      continue;
    }
    const seg = w - inner;
    g.fillRect(cx - w, cy + dy, seg, 1);
    g.fillRect(cx + inner + 1, cy + dy, seg, 1);
  }
}

/** 주인공 표시 (8×11 칸, 칸 = 2px). 1 = 몸 */
const FIGURE = [
  '..1111..',
  '..1111..',
  '..1111..',
  '...11...',
  '.111111.',
  '1.1111.1',
  '1.1111.1',
  '..1111..',
  '..1..1..',
  '..1..1..',
  '.11..11.',
];
export const FIG_UNIT = 2;
export const FIGURE_W = FIGURE[0].length * FIG_UNIT;
export const FIGURE_H = FIGURE.length * FIG_UNIT;

/** 주인공 실루엣: 그늘(S2) → 할로(층 강조 20 α0.5) → 몸(G14). 발광 글자와 같은 순서. 왼쪽 위 (0,0) */
export function drawFigure(g: Phaser.GameObjects.Graphics, scene: Phaser.Scene, stageIndex: number): void {
  const cells: [number, number][] = [];
  FIGURE.forEach((row, y) => [...row].forEach((c, x) => c === '1' && cells.push([x * FIG_UNIT, y * FIG_UNIT])));
  const pass = (color: number, alpha: number, offs: [number, number][]) => {
    g.fillStyle(color, alpha);
    for (const [ox, oy] of offs) for (const [x, y] of cells) g.fillRect(x + ox, y + oy, FIG_UNIT, FIG_UNIT);
  };
  pass(hexToNum(SEPIA[2]), 1, [
    [-2, 0],
    [2, 0],
    [0, -2],
    [0, 2],
  ]);
  pass(hexToNum(accentHex(scene, stageIndex, 20)), 0.5, [
    [-1, 0],
    [1, 0],
    [0, -1],
    [0, 1],
  ]);
  pass(hexToNum(GRAY[14]), 1, [[0, 0]]);
}

/** 노드 상태 이름 (임시 문구, text.ts ROUTE_TEXT) */
export function nodeStateName(s: UiNodeState): string {
  return routeText(STATE_KEY[s]);
}
