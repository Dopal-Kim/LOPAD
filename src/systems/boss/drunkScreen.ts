/**
 * 54라운드 Q7 '세상이 돈다': 게임 월드 카메라를 ±tiltDeg 로 천천히(periodMs) 기울이고(시작·끝 rampMs 동안 부드럽게),
 * WebGL 이면 내장 postFX 로 약한 가장자리 흐림(TiltShift)·비네팅. HUD 는 별도 씬이라 영향 없음.
 * - `feelSettings.tilt` 배율 (0 = 기울기·흐림 생략, 패턴은 그대로 — 흔들림 끄기와 같은 방식)
 * - 회전 동안 타일맵 레이어 컬링 여유(setCullPadding)를 늘려 모서리 타일이 빠지지 않게. 라이트맵은 Lighting 이 덮개 배율로 키운다
 */
import Phaser from 'phaser';
import { BOSS_FX } from '../../core/Constants';
import { feelSettings } from '../feel';
import { tiltAt, type TiltParams } from './tiltMath';

type PostFx = Phaser.GameObjects.Components.FX;

export class DrunkScreen {
  private params: TiltParams | null = null;
  private startAt = 0;
  private padded = false;
  private fx: Phaser.FX.Controller[] = [];
  private readonly webgl: boolean;
  private blurFx: Phaser.FX.Controller | null = null;
  private lowFrames = 0;
  /** 디버그: 지금 기울기 (도) · fps 가 낮아 흐림을 뗐는지 */
  angleDeg = 0;
  blurDropped = false;

  constructor(private readonly scene: Phaser.Scene) {
    this.webgl = scene.sys.game.renderer.type === Phaser.WEBGL;
  }

  get active(): boolean {
    return this.params !== null;
  }

  begin(p: TiltParams, now: number): void {
    this.params = { ...p };
    this.startAt = now;
    this.setPadding(true);
    this.addFx(p.blur ?? 1);
  }

  update(time: number): void {
    const p = this.params;
    if (!p) return;
    const t = time - this.startAt;
    if (t >= p.durationMs) {
      this.stop();
      return;
    }
    this.angleDeg = tiltAt(t, p) * feelSettings.tilt;
    this.guardFps();
    this.scene.cameras.main.setRotation((this.angleDeg * Math.PI) / 180);
  }

  /**
   * 가장자리 흐림(Bokeh 100회 표본, 1920×1080)은 내장 GPU 에서 무거울 수 있다 → 실제 fps 가 TILT.MIN_FPS 아래로
   * TILT.LOW_FRAMES 프레임 이어지면 흐림만 떼고(비네팅·기울기는 유지) 이 판 동안 다시 붙이지 않는다
   */
  private guardFps(): void {
    if (!this.blurFx) return;
    const T = BOSS_FX.TILT;
    const fps = this.scene.sys.game.loop.actualFps;
    this.lowFrames = fps < T.MIN_FPS ? this.lowFrames + 1 : 0;
    if (this.lowFrames < T.LOW_FRAMES) return;
    const pfx = (this.scene.cameras.main as unknown as { postFX?: PostFx }).postFX;
    pfx?.remove(this.blurFx);
    this.fx = this.fx.filter((f) => f !== this.blurFx);
    this.blurFx = null;
    this.blurDropped = true;
  }

  stop(): void {
    this.params = null;
    this.angleDeg = 0;
    this.scene.cameras.main?.setRotation(0);
    this.setPadding(false);
    this.removeFx();
  }

  private setPadding(on: boolean): void {
    if (this.padded === on) return;
    this.padded = on;
    const n = on ? BOSS_FX.TILT.CULL_PADDING_TILES : 1;
    for (const o of this.scene.children.list) if (o instanceof Phaser.Tilemaps.TilemapLayer) o.setCullPadding(n, n);
  }

  private addFx(blur: number): void {
    if (!this.webgl || feelSettings.tilt <= 0 || blur <= 0 || this.fx.length > 0) return;
    const pfx = (this.scene.cameras.main as unknown as { postFX?: PostFx }).postFX;
    if (!pfx) return;
    const T = BOSS_FX.TILT;
    const k = Math.min(1, blur);
    // contrast 0: Bokeh 셰이더의 대비(col²)는 화면을 어둡고 붉게 만든다
    const tilt = pfx.addTiltShift(T.BLUR_RADIUS, T.BLUR_AMOUNT * k, 0, 1, 1, T.BLUR_STRENGTH * k);
    const vig = pfx.addVignette(0.5, 0.5, T.VIGNETTE_RADIUS, T.VIGNETTE_STRENGTH * k);
    this.blurFx = tilt as unknown as Phaser.FX.Controller;
    this.lowFrames = 0;
    this.fx = [this.blurFx, vig as unknown as Phaser.FX.Controller];
  }

  private removeFx(): void {
    const pfx = (this.scene.cameras.main as unknown as { postFX?: PostFx } | undefined)?.postFX;
    for (const f of this.fx) pfx?.remove(f);
    this.fx = [];
    this.blurFx = null;
  }

  summary(): Record<string, unknown> {
    return {
      active: this.active,
      angleDeg: +this.angleDeg.toFixed(2),
      fx: this.fx.length,
      blurDropped: this.blurDropped,
      webgl: this.webgl,
      padded: this.padded,
      remainingMs: this.params
        ? Math.max(0, Math.round(this.startAt + this.params.durationMs - this.scene.time.now))
        : 0,
    };
  }

  destroy(): void {
    this.stop();
  }
}
