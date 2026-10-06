import Phaser from 'phaser';
import { UI_EVENTS, UI_SCREEN, uiCommands, type UiSnapshot, type UiTraining } from '../contract/ui';
import { debugExpose } from './debug';
import { GlowText } from './glow';
import { keyGlyph } from './keyGuide';
import { fontFamily, inkPanel, type NinePanel } from './kit';
import { fill, trainingText } from './text';
import { FONT, GRAY, hexToNum } from './theme';
import { HEALTH_BAR } from './themeR61';
import { TRAINING_UI } from './themeTransition';
import {
  doneCount,
  isTrainingHall,
  readStampEvent,
  readTaskEvent,
  taskRows,
  trainingOf,
  type TaskRow,
} from './trainingView';

/** 도장 색 (붉은 인주 — 체력 막대와 같은 팔레트 '적' 램프 값) */
const SEAL = hexToNum(HEALTH_BAR.fill);
const SEAL_DARK = hexToNum(HEALTH_BAR.lost);

/** 체크 칸 그리기: 빈 칸(G06 테) / 끝남(G13 채움 + G00 체크) */
function drawCheck(g: Phaser.GameObjects.Graphics, x: number, y: number, s: number, done: boolean): void {
  g.lineStyle(1, hexToNum(done ? GRAY[13] : GRAY[7]), 1).strokeRect(x + 0.5, y + 0.5, s - 1, s - 1);
  if (!done) return;
  g.fillStyle(hexToNum(GRAY[13]), 1).fillRect(x + 1, y + 1, s - 2, s - 2);
  g.lineStyle(2, hexToNum(GRAY[0]), 1);
  g.beginPath();
  g.moveTo(x + 2, y + s * 0.55);
  g.lineTo(x + s * 0.42, y + s - 2.5);
  g.lineTo(x + s - 2, y + 2);
  g.strokePath();
}

/** 인주 도장 (정사각 테 두 줄 + 가운데 글). 지역 (0,0) 가운데 */
function drawSeal(scene: Phaser.Scene, size: number, text: string): Phaser.GameObjects.Container {
  const g = scene.add.graphics();
  const h = size / 2;
  g.fillStyle(SEAL, 0.12).fillRect(-h, -h, size, size);
  g.lineStyle(Math.max(2, size / 16), SEAL, 1).strokeRect(-h + 2, -h + 2, size - 4, size - 4);
  g.lineStyle(1, SEAL_DARK, 0.9).strokeRect(-h + size * 0.14, -h + size * 0.14, size * 0.72, size * 0.72);
  // 인주 글씨: 발광 링 없이 붉은 본색만 (비트맵 글꼴은 정수 배율로)
  const label = scene.add
    .text(0, 0, text, { fontFamily: fontFamily('body'), fontSize: `${FONT.body.px}px`, color: HEALTH_BAR.fill })
    .setOrigin(0.5, 0.5)
    .setScale(size >= 64 ? 2 : 1);
  return scene.add.container(0, 0, [g, label]);
}

/**
 * 61 단계 6 (P14 §1, 계약 §19) 수련장 HUD: 오른쪽 과제 체크 목록(키캡 포함) · 과제 완료 알림 · 방 도장 연출.
 * 스냅샷 `training` 이 있고 지금 방이 마당(hall)이 아니면 목록을 그린다. 지도는 시스템 메뉴 'training'(TrainingMap.ts).
 */
export class TrainingLayer {
  private panel?: NinePanel;
  private objs: Phaser.GameObjects.GameObject[] = [];
  private rowsY: Map<string, { y: number; h: number }> = new Map();
  private sig = '';
  private box = { x: 0, y: 0, w: 0, h: 0 };
  private toast?: Phaser.GameObjects.Container;
  private stamp?: Phaser.GameObjects.Container;
  private stampTimer?: Phaser.Time.TimerEvent;
  private visible = true;

  constructor(
    private scene: Phaser.Scene,
    private opts: { top: () => number },
  ) {}

  subscribe(on: (event: string, h: (p: never) => void) => void): void {
    on(UI_EVENTS.TRAINING_TASK, (p: unknown) => this.taskDone(p));
    on(UI_EVENTS.TRAINING_STAMP, (p: unknown) => this.stamped(p));
  }

  /** 매 스냅샷. overlay = 메뉴·지도·일시정지가 떠 있음 (목록을 숨긴다) */
  render(s: UiSnapshot, overlay: boolean): void {
    const t = trainingOf(s);
    const show = Boolean(t) && !isTrainingHall(t as UiTraining) && !overlay;
    if (!t || isTrainingHall(t)) {
      if (this.sig) this.clear();
      return;
    }
    const rows = taskRows(t, s.weaponVerbs);
    const sig = JSON.stringify([t.room, t.roomName, t.line ?? '', t.stamped, rows, this.opts.top()]);
    if (sig !== this.sig) {
      this.sig = sig;
      this.build(t, rows);
    }
    if (show !== this.visible) {
      this.visible = show;
      this.panel?.setVisible(show);
      for (const o of this.objs) (o as unknown as Phaser.GameObjects.Components.Visible).setVisible(show);
    }
  }

  private clear(): void {
    this.sig = '';
    this.panel?.destroy();
    this.panel = undefined;
    for (const o of this.objs) o.destroy();
    this.objs = [];
    this.rowsY.clear();
  }

  private build(t: UiTraining, rows: TaskRow[]): void {
    this.clear();
    this.sig = JSON.stringify([t.room, t.roomName, t.line ?? '', t.stamped, rows, this.opts.top()]);
    const scene = this.scene;
    const U = TRAINING_UI;
    const W = UI_SCREEN.WIDTH;
    const x = W - U.right - U.w;
    const y = this.opts.top();
    const innerW = U.w - U.padX * 2;
    const add = <T extends Phaser.GameObjects.GameObject>(o: T): T => {
      (o as unknown as Phaser.GameObjects.Components.Depth).setDepth?.(U.depth + 1);
      this.objs.push(o);
      return o;
    };
    let cy = y + U.padY;
    const head = add(
      new GlowText(scene, x + U.padX, cy, fill(trainingText('hudTitle'), { room: t.roomName }), 'ink_accent'),
    );
    const c = doneCount(t);
    if (t.stamped) {
      const seal = add(drawSeal(scene, 18, trainingText('stampMark').slice(0, 1)));
      seal.setPosition(x + U.w - U.padX - 9, cy + 7).setAngle(U.stampTilt);
    } else {
      const cnt = add(
        new GlowText(scene, 0, cy, fill(trainingText('hudCount'), { done: c.done, total: c.total }), 'ink_faint'),
      );
      cnt.placeRight(x + U.w - U.padX, cy);
    }
    cy += head.displayHeight + 2;
    if (t.line) {
      const line = add(new GlowText(scene, x + U.padX, cy, t.line, 'ink_faint', { wrap: innerW }));
      cy += line.displayHeight + 4;
    }
    const g = add(scene.add.graphics());
    g.lineStyle(1, hexToNum(GRAY[5]), 1).lineBetween(x + U.padX, cy + 0.5, x + U.w - U.padX, cy + 0.5);
    cy += 5;
    for (const r of rows) {
      const rowTop = cy;
      drawCheck(g, x + U.padX, cy + 3, U.box, r.done);
      let lx = x + U.padX + U.box + 6;
      if (r.key) {
        const gl = keyGlyph(scene, r.key, 0, r.done);
        add(gl.obj).setPosition(lx, cy);
        lx += gl.width + 5;
      }
      const label = add(
        new GlowText(scene, lx, cy, r.label, r.done ? 'ink_faint' : 'ink_body', { wrap: x + U.w - U.padX - lx }),
      );
      const h = Math.max(U.rowH - 4, label.displayHeight);
      if (r.done) {
        // 끝난 과제: 가운데 줄
        g.lineStyle(1, hexToNum(GRAY[8]), 0.8).lineBetween(lx, cy + 8.5, lx + label.textW, cy + 8.5);
      }
      this.rowsY.set(r.id, { y: rowTop, h });
      cy += h + 4;
    }
    const h = cy - y + U.padY - 4;
    this.panel = inkPanel(scene, x, y, U.w, h).setDepth(U.depth);
    this.box = { x, y, w: U.w, h };
    this.visible = true;
    debugExpose('training', { room: t.room, rows: rows.length, box: this.box });
  }

  /** 과제 하나 완료: 그 줄 반짝 + 위 가운데 알림 */
  private taskDone(p: unknown): void {
    const e = readTaskEvent(p);
    if (!e) return;
    const scene = this.scene;
    const U = TRAINING_UI;
    const row = this.rowsY.get(e.id);
    if (row && this.panel) {
      const flash = scene.add
        .rectangle(this.box.x + 4, row.y - 1, this.box.w - 8, row.h + 2, hexToNum(GRAY[15]), 0.35)
        .setOrigin(0, 0)
        .setDepth(U.depth + 2);
      scene.tweens.add({ targets: flash, alpha: 0, duration: U.flashMs, onComplete: () => flash.destroy() });
    }
    this.toast?.destroy();
    const text = new GlowText(scene, 0, 0, fill(trainingText('taskDone'), { label: e.label }), 'ink_body');
    const w = text.displayWidth + 12 + 18;
    const hgt = 24;
    const bx = Math.round(UI_SCREEN.WIDTH / 2 - w / 2);
    const by = 72;
    const panel = inkPanel(scene, 0, 0, w, hgt);
    const g = scene.add.graphics();
    drawCheck(g, 8, 7, U.box, true);
    text.setPosition(8 + U.box + 6, 4);
    const toast = scene.add
      .container(bx, by, [panel, g, text])
      .setDepth(U.depth + 3)
      .setAlpha(0);
    this.toast = toast;
    scene.tweens.add({ targets: toast, alpha: 1, y: by - 4, duration: 160 });
    scene.tweens.add({
      targets: toast,
      alpha: 0,
      delay: U.toastMs,
      duration: U.toastFadeMs,
      onComplete: () => {
        toast.destroy();
        if (this.toast === toast) this.toast = undefined;
      },
    });
    debugExpose('trainingTask', e);
  }

  /** 방 도장: 가운데에 인주 도장이 찍히고(흔들림 설정 존중) 잠시 뒤 사라진다 */
  private stamped(p: unknown): void {
    const e = readStampEvent(p);
    if (!e) return;
    const scene = this.scene;
    const U = TRAINING_UI;
    this.stampTimer?.remove();
    this.stamp?.destroy();
    const seal = drawSeal(scene, U.stampSize, trainingText('stampMark'));
    const cap = new GlowText(
      scene,
      0,
      0,
      e.all ? trainingText('stampAll') : fill(trainingText('stampLine'), { room: e.name }),
      'ink_accent',
    );
    cap.setPosition(Math.round(-cap.displayWidth / 2), U.stampSize / 2 + 10);
    const box = scene.add
      .container(UI_SCREEN.WIDTH / 2, UI_SCREEN.HEIGHT / 2 - 40, [seal, cap])
      .setDepth(U.depth + 4)
      .setAlpha(0)
      .setScale(2.2);
    seal.setAngle(U.stampTilt);
    this.stamp = box;
    const shake = uiCommands.getUiSnapshot().settings?.shake ?? 1;
    scene.tweens.add({
      targets: box,
      alpha: 1,
      scale: 1,
      duration: U.stampInMs,
      ease: 'Quad.easeIn',
      onComplete: () => {
        if (shake > 0) scene.cameras.main.shake(140, (3 * shake) / UI_SCREEN.WIDTH);
      },
    });
    this.stampTimer = scene.time.delayedCall(U.stampInMs + U.stampHoldMs, () => {
      scene.tweens.add({
        targets: box,
        alpha: 0,
        duration: 300,
        onComplete: () => {
          box.destroy();
          if (this.stamp === box) this.stamp = undefined;
        },
      });
    });
    debugExpose('trainingStamp', e);
  }

  destroy(): void {
    this.clear();
    this.toast?.destroy();
    this.stamp?.destroy();
    this.stampTimer?.remove();
  }
}
