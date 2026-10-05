import Phaser from 'phaser';
import {
  UI_SCREEN,
  type UiChallengeCleared,
  type UiChallengeStarted,
  type UiInteractable,
  type UiStatus,
  type UiStructureResult,
} from '../contract/ui';
import { GlowText } from './glow';
import { NinePanel, accentHex, inkPanel } from './kit';
import { bubblePos, formatSec, holdSec, interactWords, timerRatio } from './structView';
import { fill, structText } from './text';
import { STRUCT_KIND_TEXT } from './textBuild';
import { GRAY, SEPIA, STRUCT, type SwatchRef, hexToNum } from './theme';

/**
 * 47라운드 상호작용 구조물 HUD 조각 (계약 `ui-system-interface.md` §9). HudScene 이 만들고 매 STATE 로 갱신한다.
 * - InteractBubble: `interactable` 안내 말풍선 (구조물 윗변 위)
 * - StatusChips: `statuses` 칩 목록 (좌상단 층 제목 아래)
 * - ResultToasts: `STRUCTURE_RESULT` 토스트 (우하단 공지 위, 위로 쌓임)
 * - ChallengePanel: `CHALLENGE_STARTED`/`CLEARED` (상단 가운데, 제한 시간 카운트다운)
 * 문구는 시스템이 준 문자열 그대로. UI 는 키 틀('[E]', '[E 2초]')·초 표시만 만든다.
 */

/** 팔레트 색 참조 → 숫자 색 (강조 램프는 현재 층) */
export function swatch(scene: Phaser.Scene, stageIndex: number, ref: SwatchRef): number {
  if ('slot' in ref) return hexToNum(accentHex(scene, stageIndex, ref.slot));
  if ('gray' in ref) return hexToNum(GRAY[ref.gray]);
  return hexToNum(SEPIA[ref.sepia]);
}

// ---------------------------------------------------------------------------------------------
/** 상호작용 안내 말풍선: 이름(흐림) / '[E] 행동 · 비용' / 길게 누르기 게이지 또는 불가 사유 */
export class InteractBubble {
  private box: Phaser.GameObjects.Container;
  private panel: NinePanel;
  private nameT: GlowText;
  private actT: GlowText;
  private costT: GlowText;
  private reasonT: GlowText;
  private bar: Phaser.GameObjects.Graphics;
  private layoutKey = '';
  private barRect = { x: 0, y: 0, w: 0 };
  private lastProgress = -1;
  private stageIndex: number;

  constructor(
    private scene: Phaser.Scene,
    stageIndex: number,
  ) {
    this.stageIndex = stageIndex;
    this.panel = inkPanel(scene, 0, 0, 40, 40);
    this.nameT = new GlowText(scene, 0, 0, '', 'ink_faint', { stageIndex });
    this.actT = new GlowText(scene, 0, 0, '', 'ink_body', { stageIndex });
    this.costT = new GlowText(scene, 0, 0, '', 'ink_accent', { stageIndex });
    this.reasonT = new GlowText(scene, 0, 0, '', 'ink_accent', { stageIndex });
    this.bar = scene.add.graphics();
    this.box = scene.add
      .container(0, 0, [this.panel, this.nameT, this.actT, this.costT, this.reasonT, this.bar])
      .setDepth(STRUCT.bubbleDepth)
      .setVisible(false);
  }

  update(it: UiInteractable | null, show: boolean, stageIndex: number): void {
    if (!it || !show) {
      this.box.setVisible(false);
      return;
    }
    if (stageIndex !== this.stageIndex) {
      this.stageIndex = stageIndex;
      for (const t of [this.nameT, this.actT, this.costT, this.reasonT]) t.setStageIndex(stageIndex);
      this.layoutKey = '';
    }
    const key = [
      it.id,
      it.name,
      it.key,
      it.action,
      it.cost ? `${it.cost.label}|${it.cost.affordable}` : '',
      it.usable,
      it.reasonText,
      it.hold ? it.hold.durationMs : '',
    ].join('\u0001');
    if (key !== this.layoutKey) {
      this.layoutKey = key;
      this.layout(it);
    }
    const progress = it.hold && it.usable ? Math.max(0, Math.min(1, it.hold.progress)) : -1;
    if (progress !== this.lastProgress) {
      this.lastProgress = progress;
      this.drawBar(progress);
    }
    const W = UI_SCREEN.WIDTH;
    const H = UI_SCREEN.HEIGHT;
    const p = bubblePos(it.screen, this.panel.width, this.panel.height, W, H, STRUCT.bubbleMargin, STRUCT.bubbleGap);
    this.box.setPosition(p.x, p.y).setVisible(true);
  }

  private layout(it: UiInteractable): void {
    const pad = STRUCT.bubblePad;
    // GlowText 상자는 글자 + 사방 2px 링. 링이 패널 안쪽 여백에 걸치도록 pad-2 에서 시작
    let y = pad - 2;
    const x = pad - 2;
    const words = interactWords(it, STRUCT_KIND_TEXT);
    this.nameT.setText(words.name).setPosition(x, y);
    y += this.nameT.displayHeight;
    const frame = it.hold
      ? fill(structText('keyHold'), { key: it.key, sec: holdSec(it.hold.durationMs) })
      : fill(structText('keyTap'), { key: it.key });
    this.actT
      .setText(`${frame} ${words.action}`)
      .setGlowStyle(it.usable ? 'ink_body' : 'ink_faint')
      .setPosition(x, y);
    const costLabel = it.cost && it.cost.kind !== 'none' ? it.cost.label : '';
    this.costT
      .setText(costLabel ? `· ${costLabel}` : '')
      .setGlowStyle(it.cost?.affordable === false ? 'ink_faint' : 'ink_accent')
      .setAlpha(it.cost?.affordable === false ? STRUCT.dimAlpha : 1)
      .setPosition(x + this.actT.textW + 8, y);
    let w = Math.max(this.nameT.textW, this.actT.textW + (costLabel ? 8 + this.costT.textW : 0));
    y += this.actT.displayHeight;
    const reason = !it.usable && it.reasonText ? it.reasonText : '';
    this.reasonT.setText(reason).setPosition(x, y).setVisible(Boolean(reason));
    if (reason) {
      w = Math.max(w, this.reasonT.textW);
      y += this.reasonT.displayHeight;
    }
    const hasBar = Boolean(it.hold) && it.usable;
    if (hasBar) {
      this.barRect = { x: pad, y: y + 1, w };
      y += 1 + STRUCT.holdBarH + 2;
    }
    // 오른쪽 링 2px + 여백
    this.panel.resize(w + pad * 2 + 2, y + pad);
    this.bar.setVisible(hasBar);
    this.lastProgress = -2;
  }

  private drawBar(progress: number): void {
    const g = this.bar;
    g.clear();
    if (progress < 0) return;
    const { x, y, w } = this.barRect;
    g.fillStyle(hexToNum(GRAY[3]), 1).fillRect(x, y, w, STRUCT.holdBarH);
    const fw = Math.round(w * progress);
    if (fw > 0)
      g.fillStyle(hexToNum(accentHex(this.scene, this.stageIndex, 22)), 1).fillRect(x, y, fw, STRUCT.holdBarH);
  }

  destroy(): void {
    this.box.destroy();
  }
}

// ---------------------------------------------------------------------------------------------
interface Chip {
  status: UiStatus;
  panel: NinePanel;
  stripe: Phaser.GameObjects.Graphics;
  label: GlowText;
  value: GlowText;
  bar: Phaser.GameObjects.Graphics;
  barX: number;
  barW: number;
  lastRatio: number;
}

/** HUD 상태 칩: 좌상단 층 제목 아래 세로 목록. 칩 = ink 패널 + 종류 색 띠 + 이름(흐림) + 값 + (타이머면) 줄어드는 바 */
export class StatusChips {
  private chips: Chip[] = [];
  private sig = '';
  private stageIndex = -1;

  constructor(
    private scene: Phaser.Scene,
    private x: number,
    private y: number,
  ) {}

  render(statuses: UiStatus[], stageIndex: number): void {
    const sig = statuses
      .map((s) => `${s.id}|${s.kind}|${s.label}|${s.value}|${s.durationMs ? 't' : ''}`)
      .join('\u0001');
    if (sig !== this.sig || stageIndex !== this.stageIndex) {
      this.sig = sig;
      this.stageIndex = stageIndex;
      this.rebuild(statuses, stageIndex);
    }
    // 타이머 바만 매 프레임
    statuses.forEach((s, i) => {
      const c = this.chips[i];
      if (!c) return;
      c.status = s;
      const r = timerRatio(s);
      if (r === null || r === c.lastRatio) return;
      c.lastRatio = r;
      this.drawBar(c, r, stageIndex);
    });
  }

  private rebuild(statuses: UiStatus[], si: number): void {
    this.clear();
    let y = this.y;
    for (const s of statuses) {
      const color = swatch(this.scene, si, STRUCT.statusColor[s.kind]);
      const label = new GlowText(this.scene, 0, 0, s.label, 'ink_faint', { stageIndex: si });
      const value = new GlowText(this.scene, 0, 0, s.value, s.kind === 'debuff' ? 'ink_accent' : 'ink_body', {
        stageIndex: si,
      });
      const tx = this.x + 5 + STRUCT.chipStripe + 4;
      const w = tx - this.x + label.textW + (s.value ? 6 + value.textW : 0) + 4 + 8;
      const panel = inkPanel(this.scene, this.x, y, w, STRUCT.chipH);
      const stripe = this.scene.add.graphics();
      stripe.fillStyle(color, 1).fillRect(this.x + 5, y + 5, STRUCT.chipStripe, STRUCT.chipH - 10);
      label.setPosition(tx - 2, y + 3);
      value.setPosition(tx - 2 + label.textW + 6, y + 3).setVisible(Boolean(s.value));
      const bar = this.scene.add.graphics();
      const chip: Chip = {
        status: s,
        panel,
        stripe,
        label,
        value,
        bar,
        barX: tx,
        barW: w - (tx - this.x) - 8,
        lastRatio: -1,
      };
      // 글자를 패널보다 먼저 만들었으므로 depth 로 순서를 잡는다: 패널 → 띠·바 → 글자
      panel.setDepth(STRUCT.hudDepth);
      stripe.setDepth(STRUCT.hudDepth + 1);
      bar.setDepth(STRUCT.hudDepth + 1);
      label.setDepth(STRUCT.hudDepth + 2);
      value.setDepth(STRUCT.hudDepth + 2);
      this.chips.push(chip);
      y += STRUCT.chipH + STRUCT.chipGap;
    }
  }

  private drawBar(c: Chip, ratio: number, si: number): void {
    const g = c.bar;
    g.clear();
    const y = c.panel.y + STRUCT.chipH - 6;
    g.fillStyle(hexToNum(GRAY[3]), 1).fillRect(c.barX, y, c.barW, STRUCT.chipBarH);
    const fw = Math.round(c.barW * ratio);
    if (fw > 0)
      g.fillStyle(swatch(this.scene, si, STRUCT.statusColor[c.status.kind]), 1).fillRect(
        c.barX,
        y,
        fw,
        STRUCT.chipBarH,
      );
  }

  private clear(): void {
    for (const c of this.chips) for (const o of [c.panel, c.stripe, c.label, c.value, c.bar]) o.destroy();
    this.chips = [];
  }

  /** 칩 목록 아래 끝 y (다른 요소 배치용) */
  bottom(): number {
    return this.y + this.chips.length * (STRUCT.chipH + STRUCT.chipGap);
  }

  destroy(): void {
    this.clear();
  }
}

// ---------------------------------------------------------------------------------------------
interface Toast {
  box: Phaser.GameObjects.Container;
  h: number;
  timer: Phaser.Time.TimerEvent;
}

/** 결과 알림 토스트: 오른쪽 아래(공지 패널 위)에서 위로 쌓인다. tone 별 띠 색, warn 은 강조 글자 */
export class ResultToasts {
  private toasts: Toast[] = [];

  constructor(
    private scene: Phaser.Scene,
    private right: number,
    private bottom: number,
  ) {}

  /** 60라운드: §14.11 알림(세트 단계·저주·숨은 길·소모품)도 같은 토스트로 — tone·text 만 쓴다 */
  push(r: Pick<UiStructureResult, 'tone' | 'text'>, stageIndex: number): void {
    if (!r.text) return;
    const scene = this.scene;
    const pad = 6;
    const stripeW = STRUCT.chipStripe;
    const textX = 5 + stripeW + 4;
    const style = r.tone === 'warn' ? 'ink_accent' : r.tone === 'info' ? 'ink_faint' : 'ink_body';
    const t = new GlowText(scene, textX - 2, pad - 2, r.text, style, {
      wrap: STRUCT.toastMaxW - textX - pad - 4,
      stageIndex,
    });
    const w = Math.min(STRUCT.toastMaxW, textX + t.textW + 2 + pad);
    const h = Math.max(STRUCT.chipH, t.displayHeight + pad * 2 - 4);
    const panel = inkPanel(scene, 0, 0, w, h);
    const stripe = scene.add.graphics();
    stripe.fillStyle(swatch(scene, stageIndex, STRUCT.toneColor[r.tone]), 1).fillRect(5, 5, stripeW, h - 10);
    const box = scene.add
      .container(this.right - w, 0, [panel, stripe, t])
      .setDepth(STRUCT.hudDepth)
      .setAlpha(0);
    scene.tweens.add({ targets: box, alpha: 1, duration: 120 });
    const toast: Toast = {
      box,
      h,
      timer: scene.time.delayedCall(STRUCT.toastHoldMs, () => this.fadeOut(toast)),
    };
    this.toasts.push(toast);
    while (this.toasts.length > STRUCT.toastMax) this.remove(this.toasts[0]);
    this.relayout();
  }

  private fadeOut(t: Toast): void {
    this.scene.tweens.add({
      targets: t.box,
      alpha: 0,
      duration: STRUCT.toastFadeMs,
      onComplete: () => this.remove(t),
    });
  }

  private remove(t: Toast): void {
    const i = this.toasts.indexOf(t);
    if (i < 0) return;
    this.toasts.splice(i, 1);
    t.timer.remove();
    this.scene.tweens.killTweensOf(t.box);
    t.box.destroy();
    this.relayout();
  }

  /** 최신이 아래. 아래에서 위로 쌓는다 */
  private relayout(): void {
    let y = this.bottom;
    for (let i = this.toasts.length - 1; i >= 0; i--) {
      const t = this.toasts[i];
      y -= t.h;
      t.box.setY(y);
      y -= STRUCT.chipGap + 2;
    }
  }

  clear(): void {
    for (const t of [...this.toasts]) this.remove(t);
  }
}

// ---------------------------------------------------------------------------------------------
/** 도전 판: 상단 가운데. 시작 = 이름(강조) + 남은 시간(×2) / 목표 / 시간 바. 종료 = 결과 문구 잠시 */
export class ChallengePanel {
  private box?: Phaser.GameObjects.Container;
  private panel?: NinePanel;
  private timeT?: GlowText;
  private bar?: Phaser.GameObjects.Graphics;
  private barRect = { x: 0, y: 0, w: 0 };
  private current: UiChallengeStarted | null = null;
  private startedAt = 0;
  private lastShown = '';
  private hideTimer?: Phaser.Time.TimerEvent;

  constructor(
    private scene: Phaser.Scene,
    private top: number,
  ) {}

  start(c: UiChallengeStarted, stageIndex: number): void {
    this.reset();
    this.current = c;
    this.startedAt = this.scene.time.now;
    const scene = this.scene;
    const pad = 8;
    const label = new GlowText(scene, pad - 2, pad - 2, c.label, 'ink_accent', { stageIndex });
    const goal = new GlowText(scene, pad - 2, pad - 2 + label.displayHeight, c.goal, 'ink_body', { stageIndex });
    const objs: Phaser.GameObjects.GameObject[] = [label, goal];
    let w = Math.max(label.textW, goal.textW);
    let h = pad - 2 + label.displayHeight + goal.displayHeight;
    if (c.timeLimitMs !== null) {
      this.timeT = new GlowText(scene, 0, 0, this.timeText(c.timeLimitMs), 'ink_body', { scale: 2, stageIndex });
      const tw = this.timeT.displayWidth;
      w += 16 + tw;
      this.bar = scene.add.graphics();
      this.barRect = { x: pad, y: h + 2, w };
      h += 2 + STRUCT.chipBarH + 2;
      objs.push(this.timeT, this.bar);
    }
    w += pad * 2;
    h += pad - 2;
    this.panel = inkPanel(scene, 0, 0, w, Math.max(24, h));
    this.timeT?.setPosition(w - pad + 2 - this.timeT.displayWidth, Math.round((h - this.timeT.displayHeight) / 2) - 1);
    this.box = scene.add
      .container(Math.round(UI_SCREEN.WIDTH / 2 - w / 2), this.top, [this.panel, ...objs])
      .setDepth(STRUCT.hudDepth);
    this.lastShown = '';
    this.tick(null, stageIndex);
  }

  /** 매 프레임: 남은 시간. 투견 링 상태(`ring` remainMs)가 있으면 그것을, 없으면 시작 시각 기준으로 */
  tick(ringStatus: UiStatus | null, stageIndex: number): void {
    const c = this.current;
    if (!c || c.timeLimitMs === null || !this.timeT || !this.bar) return;
    const remain =
      ringStatus?.remainMs !== undefined ? ringStatus.remainMs : c.timeLimitMs - (this.scene.time.now - this.startedAt);
    const text = this.timeText(remain);
    if (text === this.lastShown) return;
    this.lastShown = text;
    this.timeT.setText(text);
    const { x, y, w } = this.barRect;
    const ratio = Math.max(0, Math.min(1, remain / c.timeLimitMs));
    this.bar.clear().fillStyle(hexToNum(GRAY[3]), 1).fillRect(x, y, w, STRUCT.chipBarH);
    const fw = Math.round(w * ratio);
    if (fw > 0)
      this.bar
        .fillStyle(swatch(this.scene, stageIndex, STRUCT.statusColor.timer), 1)
        .fillRect(x, y, fw, STRUCT.chipBarH);
  }

  finish(r: UiChallengeCleared, stageIndex: number): void {
    this.reset();
    if (!r.text) return;
    const scene = this.scene;
    const pad = 8;
    const t = new GlowText(scene, pad - 2, pad - 2, r.text, r.outcome === 'timeout' ? 'ink_faint' : 'ink_accent', {
      stageIndex,
      wrap: UI_SCREEN.WIDTH - 320,
      align: 'center',
    });
    const w = t.textW + 4 + pad * 2 - 4;
    const h = t.displayHeight + pad * 2 - 4;
    this.panel = inkPanel(scene, 0, 0, w, Math.max(24, h));
    this.box = scene.add
      .container(Math.round(UI_SCREEN.WIDTH / 2 - w / 2), this.top, [this.panel, t])
      .setDepth(STRUCT.hudDepth);
    const box = this.box;
    this.hideTimer = scene.time.delayedCall(STRUCT.challengeResultMs, () => {
      scene.tweens.add({
        targets: box,
        alpha: 0,
        duration: STRUCT.toastFadeMs,
        onComplete: () => {
          if (this.box === box) this.reset();
          else box.destroy();
        },
      });
    });
  }

  private timeText(ms: number): string {
    return fill(structText('challengeTime'), { sec: formatSec(ms) });
  }

  get active(): boolean {
    return this.current !== null;
  }

  reset(): void {
    this.hideTimer?.remove();
    this.hideTimer = undefined;
    if (this.box) {
      this.scene.tweens.killTweensOf(this.box);
      this.box.destroy();
    }
    this.box = undefined;
    this.panel = undefined;
    this.timeT = undefined;
    this.bar = undefined;
    this.current = null;
  }
}
