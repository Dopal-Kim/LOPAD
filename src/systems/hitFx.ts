/**
 * 피격 이펙트 (35라운드 1단계, 계약 art-assets.md §3 — anchor `hitbox_center`, directions any 또는 4방향).
 * 시트가 있으면 FxPool 로 재생(아트 JSON note 를 따른다):
 * - `hit_spark` 16×16 any: 적중점, 개체 위 깊이. 치명타면 대신 `crit_burst` 32×32 any.
 * - `blood` 24×24 4방향(공격 진행 방향): 히트박스 중심, 바닥 깊이(개체 아래), 마지막 프레임(얼룩) `BLOOD_STAIN_MS` 유지 후 페이드.
 * - `knock_dust` 16×8 4방향(밀린 방향): 넉백 끝 발 접지점(피벗 8,6), 바닥 깊이.
 * - `player_hit` 24×24 any: 플레이어 hurt 와 동시에 캐릭터 중심, 개체 위 깊이.
 * 없으면 Graphics 로 만든 작은 텍스처(흰 원·점) 플레이스홀더를 트윈으로 보여준다.
 */
import Phaser from 'phaser';
import { COLORS, DEPTH, FEEL, entityDepth } from '../core/Constants';
import { PALETTE } from '../data';
import { FxPool } from './fx';
import { rampFor } from './palette';
import { facingOf, type Facing } from './spriteDefs';

const TEX_SPARK = 'fxph_spark';
const TEX_DOT = 'fxph_dot';

export interface HitFxSummary {
  sheets: Record<string, boolean>;
  placeholders: number;
}

export class HitFx {
  private bloodColor: number = COLORS.HIT_BLOOD_FALLBACK;
  private placeholders = 0;

  constructor(
    private readonly scene: Phaser.Scene,
    private readonly fx: FxPool,
    private readonly random: () => number = Math.random,
  ) {
    this.ensureTextures();
  }

  /** 층 진입: 플레이스홀더 피 색 = 층 램프 base */
  setFloor(floor: number): void {
    const ramp = rampFor(PALETTE, floor);
    const hex = ramp?.[FEEL.PLACEHOLDER.BLOOD_RAMP_INDEX];
    this.bloodColor = hex ? Phaser.Display.Color.HexStringToColor(hex).color : COLORS.HIT_BLOOD_FALLBACK;
  }

  /**
   * 적중 연출: 치명타면 crit_burst(시트) 또는 섬광+링(플레이스홀더), 아니면 섬광.
   * `critFx` 가 있고 그 시트가 있으면 crit_burst 대신 그것을 (급소 dashcrit·암살 assassin — 2차 적중형, anchor hitbox_center 라
   * 적중점이 아니라 대상 히트박스 중심 (critFx.x, critFx.y) 에)
   */
  impact(
    x: number,
    y: number,
    dirX: number,
    dirY: number,
    crit: boolean,
    critFx?: { id: string; x: number; y: number } | null,
  ): void {
    if (crit && critFx && this.fx.has(critFx.id)) {
      this.fx.play(critFx.id, critFx.x, critFx.y, { dir: this.dirOf(dirX, dirY), depth: DEPTH.HIT_FX + 0.01 });
      return;
    }
    if (crit && this.fx.has(FEEL.FX_IDS.CRIT)) {
      this.critBurst(x, y, dirX, dirY);
      return;
    }
    this.spark(x, y, dirX, dirY);
    if (crit) this.critBurst(x, y, dirX, dirY);
  }

  /** 섬광 시트 id: hit_spark JSON `alias`(43라운드 hit_burst) → 상수 SPARK_ALT → hit_spark 순으로 로드된 것 */
  get sparkId(): string {
    const alias = this.fx.sheet(FEEL.FX_IDS.SPARK)?.alias;
    if (alias && this.fx.has(alias)) return alias;
    return this.fx.has(FEEL.FX_IDS.SPARK_ALT) ? FEEL.FX_IDS.SPARK_ALT : FEEL.FX_IDS.SPARK;
  }

  /** 적중점 섬광 */
  spark(x: number, y: number, dirX: number, dirY: number): void {
    const id = this.sparkId;
    if (this.fx.has(id)) {
      this.fx.play(id, x, y, { dir: this.dirOf(dirX, dirY), depth: DEPTH.HIT_FX });
      return;
    }
    const P = FEEL.PLACEHOLDER;
    const img = this.scene.add.image(x, y, TEX_SPARK).setDepth(DEPTH.HIT_FX).setTint(COLORS.HIT_SPARK);
    this.placeholders += 1;
    this.scene.tweens.add({
      targets: img,
      scaleX: P.SPARK_SCALE_TO,
      scaleY: P.SPARK_SCALE_TO,
      alpha: 0,
      duration: P.SPARK_MS,
      onComplete: () => {
        img.destroy();
        this.placeholders -= 1;
      },
    });
  }

  /**
   * 피 튀김: 시트는 히트박스 중심(`cx, cy`)에 바닥 깊이로(방향 행 = 공격 진행 방향, 얼룩 프레임 유지 후 페이드).
   * 플레이스홀더는 적 뒤쪽(`backX, backY`)에서 공격 방향으로 점을 흩뿌린다
   */
  blood(cx: number, cy: number, backX: number, backY: number, dirX: number, dirY: number): void {
    const id = FEEL.FX_IDS.BLOOD;
    if (this.fx.has(id)) {
      this.fx.play(id, cx, cy, {
        dir: this.dirOf(dirX, dirY),
        depth: DEPTH.FX_GROUND,
        holdLastMs: FEEL.BLOOD_STAIN_MS,
      });
      return;
    }
    const P = FEEL.PLACEHOLDER;
    const x = backX;
    const y = backY;
    const base = Math.atan2(dirY, dirX);
    for (let i = 0; i < P.BLOOD_DOTS; i++) {
      const a = base + (this.random() - 0.5) * 2 * P.BLOOD_SPREAD_RAD;
      const d = P.BLOOD_DIST_PX * (0.5 + this.random() * 0.5);
      const dot = this.scene.add.image(x, y, TEX_DOT).setDepth(DEPTH.HIT_FX).setTint(this.bloodColor);
      this.placeholders += 1;
      this.scene.tweens.add({
        targets: dot,
        x: x + Math.cos(a) * d,
        y: y + Math.sin(a) * d + 3, // 살짝 아래로 떨어지는 느낌
        alpha: 0,
        duration: P.BLOOD_MS,
        ease: Phaser.Math.Easing.Quadratic.Out,
        onComplete: () => {
          dot.destroy();
          this.placeholders -= 1;
        },
      });
    }
  }

  /** 치명타 버스트 (적중점, 섬광 위에 추가) */
  critBurst(x: number, y: number, dirX: number, dirY: number): void {
    const id = FEEL.FX_IDS.CRIT;
    if (this.fx.has(id)) {
      this.fx.play(id, x, y, { dir: this.dirOf(dirX, dirY), depth: DEPTH.HIT_FX + 0.01 });
      return;
    }
    const P = FEEL.PLACEHOLDER;
    const g = this.scene.add.graphics().setDepth(DEPTH.HIT_FX + 0.01);
    g.lineStyle(1, this.bloodColor, 1);
    g.strokeCircle(0, 0, P.CRIT_RING_FROM);
    g.setPosition(x, y);
    this.placeholders += 1;
    const k = P.CRIT_RING_TO / P.CRIT_RING_FROM;
    this.scene.tweens.add({
      targets: g,
      scaleX: k,
      scaleY: k,
      alpha: 0,
      duration: P.CRIT_RING_MS,
      onComplete: () => {
        g.destroy();
        this.placeholders -= 1;
      },
    });
  }

  /** 넉백 끝 먼지 (발 접지점, 방향 행 = 밀린 방향, 바닥 깊이) */
  knockDust(x: number, y: number, dirX: number, dirY: number): void {
    const id = FEEL.FX_IDS.DUST;
    if (this.fx.has(id)) {
      this.fx.play(id, x, y, { dir: this.dirOf(dirX, dirY), depth: DEPTH.FX_GROUND });
      return;
    }
    const P = FEEL.PLACEHOLDER;
    // 밀린 방향의 반대(발이 끌린 쪽)로 흩어진다
    const base = Math.atan2(-dirY, -dirX);
    for (let i = 0; i < P.DUST_DOTS; i++) {
      const a = base + (this.random() - 0.5) * 1.2;
      const d = P.DUST_DIST_PX * (0.4 + this.random() * 0.6);
      const dot = this.scene.add
        .image(x, y, TEX_DOT)
        .setDepth(DEPTH.FX_GROUND)
        .setTint(COLORS.KNOCK_DUST)
        .setAlpha(0.8);
      this.placeholders += 1;
      this.scene.tweens.add({
        targets: dot,
        x: x + Math.cos(a) * d,
        y: y + Math.sin(a) * d * 0.4 - 2,
        alpha: 0,
        duration: P.DUST_MS,
        onComplete: () => {
          dot.destroy();
          this.placeholders -= 1;
        },
      });
    }
  }

  /** 플레이어 피격: 시트가 있으면 캐릭터 중심에 개체 위 깊이로 (없으면 기존 흰 플래시만) */
  playerHit(x: number, y: number, footY: number): void {
    const id = FEEL.FX_IDS.PLAYER_HIT;
    if (!this.fx.has(id)) return;
    this.fx.play(id, x, y, { depth: entityDepth(footY) + DEPTH.OVERLAY_STEP * 3 });
  }

  summary(): HitFxSummary {
    const sheets: Record<string, boolean> = {};
    for (const id of Object.values(FEEL.FX_IDS)) sheets[id] = this.fx.has(id);
    return { sheets, placeholders: this.placeholders };
  }

  private dirOf(dx: number, dy: number): Facing {
    return facingOf(dx, dy, 'down');
  }

  /** 플레이스홀더 텍스처: 흰 원(반지름 SPARK_RADIUS)·2×2 점. 틴트로 색을 입힌다 */
  private ensureTextures(): void {
    const tex = this.scene.textures;
    if (!tex.exists(TEX_SPARK)) {
      const r = FEEL.PLACEHOLDER.SPARK_RADIUS;
      const g = this.scene.make.graphics({ x: 0, y: 0 }, false);
      g.fillStyle(0xffffff, 1);
      g.fillCircle(r, r, r);
      g.generateTexture(TEX_SPARK, r * 2, r * 2);
      g.destroy();
    }
    if (!tex.exists(TEX_DOT)) {
      const g = this.scene.make.graphics({ x: 0, y: 0 }, false);
      g.fillStyle(0xffffff, 1);
      g.fillRect(0, 0, 2, 2);
      g.generateTexture(TEX_DOT, 2, 2);
      g.destroy();
    }
  }
}
