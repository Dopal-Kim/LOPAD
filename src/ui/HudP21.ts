import Phaser from 'phaser';
import { UI_SCREEN, type UiSnapshot } from '../contract/ui';
import { debugExpose } from './debug';
import { P21_EVENTS } from './eventsR61';
import {
  executableOf,
  executableOffUid,
  executeMsOf,
  lowHpAlpha,
  lowHpOf,
  snapshotWound,
  woundOf,
  type Wound,
} from './p21View';
import { hexToNum } from './theme';
import { DARK, EXEC_EDGE, EXEC_MARK as M, LOW_HP_VIG } from './themeP21';
import { vignetteImage } from './vignette';

type On = <T>(event: string, handler: (p: T) => void) => void;

export interface HudP21Deps {
  /** 상흔이 바뀌면 (전투 묶음 체력 막대 균열) */
  wound: (w: Wound) => void;
}

/**
 * P21 UI (contracts/dark-brutal §2): 저HP 피 비네트 · 처형 가능 표식 · 처형 순간 가장자리 · 주인공 상흔 전달.
 *  - 저HP(`ui:low-hp`): HUD 맨 아래 층 검붉은 가장자리 — 심장 박동 '쿵·쿵' 맥박, 설정 섬광 끄면 맥박 없이 고정.
 *  - 처형 가능: 자리는 스냅샷 `executable {uid, screen}`(적 발밑, 매 STATE) — 짧은 낫 모양(예고 색 '기회' #ffe08a + 먹 테).
 *    `ui:enemy-executable` on:false 면 다음 STATE 를 기다리지 않고 바로 거둔다.
 *  - 처형(`ui:player-execute`): 동작 동안 표식을 숨기고 화면 가장자리가 짧게 검붉게 조였다 풀린다.
 *  - 상흔(`ui:player-wounded` · snapshot.player.wound): 전투 묶음으로 넘긴다.
 */
export class HudP21 {
  private vig: Phaser.GameObjects.Image;
  private edge: Phaser.GameObjects.Image;
  private g: Phaser.GameObjects.Graphics;
  private low = false;
  private lowK = 0;
  private wound: Wound = { stage: 0, arrows: 0 };
  private hidden = false;
  /** 마지막 STATE (설정 섬광·처형 자리) */
  private last: UiSnapshot | null = null;
  /** 꺼진 개체 (스냅샷이 따라올 때까지) · 처형 동작이 끝나는 시각 */
  private offUid: number | null = null;
  private markHideUntil = 0;
  /** 마지막 UPDATE 시각 (게임 루프 시간 — markHideUntil 과 같은 시계) */
  private nowT = 0;
  private markShown = false;

  constructor(
    private scene: Phaser.Scene,
    private deps: HudP21Deps,
  ) {
    this.vig = vignetteImage(scene, DARK.bloodDeep, LOW_HP_VIG.depth).setAlpha(0).setVisible(false);
    this.edge = vignetteImage(scene, DARK.bloodDeep, EXEC_EDGE.depth).setAlpha(0).setVisible(false);
    this.g = scene.add.graphics().setDepth(M.depth);
    scene.events.on(Phaser.Scenes.Events.UPDATE, this.update);
  }

  subscribe(on: On): void {
    on(P21_EVENTS.LOW_HP, (p: unknown) => {
      const v = lowHpOf(p);
      if (v !== null) this.low = v;
    });
    on(P21_EVENTS.PLAYER_WOUNDED, (p: unknown) => this.setWound(woundOf(p)));
    on(P21_EVENTS.ENEMY_EXECUTABLE, (p: unknown) => {
      const off = executableOffUid(p);
      if (off !== null) this.offUid = off;
    });
    on(P21_EVENTS.PLAYER_EXECUTE, (p: unknown) => this.execute(p));
  }

  /** 매 STATE */
  render(s: UiSnapshot, hidden: boolean): void {
    this.hidden = hidden;
    this.last = s;
    const w = snapshotWound(s);
    if (w) this.setWound(w);
  }

  /** 매 프레임 (씬 UPDATE) */
  private update = (now: number, dtMs: number): void => {
    const s = this.last;
    this.nowT = now;
    // 저HP 비네트: 들어오고 나가는 것은 천천히
    const target = this.low && !this.hidden ? 1 : 0;
    const span = target > this.lowK ? LOW_HP_VIG.fadeInMs : LOW_HP_VIG.fadeOutMs;
    this.lowK = Phaser.Math.Clamp(this.lowK + (Math.sign(target - this.lowK) * dtMs) / span, 0, 1);
    const a = this.lowK * lowHpAlpha(now, s?.settings?.flash !== false, LOW_HP_VIG);
    this.vig.setVisible(a > 0.003).setAlpha(a);
    // 처형 표식
    const g = this.g.clear();
    const ex = executableOf(s);
    if (ex && ex.uid !== this.offUid) this.offUid = null;
    const show = Boolean(ex) && !this.hidden && ex?.uid !== this.offUid && now >= this.markHideUntil;
    if (show !== this.markShown) {
      this.markShown = show;
      debugExpose('execMark', show ? ex : null);
    }
    if (!ex || !show) return;
    const pulse = 0.5 + 0.5 * Math.sin((2 * Math.PI * now) / M.pulseMs);
    drawSickle(g, Math.round(ex.x), Math.round(ex.y) + M.dy, M.alpha[0] + (M.alpha[1] - M.alpha[0]) * pulse);
  };

  /** 방을 떠남·사망·런 끝 */
  clear(): void {
    this.g.clear();
    this.low = false;
    this.lowK = 0;
    this.vig.setVisible(false);
    this.scene.tweens.killTweensOf(this.edge);
    this.edge.setVisible(false);
  }

  destroy(): void {
    this.scene.events.off(Phaser.Scenes.Events.UPDATE, this.update);
    this.clear();
    this.vig.destroy();
    this.edge.destroy();
    this.g.destroy();
  }

  private setWound(w: Wound | null): void {
    if (!w || (w.stage === this.wound.stage && w.arrows === this.wound.arrows)) return;
    this.wound = w;
    this.deps.wound(w);
    debugExpose('wound', w);
  }

  private execute(p: unknown): void {
    this.markHideUntil = this.nowT + executeMsOf(p);
    if (this.hidden) return;
    const flash = this.last?.settings?.flash !== false;
    const e = this.edge;
    const W = UI_SCREEN.WIDTH;
    const H = UI_SCREEN.HEIGHT;
    this.scene.tweens.killTweensOf(e);
    // 화면보다 크게 시작해 화면 크기로 좁혀 들어온다 (가장자리가 비지 않게 1 아래로는 줄이지 않는다)
    const sq = flash ? EXEC_EDGE.squeeze : 1;
    e.setVisible(true)
      .setAlpha(0)
      .setDisplaySize(W * sq, H * sq);
    const peak = flash ? EXEC_EDGE.alpha : EXEC_EDGE.alphaNoFlash;
    this.scene.tweens.chain({
      targets: e,
      tweens: [
        { alpha: peak, displayWidth: W, displayHeight: H, duration: EXEC_EDGE.inMs },
        { alpha: peak, duration: EXEC_EDGE.holdMs },
        {
          alpha: 0,
          displayWidth: W * (1 + (sq - 1) / 2),
          displayHeight: H * (1 + (sq - 1) / 2),
          duration: EXEC_EDGE.outMs,
          ease: 'Quad.easeOut',
          onComplete: () => e.setVisible(false),
        },
      ],
    });
    debugExpose('execute', { flash });
  }
}

/** 낫 모양 (발밑에 눕힌 짧은 초승달 날 + 날 끝·자루) — 먹 테 + 기회 색 */
function drawSickle(g: Phaser.GameObjects.Graphics, cx: number, cy: number, alpha: number): void {
  const blade: Phaser.Math.Vector2[] = [];
  // 아래로 휜 호 (20° → 160°), 세로로 눌러 바닥에 눕힌다
  for (let k = 0; k <= 8; k++) {
    const a = Phaser.Math.DegToRad(20 + (140 * k) / 8);
    blade.push(new Phaser.Math.Vector2(cx + Math.cos(a) * M.r, cy + Math.sin(a) * M.r * M.flat));
  }
  const tip = blade[0];
  const end = blade[blade.length - 1];
  const stroke = (w: number, color: number, a: number): void => {
    g.lineStyle(w, color, a).strokePoints(blade, false);
    g.lineBetween(tip.x, tip.y, tip.x + 2, tip.y - 3);
    g.lineBetween(end.x, end.y, end.x - 4, end.y - 1);
  };
  stroke(M.thick + 2, hexToNum(DARK.ink), alpha * 0.85);
  stroke(M.thick, hexToNum(M.color), alpha);
}
