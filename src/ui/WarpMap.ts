import Phaser from 'phaser';
import { UI_SCREEN, type RoomType, type UiRoom, type UiSnapshot, type UiWarpDenyReason } from '../contract/ui';
import { GlowText } from './glow';
import { ICON, KIT, accentHex, book, cursor, icon, rule } from './kit';
import { structText, warpText, type WarpTextKey } from './text';
import { GRAY, SEPIA, STRUCT, WARP, hexToNum } from './theme';
import { keyToDir, nearest, pickNeighbor, type NavNode } from './warpNav';

/** 방 종류 이름 (임시 문구, text.ts WARP_TEXT) */
export const ROOM_NAME_KEY: Record<RoomType, WarpTextKey> = {
  start: 'roomStart',
  trial: 'roomTrial',
  rest: 'roomRest',
  boss: 'roomBoss',
};
export const roomName = (t: RoomType): string => warpText(ROOM_NAME_KEY[t]);

/** 워프 거부 사유 문구 */
export const DENY_KEY: Record<UiWarpDenyReason, WarpTextKey> = {
  combat: 'warpDeniedCombat',
  busy: 'warpDeniedBusy',
  'unknown-room': 'warpDeniedUnknown',
  'not-cleared': 'warpDeniedNotCleared',
  'current-room': 'warpDeniedCurrent',
};

const GLYPH: Record<RoomType, string> = {
  start: ICON.miniStart,
  trial: ICON.miniTrial,
  rest: ICON.miniRest,
  boss: ICON.miniBoss,
};
/** 미니맵 글리프 8×8 을 정수 2배로 */
const GLYPH_SCALE = 2;
const GLYPH_PX = 8 * GLYPH_SCALE;

function hasDepth(
  o: Phaser.GameObjects.GameObject,
): o is Phaser.GameObjects.GameObject & { setDepth(d: number): unknown } {
  return typeof (o as { setDepth?: unknown }).setDepth === 'function';
}

interface RoomView {
  room: UiRoom;
  node: NavNode;
  /** 방 영역(칸 묶음) 왼쪽 위·크기, px */
  x: number;
  y: number;
  w: number;
  h: number;
  /** 워프 가능 방만: Container → Graphics → 글리프 (버튼 규약) */
  btn?: Phaser.GameObjects.Container;
  g: Phaser.GameObjects.Graphics;
  glyph: Phaser.GameObjects.Image;
}

export interface WarpMapHandlers {
  /** 방을 골랐다 (클릭을 뗀 뒤·Enter/Space 를 뗀 뒤 한 프레임 늦게 부른다 — 게임 씬 입력으로 새지 않게) */
  onChoose: (roomId: string) => void;
}

/**
 * 워프 선택 화면 (45라운드 Q3·Q9·Q10, 계약 §8). HUD 씬 위에 그리는 일기장 한 페이지 오버레이.
 * 왼쪽: 미니맵 방 그래프를 크게 (방문한 방만, 칸 최대 40px, 글리프 2배). 현재 방 = 층 강조 22 테두리 + 글리프 틴트,
 * 워프 가능 = 밝은 칸(S3) + 고르면 S4 + 강조 20 테두리 + 커서, 그 외 = 어두운 칸(S2) + 글리프 흐림.
 * 오른쪽: 범례 · 고른 방 이름 · 안내. 아래: 조작 안내.
 * 키보드(WASD·방향키 이동, Enter·Space 선택)와 마우스(올리면 고름, 눌렀다 떼면 선택) 둘 다.
 */
export class WarpMap {
  private objs: Phaser.GameObjects.GameObject[] = [];
  private views: RoomView[] = [];
  private nodes: NavNode[] = [];
  private sel: string | null = null;
  private stageIndex: number;
  private cell: number = WARP.cellMax;
  private cursorSprite?: Phaser.GameObjects.Sprite;
  private selName?: GlowText;
  private selState?: GlowText;
  private message?: GlowText;
  /** 열려 있는 동안 눌린 선택 키 (열기 전부터 누르던 키를 떼어 바로 워프되지 않게) */
  private armedKey: string | null = null;
  private pressedRoom: string | null = null;
  private chosen = false;
  private destroyed = false;
  private currentCenter = { x: 0, y: 0 };
  private currentId = '';

  constructor(
    private scene: Phaser.Scene,
    snap: UiSnapshot,
    private handlers: WarpMapHandlers,
  ) {
    this.stageIndex = Math.max(0, snap.stageIndex);
    this.build(snap);
    scene.input.keyboard?.on('keydown', this.onKeyDown);
    scene.input.keyboard?.on('keyup', this.onKeyUp);
  }

  /** 안에서 거부 사유 등 짧은 글을 보인다 */
  showMessage(text: string): void {
    if (this.destroyed || !this.message) return;
    this.message.setText(text).setGlowStyle('page_selected');
  }

  destroy(): void {
    if (this.destroyed) return;
    this.destroyed = true;
    this.scene.input.keyboard?.off('keydown', this.onKeyDown);
    this.scene.input.keyboard?.off('keyup', this.onKeyUp);
    for (const o of this.objs) o.destroy();
    this.objs = [];
    this.views = [];
  }

  // -------------------------------------------------------------------------------------------
  private onKeyDown = (e: KeyboardEvent): void => {
    if (this.destroyed || this.chosen) return;
    const dir = keyToDir(e.key);
    if (dir) {
      const from = this.sel ? this.nodes.find((n) => n.id === this.sel) : undefined;
      const next = pickNeighbor(from ?? this.currentCenter, dir, this.nodes, this.sel ?? undefined);
      if (next) this.select(next);
      else if (!this.sel) this.select(nearest(this.currentCenter, this.nodes));
      return;
    }
    if ((e.key === 'Enter' || e.key === ' ') && !e.repeat) this.armedKey = e.key;
  };

  private onKeyUp = (e: KeyboardEvent): void => {
    if (this.destroyed || this.chosen) return;
    if (e.key === this.armedKey) {
      this.armedKey = null;
      if (this.sel) this.choose(this.sel);
    }
  };

  private choose(id: string): void {
    this.chosen = true;
    // 떼는 입력이 끝난 다음 프레임에 넘긴다 (같은 프레임에 게임 씬이 재개되면 그 입력을 받을 수 있다)
    this.scene.time.delayedCall(0, () => {
      if (this.destroyed) return;
      this.chosen = false;
      this.handlers.onChoose(id);
    });
  }

  // -------------------------------------------------------------------------------------------
  private build(snap: UiSnapshot): void {
    const scene = this.scene;
    const before = new Set(scene.children.list);
    const W = UI_SCREEN.WIDTH;
    const H = UI_SCREEN.HEIGHT;
    const map = snap.map;
    const si = this.stageIndex;
    this.currentId = map.currentRoomId;
    const pad = WARP.pad;

    // 배경 어둡게 + 클릭 막기 (페이지 밖 클릭이 아래로 내려가지 않게)
    scene.add.rectangle(0, 0, W, H, hexToNum(GRAY[0]), WARP.dimAlpha).setOrigin(0, 0).setInteractive();

    const gw = Math.max(1, map.gridW);
    const gh = Math.max(1, map.gridH);
    this.cell = Math.max(
      WARP.cellMin,
      Math.min(WARP.cellMax, Math.floor(WARP.mapMaxW / gw), Math.floor(WARP.mapMaxH / gh)),
    );
    const cell = this.cell;
    const mapW = gw * cell;
    const mapH = gh * cell;

    const title = new GlowText(scene, 0, 0, warpText('warpTitle'), 'page_title', { font: 'title', stageIndex: si });
    const hint = new GlowText(scene, 0, 0, warpText('warpHint'), 'page_faint');
    const sideH = 232 + 18;
    const bodyH = Math.max(mapH, sideH);
    const pageW = Math.max(pad + mapW + pad + WARP.sideW + pad, hint.displayWidth + pad * 2);
    const pageH = 14 + title.displayHeight + 6 + 4 + 12 + bodyH + 12 + hint.displayHeight + 14;
    // 글자를 먼저 만들었으므로 책을 깐 뒤 위로 올린다
    const bk = book(scene, Math.round(W / 2), Math.round(H / 2), pageW, pageH, 1, 'warp');
    const pg = bk.pages[0];
    let y = pg.y + 14;
    title.placeCenter(pg.x + pageW / 2, y);
    y += title.displayHeight + 6;
    rule(scene, pg.x + pad, y, pageW - pad * 2);
    y += 4 + 12;
    const mx = pg.x + pad;
    const my = y + Math.floor((bodyH - mapH) / 2);
    hint.placeCenter(pg.x + pageW / 2, y + bodyH + 12);

    // ---- 지도
    const g = scene.add.graphics();
    // 지도 영역 테두리 (흐린 괘선 색)
    g.lineStyle(1, hexToNum(SEPIA[2]), 1);
    g.strokeRect(mx - 4 + 0.5, my - 4 + 0.5, mapW + 8 - 1, mapH + 8 - 1);
    const visitedCells = new Set<string>();
    for (const r of map.rooms) if (r.visited) for (const c of r.cells) visitedCells.add(`${c.cx},${c.cy}`);
    g.lineStyle(2, hexToNum(SEPIA[1]), 1);
    for (const c of map.connections) {
      if (!visitedCells.has(`${c.a.cx},${c.a.cy}`) && !visitedCells.has(`${c.b.cx},${c.b.cy}`)) continue;
      g.lineBetween(
        mx + c.a.cx * cell + cell / 2,
        my + c.a.cy * cell + cell / 2,
        mx + c.b.cx * cell + cell / 2,
        my + c.b.cy * cell + cell / 2,
      );
    }

    for (const r of map.rooms) {
      if (!r.visited || !r.cells.length) continue;
      const xs = r.cells.map((c) => c.cx);
      const ys = r.cells.map((c) => c.cy);
      const x0 = Math.min(...xs);
      const y0 = Math.min(...ys);
      const x1 = Math.max(...xs) + 1;
      const y1 = Math.max(...ys) + 1;
      const node: NavNode = { id: r.id, x: (x0 + x1) / 2, y: (y0 + y1) / 2 };
      const vx = mx + x0 * cell;
      const vy = my + y0 * cell;
      const vw = (x1 - x0) * cell;
      const vh = (y1 - y0) * cell;
      const rg = scene.add.graphics();
      const glyph = scene.add
        .image(Math.floor((vw - GLYPH_PX) / 2), Math.floor((vh - GLYPH_PX) / 2), KIT.icons, GLYPH[r.type])
        .setOrigin(0, 0)
        .setScale(GLYPH_SCALE);
      const view: RoomView = { room: r, node, x: vx, y: vy, w: vw, h: vh, g: rg, glyph };
      // 버튼 규약: Container → Graphics → (글리프). 그래프·글리프는 컨테이너 지역 좌표
      const box = scene.add.container(vx, vy, [rg, glyph]).setSize(vw, vh);
      if (r.warpable) {
        const cellSet = new Set(r.cells.map((c) => `${c.cx - x0},${c.cy - y0}`));
        // Container 입력 판정은 지역 좌표 + 폭·높이 절반으로 들어온다 (glow.ts makeInteractive 참조)
        box.setInteractive(
          new Phaser.Geom.Rectangle(vw / 2, vh / 2, vw, vh),
          (_area: Phaser.Geom.Rectangle, hx: number, hy: number) => {
            const lx = hx - vw / 2;
            const ly = hy - vh / 2;
            if (lx < 0 || ly < 0 || lx >= vw || ly >= vh) return false;
            return cellSet.has(`${Math.floor(lx / cell)},${Math.floor(ly / cell)}`);
          },
        );
        if (box.input) box.input.cursor = 'pointer';
        box.on('pointerover', () => this.select(r.id));
        box.on('pointerdown', () => {
          this.pressedRoom = r.id;
          this.select(r.id);
        });
        box.on('pointerup', () => {
          if (this.pressedRoom === r.id && !this.chosen) this.choose(r.id);
          this.pressedRoom = null;
        });
        view.btn = box;
        this.nodes.push(node);
      }
      if (r.id === map.currentRoomId) this.currentCenter = { x: node.x, y: node.y };
      this.views.push(view);
    }

    // ---- 오른쪽: 범례 · 고른 방 · 안내
    const sx = mx + mapW + pad;
    let sy = y;
    const legend: [RoomType, string][] = [
      ['start', roomName('start')],
      ['trial', roomName('trial')],
      ['rest', roomName('rest')],
      ['boss', roomName('boss')],
    ];
    for (const [t, name] of legend) {
      icon(scene, sx, sy + 2, GLYPH[t]);
      new GlowText(scene, sx + 14, sy, name, 'page_body', { stageIndex: si });
      sy += 18;
    }
    sy += 4;
    // 현재 방 · 건너갈 수 있는 방 표본
    const sw = scene.add.graphics();
    sw.fillStyle(hexToNum(SEPIA[1]), 1).fillRect(sx, sy + 3, 10, 10);
    sw.lineStyle(1, hexToNum(accentHex(scene, si, 22)), 1).strokeRect(sx + 0.5, sy + 3.5, 9, 9);
    new GlowText(scene, sx + 14, sy, warpText('warpHere'), 'page_body', { stageIndex: si });
    sy += 18;
    sw.fillStyle(hexToNum(SEPIA[1]), 1).fillRect(sx, sy + 3, 10, 10);
    sw.lineStyle(1, hexToNum(SEPIA[5]), 1).strokeRect(sx + 0.5, sy + 3.5, 9, 9);
    new GlowText(scene, sx + 14, sy, warpText('warpCan'), 'page_body', { stageIndex: si });
    sy += 18;
    sw.fillStyle(hexToNum(SEPIA[2]), 1).fillRect(sx, sy + 3, 10, 10);
    new GlowText(scene, sx + 14, sy, warpText('warpCannot'), 'page_faint');
    sy += 18;
    // 47라운드: 구조물 점 (미니맵과 같은 뜻)
    sw.fillStyle(hexToNum(accentHex(scene, si, 25)), 1).fillRect(sx + 3, sy + 6, STRUCT.warpDot, STRUCT.warpDot);
    new GlowText(scene, sx + 14, sy, structText('legendStructure'), 'page_body', { stageIndex: si });
    sy += 18 + 6;
    rule(scene, sx, sy, WARP.sideW - 8);
    sy += 4 + 10;
    this.selName = new GlowText(scene, sx, sy, '', 'page_selected', { scale: 2, stageIndex: si });
    sy += 30;
    this.selState = new GlowText(scene, sx, sy, '', 'page_faint', { wrap: WARP.sideW - 8 });
    sy += 18;
    this.message = new GlowText(scene, sx, sy, this.nodes.length ? '' : warpText('warpEmpty'), 'page_faint', {
      wrap: WARP.sideW - 8,
      stageIndex: si,
    });

    this.cursorSprite = cursor(scene).setVisible(false);

    // 이번에 만든 최상위 객체를 모아 HUD 위로 (같은 depth 는 만든 순서대로 그려진다)
    for (const o of scene.children.list) {
      if (before.has(o)) continue;
      this.objs.push(o);
    }
    // 책·페이지는 글자보다 나중에 만들어졌으므로 맨 아래로 내린다
    const texts = new Set<Phaser.GameObjects.GameObject>([title, hint]);
    this.objs.forEach((o, i) => {
      if (!hasDepth(o)) return;
      if (i === 0) o.setDepth(WARP.depth);
      else if (o === this.cursorSprite) o.setDepth(WARP.depth + 3);
      else o.setDepth(texts.has(o) ? WARP.depth + 2 : WARP.depth + 1);
    });

    this.select(nearest(this.currentCenter, this.nodes));
    this.redraw();
  }

  private select(id: string | null): void {
    if (this.destroyed || id === this.sel) return;
    this.sel = id;
    this.redraw();
  }

  /** 방 칸·테두리·글리프를 상태에 맞게 다시 칠한다 */
  private redraw(): void {
    if (this.destroyed) return;
    const scene = this.scene;
    const si = this.stageIndex;
    const cell = this.cell;
    const inset = WARP.cellInset;
    const accentCur = hexToNum(accentHex(scene, si, 22));
    const accentSel = hexToNum(accentHex(scene, si, 20));
    for (const v of this.views) {
      const r = v.room;
      const current = r.id === this.currentId;
      const selected = r.id === this.sel;
      // 종이 바탕이 S3 이라 방은 잉크처럼 어둡게: 갈 수 있는 방·현재 방 S1, 그 외 S2
      const fill = r.warpable || current ? SEPIA[1] : SEPIA[2];
      const x0 = Math.min(...r.cells.map((c) => c.cx));
      const y0 = Math.min(...r.cells.map((c) => c.cy));
      const cells = new Set(r.cells.map((c) => `${c.cx},${c.cy}`));
      const g = v.g;
      g.clear();
      g.fillStyle(hexToNum(fill), 1);
      for (const c of r.cells) {
        const lx = (c.cx - x0) * cell;
        const ly = (c.cy - y0) * cell;
        g.fillRect(lx + inset, ly + inset, cell - inset * 2, cell - inset * 2);
        // 같은 방 이웃 칸과의 틈을 메운다
        if (cells.has(`${c.cx + 1},${c.cy}`)) g.fillRect(lx + cell - inset, ly + inset, inset * 2, cell - inset * 2);
        if (cells.has(`${c.cx},${c.cy + 1}`)) g.fillRect(lx + inset, ly + cell - inset, cell - inset * 2, inset * 2);
      }
      if (current || selected) {
        g.lineStyle(2, current ? accentCur : accentSel, 1);
        g.strokeRect(inset - 1, inset - 1, v.w - inset * 2 + 2, v.h - inset * 2 + 2);
      } else if (r.warpable) {
        // 고를 수 있는 방: 밝은 세피아 1px 테두리
        g.lineStyle(1, hexToNum(SEPIA[5]), 1);
        g.strokeRect(inset + 0.5, inset + 0.5, v.w - inset * 2 - 1, v.h - inset * 2 - 1);
      }
      if (r.structureDot) {
        // 47라운드: 쓸 수 있는 구조물이 남은 방 — 가장 위 줄 오른쪽 칸의 오른쪽 위에 점
        const tx = Math.max(...r.cells.filter((c) => c.cy === y0).map((c) => c.cx));
        g.fillStyle(hexToNum(accentHex(scene, si, 25)), 1);
        g.fillRect((tx - x0) * cell + cell - inset - 3 - STRUCT.warpDot, inset + 3, STRUCT.warpDot, STRUCT.warpDot);
      }
      v.glyph.clearTint().setAlpha(1);
      if (current) v.glyph.setTint(accentCur);
      else if (!r.warpable) v.glyph.setAlpha(WARP.dimGlyphAlpha);
    }
    // 커서 촉 + 오른쪽 안내
    const sv = this.views.find((v) => v.room.id === this.sel);
    if (sv && this.cursorSprite) {
      this.cursorSprite.setVisible(true).setPosition(sv.x - 2, sv.y + Math.floor(sv.h / 2));
    } else this.cursorSprite?.setVisible(false);
    this.selName?.setText(sv ? roomName(sv.room.type) : '');
    this.selState?.setText(sv ? warpText('warpPick') : '');
  }
}
