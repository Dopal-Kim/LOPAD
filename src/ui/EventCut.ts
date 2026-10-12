import Phaser from 'phaser';
import { UI_SCREEN, type UiEventIcon, type UiEventResult, type UiHiddenReward } from '../contract/ui';
import { debugExpose } from './debug';
import { iconList } from './eventIcons';
import { readIcons } from './eventView';
import { fill } from './fmt';
import { GlowText } from './glow';
import { bandRect, type AlertSpec } from './HudAlerts';
import { artTex } from './paintArt';
import { GRAY, SEPIA, hexToNum } from './theme';
import { ALERT_UI } from './themeAlerts';
import { GROWTH_BANNER } from './themeGrowth';
import { EVENT_CUT as C } from './themeLoop2F';
import { l2fText } from './textLoop2F';
import { sequenceGone, sequenceShown } from './uiSequence';

const SEQ_TAG = 'eventCut';

/** 머리말 (사연 메뉴 heads — 없으면 UI 대체) */
export interface CutHeads {
  costHead: string;
  gainHead: string;
}

/**
 * 62 루프 2 UI F (계약 D P1-12 `ui:event-result`): 사연을 고른 뒤 결과 컷 한 장 — 화면 가운데 위쪽 종이 패널.
 *  컷 그림(아트 §31-7 `events/cut_*` 320×180, UI 1배 — 없으면 그림 칸 없이) · 한 줄(읽는 글) · '내준다 [아이콘] · 얻는다 [아이콘]' · '[E] 계속'.
 * 머문 뒤 사라진다 — E(설정의 상호작용 키)·클릭으로 바로 닫힌다. 이어서 열리는 보상 메뉴(유품 고르기 등)는 컷이 떠 있는 동안
 * 잠깐(최대 `menuWaitMaxMs`) 기다린다(uiSequence) — 기다림이 끝나면 컷이 그때 맞춰 접힌다.
 */
export class EventCutPanel {
  private box?: Phaser.GameObjects.Container;
  private timer?: Phaser.Time.TimerEvent;
  private interactKey = 'E';
  private onKey = (e: KeyboardEvent): void => {
    if (!this.box || e.repeat) return;
    const k = this.interactKey.toUpperCase();
    if (e.code === `Key${k}` || e.key.toUpperCase() === k) this.hide(0);
  };

  constructor(private scene: Phaser.Scene) {
    scene.input.keyboard?.on('keydown', this.onKey);
  }

  get open(): boolean {
    return Boolean(this.box);
  }

  show(r: UiEventResult, heads: CutHeads, si: number, interactKey: string): void {
    this.clear();
    const line = (r?.line ?? '').trim();
    const tex = artTex(this.scene, r?.cutKey);
    const losses = readIcons(r?.losses);
    const gains = readIcons(r?.gains).filter((g) => !g.hidden);
    if (!line && !tex && losses.length + gains.length === 0) return;
    this.interactKey = interactKey || 'E';
    const sc = this.scene;
    const pad = C.pad;
    const innerW = C.w;
    const parts: Phaser.GameObjects.GameObject[] = [];
    const bg = sc.add.graphics();
    parts.push(bg);
    let y = pad;
    if (tex) {
      const img = sc.add.image(pad, y, tex).setOrigin(0, 0);
      const s = Math.min(1, innerW / Math.max(1, img.width), C.h / Math.max(1, img.height));
      img.setScale(s);
      parts.push(img);
      y += Math.round(img.height * s) + 6;
    }
    if (line) {
      const t = new GlowText(sc, 0, y, line, 'page_selected', {
        wrap: innerW,
        align: 'center',
        stageIndex: si,
        readable: true,
      });
      t.placeCenter(pad + innerW / 2, y);
      parts.push(t);
      y += t.displayHeight + 4;
    }
    const row = this.iconRow(losses, gains, heads, si);
    if (row) {
      row.box.setPosition(Math.round(pad + innerW / 2 - row.w / 2), y);
      parts.push(row.box);
      y += row.h + 2;
    }
    const hint = new GlowText(sc, 0, y, fill(l2fText('cutContinue'), { key: this.interactKey }), 'page_faint');
    hint.placeRight(pad + innerW + 2, y);
    parts.push(hint);
    y += hint.displayHeight;
    const w = innerW + pad * 2;
    const h = y + pad - 2;
    // 종이: 그늘 · 먹 외곽 · S4 테 · S3 바탕 · 그림 아래 강조 없음 (그림이 주인공)
    bg.fillStyle(hexToNum(GRAY[0]), 0.5).fillRect(3, 3, w, h);
    bg.fillStyle(hexToNum(GRAY[0]), 1).fillRect(-1, -1, w + 2, h + 2);
    bg.fillStyle(hexToNum(SEPIA[4]), 1).fillRect(0, 0, w, h);
    bg.fillStyle(hexToNum(SEPIA[3]), 1).fillRect(1, 1, w - 2, h - 2);
    const x = Math.round(UI_SCREEN.WIDTH / 2 - w / 2);
    const top = Math.round(UI_SCREEN.HEIGHT * C.centerY - h / 2);
    const box = sc.add
      .container(x, top - C.drop, parts)
      .setDepth(C.depth)
      .setAlpha(0);
    box.setSize(w, h);
    box.setInteractive(new Phaser.Geom.Rectangle(w / 2, h / 2, w, h), Phaser.Geom.Rectangle.Contains);
    box.on('pointerup', (p: Phaser.Input.Pointer) => {
      if (p.button === 0) this.hide(0);
    });
    this.box = box;
    sc.tweens.add({ targets: box, alpha: 1, y: top, duration: C.inMs, ease: 'Cubic.Out' });
    this.timer = sc.time.delayedCall(C.inMs + C.holdMs, () => this.hide(C.outMs));
    sequenceShown(SEQ_TAG, C.inMs + C.holdMs, {
      maxWaitMs: C.menuWaitMaxMs,
      shorten: (ms) => {
        this.timer?.remove(false);
        this.timer = sc.time.delayedCall(ms, () => this.hide(C.outMs / 2));
      },
    });
    debugExpose('eventCut', {
      eventId: r.eventId,
      option: r.optionKey,
      cut: tex ?? null,
      line,
      losses: losses.length,
      gains: gains.length,
      x,
      y: top,
      w,
      h,
    });
  }

  /** 접는다 (ms 0 = 바로) */
  hide(ms: number): void {
    const box = this.box;
    if (!box) return;
    this.box = undefined;
    this.timer?.remove(false);
    this.timer = undefined;
    sequenceGone(SEQ_TAG);
    this.scene.tweens.killTweensOf(box);
    if (ms <= 0) {
      box.destroy(true);
      return;
    }
    this.scene.tweens.add({ targets: box, alpha: 0, duration: ms, onComplete: () => box.destroy(true) });
  }

  clear(): void {
    this.hide(0);
  }

  destroy(): void {
    this.clear();
    this.scene.input.keyboard?.off('keydown', this.onKey);
  }

  /** '내준다 [아이콘…]  얻는다 [아이콘…]' 한 줄 */
  private iconRow(
    losses: UiEventIcon[],
    gains: UiEventIcon[],
    heads: CutHeads,
    si: number,
  ): { box: Phaser.GameObjects.Container; w: number; h: number } | null {
    if (losses.length + gains.length === 0) return null;
    const sc = this.scene;
    const box = sc.add.container(0, 0);
    let x = 0;
    const group = (head: string, icons: UiEventIcon[]): void => {
      if (!icons.length) return;
      if (x > 0) x += 14;
      const h = new GlowText(sc, x, 1, head, 'page_faint');
      box.add(h);
      x += h.displayWidth + 4;
      const l = iconList(sc, icons, { layout: 'row', style: 'page_body', stageIndex: si, gap: 8 });
      l.box.setPosition(x, 0);
      box.add(l.box);
      x += l.w;
    };
    group(heads.costHead, losses);
    group(heads.gainHead, gains);
    return { box, w: x, h: 18 };
  }
}

/**
 * 62 루프 2 UI F (계약 D P1-12 `ui:hidden-reward`): 숨은 보상 알림 — 위 가운데 알림 줄의 '개성' 급(growth, 낮은 안내가 아니다).
 * 잉크 띠(알림 키트) 위 '다음에 받는다'·'받았다'(흐림) / [아이콘] 한 줄. 같은 문장은 합친다.
 */
export function hiddenRewardAlert(p: UiHiddenReward, si: number): AlertSpec | null {
  const text = (p?.text ?? '').trim();
  if (!text) return null;
  const head = p.state === 'paid' ? l2fText('hiddenPaid') : l2fText('hiddenLater');
  const icon = p.icon && typeof p.icon === 'object' ? p.icon : null;
  const T = GROWTH_BANNER.trait;
  return {
    kind: 'growth',
    key: `hidden:${p.state}:${text}`,
    label: `${head} · ${text}`,
    timing: { inMs: T.inMs, holdMs: T.holdMs + 600, outMs: T.outMs, drop: T.drop },
    merge: (prev) => prev,
    build: (sc) => {
      const W = UI_SCREEN.WIDTH;
      const box = sc.add.container(0, 0);
      const pad = ALERT_UI.bandPad;
      const headT = new GlowText(sc, 0, pad, head, 'ink_faint', { stageIndex: si });
      headT.placeCenter(W / 2, pad);
      let y = pad + headT.displayHeight;
      const ic = icon ? iconList(sc, [icon], { layout: 'row', style: 'ink_accent', stageIndex: si }) : null;
      const body = new GlowText(sc, 0, y, text, 'ink_body', { stageIndex: si, readable: true });
      const rowW = (ic ? ic.w + 6 : 0) + body.displayWidth;
      const x0 = Math.round(W / 2 - rowW / 2);
      if (ic) {
        ic.box.setPosition(x0, y + Math.round((body.displayHeight - 18) / 2));
        body.setPosition(x0 + ic.w + 6, y);
      } else body.setPosition(x0, y);
      y += Math.max(body.displayHeight, ic ? 18 : 0);
      const h = y + pad;
      const g = sc.add.graphics();
      const bw = Math.min(ALERT_UI.bandMaxW, Math.max(ALERT_UI.bandMinW, rowW + ALERT_UI.bandFade * 2 + 24));
      bandRect(sc, g, Math.round(W / 2 - bw / 2), 0, bw, h, si);
      box.add([g, headT, ...(ic ? [ic.box] : []), body]);
      return { box, h };
    },
  };
}
