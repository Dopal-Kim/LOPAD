import Phaser from 'phaser';
import type { UiMap } from '../contract/ui';
import { ICON, KIT, MINI, NinePanel, SLICE, accentHex } from './kit';
import { GRAY, hexToNum } from './theme';

/**
 * 방 그래프 미니맵 (minimap_frame 9-slice + 방 글리프 mini_*).
 * 방문한 방만: 칸 G01, 연결선 G02, 글리프 G12(8×8), 클리어한 시련은 글리프 흐림, 현재 방은 층 강조 22 테두리.
 */
export class Minimap {
  private g: Phaser.GameObjects.Graphics;
  private glyphs: Phaser.GameObjects.Image[] = [];
  private lastKey = '';
  private frame: NinePanel;
  /** 틀 바깥 크기 */
  readonly w: number;
  readonly h: number;

  constructor(
    private scene: Phaser.Scene,
    private x: number,
    private y: number,
    gridW: number,
    gridH: number,
  ) {
    const size = Minimap.size(gridW, gridH);
    this.w = size.w;
    this.h = size.h;
    this.frame = new NinePanel(scene, x, y, KIT.minimapFrame, SLICE.minimapFrame, this.w, this.h);
    this.g = scene.add.graphics();
  }

  /** 틀 바깥 크기 (격자 7×7 기본) */
  static size(gridW: number, gridH: number): { w: number; h: number } {
    const pad = SLICE.minimapFrame.inner + 4;
    return { w: Math.max(7, gridW) * MINI + pad * 2, h: Math.max(7, gridH) * MINI + pad * 2 };
  }

  setDepth(d: number): void {
    this.frame.setDepth(d);
    this.g.setDepth(d + 1);
    for (const im of this.glyphs) im.setDepth(d + 2);
  }

  render(map: UiMap, stageIndex: number): void {
    const key = `${stageIndex}|${map.currentRoomId}|${map.rooms.map((r) => `${r.id}${r.visited ? 'v' : ''}${r.cleared ? 'c' : ''}`).join(',')}`;
    if (key === this.lastKey) return;
    this.lastKey = key;
    this.g.clear();
    for (const im of this.glyphs) im.destroy();
    this.glyphs = [];
    if (!map.rooms.length) return;
    const cell = MINI;
    const ox = this.x + Math.floor((this.w - map.gridW * cell) / 2);
    const oy = this.y + Math.floor((this.h - map.gridH * cell) / 2);
    const visitedCells = new Set<string>();
    for (const r of map.rooms) if (r.visited) for (const c of r.cells) visitedCells.add(`${c.cx},${c.cy}`);
    // 연결선 (양쪽 중 하나라도 방문한 경우)
    this.g.lineStyle(1, hexToNum(GRAY[2]), 1);
    for (const c of map.connections) {
      if (!visitedCells.has(`${c.a.cx},${c.a.cy}`) && !visitedCells.has(`${c.b.cx},${c.b.cy}`)) continue;
      this.g.lineBetween(
        ox + c.a.cx * cell + cell / 2,
        oy + c.a.cy * cell + cell / 2,
        ox + c.b.cx * cell + cell / 2,
        oy + c.b.cy * cell + cell / 2,
      );
    }
    const accent = hexToNum(accentHex(this.scene, stageIndex, 22));
    for (const r of map.rooms) {
      if (!r.visited) continue;
      const current = r.id === map.currentRoomId;
      for (const c of r.cells) {
        this.g.fillStyle(hexToNum(GRAY[1]), 1);
        this.g.fillRect(ox + c.cx * cell + 1, oy + c.cy * cell + 1, cell - 2, cell - 2);
      }
      const xs = r.cells.map((c) => c.cx);
      const ys = r.cells.map((c) => c.cy);
      const x0 = Math.min(...xs);
      const y0 = Math.min(...ys);
      const x1 = Math.max(...xs) + 1;
      const y1 = Math.max(...ys) + 1;
      // 글리프 8×8 을 방 영역 가운데에 (정수)
      const gx = ox + x0 * cell + Math.floor(((x1 - x0) * cell - 8) / 2);
      const gy = oy + y0 * cell + Math.floor(((y1 - y0) * cell - 8) / 2);
      const name =
        r.type === 'start'
          ? ICON.miniStart
          : r.type === 'rest'
            ? ICON.miniRest
            : r.type === 'boss'
              ? ICON.miniBoss
              : ICON.miniTrial;
      const im = this.scene.add
        .image(gx, gy, KIT.icons, name)
        .setOrigin(0, 0)
        .setDepth(this.g.depth + 1);
      if (current) im.setTint(accent);
      else if (r.type === 'trial' && r.cleared) im.setAlpha(0.45);
      this.glyphs.push(im);
      if (current) {
        this.g.lineStyle(1, accent, 1);
        this.g.strokeRect(ox + x0 * cell + 0.5, oy + y0 * cell + 0.5, (x1 - x0) * cell - 1, (y1 - y0) * cell - 1);
      }
    }
  }
}
