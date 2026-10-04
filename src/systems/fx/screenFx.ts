/**
 * 화면 섬광·색 오버레이 (42라운드 Q3, fx-design §6.2). 카메라 위 풀스크린 사각형(scrollFactor 0, DEPTH.SCREEN_FX).
 * - 섬광: 시트 JSON `flash {color, alpha, ms}`(거합·만월·쌍격·난무·지진·분쇄·파쇄·중시 적중·패링) + 보스 페이즈 전환(+ 진화 선택).
 *   사각형 하나를 쓰고 alpha → 0 으로 ms 동안 줄인다. 연속 발동 시 **알파를 더하지 않고 큰 쪽**(남은 알파 ≤ 새 알파면 교체).
 * - 채도 감소(보스 페이즈 전환 감쇠, 선택적으로 히트스톱): WebGL 이면 `camera.postFX` ColorMatrix 를 **필요할 때만** 붙이고,
 *   캔버스면 회색 사각형 SATURATION 블렌드(알파 = v).
 * - 사망: 서서히 어둡게(결과 화면까지 유지).
 * 시간은 update(time) 로 잰다(트윈 없음 — 히트스톱 중에도 섬광은 줄어든다). UI 는 별도 씬이라 덮지 않는다.
 * `feelSettings.flash` 가 false 면 전부 무시.
 */
import Phaser from 'phaser';
import { DEPTH, FEEL } from '../core/Constants';
import { PALETTE } from '../data';
import { feelSettings } from './feel';
import { hexToInt, rampFor } from './palette';
import { flashAlphaAt } from './trailMath';

export interface ScreenFxSummary {
  flash: { color: number; alpha: number } | null;
  /** 지금까지 낸 섬광 수 (디버그) */
  flashCount: number;
  lastFlash: { color: number; alpha: number; ms: number } | null;
  death: number;
  desaturation: number;
  mode: 'postfx' | 'blend';
  hitStopped: boolean;
}

export class ScreenFx {
  private evolveColor: number = FEEL.SCREEN.DEFAULT_FLASH.COLOR;
  private hitStopped = false;
  private phaseDesatFrom = 0;
  private phaseDesatUntil = 0;
  private phaseDesatAmount = 0;
  private applied = 0;
  private readonly webgl: boolean;
  private matrix: Phaser.FX.ColorMatrix | null = null;
  private grayRect: Phaser.GameObjects.Rectangle | null = null;
  private readonly flashRect: Phaser.GameObjects.Rectangle;
  private flashState: { color: number; alpha0: number; start: number; ms: number } | null = null;
  private deathRect: Phaser.GameObjects.Rectangle | null = null;
  private flashCount = 0;
  private lastFlash: { color: number; alpha: number; ms: number } | null = null;

  constructor(private readonly scene: Phaser.Scene) {
    this.webgl = scene.sys.game.renderer.type === Phaser.WEBGL;
    this.flashRect = this.rect(0xffffff, 0).setVisible(false);
  }

  /** 층 진입: 진화 오버레이 색 = 층 램프 light1 */
  setFloor(floor: number): void {
    const hex = rampFor(PALETTE, floor)?.[FEEL.SCREEN.EVOLVE.RAMP_INDEX];
    this.evolveColor = hex ? hexToInt(hex) : FEEL.SCREEN.DEFAULT_FLASH.COLOR;
  }

  /** 단색 섬광: alpha 에서 0 으로 ms 동안. 진행 중인 섬광의 남은 알파보다 크거나 같을 때만 교체 (합산 없음) */
  flash(color: number, ms: number, alpha: number): void {
    if (!feelSettings.flash || ms <= 0 || alpha <= 0) return;
    const now = this.scene.time.now;
    const cur = this.flashState;
    if (cur && flashAlphaAt(cur.alpha0, cur.ms, now - cur.start) > alpha) return;
    this.flashState = { color, alpha0: alpha, start: now, ms };
    this.flashRect.setFillStyle(color, 1).setAlpha(alpha).setVisible(true);
    this.flashCount += 1;
    this.lastFlash = { color, alpha, ms };
  }

  crit(): void {
    const C = FEEL.SCREEN.CRIT;
    this.flash(C.COLOR, C.MS, C.ALPHA);
  }

  evolve(): void {
    const E = FEEL.SCREEN.EVOLVE;
    this.flash(this.evolveColor, E.MS, E.ALPHA);
  }

  /** 보스 페이즈 전환: 흰 섬광 + 채도 감소 감쇠 */
  bossPhase(): void {
    const B = FEEL.SCREEN.BOSS_PHASE;
    this.flash(B.COLOR, B.MS, B.ALPHA);
    if (!feelSettings.flash || B.DESAT <= 0) return;
    const now = this.scene.time.now;
    this.phaseDesatFrom = now;
    this.phaseDesatUntil = now + B.DESAT_MS;
    this.phaseDesatAmount = B.DESAT;
  }

  /** 사망: ms 동안 서서히 어둡게 (결과 화면까지 유지) */
  death(ms: number): void {
    if (!feelSettings.flash || this.deathRect) return;
    const D = FEEL.SCREEN.DEATH;
    const r = this.rect(D.COLOR, 0);
    this.deathRect = r;
    this.scene.tweens.add({ targets: r, alpha: D.ALPHA, duration: Math.max(D.MIN_MS, ms) });
  }

  /** 히트스톱 중 채도 감소 (FEEL.SCREEN.HITSTOP_DESAT > 0 일 때만) */
  setHitStopped(on: boolean): void {
    this.hitStopped = on;
  }

  /** 매 프레임: 섬광 감쇠 · 채도 감소 합산 적용 */
  update(time: number): void {
    const f = this.flashState;
    if (f) {
      const a = flashAlphaAt(f.alpha0, f.ms, time - f.start);
      if (a <= 0) {
        this.flashState = null;
        this.flashRect.setVisible(false).setAlpha(0);
      } else this.flashRect.setAlpha(a);
    }
    let v = this.hitStopped && feelSettings.flash ? FEEL.SCREEN.HITSTOP_DESAT : 0;
    if (time < this.phaseDesatUntil) {
      const t = (time - this.phaseDesatFrom) / (this.phaseDesatUntil - this.phaseDesatFrom);
      v = Math.max(v, this.phaseDesatAmount * (1 - t));
    }
    v = +Math.min(1, Math.max(0, v)).toFixed(3);
    if (v === this.applied) return;
    this.applied = v;
    this.applyDesat(v);
  }

  summary(): ScreenFxSummary {
    const f = this.flashState;
    return {
      flash: f ? { color: f.color, alpha: +this.flashRect.alpha.toFixed(3) } : null,
      flashCount: this.flashCount,
      lastFlash: this.lastFlash,
      death: this.deathRect ? +this.deathRect.alpha.toFixed(3) : 0,
      desaturation: this.applied,
      mode: this.webgl ? 'postfx' : 'blend',
      hitStopped: this.hitStopped,
    };
  }

  destroy(): void {
    this.flashRect.destroy();
    this.deathRect?.destroy();
    this.deathRect = null;
    this.grayRect?.destroy();
    this.grayRect = null;
    this.removeMatrix();
    this.flashState = null;
  }

  /** v > 0 이면 채도 감소를 켜고(WebGL: ColorMatrix 를 그때 붙임), 0 이면 떼어 평소에는 후처리 패스가 없다 */
  private applyDesat(v: number): void {
    if (this.webgl) {
      if (v <= 0) {
        this.removeMatrix();
        return;
      }
      if (!this.matrix) {
        const fx = (this.scene.cameras.main as unknown as { postFX?: Phaser.GameObjects.Components.FX }).postFX;
        this.matrix = fx ? fx.addColorMatrix() : null;
      }
      if (this.matrix) {
        this.matrix.reset();
        this.matrix.saturate(-v);
        return;
      }
    }
    if (!this.grayRect)
      this.grayRect = this.rect(FEEL.SCREEN.DESAT_FALLBACK_COLOR, 0)
        .setBlendMode(Phaser.BlendModes.SATURATION)
        .setVisible(false);
    this.grayRect.setAlpha(v).setVisible(v > 0);
  }

  private removeMatrix(): void {
    if (!this.matrix) return;
    const cam = this.scene.cameras.main as unknown as { postFX?: Phaser.GameObjects.Components.FX };
    // 타입 선언이 Controller 로 좁아 캐스트 (런타임 ColorMatrix 는 Controller 를 상속)
    cam.postFX?.remove(this.matrix as unknown as Phaser.FX.Controller);
    this.matrix = null;
  }

  private rect(color: number, alpha: number): Phaser.GameObjects.Rectangle {
    const cam = this.scene.cameras.main;
    return this.scene.add
      .rectangle(0, 0, cam.width, cam.height, color, 1)
      .setOrigin(0, 0)
      .setScrollFactor(0)
      .setDepth(DEPTH.SCREEN_FX)
      .setAlpha(alpha);
  }
}
