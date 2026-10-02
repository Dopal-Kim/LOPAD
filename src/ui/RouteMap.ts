import Phaser from 'phaser';
import type { UiNodeState, UiNodeType, UiRoute, UiRouteNode } from '../contract/ui';
import { debugExpose } from './debug';
import { GlowText } from './glow';
import { ICON, KIT, NODE_ICON_SHEET, accentHex, book, cursor, nodeIconKey, rule } from './kit';
import { cycle, dottedPoints, layoutRoute, linkKind, sortNodes, type LinkKind } from './routeView';
import { routeText, type RouteTextKey } from './text';
import { GRAY, ROUTE, SEPIA, type TextStyleName, hexToNum } from './theme';
import { keyToDir, pickNeighbor, type NavNode } from './warpNav';

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
    return scene.add
      .image(-8, -8, KIT.icons, gl.frame)
      .setOrigin(0, 0)
      .setScale(gl.scale);
  }
  const q = new GlowText(scene, 0, 0, '?', 'ink_body', { stageIndex });
  q.setPosition(-Math.round(q.displayWidth / 2), -Math.round(q.displayHeight / 2));
  return q;
}

/** 계단식 픽셀 마름모 (반대각선 r, 중심 0,0) 채우기 */
export function pixelDiamond(g: Phaser.GameObjects.Graphics, r: number, color: number, alpha = 1, cx = 0, cy = 0): void {
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
const FIG_UNIT = 2;
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

interface NodeView {
  node: UiRouteNode;
  x: number;
  y: number;
  box: Phaser.GameObjects.Container;
  g: Phaser.GameObjects.Graphics;
  glyph: Phaser.GameObjects.GameObject;
  sheet?: Phaser.GameObjects.Image;
  label: GlowText;
  pulse?: Phaser.GameObjects.Graphics;
}

export type RouteMapMode = 'choose' | 'view';

export interface RouteMapOptions {
  stageIndex: number;
  floorTitle: string;
  shopName?: string;
  /** 노드를 골랐다 (뗀 뒤 한 프레임 늦게 — 게임 씬 입력으로 새지 않게). 고르기 모드만 */
  onChoose: (id: string) => void;
}

function hasDepth(
  o: Phaser.GameObjects.GameObject,
): o is Phaser.GameObjects.GameObject & { setDepth(d: number): unknown } {
  return typeof (o as { setDepth?: unknown }).setDepth === 'function';
}

/**
 * 48라운드 노드 지도 (계약 §10). HUD 씬 위 일기장 한 페이지 오버레이 (depth 100~).
 * 왼→오 진행, 노드는 마름모(종류 글리프) + 아래 이름표, 다음 단계와 점선으로 잇는다.
 * - 'choose': ROUTE_CHOOSE_OPEN. available 노드만 고를 수 있다(맥동 고리). 마우스(올리면 고름, 눌렀다 떼면 간다)
 *   또는 ←→↑↓·WASD + Enter·Space(뗀 뒤). 닫기는 HUD 가 chooseNode 결과로 한다.
 * - 'view': Tab 보기 전용. 방향키로 둘러보기만, 고르기 없음.
 */
export class RouteMap {
  private objs: Phaser.GameObjects.GameObject[] = [];
  private views: NodeView[] = [];
  private sel: string | null = null;
  private stageIndex: number;
  private cursorSprite?: Phaser.GameObjects.Sprite;
  private figure?: Phaser.GameObjects.Graphics;
  private figureY = 0;
  private bobTimer?: Phaser.Time.TimerEvent;
  private tweens: Phaser.Tweens.Tween[] = [];
  private selName?: GlowText;
  private selDesc?: GlowText;
  private message?: GlowText;
  private armedKey: string | null = null;
  private pressed: string | null = null;
  private chosen = false;
  private destroyed = false;
  private choices: string[] = [];
  private navNodes: NavNode[] = [];
  private messageRight = 0;

  constructor(
    private scene: Phaser.Scene,
    route: UiRoute,
    readonly mode: RouteMapMode,
    private opts: RouteMapOptions,
  ) {
    this.stageIndex = Math.max(0, opts.stageIndex);
    this.build(route);
    scene.input.keyboard?.on('keydown', this.onKeyDown);
    scene.input.keyboard?.on('keyup', this.onKeyUp);
  }

  /** 고를 수 있는 노드가 있는가 (고르기 모드에서 없으면 Esc 로 닫을 수 있게) */
  get hasChoices(): boolean {
    return this.choices.length > 0;
  }

  /** 거부 사유 등 짧은 글 (오른쪽 아래) */
  showMessage(text: string): void {
    if (this.destroyed || !this.message) return;
    this.message.setText(text).placeRight(this.messageRight, this.message.y);
  }

  destroy(): void {
    if (this.destroyed) return;
    this.destroyed = true;
    this.scene.input.keyboard?.off('keydown', this.onKeyDown);
    this.scene.input.keyboard?.off('keyup', this.onKeyUp);
    this.bobTimer?.remove();
    for (const t of this.tweens) t.remove();
    this.tweens = [];
    for (const o of this.objs) o.destroy();
    this.objs = [];
    this.views = [];
    debugExpose('routeMap', null);
  }

  // -------------------------------------------------------------------------------------------
  private onKeyDown = (e: KeyboardEvent): void => {
    if (this.destroyed || this.chosen) return;
    const dir = keyToDir(e.key);
    if (dir) {
      if (this.mode === 'choose') {
        // 고를 곳은 보통 다음 단계 한 줄이라 ←↑ = 앞, →↓ = 뒤 로 돌아가며 고른다
        this.select(cycle(this.choices, this.sel, dir.dx + dir.dy > 0 ? 1 : -1));
      } else {
        const from = this.navNodes.find((n) => n.id === this.sel);
        const next = from ? pickNeighbor(from, dir, this.navNodes, from.id) : null;
        if (next) this.select(next);
      }
      return;
    }
    if (this.mode === 'choose' && (e.key === 'Enter' || e.key === ' ') && !e.repeat) this.armedKey = e.key;
  };

  private onKeyUp = (e: KeyboardEvent): void => {
    if (this.destroyed || this.chosen) return;
    if (e.key === this.armedKey) {
      this.armedKey = null;
      if (this.sel && this.choices.includes(this.sel)) this.choose(this.sel);
    }
  };

  private choose(id: string): void {
    this.chosen = true;
    // 떼는 입력이 끝난 다음 프레임에 넘긴다 (45라운드 워프 지도와 같은 방식)
    this.scene.time.delayedCall(0, () => {
      if (this.destroyed) return;
      this.chosen = false;
      this.opts.onChoose(id);
    });
  }

  // -------------------------------------------------------------------------------------------
  private build(route: UiRoute): void {
    const scene = this.scene;
    const before = new Set(scene.children.list);
    const W = scene.scale.width;
    const H = scene.scale.height;
    const si = this.stageIndex;
    const pad = ROUTE.pad;
    const pageW = ROUTE.pageW;

    // 배경 어둡게 + 클릭 막기 (페이지 밖 클릭이 게임 씬으로 내려가지 않게)
    scene.add.rectangle(0, 0, W, H, hexToNum(GRAY[0]), ROUTE.dimAlpha).setOrigin(0, 0).setInteractive();
    const bk = book(scene, Math.round(W / 2), Math.round(H / 2), pageW, ROUTE.pageH, 1, 'route');
    const pg = bk.pages[0];
    const right = pg.x + pageW - pad;

    // ---- 제목 줄: 가운데 '가는 길', 왼쪽 층 이름(흐림), 오른쪽 고르기 안내
    let y = pg.y + 14;
    const title = new GlowText(scene, 0, y, routeText('mapTitle'), 'page_title', { font: 'title', stageIndex: si });
    title.placeCenter(pg.x + pageW / 2, y);
    if (this.opts.floorTitle) new GlowText(scene, pg.x + pad, y + 2, this.opts.floorTitle, 'page_faint');
    if (this.mode === 'choose')
      new GlowText(scene, 0, y + 2, routeText('choosePrompt'), 'page_selected', { stageIndex: si }).placeRight(
        right,
        y + 2,
      );
    y += title.displayHeight + 6;
    rule(scene, pg.x + pad, y, pageW - pad * 2);
    y += 4 + 8;

    // ---- 지도
    const area = { x: pg.x + pad, y: y - ROUTE.labelLift, w: pageW - pad * 2, h: ROUTE.mapH };
    const nodes = sortNodes(route.nodes);
    const L = layoutRoute(nodes, area, ROUTE.colMax, ROUTE.rowMax);
    const useSheet = NODE_ICON_SHEET.available && scene.textures.exists(NODE_ICON_SHEET.key);
    const r = useSheet ? ROUTE.iconR : ROUTE.nodeR;
    const byId = new Map(nodes.map((n) => [n.id, n]));
    // 연결선 (노드보다 먼저 = 아래)
    const lg = scene.add.graphics();
    const dotColor: Record<LinkKind, number> = {
      walked: hexToNum(SEPIA[0]),
      option: hexToNum(accentHex(scene, si, 22)),
      faint: hexToNum(SEPIA[1]),
    };
    for (const a of nodes) {
      const pa = L.pos.get(a.id);
      if (!pa) continue;
      for (const bid of a.links) {
        const b = byId.get(bid);
        const pb = b && L.pos.get(bid);
        if (!b || !pb) continue;
        const kind = linkKind(a.state, b.state);
        const step = kind === 'faint' ? ROUTE.dotStepFaint : ROUTE.dotStep;
        const trim = r + ROUTE.dotTrim;
        lg.fillStyle(dotColor[kind], 1);
        for (const p of dottedPoints(pa.x, pa.y, pb.x, pb.y, trim, trim, step))
          lg.fillRect(p.x - ROUTE.dot / 2, p.y - ROUTE.dot / 2, ROUTE.dot, ROUTE.dot);
      }
    }
    // 노드: Container → Graphics → 글리프 (버튼 규약)
    const wrap = Math.max(48, (L.colStep || ROUTE.colMax) - ROUTE.wrapPad);
    for (const n of nodes) {
      const p = L.pos.get(n.id);
      if (!p) continue;
      let pulse: Phaser.GameObjects.Graphics | undefined;
      if (n.state === 'available') {
        pulse = scene.add.graphics({ x: p.x, y: p.y });
        diamondRing(pulse, ROUTE.pulseR, 1, hexToNum(accentHex(scene, si, 20)), 1);
        this.tweens.push(
          scene.tweens.add({
            targets: pulse,
            alpha: { from: 1, to: 0.2 },
            duration: ROUTE.pulseMs,
            yoyo: true,
            repeat: -1,
            ease: 'Sine.easeInOut',
          }),
        );
      }
      const g = scene.add.graphics();
      let sheet: Phaser.GameObjects.Image | undefined;
      let glyph: Phaser.GameObjects.GameObject;
      if (useSheet) {
        const col = Math.max(0, NODE_ICON_SHEET.order.indexOf(n.type));
        const row = n.state === 'cleared' ? 1 : n.state === 'passed' || n.state === 'locked' ? 2 : 0;
        sheet = scene.add
          .image(-16, -16, nodeIconKey(scene, si), row * NODE_ICON_SHEET.order.length + col)
          .setOrigin(0, 0);
        glyph = sheet;
      } else glyph = makeGlyph(scene, n.type, si);
      const box = scene.add.container(p.x, p.y, [g, glyph]).setSize(r * 2 + 2, r * 2 + 2);
      const label = new GlowText(scene, 0, 0, n.name, 'page_body', { wrap, align: 'center', stageIndex: si });
      label.placeCenter(p.x, p.y + r + ROUTE.labelGap);
      const view: NodeView = { node: n, x: p.x, y: p.y, box, g, glyph, sheet, label, pulse };
      this.views.push(view);
      this.navNodes.push({ id: n.id, x: p.x, y: p.y });
      if (this.mode === 'choose' && n.state === 'available') this.choices.push(n.id);
      // 입력: 마름모 모양(가장자리 2px 여유). Container 판정은 지역 좌표 + 폭·높이 절반 (glow.ts 참조)
      const half = r + 1;
      const pickable = this.mode === 'view' || n.state === 'available';
      if (pickable) {
        box.setInteractive(
          new Phaser.Geom.Rectangle(half, half, half * 2, half * 2),
          (_a: Phaser.Geom.Rectangle, hx: number, hy: number) => Math.abs(hx - half) + Math.abs(hy - half) <= r + 2,
        );
        if (box.input && this.mode === 'choose') box.input.cursor = 'pointer';
        box.on('pointerover', () => this.select(n.id));
        if (this.mode === 'choose') {
          box.on('pointerdown', () => {
            this.pressed = n.id;
            this.select(n.id);
          });
          box.on('pointerup', () => {
            if (this.pressed === n.id && !this.chosen) this.choose(n.id);
            this.pressed = null;
          });
        }
      }
    }

    // 주인공 표시 (현재 노드 위)
    const cur = this.views.find((v) => v.node.id === route.currentId || v.node.state === 'current');
    if (cur) {
      this.figure = scene.add.graphics();
      drawFigure(this.figure, scene, si);
      this.figureY = cur.y - r - 4 - FIGURE_H;
      this.figure.setPosition(cur.x - FIGURE_W / 2, this.figureY);
      let up = false;
      this.bobTimer = scene.time.addEvent({
        delay: ROUTE.bobMs,
        loop: true,
        callback: () => {
          up = !up;
          this.figure?.setY(this.figureY - (up ? FIG_UNIT : 0));
        },
      });
    }
    this.cursorSprite = cursor(scene).setVisible(false);

    // ---- 아래: 고른 노드 · 범례 · 안내
    y = area.y + ROUTE.labelLift + ROUTE.mapH + 4;
    rule(scene, pg.x + pad, y, pageW - pad * 2);
    y += 4 + 10;
    this.selName = new GlowText(scene, pg.x + pad, y, '', 'page_selected', { scale: 2, stageIndex: si });
    // 범례: 종류 글리프 + 이름 (오른쪽 정렬)
    const legend: UiNodeType[] = ['journey', 'battle', 'shop', 'rest', 'event', 'boss'];
    const items = legend.map((t) => {
      const name = new GlowText(scene, 0, y + 6, nodeTypeName(t, this.opts.shopName), 'page_body', { stageIndex: si });
      return { t, name };
    });
    let lx = right;
    for (let i = items.length - 1; i >= 0; i--) {
      const it = items[i];
      const nx = lx - it.name.displayWidth;
      it.name.setX(nx);
      // 글리프(16×16, 중심 기준으로 만들어진다)는 이름 왼쪽 2px
      const cx = nx - 2 - 8;
      const cy = y + 6 + Math.round(it.name.displayHeight / 2);
      if (useSheet) {
        // 시트가 있으면 범례도 같은 아이콘(32×32, 정수 배율 그대로)
        const col = Math.max(0, NODE_ICON_SHEET.order.indexOf(it.t));
        const ix = nx - 2 - 32;
        scene.add.image(ix, cy - 16, nodeIconKey(scene, si), col).setOrigin(0, 0);
        lx = ix - 10;
        continue;
      }
      const glyph = makeGlyph(scene, it.t, si) as Phaser.GameObjects.GameObject &
        Phaser.GameObjects.Components.Transform;
      glyph.setPosition(glyph.x + cx, glyph.y + cy);
      lx = cx - 8 - 12;
    }
    y += 34;
    this.selDesc = new GlowText(scene, pg.x + pad, y, '', 'page_body', { stageIndex: si });
    this.messageRight = right;
    this.message = new GlowText(scene, 0, y, '', 'page_selected', { stageIndex: si });
    const hint = new GlowText(scene, 0, 0, routeText(this.mode === 'choose' ? 'chooseHint' : 'viewHint'), 'page_faint');
    hint.placeCenter(pg.x + pageW / 2, pg.y + ROUTE.pageH - 14 - hint.displayHeight);

    // 이번에 만든 최상위 객체를 HUD 위로 (같은 depth 는 만든 순서 = 책 → 선 → 노드 → 글 → 커서)
    for (const o of scene.children.list) {
      if (before.has(o)) continue;
      this.objs.push(o);
      if (hasDepth(o)) o.setDepth(ROUTE.depth);
    }
    if (this.cursorSprite) this.cursorSprite.setDepth(ROUTE.depth + 1);
    if (this.figure) this.figure.setDepth(ROUTE.depth + 1);

    // 처음 고른 노드: 고르기 = 첫 available, 보기 = 현재
    debugExpose('routeMap', {
      mode: this.mode,
      nodes: this.views.map((v) => ({ id: v.node.id, x: v.x, y: v.y, state: v.node.state })),
    });
    this.select(this.mode === 'choose' ? (this.choices[0] ?? cur?.node.id ?? null) : (cur?.node.id ?? nodes[0]?.id ?? null));
    if (this.mode === 'choose' && !this.choices.length) this.showMessage(routeText('chooseDenied'));
    this.redraw();
  }

  private select(id: string | null): void {
    if (this.destroyed || !id || id === this.sel) return;
    this.sel = id;
    this.redraw();
  }

  /** 노드 마름모·글리프·이름표·커서·아래 안내를 상태에 맞게 */
  private redraw(): void {
    if (this.destroyed) return;
    const scene = this.scene;
    const si = this.stageIndex;
    const useSheet = this.views.some((v) => v.sheet);
    const r = useSheet ? ROUTE.iconR : ROUTE.nodeR;
    const accentCur = hexToNum(accentHex(scene, si, 22));
    const accentSel = hexToNum(accentHex(scene, si, 20));
    for (const v of this.views) {
      const st = v.node.state;
      const selected = v.node.id === this.sel;
      const g = v.g;
      g.clear();
      if (!v.sheet) {
        // 종이(S3) 위 잉크 마름모: 지나온·지금·갈 수 있는 곳 S1, 지나친·먼 곳 S2
        const fill = st === 'passed' || st === 'locked' ? SEPIA[2] : SEPIA[1];
        pixelDiamond(g, r, hexToNum(fill));
        if (st === 'available') diamondRing(g, r, 1, hexToNum(SEPIA[5]));
        else if (st === 'cleared' || st === 'locked') diamondRing(g, r, 1, hexToNum(SEPIA[4]));
      }
      if (st === 'current') diamondRing(g, r + 2, 2, accentCur);
      else if (selected) diamondRing(g, r + 2, 2, accentSel);
      // 글리프: 지금 = 층 강조 22, 지나온 곳 = 식음, 지나친·먼 곳 = 흐림
      const gl = v.glyph as Phaser.GameObjects.GameObject & Phaser.GameObjects.Components.Alpha;
      if (gl instanceof Phaser.GameObjects.Image) {
        gl.clearTint();
        if (st === 'current' && !v.sheet) gl.setTint(accentCur);
      }
      // 시트는 행(기본·지나옴·잠김)에 식음·흐림이 그려져 있으므로 알파를 더 내리지 않는다
      if (v.sheet) gl.setAlpha(1);
      else gl.setAlpha(st === 'current' || st === 'available' ? 1 : st === 'cleared' ? ROUTE.dimAlpha : ROUTE.faintAlpha);
      v.box.setAlpha(st === 'passed' ? ROUTE.dimAlpha : 1);
      // 이름표
      let style: TextStyleName = 'page_faint';
      if (selected) style = 'page_selected';
      else if (st === 'current') style = 'page_title';
      else if (st === 'available') style = 'page_body';
      v.label.setGlowStyle(style).setAlpha(st === 'passed' ? ROUTE.dimAlpha : 1);
    }
    const sv = this.views.find((v) => v.node.id === this.sel);
    if (sv && this.cursorSprite) this.cursorSprite.setVisible(true).setPosition(sv.x - r - 10, sv.y);
    else this.cursorSprite?.setVisible(false);
    if (sv) {
      this.selName?.setText(sv.node.name);
      this.selDesc?.setText(
        `${nodeTypeName(sv.node.type, this.opts.shopName)} · ${routeText(STATE_KEY[sv.node.state])}`,
      );
    }
  }
}
