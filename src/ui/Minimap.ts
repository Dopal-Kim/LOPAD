import Phaser from 'phaser';
import type { UiMap } from '../contract/ui';
import { THEME } from './theme';
import { panel } from './widgets';

/** 방 그래프 미니맵: 방문한 방만 표시, 현재 방 강조, 방 종류별 색 */
export class Minimap {
  private g: Phaser.GameObjects.Graphics;
  private lastKey = '';

  constructor(
    scene: Phaser.Scene,
    private x: number,
    private y: number,
    private w: number,
    private h: number,
  ) {
    panel(scene, x, y, w, h);
    this.g = scene.add.graphics();
  }

  render(map: UiMap): void {
    const key = `${map.currentRoomId}|${map.rooms.map((r) => `${r.id}${r.visited ? 'v' : ''}${r.cleared ? 'c' : ''}`).join(',')}`;
    if (key === this.lastKey) return;
    this.lastKey = key;
    this.g.clear();
    if (!map.rooms.length) return;
    const cell = THEME.minimap.cell;
    const ox = this.x + (this.w - map.gridW * cell) / 2;
    const oy = this.y + (this.h - map.gridH * cell) / 2;
    const visitedCells = new Set<string>();
    for (const r of map.rooms) if (r.visited) for (const c of r.cells) visitedCells.add(`${c.cx},${c.cy}`);
    // 연결선 (양쪽 중 하나라도 방문한 경우)
    this.g.lineStyle(1, THEME.minimap.link, 1);
    for (const c of map.connections) {
      if (!visitedCells.has(`${c.a.cx},${c.a.cy}`) && !visitedCells.has(`${c.b.cx},${c.b.cy}`)) continue;
      this.g.lineBetween(
        ox + c.a.cx * cell + cell / 2,
        oy + c.a.cy * cell + cell / 2,
        ox + c.b.cx * cell + cell / 2,
        oy + c.b.cy * cell + cell / 2,
      );
    }
    for (const r of map.rooms) {
      if (!r.visited) continue;
      const color =
        r.type === 'start'
          ? THEME.minimap.start
          : r.type === 'rest'
            ? THEME.minimap.rest
            : r.type === 'boss'
              ? THEME.minimap.boss
              : r.cleared
                ? THEME.minimap.trialCleared
                : THEME.minimap.trial;
      for (const c of r.cells) {
        this.g.fillStyle(color, 1);
        this.g.fillRect(ox + c.cx * cell + 1, oy + c.cy * cell + 1, cell - 2, cell - 2);
      }
      if (r.id === map.currentRoomId) {
        this.g.lineStyle(1, THEME.minimap.current, 1);
        const xs = r.cells.map((c) => c.cx);
        const ys = r.cells.map((c) => c.cy);
        const x0 = Math.min(...xs);
        const y0 = Math.min(...ys);
        const x1 = Math.max(...xs) + 1;
        const y1 = Math.max(...ys) + 1;
        this.g.strokeRect(ox + x0 * cell + 0.5, oy + y0 * cell + 0.5, (x1 - x0) * cell - 1, (y1 - y0) * cell - 1);
      }
    }
  }
}
