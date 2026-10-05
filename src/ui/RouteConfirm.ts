import Phaser from 'phaser';
import type { UiRouteNode } from '../contract/ui';
import { GlowText } from './glow';
import { KIT, NinePanel, SLICE, accentHex } from './kit';
import { routeText } from './text';
import { GRAY, MAP3D, ROUTE, SEPIA, hexToNum } from './theme';
import { keyToDir } from './warpNav';

/** 입력 이벤트 시각 (없으면 0 = 거르지 않음) */
export function eventStamp(pointer?: Phaser.Input.Pointer): number {
  const t = pointer?.event?.timeStamp;
  return typeof t === 'number' ? t : 0;
}

export function hasDepth(
  o: Phaser.GameObjects.GameObject,
): o is Phaser.GameObjects.GameObject & { setDepth(d: number): unknown } {
  return typeof (o as { setDepth?: unknown }).setDepth === 'function';
}

export interface RouteConfirmContext {
  stageIndex: number;
  /** 책 전체 (뒤 덮기·클릭 막기) */
  bookRect: { x: number; y: number; w: number; h: number };
  /** 지도 칸 (창은 그 가운데) */
  mapArea: { x: number; y: number; w: number; h: number };
  /** 예·아니오 (stamp = 답한 입력 이벤트 시각) */
  onAnswer: (yes: boolean, stamp: number) => void;
}

/**
 * 49라운드 '넘어가시겠습니까?' 확인 창 (RouteMap 에서 분리, 60라운드). `panel_paper` 창 — 제목 / '지역 · 이름' /
 * (60라운드 §14.5 위험 노드면 `riskText` 한 줄, 층 강조) / [예] [아니오] (Container → Graphics → 글자) / 안내.
 * ←→·A·D 전환, Enter·Space·Y(뗀 뒤) 정하기, Esc·N 아니오. 키 이벤트를 걸러내는 일(`inputAfter`)은 RouteMap 이 한다.
 */
export class RouteConfirm {
  readonly id: string;
  private objs: Phaser.GameObjects.GameObject[] = [];
  private buttons: { box: Phaser.GameObjects.Container; draw: (focus: boolean) => void }[] = [];
  private focus = 0;
  private armedKey: string | null = null;
  private pressed: number | null = null;
  private bw = 0;
  private bh = 0;
  private closed = false;

  constructor(
    scene: Phaser.Scene,
    node: UiRouteNode,
    private ctx: RouteConfirmContext,
  ) {
    this.id = node.id;
    const si = ctx.stageIndex;
    const before = new Set(scene.children.list);
    const b = ctx.bookRect;
    // 페이지 위를 살짝 어둡게 + 아래 노드 클릭 막기
    scene.add.rectangle(b.x, b.y, b.w, b.h, hexToNum(GRAY[0]), MAP3D.confirmDim).setOrigin(0, 0).setInteractive();
    const cw = MAP3D.confirmW;
    const riskLine = node.risk && node.riskText ? node.riskText : '';
    const risk = riskLine
      ? new GlowText(scene, 0, 0, riskLine, 'ink_accent', { stageIndex: si, wrap: cw - 32, align: 'center' })
      : null;
    const ch = MAP3D.confirmH + (risk ? risk.displayHeight + 2 : 0);
    const area = ctx.mapArea;
    const cx = Math.round(area.x + area.w / 2 - cw / 2);
    const cy = Math.round(area.y + area.h / 2 - ch / 2);
    new NinePanel(scene, cx, cy, KIT.panelPaper, SLICE.panelPaper, cw, ch);
    let y = cy + 14;
    const title = new GlowText(scene, 0, y, routeText('confirmTitle'), 'page_title', { font: 'title', stageIndex: si });
    title.placeCenter(cx + cw / 2, y);
    y += title.displayHeight + 2;
    const where = [node.region, node.name].filter(Boolean).join(' · ');
    new GlowText(scene, 0, y, where, 'page_selected', { stageIndex: si }).placeCenter(cx + cw / 2, y);
    y += 20;
    if (risk) {
      // 종이 위지만 경고라 잉크 강조 글자로 (계약 §14.5 진입 확인에 붙일 위험 한 줄)
      risk.placeCenter(cx + cw / 2, y - 2);
      y += risk.displayHeight + 2;
    }
    const labels = [routeText('confirmYes'), routeText('confirmNo')];
    const texts = labels.map((t) => new GlowText(scene, 0, 0, t, 'page_body', { stageIndex: si }));
    const bw = Math.max(MAP3D.buttonMinW, ...texts.map((t) => t.displayWidth + 16));
    const bh = MAP3D.buttonH;
    this.bw = bw;
    this.bh = bh;
    const total = bw * 2 + MAP3D.buttonGap;
    const bx0 = Math.round(cx + cw / 2 - total / 2);
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
      box.on('pointerover', () => this.setFocus(i));
      box.on('pointerdown', () => {
        this.pressed = i;
        this.setFocus(i);
      });
      box.on('pointerup', (pointer: Phaser.Input.Pointer) => {
        if (this.pressed === i) this.answer(i === 0, eventStamp(pointer));
        else this.pressed = null;
      });
      this.buttons.push({ box, draw });
    });
    y += bh + 8;
    const hint = new GlowText(scene, 0, y, routeText('confirmHint'), 'page_faint');
    hint.placeCenter(cx + cw / 2, y);
    for (const o of scene.children.list) {
      if (before.has(o)) continue;
      this.objs.push(o);
      if (hasDepth(o)) o.setDepth(ROUTE.depth + 5);
    }
    // 위험 한 줄은 창 크기를 재려고 창보다 먼저 만들었다 — 같은 depth 안에서 창 위로
    if (risk) scene.children.bringToTop(risk);
    this.setFocus(0, true);
  }

  /** 디버그용: 예·아니오 버튼 가운데 화면 좌표 */
  buttonCenters(): { yes: { x: number; y: number }; no: { x: number; y: number } } {
    const c = (i: number) => ({ x: this.buttons[i].box.x + this.bw / 2, y: this.buttons[i].box.y + this.bh / 2 });
    return { yes: c(0), no: c(1) };
  }

  keyDown(e: KeyboardEvent): void {
    if (this.closed) return;
    if (e.key === 'Escape' || e.key === 'n' || e.key === 'N') {
      this.answer(false, e.timeStamp);
      return;
    }
    if (e.repeat) return;
    if (e.key === 'Enter' || e.key === ' ') {
      this.armedKey = e.key;
      return;
    }
    if (e.key === 'y' || e.key === 'Y') {
      this.setFocus(0);
      this.armedKey = e.key;
      return;
    }
    const dir = keyToDir(e.key);
    if (dir && dir.dx !== 0) this.setFocus(this.focus === 0 ? 1 : 0);
  }

  keyUp(e: KeyboardEvent): void {
    if (this.closed || e.key !== this.armedKey) return;
    this.armedKey = null;
    this.answer(this.focus === 0, e.timeStamp);
  }

  destroy(): void {
    this.closed = true;
    for (const o of this.objs) o.destroy();
    this.objs = [];
    this.buttons = [];
  }

  private setFocus(i: number, force = false): void {
    if (!force && this.focus === i) return;
    this.focus = i;
    this.buttons.forEach((b, k) => b.draw(k === i));
  }

  private answer(yes: boolean, stamp: number): void {
    if (this.closed) return;
    this.ctx.onAnswer(yes, stamp);
  }
}
