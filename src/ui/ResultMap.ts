import Phaser from 'phaser';
import type { UiPathNode, UiRoute } from '../contract/ui';
import { accentHex } from './kit';
import { mapLayout, type MapDot } from './resultView';
import { pixelDiamond } from './routeGlyph';
import { GRAY, SEPIA, hexToNum } from './theme';
import { RESULT_UI as R } from './themeLoop2E';

/**
 * 62 루프 2 UI E (계약 C `UiRunSummary.route`·`path`): 결산 '지나온 길' 미니맵 — 종이 위 먹 선.
 * 지도 길은 흐린 세피아, 지나온 길은 층 강조색 굵은 선(차례대로 이어짐), 지난 곳은 채운 마름모, 군주의 방은 큰 마름모.
 * 쓰러진 곳에는 지도 표식 '먹 붓 망령'(아트 §31-9 `map_marker_ghost`, 6칸 160ms 반복 — 없으면 먹 ×).
 * 층 끝이면 마지막 곳에 같은 망령이 서 있다(쓰러지지 않음 = ×없음).
 */
export function preloadResultMap(scene: Phaser.Scene): void {
  const G = R.ghost;
  if (!scene.textures.exists(G.key)) scene.load.spritesheet(G.key, G.url, { frameWidth: G.w, frameHeight: G.h });
}

function ensureGhostAnim(scene: Phaser.Scene): boolean {
  const G = R.ghost;
  if (!scene.textures.exists(G.key)) return false;
  if (!scene.anims.exists(G.key))
    scene.anims.create({
      key: G.key,
      frames: scene.anims.generateFrameNumbers(G.key, { start: 0, end: G.frames - 1 }),
      frameRate: 1000 / G.ms,
      repeat: -1,
    });
  return true;
}

export function drawResultMap(
  scene: Phaser.Scene,
  route: UiRoute | null,
  path: readonly UiPathNode[],
  x: number,
  y: number,
  w: number,
  h: number,
  stageIndex: number,
): Phaser.GameObjects.GameObject[] {
  const lay = mapLayout(route, path, x, y, w, h, 14);
  const g = scene.add.graphics();
  const out: Phaser.GameObjects.GameObject[] = [g];
  const faint = hexToNum(SEPIA[4]);
  const accent = hexToNum(accentHex(scene, stageIndex, 20));
  const ink = hexToNum(GRAY[0]);
  // 지도 길 (흐림)
  g.lineStyle(1, faint, 0.7);
  for (const [a, b] of lay.edges) g.lineBetween(a.x, a.y, b.x, b.y);
  // 지나온 길 (굵게)
  g.lineStyle(R.pathLine, accent, 1);
  for (let i = 1; i < lay.path.length; i++) {
    const a = lay.path[i - 1];
    const b = lay.path[i];
    g.lineBetween(a.x, a.y, b.x, b.y);
  }
  // 점
  for (const d of lay.dots) dot(g, d, accent, faint, ink);
  // 망령 표식: 쓰러진 곳(없으면 지나온 마지막 곳)
  const at = lay.path.find((d) => d.died) ?? lay.path[lay.path.length - 1];
  if (at) {
    if (at.died) {
      // 먹 × (망령 발밑 — 망령보다 먼저 그린다)
      const xg = scene.add.graphics();
      xg.lineStyle(2, hexToNum(GRAY[13]), 1);
      xg.lineBetween(at.x - 5, at.y - 5, at.x + 5, at.y + 5);
      xg.lineBetween(at.x + 5, at.y - 5, at.x - 5, at.y + 5);
      out.push(xg);
    }
    if (ensureGhostAnim(scene)) {
      const G = R.ghost;
      // 먹 망령은 어두운 종이 위에서 묻힌다 — 발밑부터 몸까지 옅은 종이빛 번짐을 깐다
      const halo = scene.add.graphics();
      halo.fillStyle(hexToNum(SEPIA[5]), 0.18).fillEllipse(at.x, at.y - 22, 34, 50);
      halo.fillStyle(hexToNum(SEPIA[5]), 0.22).fillEllipse(at.x, at.y - 20, 22, 36);
      out.push(halo);
      const s = scene.add.sprite(at.x, at.y + 2, G.key, 0).setOrigin(G.pivotX / G.w, G.pivotY / G.h);
      s.play(G.key);
      out.push(s);
    }
  }
  return out;
}

function dot(g: Phaser.GameObjects.Graphics, d: MapDot, accent: number, faint: number, ink: number): void {
  const r = d.type === 'boss' ? R.nodeR + 2 : R.nodeR;
  if (d.step >= 0) {
    pixelDiamond(g, r + 1, ink, 1, d.x, d.y);
    pixelDiamond(g, r, accent, 1, d.x, d.y);
  } else {
    pixelDiamond(g, r, faint, 0.55, d.x, d.y);
    pixelDiamond(g, Math.max(1, r - 2), hexToNum(SEPIA[1]), 1, d.x, d.y);
  }
}
