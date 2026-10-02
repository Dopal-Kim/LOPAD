import Phaser from 'phaser';
import type { UiNodeState, UiRoute } from '../contract/ui';
import { GlowText } from './glow';
import { KIT, NinePanel, SLICE, accentHex } from './kit';
import { diamondRing, pixelDiamond } from './RouteMap';
import { dottedPoints, layoutRoute, linkKind, remainingSteps } from './routeView';
import { fill, routeText } from './text';
import { GRAY, ROUTE, hexToNum } from './theme';

/**
 * 48라운드 HUD 우상단 노드 띠 (route 가 있을 때 방 미니맵 대신). minimap_frame 9-slice 안에
 * 전체 노드를 작은 마름모로(지금 = 층 강조 22 한 칸 크게, 지나온 곳 G08, 갈 수 있는 곳 G12 테두리, 먼 곳 G05 테두리,
 * 지나친 갈래 G03), 아래에 '남은 길 N' (ink_faint). 크기는 단계·줄 수에 맞춘다 (오른쪽 끝 고정).
 */
export class RouteStrip {
  private frame: NinePanel;
  private g: Phaser.GameObjects.Graphics;
  private text: GlowText;
  private lastKey = '';
  w: number = ROUTE.strip.minW;
  h: number = 40;

  constructor(
    private scene: Phaser.Scene,
    private right: number,
    private y: number,
  ) {
    this.frame = new NinePanel(scene, right - this.w, y, KIT.minimapFrame, SLICE.minimapFrame, this.w, this.h);
    this.g = scene.add.graphics();
    this.text = new GlowText(scene, 0, 0, '', 'ink_faint');
  }

  setVisible(v: boolean): void {
    this.frame.setVisible(v);
    this.g.setVisible(v);
    this.text.setVisible(v);
  }

  /** 다시 그린다. 틀 크기가 바뀌었으면 true (HUD 가 아래 안내 줄을 옮긴다) */
  render(route: UiRoute, stageIndex: number): boolean {
    const key = `${stageIndex}|${route.currentId}|${route.nodes.map((n) => `${n.id}:${n.col},${n.row}:${n.state}:${n.links.join('+')}`).join(',')}`;
    if (key === this.lastKey) return false;
    this.lastKey = key;
    const S = ROUTE.strip;
    const inner = SLICE.minimapFrame.inner;
    const cols = new Set(route.nodes.map((n) => n.col)).size;
    const rowsIn = new Map<number, number>();
    for (const n of route.nodes) rowsIn.set(n.col, Math.max(rowsIn.get(n.col) ?? 0, n.row + 1));
    const maxRows = Math.max(1, ...rowsIn.values());
    const graphW = (cols - 1) * S.col + S.r * 2 + 1;
    const graphH = (maxRows - 1) * S.row + S.r * 2 + 1;
    const w = Math.max(S.minW, graphW + (inner + S.pad) * 2);
    const h = graphH + (inner + S.pad) * 2 + S.textH;
    const resized = w !== this.w || h !== this.h;
    this.w = w;
    this.h = h;
    const x = this.right - w;
    this.frame.resize(w, h).setPosition(x, this.y);
    // 그래프 영역 (가로 가운데, 위 여백 안). 단계·줄 간격은 고정, 단계마다 세로 가운데 정렬 (routeView 와 같은 규칙)
    const gx = x + Math.floor((w - graphW) / 2) + S.r;
    const gy = this.y + inner + S.pad;
    const L = layoutRoute(
      route.nodes,
      { x: gx - Math.floor(S.col / 2), y: gy + S.r - Math.floor(S.row / 2), w: cols * S.col, h: maxRows * S.row },
      S.col,
      S.row,
    );
    const g = this.g.clear();
    const accent22 = hexToNum(accentHex(this.scene, stageIndex, 22));
    const byId = new Map(route.nodes.map((n) => [n.id, n]));
    for (const a of route.nodes) {
      const pa = L.pos.get(a.id);
      if (!pa) continue;
      for (const bid of a.links) {
        const b = byId.get(bid);
        const pb = b && L.pos.get(bid);
        if (!b || !pb) continue;
        const kind = linkKind(a.state, b.state);
        g.fillStyle(hexToNum(kind === 'walked' ? GRAY[8] : kind === 'option' ? GRAY[11] : GRAY[4]), 1);
        for (const p of dottedPoints(pa.x, pa.y, pb.x, pb.y, S.r + 1, S.r + 1, kind === 'faint' ? 3 : 2))
          g.fillRect(p.x, p.y, 1, 1);
      }
    }
    const look: Record<UiNodeState, { fill?: number; ring?: number }> = {
      current: { fill: accent22 },
      cleared: { fill: hexToNum(GRAY[8]) },
      available: { fill: hexToNum(GRAY[2]), ring: hexToNum(GRAY[12]) },
      locked: { fill: hexToNum(GRAY[1]), ring: hexToNum(GRAY[5]) },
      passed: { fill: hexToNum(GRAY[3]) },
    };
    for (const n of route.nodes) {
      const p = L.pos.get(n.id);
      if (!p) continue;
      const lk = look[n.state];
      // 지금 노드는 한 칸 크게 (고리를 두르면 작은 크기에서 체크 무늬처럼 보였다)
      const rr = n.state === 'current' ? S.r + 1 : S.r;
      if (lk.fill !== undefined) pixelDiamond(g, rr, lk.fill, 1, p.x, p.y);
      if (lk.ring !== undefined) diamondRing(g, rr, 1, lk.ring, 1, p.x, p.y);
    }
    const left = remainingSteps(route);
    this.text.setText(left > 0 ? fill(routeText('stripRemain'), { n: left }) : routeText('stripLast'));
    this.text.placeCenter(x + Math.round(w / 2), this.y + h - inner - S.textH - 2);
    return resized;
  }

  setDepth(d: number): void {
    this.frame.setDepth(d);
    this.g.setDepth(d + 1);
    this.text.setDepth(d + 1);
  }
}
