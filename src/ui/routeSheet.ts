import Phaser from 'phaser';
import { derivedTexture, ensureImage, mapBgKey, mapBgUrl } from './kit';
import { dottedPoints, trapezoidRows, type Area, type MapPathSpec } from './routeView';
import { MAP3D, MAP_BG_FLOORS, MAP_ILLUST, MAP_PATHS, SEPIA, hexToNum } from './theme';

/**
 * 노드 지도 바닥 (RouteMap 에서 분리, 60라운드 정리): 49라운드 펼친 양피지 / 50라운드 지도 일러스트.
 * `late` 는 늦게 읽힌 그림을 기준 객체 위·아래에 끼우는 RouteMap 의 함수, `alive` 는 지도가 아직 떠 있는지.
 */
export type LateInsert = (
  o: Phaser.GameObjects.GameObject & { setDepth(d: number): unknown },
  anchor: Phaser.GameObjects.GameObject,
  where: 'above' | 'below',
) => void;

/** 양피지 색 (팔레트 세피아 안에서): 바탕·격자 */
const MAP3D_SHEET = { fill: SEPIA[4], grid: SEPIA[3] } as const;

/** 50라운드: 이 층에 지도 그림이 있으면 그 그림 속 길 (없으면 그림 가운데 가로 직선) */
export function illustrationPath(floor: number): MapPathSpec | null {
  if (!MAP_BG_FLOORS.includes(floor)) return null;
  return (
    MAP_PATHS[floor] ?? {
      srcW: 960,
      srcH: 540,
      points: [
        [80, 270],
        [880, 270],
      ],
      rowSpread: 100,
      margin: 34,
      farScale: 0.82,
      tangentSpan: 40,
    }
  );
}

/**
 * 펼친 양피지 (계단식 사다리꼴, 아래가 넓고 위가 좁다 = 멀어짐): 그림자 → 바탕 → 지평선 격자 → 말린 위·아래 가장자리 → 테두리.
 */
export function drawSheet(scene: Phaser.Scene, area: Area, yAt: (d: number) => number): void {
  const cx = area.x + area.w / 2;
  const yTop = area.y + MAP3D.sheetInsetY;
  const yBottom = area.y + area.h - MAP3D.sheetInsetY;
  const wBottom = area.w - MAP3D.sheetInsetX * 2;
  const wTop = Math.round(wBottom * MAP3D.sheetTopRatio);
  const rows = trapezoidRows(cx, yTop, yBottom, wTop, wBottom);
  const g = scene.add.graphics();
  // 그림자 (오른쪽 아래로 어긋남, 허용 알파 0.55)
  g.fillStyle(hexToNum(SEPIA[0]), 0.55);
  for (const r of rows) g.fillRect(r.x + MAP3D.sheetShadow, r.y + MAP3D.sheetShadow, r.w, 1);
  g.fillStyle(hexToNum(MAP3D_SHEET.fill), 1);
  for (const r of rows) g.fillRect(r.x, r.y, r.w, 1);
  // 지평선 격자: 가로 = 깊이 고르게 (멀수록 촘촘), 세로 = 아래에서 위로 모이는 선
  g.fillStyle(hexToNum(MAP3D_SHEET.grid), 1);
  for (let i = 0; i <= MAP3D.gridRows; i++) {
    const yy = yAt(i / MAP3D.gridRows);
    const row = rows[yy - yTop];
    if (!row) continue;
    for (let x = row.x + 2; x < row.x + row.w - 2; x += 4) g.fillRect(x, yy, 2, 1);
  }
  for (let i = 1; i < MAP3D.gridCols; i++) {
    const t = i / MAP3D.gridCols;
    const xb = Math.round(cx - wBottom / 2 + wBottom * t);
    const xt = Math.round(cx - wTop / 2 + wTop * t);
    for (const p of dottedPoints(xb, yBottom - MAP3D.sheetRoll, xt, yTop + MAP3D.sheetRoll, 2, 2, 5))
      g.fillRect(p.x, p.y, 1, 2);
  }
  // 말린 가장자리: 위 = 밝은 띠(종이가 넘어감), 아래 = 어두운 둥근 말림 + 윗선 하이라이트
  const roll = MAP3D.sheetRoll;
  for (const r of rows.slice(0, roll)) {
    g.fillStyle(hexToNum(SEPIA[5]), 0.55).fillRect(r.x, r.y, r.w, 1);
  }
  g.fillStyle(hexToNum(SEPIA[1]), 1).fillRect(rows[roll].x, rows[roll].y, rows[roll].w, 1);
  for (const r of rows.slice(rows.length - roll)) g.fillStyle(hexToNum(SEPIA[2]), 1).fillRect(r.x - 1, r.y, r.w + 2, 1);
  const hl = rows[rows.length - roll - 1];
  g.fillStyle(hexToNum(SEPIA[5]), 0.55).fillRect(hl.x, hl.y, hl.w, 1);
  // 좌우 테두리 (계단)
  g.fillStyle(hexToNum(SEPIA[1]), 1);
  for (const r of rows) {
    g.fillRect(r.x, r.y, 1, 1);
    g.fillRect(r.x + r.w - 1, r.y, 1, 1);
  }
}

/**
 * 50라운드: 지도 그림 (비율 유지, 사각형). 그림자 → 바탕(S1, 그림을 읽는 동안) → 그림 → 테두리 S0 1px.
 * 그림은 표시 크기로 한 번 줄인 텍스처를 1:1 로 깐다. 아직 안 읽었으면 읽기 시작하고, 오면 바탕 바로 위에 끼운다.
 */
export function drawIllustration(
  scene: Phaser.Scene,
  rect: Area,
  floor: number,
  late: LateInsert,
  alive: () => boolean,
): void {
  const g = scene.add.graphics();
  g.fillStyle(hexToNum(SEPIA[0]), 0.55).fillRect(
    rect.x + MAP_ILLUST.shadow,
    rect.y + MAP_ILLUST.shadow,
    rect.w,
    rect.h,
  );
  g.fillStyle(hexToNum(SEPIA[1]), 1).fillRect(rect.x, rect.y, rect.w, rect.h);
  const place = (): void => {
    if (!alive()) return;
    const key = derivedTexture(scene, mapBgKey(floor), rect.w, rect.h, 'stretch');
    if (!key) return;
    late(scene.add.image(rect.x, rect.y, key).setOrigin(0, 0), g, 'above');
  };
  const frame = scene.add.graphics();
  frame.lineStyle(1, hexToNum(SEPIA[0]), 1).strokeRect(rect.x - 0.5, rect.y - 0.5, rect.w + 1, rect.h + 1);
  if (scene.textures.exists(mapBgKey(floor))) place();
  else ensureImage(scene, mapBgKey(floor), mapBgUrl(floor), (ok) => ok && place());
}
