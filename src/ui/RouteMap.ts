import Phaser from 'phaser';
import { UI_SCREEN, type UiRoute, type UiRouteNode } from '../contract/ui';
import { nodeLook } from './bundleView';
import { debugExpose } from './debug';
import { GlowText } from './glow';
import { NODE_ICON_SHEET, accentHex, book, cursor, nodeIconKey, rule } from './kit';
import { RouteConfirm, eventStamp, hasDepth } from './RouteConfirm';
import { gradeMark, rewardBadge, riskBadge, riskRing, smudgeMark } from './routeMarks';
import { FIGURE_H, FIGURE_W, FIG_UNIT, diamondRing, drawFigure, makeGlyph, pixelDiamond } from './routeGlyph';
import { drawIllustration, drawSheet, illustrationPath, type LateInsert } from './routeSheet';
import { RouteSide } from './RouteSide';
import {
  cycle,
  dottedPoints,
  ellipseRows,
  fitContain,
  layoutOnPath,
  layoutPerspective,
  linkKind,
  sortNodes,
  type LinkKind,
  type PerspectiveLayout,
} from './routeView';
import { routeText } from './text';
import { GRAY, MAP3D, MAP_ILLUST, ROUTE, SEPIA, type TextStyleName, hexToNum } from './theme';
import { keyToDir, pickNeighbor, type NavNode } from './warpNav';
import { placeLabels, type Rect } from './routeLabels';
import { MARKS } from './themeBuild';

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
  /** 61라운드: 이 노드의 표지(보상·위험·도장) 자리 — 이름표가 피한다 */
  marks: Rect[];
  pulse?: Phaser.GameObjects.Graphics;
  /** 60라운드 §14.5: 숨은 노드 얼룩(smudge·located) — 아이콘·고리 없이 얼룩만 */
  smudge: boolean;
  /** §14.5: 위험 노드 (붉은 테두리) */
  risk: boolean;
}

export type RouteMapMode = 'choose' | 'view';

export interface RouteMapOptions {
  stageIndex: number;
  floorTitle: string;
  shopName?: string;
  /** 노드를 골랐다 ('넘어가시겠습니까?' 에 예 → 뗀 뒤 한 프레임 늦게). 고르기 모드만 */
  onChoose: (id: string) => void;
}

/** 아이콘 반 크기 (시트 32×32) */
const ICON_HALF = 16;

/**
 * 노드 지도 (48라운드 계약 §10, 49라운드 §11 — M 지도 + 위치 정보 + 넘어가기 확인). HUD 씬 위 일기장 한 페이지 (depth 100~).
 * 왼쪽: 펼친 양피지 위 입체 지도 — 진행은 아래(가까움) → 위(멂), 같은 단계의 갈래는 좌우. 멀수록 작고 촘촘하게,
 *   노드는 땅에서 살짝 들린 표지(아이콘 + 기둥 + 그림자), 길은 땅 위 점선(가까울수록 굵게).
 *   50라운드: `assets/ui/map_bg_<floor>.png` 가 있는 층(theme `MAP_BG_FLOORS`)은 **일러스트 좌표계 우선**(routeSheet.ts).
 *   60라운드 §14.5: 보상 미리보기 표(아이콘 오른쪽 아래)·위험 노드(붉은 테두리 + 표)·숨은 노드 얼룩·성과 도장(routeMarks.ts).
 * 오른쪽: 지금 있는 곳 / 살펴보는(고른) 곳(+ 보상·위험·접두어·이벤트 내용·도장) / 보상 범례·산 지도 정보 / 범례 (RouteSide.ts).
 * - 'choose': ROUTE_CHOOSE_OPEN. available 노드를 고르면 '넘어가시겠습니까?' 확인(RouteConfirm.ts, 위험 노드면 위험 한 줄)
 *   → 예일 때만 onChoose. Esc(확인 창이 없을 때)는 HUD 가 받아 지도를 닫고 `cancelChoose()` (53라운드 Q47).
 * - 'view': M·Tab 보기 전용. 방향키로 둘러보기만 (숨은 노드 얼룩도 살펴볼 수 있다).
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
  private side?: RouteSide;
  private message?: GlowText;
  private armedKey: string | null = null;
  private pressed: string | null = null;
  private chosen = false;
  private destroyed = false;
  private choices: string[] = [];
  private navNodes: NavNode[] = [];
  private messageRight = 0;
  private currentId: string | null = null;
  private confirm?: RouteConfirm;
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
    this.objs = [];
    this.views = [];
    this.side = undefined;
    debugExpose('routeMap', null);
  }

  // -------------------------------------------------------------------------------------------
  private stale(e: KeyboardEvent): boolean {
    return typeof e.timeStamp === 'number' && e.timeStamp > 0 && e.timeStamp <= this.inputAfter;
  }

  private onKeyDown = (e: KeyboardEvent): void => {
    if (this.destroyed || this.stale(e)) return;
    if (this.confirm) {
      this.confirm.keyDown(e);
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
      this.confirm.keyUp(e);
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
    const W = UI_SCREEN.WIDTH;
    const H = UI_SCREEN.HEIGHT;
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
      drawIllustration(scene, rect, route.floor, this.late, () => !this.destroyed);
    } else {
      L = layoutPerspective(nodes, area, {
        rowMax: MAP3D.rowMax,
        farScale: MAP3D.farScale,
        ease: MAP3D.ease,
        minGap: MAP3D.minGap,
        padTop: MAP3D.padTop,
        padBottom: MAP3D.padBottom,
      });
      drawSheet(scene, area, L.yAt);
    }

    this.drawLinks(nodes, L, Boolean(illust));
    this.buildNodes(nodes, L);
    // 고르기 순서는 단계 → 줄 (좌→우). 숨은 노드 얼룩은 고를 수 없다
    if (this.mode === 'choose') {
      const ok = new Set(this.views.filter((v) => v.node.state === 'available' && !v.smudge).map((v) => v.node.id));
      this.choices = nodes.filter((n) => ok.has(n.id)).map((n) => n.id);
    }

    // 주인공 표시 (현재 노드 왼쪽, 발이 땅에)
    const cur =
      this.views.find((v) => v.node.id === route.currentId) ?? this.views.find((v) => v.node.state === 'current');
    this.layoutLabels(
      cur ? { x: cur.x - ICON_HALF - 4 - FIGURE_W, y: cur.gy - FIGURE_H + 1, w: FIGURE_W, h: FIGURE_H } : null,
      area,
    );
    if (cur) {
      this.figure = scene.add.graphics();
      drawFigure(this.figure, scene, si);
      this.figureY = cur.gy - FIGURE_H + 1;
      this.figure.setPosition(cur.x - ICON_HALF - 4 - FIGURE_W, this.figureY);
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
    this.side = new RouteSide(scene, sideX, area.y, MAP3D.sideW, bottom, cur?.node ?? null, {
      stageIndex: si,
      shopName: this.opts.shopName,
      mode: this.mode,
      late: this.late,
      alive: () => !this.destroyed,
      route,
    });

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

    this.expose();
    this.select(
      this.mode === 'choose' ? (this.choices[0] ?? cur?.node.id ?? null) : (cur?.node.id ?? nodes[0]?.id ?? null),
    );
    if (this.mode === 'choose' && !this.choices.length) this.showMessage(routeText('chooseDenied'));
    this.redraw();
  }

  /** 길 (땅 위 점선, 노드보다 먼저 = 아래). 숨은 노드는 links 에 들어가지 않으므로 길이 없다(§14.5) */
  private drawLinks(nodes: UiRouteNode[], L: PerspectiveLayout, illust: boolean): void {
    const scene = this.scene;
    const si = this.stageIndex;
    const byId = new Map(nodes.map((n) => [n.id, n]));
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
        const trimA = this.shadowAt(pa.scale).rx + 2;
        const trimB = this.shadowAt(pb.scale).rx + 2;
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
  }

  private shadowAt(scale: number): { rx: number; ry: number } {
    return {
      rx: Math.max(6, Math.round(MAP3D.shadowRx * scale)),
      ry: Math.max(2, Math.round(MAP3D.shadowRy * scale)),
    };
  }

  /**
   * 노드: 먼 것부터 (가까운 것이 위에 겹친다). 그림자 → 기둥 → Container(Graphics → 아이콘 → 표지) (버튼 규약).
   * 60라운드: 숨은 노드(얼룩)는 그림자·기둥·아이콘 대신 땅 점에 얼룩, 이름표 없음(보기 모드에서 살펴보기만).
   */
  private buildNodes(nodes: UiRouteNode[], L: PerspectiveLayout): void {
    const scene = this.scene;
    const si = this.stageIndex;
    const useSheet = NODE_ICON_SHEET.available && scene.textures.exists(NODE_ICON_SHEET.key);
    const r = useSheet ? ROUTE.iconR : ROUTE.nodeR;
    const liftAt = (scale: number): number =>
      Math.round(MAP3D.liftFar + (MAP3D.liftNear - MAP3D.liftFar) * ((scale - L.farScale) / (1 - L.farScale || 1)));
    const order = [...nodes].sort((a, b) => (L.pos.get(b.id)?.depth ?? 0) - (L.pos.get(a.id)?.depth ?? 0));
    const shadowColor = hexToNum(SEPIA[1]);
    for (const n of order) {
      const p = L.pos.get(n.id);
      if (!p) continue;
      const look = nodeLook(n);
      const smudge = look.hidden !== null;
      const lift = smudge ? 0 : liftAt(p.scale);
      const ix = p.x;
      const iy = smudge ? p.y : p.y - lift - ICON_HALF;
      if (!smudge) {
        const sh = this.shadowAt(p.scale);
        const base = scene.add.graphics();
        base.fillStyle(shadowColor, 1);
        for (const row of ellipseRows(p.x, p.y, sh.rx, sh.ry)) base.fillRect(row.x, row.y, row.w, 1);
        // 기둥: 아이콘 아래 꼭짓점에서 땅까지 2px
        base.fillRect(p.x - 1, iy + ICON_HALF - 2, 2, lift + 2);
      }
      let pulse: Phaser.GameObjects.Graphics | undefined;
      if (n.state === 'available' && !smudge) {
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
      const parts: Phaser.GameObjects.GameObject[] = [g];
      if (smudge) {
        // 얼룩 (+ 위치 표시면 점선 고리·'?')
        parts.push(...smudgeMark(scene, 0, 0, look.hidden === 'located', si));
      } else if (useSheet) {
        const col = Math.max(0, NODE_ICON_SHEET.order.indexOf(n.type));
        const row = n.state === 'cleared' ? 1 : n.state === 'passed' || n.state === 'locked' ? 2 : 0;
        sheet = scene.add
          .image(-ICON_HALF, -ICON_HALF, nodeIconKey(scene, si), row * NODE_ICON_SHEET.order.length + col)
          .setOrigin(0, 0);
        parts.push(sheet);
      } else parts.push(makeGlyph(scene, n.type, si));
      const glyph = parts[1];
      // 60라운드 §14.5 표지: 보상 미리보기 · 위험 표 · 성과 도장 (아이콘 가운데 기준, 같은 Container 안)
      if (look.reward) parts.push(rewardBadge(scene, 0, 0, look.reward, si));
      if (look.risk) parts.push(riskBadge(scene, 0, 0, look.risk, si));
      if (look.grade) parts.push(gradeMark(scene, 0, 0, look.grade, si));
      const box = scene.add.container(ix, iy, parts).setSize(r * 2 + 2, r * 2 + 2);
      // 이름표: 아이콘 오른쪽 (지도 칸 오른쪽을 넘으면 왼쪽). 얼룩은 이름을 보이지 않는다
      const label = new GlowText(scene, 0, 0, smudge ? '' : n.name, 'page_body', {
        wrap: MAP3D.labelWrap,
        stageIndex: si,
      });
      // 자리는 모든 노드를 만든 뒤 겹침을 피해 고른다 (layoutLabels, 61라운드 플레이 점검 #10)
      const labelLeft = false;
      const B = MARKS.badge;
      const marks: Rect[] = [];
      if (look.reward) marks.push({ x: ix + MARKS.rewardDx, y: iy + MARKS.rewardDy, w: B, h: B });
      if (look.risk) marks.push({ x: ix + MARKS.riskDx, y: iy + MARKS.riskDy, w: B, h: B });
      if (look.grade) marks.push({ x: ix + MARKS.gradeDx, y: iy + MARKS.gradeDy, w: 16, h: 16 });
      this.views.push({
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
        marks,
        pulse,
        smudge,
        risk: Boolean(look.risk),
      });
      this.navNodes.push({ id: n.id, x: ix, y: iy });
      // 입력: 마름모 모양(가장자리 2px 여유). Container 판정은 지역 좌표 + 폭·높이 절반 (glow.ts 참조)
      const half = r + 1;
      const pickable = this.mode === 'view' || (n.state === 'available' && !smudge);
      if (!pickable) continue;
      box.setInteractive(
        new Phaser.Geom.Rectangle(half, half, half * 2, half * 2),
        (_a: Phaser.Geom.Rectangle, hx: number, hy: number) => Math.abs(hx - half) + Math.abs(hy - half) <= r + 2,
      );
      if (box.input && this.mode === 'choose') box.input.cursor = 'pointer';
      box.on('pointerover', () => {
        if (!this.confirm) this.select(n.id);
      });
      if (this.mode !== 'choose') continue;
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

  /**
   * 늦게 만든 객체를 기준 객체 바로 위(above)·아래(below)에 끼운다 (같은 depth 안의 표시 순서).
   * 지도를 만드는 중이면(build 끝에서 depth 를 줄 것이므로) 순서만 맞춘다.
   */
  private late: LateInsert = (o, anchor, where) => {
    const list = this.scene.children;
    if (where === 'above') list.moveAbove(o, anchor);
    else list.moveBelow(o, anchor);
    if (this.objs.length) {
      o.setDepth(ROUTE.depth);
      this.objs.push(o);
    }
  };

  private select(id: string | null): void {
    if (this.destroyed || !id || id === this.sel) return;
    this.sel = id;
    this.redraw();
  }

  /**
   * 61라운드 플레이 점검 #10: 이름표 자리 — 다른 노드 아이콘·표지·주인공 표시·먼저 놓은 이름표와 겹치지 않는 곳
   * (오른쪽 → 왼쪽 → 아래 → 위 …, routeLabels.ts). 지금·갈 수 있는 곳을 먼저 놓는다.
   */
  private layoutLabels(figure: Rect | null, area: Rect): void {
    const obstacles: Rect[] = figure ? [figure] : [];
    for (const v of this.views) {
      if (!v.smudge) obstacles.push({ x: v.x - ICON_HALF, y: v.y - ICON_HALF, w: ICON_HALF * 2, h: ICON_HALF * 2 });
      obstacles.push(...v.marks);
    }
    const prio = (st: string): number => (st === 'current' ? 0 : st === 'available' ? 1 : 2);
    const items = this.views
      .filter((v) => !v.smudge && v.label.textW > 0)
      .map((v) => ({
        id: v.node.id,
        x: v.x,
        y: v.y,
        w: v.label.displayWidth,
        h: v.label.displayHeight,
        priority: prio(v.node.state),
      }));
    const placed = placeLabels(items, obstacles, area, ICON_HALF, MAP3D.labelGap);
    for (const v of this.views) {
      const p = placed.get(v.node.id);
      if (!p) continue;
      v.label.setPosition(p.x, p.y);
      v.labelLeft = p.side === 'left';
    }
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
      if (v.smudge) {
        // 얼룩: 살펴볼 때만 고리
        if (selected) diamondRing(g, r + 2, 2, accentSel);
        v.label.setVisible(false);
        continue;
      }
      if (!v.sheet) {
        // 종이 위 잉크 마름모: 지나온·지금·갈 수 있는 곳 S1, 지나친·먼 곳 S2
        const fillC = st === 'passed' || st === 'locked' ? SEPIA[2] : SEPIA[1];
        pixelDiamond(g, r, hexToNum(fillC));
        if (st === 'available') diamondRing(g, r, 1, hexToNum(SEPIA[5]));
        else if (st === 'cleared' || st === 'locked') diamondRing(g, r, 1, hexToNum(SEPIA[4]));
      }
      if (st === 'current') diamondRing(g, r + 2, 2, accentCur);
      else if (selected) diamondRing(g, r + 2, 2, accentSel);
      // 60라운드 §14.5: 위험 노드 붉은 테두리 (지나온·지나친 뒤에는 끈다)
      if (v.risk && st !== 'cleared' && st !== 'passed') riskRing(g, scene, r, si);
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
    this.side?.show(sv?.node ?? null, !sv || sv.node.id === this.currentId);
  }

  // -------------------------------------------------------------------------------------------
  // 49라운드: '넘어가시겠습니까?' 확인 (예일 때만 onChoose) — RouteConfirm.ts
  private openConfirm(id: string, stamp: number): void {
    if (this.destroyed || this.confirm || this.mode !== 'choose') return;
    const v = this.views.find((x) => x.node.id === id);
    if (!v) return;
    this.armedKey = null;
    this.pressed = null;
    this.inputAfter = stamp;
    this.confirm = new RouteConfirm(this.scene, v.node, {
      stageIndex: this.stageIndex,
      bookRect: this.bookRect,
      mapArea: this.mapArea,
      onAnswer: (yes, at) => {
        this.closeConfirm(at);
        if (yes) this.choose(id);
      },
    });
    this.expose();
  }

  private closeConfirm(stamp = 0): void {
    const c = this.confirm;
    if (!c) return;
    this.confirm = undefined;
    this.inputAfter = Math.max(this.inputAfter, stamp);
    this.armedKey = null;
    c.destroy();
    if (!this.destroyed) this.expose();
  }

  /** 헤드리스 확인용 (`uidebug=1`): 노드 화면 좌표·확인 창 버튼 */
  private expose(): void {
    const c = this.confirm;
    debugExpose('routeMap', {
      mode: this.mode,
      nodes: this.views.map((x) => ({ id: x.node.id, x: x.x, y: x.y, state: x.node.state, smudge: x.smudge })),
      confirm: c ? { id: c.id, ...c.buttonCenters() } : null,
    });
  }
}
