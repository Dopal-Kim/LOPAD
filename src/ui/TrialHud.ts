import Phaser from 'phaser';
import { UI_SCREEN, type UiNodeGraded, type UiNodeTrial } from '../contract/ui';
import { gradedView, trialView } from './buildView';
import { GlowText } from './glow';
import { KIT, NinePanel, SLICE, accentHex, inkPanel } from './kit';
import { r60Text } from './text';
import { GRAY, LAYOUT, STRUCT, hexToNum } from './theme';
import { GRADE_CARD, TRIAL } from './themeBuild';

/**
 * 60라운드 계약 §14.10 성과 진행 칩 — 잔 구간 전투·위험 노드 진행 중(`UiSnapshot.nodeTrial`)에만 상단 가운데(도전 판이
 * 떠 있으면 그 아래): '32초'(남은 제한 시간, 올림) · '무피격'/'피격' + 아래 시간 선. 완(完) 조건 두 가지를 읽게 한다.
 * 남은 시간이 적으면 강조색, 피격이면 흐림.
 */
export class TrialChip {
  private box?: Phaser.GameObjects.Container;
  private panel?: NinePanel;
  private timeT?: GlowText;
  private hitT?: GlowText;
  private bar?: Phaser.GameObjects.Graphics;
  private sig = '';
  private w = 0;

  constructor(private scene: Phaser.Scene) {}

  render(t: UiNodeTrial | null | undefined, show: boolean, challengeOn: boolean, stageIndex: number): void {
    const v = show ? trialView(t, r60Text) : null;
    if (!v) {
      this.hide();
      return;
    }
    if (!this.box) this.build(stageIndex);
    const sig = `${v.text}|${v.hitText}|${Math.round(v.ratio * 100)}|${stageIndex}`;
    if (sig !== this.sig) {
      this.sig = sig;
      const low = v.over || v.ratio <= TRIAL.lowRatio;
      this.timeT!.setText(v.text).setGlowStyle(low ? 'ink_accent' : 'ink_body');
      this.hitT!.setText(v.hitText)
        .setGlowStyle(v.hit ? 'ink_faint' : 'ink_body')
        .setX(this.timeT!.x + this.timeT!.textW + 8);
      const w = this.hitT!.x + this.hitT!.textW + 2 + 8;
      if (w !== this.w) {
        this.w = w;
        this.panel!.resize(w, STRUCT.chipH);
      }
      const g = this.bar!.clear();
      const bw = this.w - 16;
      g.fillStyle(hexToNum(GRAY[3]), 1).fillRect(8, STRUCT.chipH - 6, bw, TRIAL.barH);
      const fw = Math.round(bw * v.ratio);
      if (fw > 0)
        g.fillStyle(hexToNum(accentHex(this.scene, stageIndex, low ? 22 : 25)), 1).fillRect(
          8,
          STRUCT.chipH - 6,
          fw,
          TRIAL.barH,
        );
    }
    this.box!.setPosition(
      Math.round(UI_SCREEN.WIDTH / 2 - this.w / 2),
      challengeOn ? TRIAL.top + TRIAL.belowChallenge : TRIAL.top,
    ).setVisible(true);
  }

  private build(si: number): void {
    const scene = this.scene;
    this.panel = inkPanel(scene, 0, 0, 40, STRUCT.chipH);
    this.timeT = new GlowText(scene, 6, 3, '', 'ink_body', { stageIndex: si });
    this.hitT = new GlowText(scene, 6, 3, '', 'ink_body', { stageIndex: si });
    this.bar = scene.add.graphics();
    this.box = scene.add.container(0, 0, [this.panel, this.timeT, this.hitT, this.bar]).setDepth(STRUCT.hudDepth);
    this.sig = '';
    this.w = 0;
  }

  private hide(): void {
    if (!this.box) return;
    this.box.destroy();
    this.box = undefined;
    this.panel = undefined;
    this.timeT = undefined;
    this.hitT = undefined;
    this.bar = undefined;
  }

  destroy(): void {
    this.hide();
  }
}

/**
 * 60라운드 계약 §14.10 `NODE_GRADED` 일기장 도장 연출 — 상단 가운데 종이 쪽지(`panel_paper`): 왼쪽 큰 도장(完·良, 2배 정수,
 * 바랜 잉크 α0.85, 위에서 살짝 내려와 찍힘) / 오른쪽 결과 문구(시스템) · '무피격 ○ · 제한 시간 ×' · '+20 전표 +15 개성'.
 * 등급 없음(null)이면 도장 없이 글만. 2.4초 뒤 사라진다. 한 번에 하나(새 결과가 오면 바꾼다).
 */
export class GradeCard {
  private box?: Phaser.GameObjects.Container;
  private timer?: Phaser.Time.TimerEvent;

  constructor(private scene: Phaser.Scene) {}

  show(g: UiNodeGraded | null | undefined, goldName: string, stageIndex: number): void {
    const v = gradedView(g, goldName, r60Text);
    if (!v) return;
    this.clear();
    const scene = this.scene;
    const pad = 14;
    const objs: Phaser.GameObjects.GameObject[] = [];
    let x = pad;
    let stamp: GlowText | undefined;
    if (v.stamp) {
      // 도장 = 바랜 발광 잉크 (키트 §1.3 도장 S4 본색 + S5) — 종이 본문 글자 스타일을 2배로
      stamp = new GlowText(scene, x, pad, v.stamp, 'page_body', { scale: GRADE_CARD.stampScale, stageIndex });
      stamp.setAlpha(LAYOUT.stampAlpha);
      x += stamp.displayWidth + 10;
    }
    const lines = [v.text || v.name, v.conds, v.deltas].filter(Boolean);
    const texts = lines.map(
      (t, i) => new GlowText(scene, x, pad, t, i === 0 ? 'page_selected' : 'page_body', { stageIndex, wrap: 260 }),
    );
    let y = pad;
    for (const t of texts) {
      t.setY(y);
      y += t.displayHeight + 2;
    }
    const textW = Math.max(...texts.map((t) => t.displayWidth));
    const w = Math.max(GRADE_CARD.minW, x + textW + pad);
    const h = Math.max(y, pad + (stamp?.displayHeight ?? 0)) + pad - 2;
    const panel = new NinePanel(scene, 0, 0, KIT.panelPaper, SLICE.panelPaper, w, h);
    objs.push(panel);
    if (stamp) {
      stamp.setY(Math.round(h / 2 - stamp.displayHeight / 2));
      objs.push(stamp);
    }
    objs.push(...texts);
    const bx = Math.round(UI_SCREEN.WIDTH / 2 - w / 2);
    const box = scene.add.container(bx, GRADE_CARD.top, objs).setDepth(GRADE_CARD.depth).setAlpha(0);
    this.box = box;
    scene.tweens.add({ targets: box, alpha: 1, duration: GRADE_CARD.inMs });
    if (stamp) {
      const sy = stamp.y;
      stamp.setY(sy - GRADE_CARD.drop);
      scene.tweens.add({ targets: stamp, y: sy, duration: GRADE_CARD.inMs, ease: 'Quad.easeIn' });
    }
    this.timer = scene.time.delayedCall(GRADE_CARD.inMs + GRADE_CARD.holdMs, () => {
      scene.tweens.add({
        targets: box,
        alpha: 0,
        duration: GRADE_CARD.fadeMs,
        onComplete: () => {
          if (this.box === box) this.clear();
          else box.destroy();
        },
      });
    });
  }

  clear(): void {
    this.timer?.remove();
    this.timer = undefined;
    if (this.box) {
      this.scene.tweens.killTweensOf([this.box, ...this.box.list]);
      this.box.destroy();
    }
    this.box = undefined;
  }

  destroy(): void {
    this.clear();
  }
}
