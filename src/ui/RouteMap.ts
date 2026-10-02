import Phaser from 'phaser';
import type { UiNodeState, UiNodeType, UiRoute, UiRouteNode } from '../contract/ui';
import { debugExpose } from './debug';
import { GlowText } from './glow';
import {
  ICON,
  KIT,
  NODE_ICON_SHEET,
  NinePanel,
  SLICE,
  accentHex,
  book,
  cursor,
  derivedTexture,
  ensureImage,
  keyartKey,
  keyartUrl,
  mapBgKey,
  mapBgUrl,
  nodeIconKey,
  rule,
} from './kit';
import {
  cycle,
  dottedPoints,
  ellipseRows,
  fitContain,
  layoutOnPath,
  layoutPerspective,
  linkKind,
  sortNodes,
  trapezoidRows,
  type Area,
  type LinkKind,
  type MapPathSpec,
  type PerspectiveLayout,
} from './routeView';
import { regionArtKey } from './regionView';
import { routeText, type RouteTextKey } from './text';
import {
  GRAY,
  MAP3D,
  MAP_BG_FLOORS,
  MAP_ILLUST,
  MAP_PATHS,
  ROUTE,
  SEPIA,
  SIDE_ART,
  type TextStyleName,
  hexToNum,
} from './theme';

import { keyToDir, pickNeighbor, type NavNode } from './warpNav';

/** 양피지 색 (팔레트 세피아 안에서): 바탕·격자 */
const MAP3D_SHEET = { fill: SEPIA[4], grid: SEPIA[3] } as const;

/** 50라운드: 이 층에 지도 그림이 있으면 그 그림 속 길 (없으면 그림 가운데 가로 직선) */
function illustrationPath(floor: number): MapPathSpec | null {
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
  /** 아이콘 중심 (들린 자리) */
  x: number;
  y: number;
  /** 땅에 닿은 점 */
  gx: number;
  gy: number;
  depth: number;
  box: Phaser.GameObjects.Container;
  g: Phaser.GameObjects.Graphics;
  glyph: Phaser.GameObjects.GameObject;
  sheet?: Phaser.GameObjects.Image;
  label: GlowText;
  labelLeft: boolean;
  pulse?: Phaser.GameObjects.Graphics;
}

export type RouteMapMode = 'choose' | 'view';

export interface RouteMapOptions {
  stageIndex: number;
  floorTitle: string;
  shopName?: string;
  /** 노드를 골랐다 ('넘어가시겠습니까?' 에 예 → 뗀 뒤 한 프레임 늦게). 고르기 모드만 */
  onChoose: (id: string) => void;
}

interface ConfirmView {
  id: string;
  objs: Phaser.GameObjects.GameObject[];
  buttons: { box: Phaser.GameObjects.Container; draw: (focus: boolean) => void; text: GlowText }[];
  focus: number;
  armedKey: string | null;
  pressed: number | null;
}

function hasDepth(
  o: Phaser.GameObjects.GameObject,
): o is Phaser.GameObjects.GameObject & { setDepth(d: number): unknown } {
  return typeof (o as { setDepth?: unknown }).setDepth === 'function';
}

/** 입력 이벤트 시각 (없으면 0 = 거르지 않음) */
function eventStamp(pointer?: Phaser.Input.Pointer): number {
  const t = pointer?.event?.timeStamp;
  return typeof t === 'number' ? t : 0;
}

/** 아이콘 반 크기 (시트 32×32) */
const ICON_HALF = 16;

/**
 * 노드 지도 (48라운드 계약 §10, 49라운드 §11 — M 지도 + 위치 정보 + 넘어가기 확인). HUD 씬 위 일기장 한 페이지 (depth 100~).
 * 왼쪽: 펼친 양피지 위 입체 지도 — 진행은 아래(가까움) → 위(멂), 같은 단계의 갈래는 좌우. 멀수록 작고 촘촘하게,
 *   노드는 땅에서 살짝 들린 표지(아이콘 + 기둥 + 그림자), 길은 땅 위 점선(가까울수록 굵게).
 *   50라운드: `assets/ui/map_bg_<floor>.png` 가 있는 층(theme `MAP_BG_FLOORS`)은 **일러스트 좌표계 우선** — 그림을 비율 유지로
 *   깔고(사다리꼴·원근 대신) 노드를 그림 속 길(`MAP_PATHS`)에 맞춰 놓는다. 깊이(들림·그림자 크기)는 그림 위쪽일수록 멂(약하게).
 *   오른쪽 위치 정보 칸 뒤에는 지금 지역 키아트를 어둡게 깐다. 큰 그림은 처음 필요할 때 읽고, 늦게 오면 그 자리에 끼운다.
 * 오른쪽: 지금 있는 곳(지역·이름·종류·설명) / 살펴보는(고른) 곳 / 범례.
 * - 'choose': ROUTE_CHOOSE_OPEN. available 노드를 고르면 '넘어가시겠습니까?' 확인 → 예일 때만 onChoose.
 * - 'view': M·Tab 보기 전용. 방향키로 둘러보기만.
 */
export class RouteMap {
  private objs: Phaser.GameObjects.GameObject[] = [];
  private extra: Phaser.GameObjects.GameObject[] = [];
  private views: NodeView[] = [];
  private sel: string | null = null;
  private stageIndex: number;
  private cursorSprite?: Phaser.GameObjects.Sprite;
  private figure?: Phaser.GameObjects.Graphics;
  private figureY = 0;
  private bobTimer?: Phaser.Time.TimerEvent;
  private tweens: Phaser.Tweens.Tween[] = [];
  private lookTitle?: GlowText;
  private selName?: GlowText;
  private selMeta?: GlowText;
  private selDesc?: GlowText;
  private message?: GlowText;
  private armedKey: string | null = null;
  private pressed: string | null = null;
  private chosen = false;
  private destroyed = false;
  private choices: string[] = [];
  private navNodes: NavNode[] = [];
  private messageRight = 0;
  private currentId: string | null = null;
  private confirm?: ConfirmView;
  private mapArea = { x: 0, y: 0, w: 0, h: 0 };
  /**
   * 확인 창을 열고 닫게 한 입력 이벤트의 시각 (event.timeStamp). 그 시각 이전(같은 이벤트 포함)의 키 이벤트는 무시한다 —
   * 프레임이 밀리면 Phaser 가 같은 키 이벤트를 다시 넘겨, 확인 창을 연 Enter 가 곧바로 '예' 로 먹히는 일이 있었다
   * (49라운드 헤드리스 확인). 처리 시각이 아니라 이벤트 시각을 쓰므로 밀린 동안 새로 누른 키는 살아남는다.
   */
  private inputAfter = 0;
  private bookRect = { x: 0, y: 0, w: 0, h: 0 };

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

  /** '넘어가시겠습니까?' 확인 창이 떠 있는가 */
  get confirmOpen(): boolean {
    return Boolean(this.confirm);
  }

  /** 거부 사유 등 짧은 글 (오른쪽 아래) */
  showMessage(text: string): void {
    if (this.destroyed || !this.message) return;
    this.message.setText(text).placeRight(this.messageRight, this.message.y);
  }

  destroy(): void {
    if (this.destroyed) return;
    this.closeConfirm();
    this.destroyed = true;
    this.scene.input.keyboard?.off('keydown', this.onKeyDown);
    this.scene.input.keyboard?.off('keyup', this.onKeyUp);
    this.bobTimer?.remove();
    for (const t of this.tweens) t.remove();
    this.tweens = [];
    for (const o of this.objs) o.destroy();
    for (const o of this.extra) o.destroy();
    this.objs = [];
    this.extra = [];
    this.views = [];
    debugExpose('routeMap', null);
  }

  // -------------------------------------------------------------------------------------------
  private stale(e: KeyboardEvent): boolean {
    return typeof e.timeStamp === 'number' && e.timeStamp > 0 && e.timeStamp <= this.inputAfter;
  }

  private onKeyDown = (e: KeyboardEvent): void => {
    if (this.destroyed || this.stale(e)) return;
    if (this.confirm) {
      this.confirmKeyDown(e);
      return;
    }
    if (this.chosen) return;
    const dir = keyToDir(e.key);
    if (dir) {
      if (this.mode === 'choose') {
        // 고를 곳은 보통 다음 단계 한 줄(좌우)이라 ←↑ = 앞, →↓ = 뒤 로 돌아가며 고른다
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
    if (this.destroyed || this.stale(e)) return;
    if (this.confirm) {
      this.confirmKeyUp(e);
      return;
    }
    if (this.chosen) return;
    if (e.key === this.armedKey) {
      this.armedKey = null;
      if (this.sel && this.choices.includes(this.sel)) this.openConfirm(this.sel, e.timeStamp);
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
    const pageH = ROUTE.pageH;
    this.currentId = route.currentId;

    // 배경 어둡게 + 클릭 막기 (페이지 밖 클릭이 게임 씬으로 내려가지 않게)
    scene.add.rectangle(0, 0, W, H, hexToNum(GRAY[0]), ROUTE.dimAlpha).setOrigin(0, 0).setInteractive();
    const bk = book(scene, Math.round(W / 2), Math.round(H / 2), pageW, pageH, 1, 'route');
    this.bookRect = { x: bk.x, y: bk.y, w: bk.w, h: bk.h };
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
    y += 4 + 6;

    // ---- 칸 나누기: 왼쪽 지도, 오른쪽 위치 정보
    const mapW = pageW - pad * 2 - MAP3D.sideW - MAP3D.sideGap;
    const bottom = pg.y + pageH - MAP3D.hintH - 6;
    const area = { x: pg.x + pad, y, w: mapW, h: bottom - y };
    this.mapArea = area;
    const sideX = area.x + mapW + MAP3D.sideGap;

    const nodes = sortNodes(route.nodes);
    const illust = illustrationPath(route.floor);
    let L: PerspectiveLayout;
    if (illust) {
      // 50라운드: 일러스트 좌표계 우선 — 그림을 비율 유지로 깔고 그 위 길에 노드를 놓는다
      const rect = fitContain(area, illust.srcW, illust.srcH);
      L = layoutOnPath(nodes, rect, illust);
      this.drawIllustration(rect, route.floor);
    } else {
      L = layoutPerspective(nodes, area, {
        rowMax: MAP3D.rowMax,
        farScale: MAP3D.farScale,
        ease: MAP3D.ease,
        minGap: MAP3D.minGap,
        padTop: MAP3D.padTop,
        padBottom: MAP3D.padBottom,
      });
      this.drawSheet(area, L.yAt);
    }

    const useSheet = NODE_ICON_SHEET.available && scene.textures.exists(NODE_ICON_SHEET.key);
    const r = useSheet ? ROUTE.iconR : ROUTE.nodeR;
    const byId = new Map(nodes.map((n) => [n.id, n]));
    const liftAt = (scale: number): number =>
      Math.round(MAP3D.liftFar + (MAP3D.liftNear - MAP3D.liftFar) * ((scale - L.farScale) / (1 - L.farScale || 1)));
    const shadowAt = (scale: number) => ({
      rx: Math.max(6, Math.round(MAP3D.shadowRx * scale)),
      ry: Math.max(2, Math.round(MAP3D.shadowRy * scale)),
    });

    // ---- 길 (땅 위 점선, 노드보다 먼저 = 아래)
    const lg = scene.add.graphics();
    const dotColor: Record<LinkKind, number> = {
      walked: hexToNum(SEPIA[0]),
      option: hexToNum(accentHex(scene, si, 22)),
      faint: hexToNum(SEPIA[2]),
    };
    for (const a of nodes) {
      const pa = L.pos.get(a.id);
      if (!pa) continue;
      for (const bid of a.links) {
        const b = byId.get(bid);
        const pb = b && L.pos.get(bid);
        if (!b || !pb) continue;
        const kind = linkKind(a.state, b.state);
        const depth = (pa.depth + pb.depth) / 2;
        const scale = (pa.scale + pb.scale) / 2;
        const dot = depth < MAP3D.nearDotDepth ? 3 : 2;
        const step = Math.round((kind === 'faint' ? ROUTE.dotStepFaint : ROUTE.dotStep + 1) * (0.6 + 0.4 * scale));
        lg.fillStyle(dotColor[kind], 1);
        const trimA = shadowAt(pa.scale).rx + 2;
        const trimB = shadowAt(pb.scale).rx + 2;
        const pts = dottedPoints(pa.x, pa.y, pb.x, pb.y, trimA, trimB, Math.max(4, step));
        if (illust) {
          // 어두운 그림 위: 점마다 S0 테두리 1px 를 먼저 깔고, 지나온 길은 S5(밝게)로
          const rim = MAP_ILLUST.dotRim;
          lg.fillStyle(hexToNum(SEPIA[0]), 1);
          for (const p of pts)
            lg.fillRect(p.x - Math.floor(dot / 2) - rim, p.y - Math.floor(dot / 2) - rim, dot + rim * 2, dot + rim * 2);
          lg.fillStyle(kind === 'walked' ? hexToNum(SEPIA[5]) : dotColor[kind], 1);
        }
        for (const p of pts) lg.fillRect(p.x - Math.floor(dot / 2), p.y - Math.floor(dot / 2), dot, dot);
      }
    }

    // ---- 노드: 먼 것부터 (가까운 것이 위에 겹친다). 그림자 → 기둥 → Container(Graphics → 아이콘) (버튼 규약)
    const order = [...nodes].sort((a, b) => (L.pos.get(b.id)?.depth ?? 0) - (L.pos.get(a.id)?.depth ?? 0));
    const shadowColor = hexToNum(SEPIA[1]);
    for (const n of order) {
      const p = L.pos.get(n.id);
      if (!p) continue;
      const lift = liftAt(p.scale);
      const sh = shadowAt(p.scale);
      const ix = p.x;
      const iy = p.y - lift - ICON_HALF;
      const base = scene.add.graphics();
      base.fillStyle(shadowColor, 1);
      for (const row of ellipseRows(p.x, p.y, sh.rx, sh.ry)) base.fillRect(row.x, row.y, row.w, 1);
      // 기둥: 아이콘 아래 꼭짓점에서 땅까지 2px
      base.fillRect(p.x - 1, iy + ICON_HALF - 2, 2, lift + 2);
      let pulse: Phaser.GameObjects.Graphics | undefined;
      if (n.state === 'available') {
        pulse = scene.add.graphics({ x: ix, y: iy });
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
          .image(-ICON_HALF, -ICON_HALF, nodeIconKey(scene, si), row * NODE_ICON_SHEET.order.length + col)
          .setOrigin(0, 0);
        glyph = sheet;
      } else glyph = makeGlyph(scene, n.type, si);
      const box = scene.add.container(ix, iy, [g, glyph]).setSize(r * 2 + 2, r * 2 + 2);
      // 이름표: 아이콘 오른쪽 (지도 칸 오른쪽을 넘으면 왼쪽)
      const label = new GlowText(scene, 0, 0, n.name, 'page_body', { wrap: MAP3D.labelWrap, stageIndex: si });
      const lx = ix + ICON_HALF + MAP3D.labelGap;
      const labelLeft = lx + label.displayWidth > area.x + area.w;
      if (labelLeft) label.setPosition(ix - ICON_HALF - MAP3D.labelGap - label.displayWidth, iy - 8);
      else label.setPosition(lx, iy - 8);
      const view: NodeView = {
        node: n,
        x: ix,
        y: iy,
        gx: p.x,
        gy: p.y,
        depth: p.depth,
        box,
        g,
        glyph,
        sheet,
        label,
        labelLeft,
        pulse,
      };
      this.views.push(view);
      this.navNodes.push({ id: n.id, x: ix, y: iy });
      // 입력: 마름모 모양(가장자리 2px 여유). Container 판정은 지역 좌표 + 폭·높이 절반 (glow.ts 참조)
      const half = r + 1;
      const pickable = this.mode === 'view' || n.state === 'available';
      if (pickable) {
        box.setInteractive(
          new Phaser.Geom.Rectangle(half, half, half * 2, half * 2),
          (_a: Phaser.Geom.Rectangle, hx: number, hy: number) => Math.abs(hx - half) + Math.abs(hy - half) <= r + 2,
        );
        if (box.input && this.mode === 'choose') box.input.cursor = 'pointer';
        box.on('pointerover', () => {
          if (!this.confirm) this.select(n.id);
        });
        if (this.mode === 'choose') {
          box.on('pointerdown', () => {
            if (this.confirm) return;
            this.pressed = n.id;
            this.select(n.id);
          });
          box.on('pointerup', (pointer: Phaser.Input.Pointer) => {
            if (!this.confirm && this.pressed === n.id && !this.chosen) this.openConfirm(n.id, eventStamp(pointer));
            this.pressed = null;
          });
        }
      }
    }
    // 고르기 순서는 단계 → 줄 (좌→우)
    if (this.mode === 'choose') this.choices = nodes.filter((n) => n.state === 'available').map((n) => n.id);

    // 주인공 표시 (현재 노드 왼쪽, 발이 땅에)
    const cur =
      this.views.find((v) => v.node.id === route.currentId) ?? this.views.find((v) => v.node.state === 'current');
    if (cur) {
      this.figure = scene.add.graphics();
      drawFigure(this.figure, scene, si);
      this.figureY = cur.gy - FIGURE_H + 1;
      this.figure.setPosition(cur.x - ICON_HALF - 4 - FIGURE_W, this.figureY);
      // 이름표가 왼쪽으로 넘어간 지금 노드(지도 오른쪽 끝, 예: 보스)는 주인공 표시 왼쪽으로 더 비킨다
      if (cur.labelLeft) cur.label.setX(cur.label.x - FIGURE_W - 4);
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

    // ---- 오른쪽 위치 정보
    this.buildSide(sideX, area.y, MAP3D.sideW, bottom, cur?.node ?? null);

    // ---- 아래 안내 줄
    const hint = new GlowText(scene, 0, 0, routeText(this.mode === 'choose' ? 'chooseHint' : 'viewHint'), 'page_faint');
    const hy = pg.y + pageH - 12 - hint.displayHeight;
    hint.placeCenter(area.x + mapW / 2, hy);
    this.messageRight = right;
    this.message = new GlowText(scene, 0, hy, '', 'page_selected', { stageIndex: si });

    // 이번에 만든 최상위 객체를 HUD 위로 (같은 depth 는 만든 순서 = 책 → 양피지 → 길 → 노드 → 글 → 커서)
    for (const o of scene.children.list) {
      if (before.has(o)) continue;
      this.objs.push(o);
      if (hasDepth(o)) o.setDepth(ROUTE.depth);
    }
    if (this.cursorSprite) this.cursorSprite.setDepth(ROUTE.depth + 1);
    if (this.figure) this.figure.setDepth(ROUTE.depth + 1);

    debugExpose('routeMap', {
      mode: this.mode,
      nodes: this.views.map((v) => ({ id: v.node.id, x: v.x, y: v.y, state: v.node.state })),
      confirm: null,
    });
    this.select(
      this.mode === 'choose' ? (this.choices[0] ?? cur?.node.id ?? null) : (cur?.node.id ?? nodes[0]?.id ?? null),
    );
    if (this.mode === 'choose' && !this.choices.length) this.showMessage(routeText('chooseDenied'));
    this.redraw();
  }

  /**
   * 펼친 양피지 (계단식 사다리꼴, 아래가 넓고 위가 좁다 = 멀어짐): 그림자 → 바탕 → 지평선 격자 → 말린 위·아래 가장자리 → 테두리.
   * 지도 배경 일러스트가 있으면 바탕·격자 대신 그 그림을 사다리꼴로 잘라 깐다.
   */
  private drawSheet(area: { x: number; y: number; w: number; h: number }, yAt: (d: number) => number): void {
    const scene = this.scene;
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
    for (const r of rows.slice(rows.length - roll))
      g.fillStyle(hexToNum(SEPIA[2]), 1).fillRect(r.x - 1, r.y, r.w + 2, 1);
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
  private drawIllustration(rect: Area, floor: number): void {
    const scene = this.scene;
    const g = scene.add.graphics();
    g.fillStyle(hexToNum(SEPIA[0]), 0.55).fillRect(
      rect.x + MAP_ILLUST.shadow,
      rect.y + MAP_ILLUST.shadow,
      rect.w,
      rect.h,
    );
    g.fillStyle(hexToNum(SEPIA[1]), 1).fillRect(rect.x, rect.y, rect.w, rect.h);
    const place = (): void => {
      if (this.destroyed) return;
      const key = derivedTexture(scene, mapBgKey(floor), rect.w, rect.h, 'stretch');
      if (!key) return;
      const img = scene.add.image(rect.x, rect.y, key).setOrigin(0, 0);
      this.insertLate(img, g, 'above');
    };
    const frame = scene.add.graphics();
    frame.lineStyle(1, hexToNum(SEPIA[0]), 1).strokeRect(rect.x - 0.5, rect.y - 0.5, rect.w + 1, rect.h + 1);
    if (scene.textures.exists(mapBgKey(floor))) place();
    else ensureImage(scene, mapBgKey(floor), mapBgUrl(floor), (ok) => ok && place());
  }

  /**
   * 늦게 만든 객체를 기준 객체 바로 위(above)·아래(below)에 끼운다 (같은 depth 안의 표시 순서).
   * 지도를 만드는 중이면(build 끝에서 depth 를 줄 것이므로) 순서만 맞춘다.
   */
  private insertLate(
    o: Phaser.GameObjects.GameObject & { setDepth(d: number): unknown },
    anchor: Phaser.GameObjects.GameObject,
    where: 'above' | 'below',
  ): void {
    const list = this.scene.children;
    if (where === 'above') list.moveAbove(o, anchor);
    else list.moveBelow(o, anchor);
    if (this.objs.length) {
      o.setDepth(ROUTE.depth);
      this.objs.push(o);
    }
  }

  /**
   * 50라운드: 오른쪽 위치 정보 칸 뒤 지금 지역 키아트 (가운데를 잘라 덮고 G00 α0.55 로 두 번 어둡게) + 테두리 S1.
   * 키아트가 없는 지역이면 그리지 않는다. 아직 안 읽었으면 읽기 시작하고 오면 테두리 아래에 끼운다.
   */
  private drawSideArt(rect: Area, region: string | undefined): void {
    const art = regionArtKey(region);
    if (!art) return;
    const scene = this.scene;
    const frame = scene.add.graphics();
    frame.lineStyle(1, hexToNum(SEPIA[1]), 1).strokeRect(rect.x + 0.5, rect.y + 0.5, rect.w - 1, rect.h - 1);
    const src = keyartKey(art);
    const place = (): void => {
      if (this.destroyed) return;
      const key = derivedTexture(scene, src, rect.w, rect.h, 'cover', SIDE_ART.darken);
      if (!key) return;
      this.insertLate(scene.add.image(rect.x, rect.y, key).setOrigin(0, 0), frame, 'below');
    };
    if (scene.textures.exists(src)) place();
    else ensureImage(scene, src, keyartUrl(art), (ok) => ok && place());
  }

  /** 오른쪽 칸: 지금 있는 곳 · 살펴보는(고른) 곳 · 범례 */
  private buildSide(x: number, top: number, w: number, bottom: number, here: UiRouteNode | null): void {
    const scene = this.scene;
    const si = this.stageIndex;
    const useSheetIcons = NODE_ICON_SHEET.available && scene.textures.exists(NODE_ICON_SHEET.key);
    const legendTop = bottom - (useSheetIcons ? 34 : 22) * 3 - 8;
    // 50라운드: 범례 위까지 지금 지역 키아트를 어둡게 (글자보다 먼저 = 아래)
    this.drawSideArt(
      {
        x: x - SIDE_ART.padX,
        y: top - SIDE_ART.padY,
        w: w + SIDE_ART.padX * 2,
        h: legendTop - SIDE_ART.padY - (top - SIDE_ART.padY),
      },
      here?.region,
    );
    let y = top;
    const head = new GlowText(scene, x, y, routeText('hereTitle'), 'page_faint');
    y += head.displayHeight + 2;
    if (here) {
      if (here.region) {
        const reg = new GlowText(scene, x, y, here.region, 'page_title', { scale: 2, stageIndex: si });
        y += reg.displayHeight + 2;
      }
      const nm = new GlowText(
        scene,
        x,
        y,
        `${here.name} · ${nodeTypeName(here.type, this.opts.shopName)}`,
        here.region ? 'page_body' : 'page_title',
        { wrap: w, stageIndex: si },
      );
      y += nm.displayHeight + 2;
      if (here.desc) {
        const d = new GlowText(scene, x, y, here.desc, 'page_body', { wrap: w, stageIndex: si });
        y += d.displayHeight;
      }
    } else {
      const none = new GlowText(scene, x, y, '―', 'page_body', { stageIndex: si });
      y += none.displayHeight;
    }
    y += 6;
    rule(scene, x, y, w);
    y += 4 + 8;
    this.lookTitle = new GlowText(scene, x, y, '', 'page_faint');
    y += 16;
    this.selName = new GlowText(scene, x, y, '', 'page_selected', { wrap: w, stageIndex: si });
    this.selMeta = new GlowText(scene, x, y, '', 'page_body', { wrap: w, stageIndex: si });
    this.selDesc = new GlowText(scene, x, y, '', 'page_faint', { wrap: w });

    // 범례 (아래에 붙임): 2열 × 3줄, 아이콘 + 종류 이름
    const legend: UiNodeType[] = ['journey', 'battle', 'shop', 'rest', 'event', 'boss'];
    const useSheet = NODE_ICON_SHEET.available && scene.textures.exists(NODE_ICON_SHEET.key);
    const rowH = useSheet ? 34 : 22;
    const ly0 = bottom - rowH * 3;
    rule(scene, x, ly0 - 8, w);
    legend.forEach((t, i) => {
      const lx = x + (i % 2) * Math.floor(w / 2);
      const ly = ly0 + Math.floor(i / 2) * rowH;
      const iw = useSheet ? 32 : 16;
      if (useSheet) {
        const col = Math.max(0, NODE_ICON_SHEET.order.indexOf(t));
        scene.add.image(lx, ly, nodeIconKey(scene, si), col).setOrigin(0, 0);
      } else {
        const glyph = makeGlyph(scene, t, si) as Phaser.GameObjects.GameObject &
          Phaser.GameObjects.Components.Transform;
        glyph.setPosition(glyph.x + lx + 8, glyph.y + ly + 8);
      }
      new GlowText(
        scene,
        lx + iw + 4,
        ly + Math.round((useSheet ? 32 : 16) / 2) - 8,
        nodeTypeName(t, this.opts.shopName),
        'page_body',
        {
          stageIndex: si,
        },
      );
    });
  }

  private select(id: string | null): void {
    if (this.destroyed || !id || id === this.sel) return;
    this.sel = id;
    this.redraw();
  }

  /** 노드 고리·아이콘·이름표·커서·오른쪽 '살펴보는 곳' 을 상태에 맞게 */
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
        // 종이 위 잉크 마름모: 지나온·지금·갈 수 있는 곳 S1, 지나친·먼 곳 S2
        const fillC = st === 'passed' || st === 'locked' ? SEPIA[2] : SEPIA[1];
        pixelDiamond(g, r, hexToNum(fillC));
        if (st === 'available') diamondRing(g, r, 1, hexToNum(SEPIA[5]));
        else if (st === 'cleared' || st === 'locked') diamondRing(g, r, 1, hexToNum(SEPIA[4]));
      }
      if (st === 'current') diamondRing(g, r + 2, 2, accentCur);
      else if (selected) diamondRing(g, r + 2, 2, accentSel);
      const gl = v.glyph as Phaser.GameObjects.GameObject & Phaser.GameObjects.Components.Alpha;
      if (gl instanceof Phaser.GameObjects.Image) {
        gl.clearTint();
        if (st === 'current' && !v.sheet) gl.setTint(accentCur);
      }
      if (v.sheet) gl.setAlpha(1);
      else
        gl.setAlpha(st === 'current' || st === 'available' ? 1 : st === 'cleared' ? ROUTE.dimAlpha : ROUTE.faintAlpha);
      v.box.setAlpha(st === 'passed' ? ROUTE.dimAlpha : 1);
      // 이름표: 지금·갈 수 있는 곳·고른 곳만 (멀리 있는 곳은 아이콘과 오른쪽 칸으로 읽는다)
      const showLabel = selected || st === 'current' || st === 'available';
      let style: TextStyleName = 'page_body';
      if (selected) style = 'page_selected';
      else if (st === 'current') style = 'page_title';
      v.label.setVisible(showLabel).setGlowStyle(style);
    }
    const sv = this.views.find((v) => v.node.id === this.sel);
    if (sv && this.cursorSprite) {
      // 커서 촉: 아이콘 고리 왼쪽. 지금 노드는 왼쪽에 주인공이 서 있으므로 고리만
      this.cursorSprite.setVisible(sv.node.id !== this.currentId).setPosition(sv.x - r - 8, sv.y);
    } else this.cursorSprite?.setVisible(false);
    // 오른쪽 '살펴보는(고른) 곳': 지금 있는 곳과 같으면 비운다
    const showSel = Boolean(sv) && sv!.node.id !== this.currentId;
    this.lookTitle?.setText(showSel ? routeText(this.mode === 'choose' ? 'pickTitle' : 'lookTitle') : '');
    if (sv && showSel && this.selName && this.selMeta && this.selDesc) {
      const n = sv.node;
      this.selName.setText(n.name);
      const meta = [n.region, nodeTypeName(n.type, this.opts.shopName), routeText(STATE_KEY[n.state])].filter(Boolean);
      this.selMeta.setText(meta.join(' · ')).setY(this.selName.y + this.selName.displayHeight + 2);
      this.selDesc.setText(n.desc ?? '').setY(this.selMeta.y + this.selMeta.displayHeight + 2);
    } else {
      this.selName?.setText('');
      this.selMeta?.setText('');
      this.selDesc?.setText('');
    }
  }

  // -------------------------------------------------------------------------------------------
  // 49라운드: '넘어가시겠습니까?' 확인 (예일 때만 onChoose)
  private openConfirm(id: string, stamp: number): void {
    if (this.destroyed || this.confirm || this.mode !== 'choose') return;
    const v = this.views.find((x) => x.node.id === id);
    if (!v) return;
    const scene = this.scene;
    const si = this.stageIndex;
    const before = new Set(scene.children.list);
    const b = this.bookRect;
    // 페이지 위를 살짝 어둡게 + 아래 노드 클릭 막기
    scene.add.rectangle(b.x, b.y, b.w, b.h, hexToNum(GRAY[0]), MAP3D.confirmDim).setOrigin(0, 0).setInteractive();
    const cw = MAP3D.confirmW;
    const ch = MAP3D.confirmH;
    const cx = Math.round(this.mapArea.x + this.mapArea.w / 2 - cw / 2);
    const cy = Math.round(this.mapArea.y + this.mapArea.h / 2 - ch / 2);
    new NinePanel(scene, cx, cy, KIT.panelPaper, SLICE.panelPaper, cw, ch);
    let y = cy + 14;
    const title = new GlowText(scene, 0, y, routeText('confirmTitle'), 'page_title', { font: 'title', stageIndex: si });
    title.placeCenter(cx + cw / 2, y);
    y += title.displayHeight + 2;
    const where = [v.node.region, v.node.name].filter(Boolean).join(' · ');
    new GlowText(scene, 0, y, where, 'page_selected', { stageIndex: si }).placeCenter(cx + cw / 2, y);
    y += 20;
    const labels = [routeText('confirmYes'), routeText('confirmNo')];
    const texts = labels.map((t) => new GlowText(scene, 0, 0, t, 'page_body', { stageIndex: si }));
    const bw = Math.max(MAP3D.buttonMinW, ...texts.map((t) => t.displayWidth + 16));
    const bh = MAP3D.buttonH;
    const total = bw * 2 + MAP3D.buttonGap;
    const bx0 = Math.round(cx + cw / 2 - total / 2);
    const buttons: ConfirmView['buttons'] = [];
    texts.forEach((t, i) => {
      const g = scene.add.graphics();
      t.setPosition(Math.round(bw / 2 - t.displayWidth / 2), Math.round(bh / 2 - t.displayHeight / 2));
      const draw = (focus: boolean): void => {
        g.clear();
        g.fillStyle(hexToNum(SEPIA[1]), 1).fillRect(0, 0, bw, bh);
        g.lineStyle(focus ? 2 : 1, focus ? hexToNum(accentHex(scene, si, 20)) : hexToNum(SEPIA[4]), 1);
        if (focus) g.strokeRect(1, 1, bw - 2, bh - 2);
        else g.strokeRect(0.5, 0.5, bw - 1, bh - 1);
        t.setGlowStyle(focus ? 'page_selected' : 'page_unsel');
      };
      // 버튼 규약: Container → Graphics → 글자
      const box = scene.add.container(bx0 + i * (bw + MAP3D.buttonGap), y, [g, t]).setSize(bw, bh);
      box.setInteractive(new Phaser.Geom.Rectangle(bw / 2, bh / 2, bw, bh), Phaser.Geom.Rectangle.Contains);
      if (box.input) box.input.cursor = 'pointer';
      box.on('pointerover', () => this.focusConfirm(i));
      box.on('pointerdown', () => {
        if (this.confirm) this.confirm.pressed = i;
        this.focusConfirm(i);
      });
      box.on('pointerup', (pointer: Phaser.Input.Pointer) => {
        if (this.confirm?.pressed === i) this.answerConfirm(i === 0, eventStamp(pointer));
        else if (this.confirm) this.confirm.pressed = null;
      });
      buttons.push({ box, draw, text: t });
    });
    y += bh + 8;
    const hint = new GlowText(scene, 0, y, routeText('confirmHint'), 'page_faint');
    hint.placeCenter(cx + cw / 2, y);
    const objs: Phaser.GameObjects.GameObject[] = [];
    for (const o of scene.children.list) {
      if (before.has(o)) continue;
      objs.push(o);
      if (hasDepth(o)) o.setDepth(ROUTE.depth + 5);
    }
    this.armedKey = null;
    this.pressed = null;
    this.inputAfter = stamp;
    this.confirm = { id, objs, buttons, focus: 0, armedKey: null, pressed: null };
    this.focusConfirm(0, true);
    debugExpose('routeMap', {
      mode: this.mode,
      nodes: this.views.map((x) => ({ id: x.node.id, x: x.x, y: x.y, state: x.node.state })),
      confirm: {
        id,
        yes: { x: buttons[0].box.x + bw / 2, y: buttons[0].box.y + bh / 2 },
        no: { x: buttons[1].box.x + bw / 2, y: buttons[1].box.y + bh / 2 },
      },
    });
  }

  private focusConfirm(i: number, force = false): void {
    const c = this.confirm;
    if (!c || (!force && c.focus === i)) return;
    c.focus = i;
    c.buttons.forEach((b, k) => b.draw(k === i));
  }

  private confirmKeyDown(e: KeyboardEvent): void {
    const c = this.confirm;
    if (!c) return;
    if (e.key === 'Escape' || e.key === 'n' || e.key === 'N') {
      this.answerConfirm(false, e.timeStamp);
      return;
    }
    if (e.repeat) return;
    if (e.key === 'Enter' || e.key === ' ') {
      c.armedKey = e.key;
      return;
    }
    if (e.key === 'y' || e.key === 'Y') {
      this.focusConfirm(0);
      c.armedKey = e.key;
      return;
    }
    const dir = keyToDir(e.key);
    if (dir && dir.dx !== 0) this.focusConfirm(c.focus === 0 ? 1 : 0);
  }

  private confirmKeyUp(e: KeyboardEvent): void {
    const c = this.confirm;
    if (!c || e.key !== c.armedKey) return;
    c.armedKey = null;
    this.answerConfirm(c.focus === 0, e.timeStamp);
  }

  private answerConfirm(yes: boolean, stamp: number): void {
    const c = this.confirm;
    if (!c) return;
    const id = c.id;
    this.closeConfirm(stamp);
    if (yes) this.choose(id);
  }

  private closeConfirm(stamp = 0): void {
    const c = this.confirm;
    if (!c) return;
    this.confirm = undefined;
    this.inputAfter = Math.max(this.inputAfter, stamp);
    this.armedKey = null;
    for (const o of c.objs) o.destroy();
    if (!this.destroyed)
      debugExpose('routeMap', {
        mode: this.mode,
        nodes: this.views.map((x) => ({ id: x.node.id, x: x.x, y: x.y, state: x.node.state })),
        confirm: null,
      });
  }
}
