/**
 * 54라운드 Q18 보스 불타기: 보스가 불붙은 술 웅덩이(LiquorPools 불 칸) 위에 서 있으면 **피해 없이** 불타는 상태 —
 * 몸 불길 오버레이(`fx/v3/boss1_onfire` phaseFrames ignite → loop, 나오면 lingerMs 뒤 out) + 불빛(JSON lightByPhase·light).
 * 타는 동안 플레이어가 보스 몸에 닿으면 touchTickMs 마다 불 피해(접촉 공격과 별개). 오버레이 시트가 없으면 기존 fire_pool 을 몸에 얹는다(임시).
 * 상태 흐름은 `burnMath` (테스트), 이 파일은 그림·빛·피해 연결. BossArena 가 만들고 매 프레임 update.
 */
import Phaser from 'phaser';
import { BOSS_FX, DEPTH, fxLitDepth } from '../../core/Constants';
import type { BossOnFireParams } from '../../data/types';
import type { Mob } from '../../objects/Mob';
import type { FxHandle, FxPool } from '../fx';
import { lightRegistryOf, type LightSource } from '../lighting/lightRegistry';
import { spriteLibrary } from '../sprites';
import { FX_ACTION, artScale, frameDurations, type LightSpec, type SheetDef } from '../spriteDefs';
import { lightOffsetOf } from '../../world/tileskin';
import {
  burnColumn,
  isBurning,
  newBurnState,
  phaseLengthMs,
  stepBurn,
  type BurnPhase,
  type BurnTiming,
} from './burnMath';

export interface BossBurnHost {
  scene: Phaser.Scene;
  fx: FxPool;
  boss(): Mob | null;
  /** 사각형(보스 발밑)이 불붙은 웅덩이에 닿는지 */
  fireUnder(r: Phaser.Geom.Rectangle): boolean;
  player: {
    body: Phaser.Physics.Arcade.Body;
    takeHit(attack: number, time: number, source?: { dirX: number; dirY: number }): unknown;
  };
  /** 불붙은 순간 (효과음) */
  onIgnite(): void;
}

/** 오버레이를 숨기는 보스 동작 (누운 그림 — 아트 anchorNote: fall·death 에서는 숨김 권장) */
const HIDE_ON_ACTIONS = ['fall', 'death'] as const;

export class BossBurn {
  readonly state = newBurnState();
  private sprite: Phaser.GameObjects.Sprite | null = null;
  private fallback: FxHandle | null = null;
  private light: LightSource | null = null;
  private lightPhase: BurnPhase = 'off';
  private nextTouchAt = 0;
  private readonly foot = new Phaser.Geom.Rectangle();
  private readonly touch = new Phaser.Geom.Rectangle();
  private readonly playerRect = new Phaser.Geom.Rectangle();
  /** 디버그 */
  readonly debug = { ignites: 0, touchHits: 0 };

  constructor(
    private readonly host: BossBurnHost,
    private readonly P: BossOnFireParams,
  ) {}

  private get def(): SheetDef | undefined {
    const d = spriteLibrary.sheet(BOSS_FX.SHEETS.ONFIRE, FX_ACTION);
    const tex = spriteLibrary.textureKey(BOSS_FX.SHEETS.ONFIRE, FX_ACTION);
    return d && tex && this.host.scene.textures.exists(tex) ? d : undefined;
  }

  get burning(): boolean {
    return isBurning(this.state);
  }

  private timing(def: SheetDef | undefined): BurnTiming {
    const F = BOSS_FX.ONFIRE;
    const d = def ? frameDurations(def) : [];
    return {
      igniteMs: phaseLengthMs(def?.phaseFrames?.ignite, d, F.FALLBACK_IGNITE_MS),
      outMs: phaseLengthMs(def?.phaseFrames?.out, d, F.FALLBACK_OUT_MS),
      lingerMs: this.P.lingerMs,
    };
  }

  update(time: number): void {
    const b = this.host.boss();
    if (!b) {
      this.stop();
      return;
    }
    const body = b.body;
    const fw = body.width * this.P.footWidthRatio;
    this.foot.setTo(body.center.x - fw / 2, body.bottom - this.P.footHeightPx, fw, this.P.footHeightPx);
    const def = this.def;
    if (stepBurn(this.state, this.host.fireUnder(this.foot), time, this.timing(def)) === 'ignited') {
      this.debug.ignites++;
      this.host.onIgnite();
    }
    this.draw(b, def, time);
    this.syncLight(b, def);
    if (this.burning) this.touchFire(b, time);
  }

  // --- 그림 ---

  private draw(b: Mob, def: SheetDef | undefined, time: number): void {
    const phase = this.state.phase;
    if (phase === 'off') {
      this.hideArt();
      return;
    }
    if (!def) {
      this.drawFallback(b, phase);
      return;
    }
    const tex = spriteLibrary.textureKey(BOSS_FX.SHEETS.ONFIRE, FX_ACTION)!;
    if (!this.sprite) {
      this.sprite = this.host.scene.add
        .sprite(b.x, b.y, tex, 0)
        .setOrigin(def.pivot.x / def.frameWidth, def.pivot.y / def.frameHeight)
        .setScale(artScale(def));
    }
    const cols = def.phaseFrames?.[phase] ?? [];
    const col = burnColumn(cols, frameDurations(def), time - this.state.since, phase === 'loop');
    const row = Math.max(0, def.directions.indexOf(b.visual.facing));
    // 보스 스프라이트와 같은 자리·같은 방향 행, 보스 바로 위 깊이(조명 위 띠 — fx 규칙)
    this.sprite
      .setPosition(b.x, b.y)
      .setFrame(row * def.frames + col)
      .setDepth(fxLitDepth(b.depth + DEPTH.OVERLAY_STEP))
      .setVisible(b.visible && !this.lying(b));
  }

  /** 시트가 없을 때 임시: fire_pool 루프를 몸에 얹고 out 이면 페이드 */
  private drawFallback(b: Mob, phase: BurnPhase): void {
    const F = BOSS_FX.ONFIRE;
    const fx = this.host.fx;
    if (phase === 'out') {
      if (this.fallback && fx.isActive(this.fallback)) fx.stop(this.fallback);
      this.fallback = null;
      return;
    }
    if (this.fallback && fx.isActive(this.fallback)) return;
    this.fallback = fx.play(F.FALLBACK_FX, b.x, b.y - F.FALLBACK_LIFT_PX, {
      follow: b,
      followOffset: { x: 0, y: -F.FALLBACK_LIFT_PX },
      depthOffset: DEPTH.OVERLAY_STEP,
      scaleMult: F.FALLBACK_SCALE,
      hooks: false,
    });
  }

  private lying(b: Mob): boolean {
    const key = b.texture.key;
    return HIDE_ON_ACTIONS.some((a) => spriteLibrary.textureKey(b.spriteId, a) === key);
  }

  private hideArt(): void {
    this.sprite?.destroy();
    this.sprite = null;
    if (this.fallback && this.host.fx.isActive(this.fallback)) this.host.fx.stop(this.fallback, 0, false);
    this.fallback = null;
  }

  // --- 불빛 (국면별: JSON lightByPhase → light → 임시) ---

  private syncLight(b: Mob, def: SheetDef | undefined): void {
    const phase = this.state.phase;
    if (phase === this.lightPhase) return;
    this.lightPhase = phase;
    const reg = lightRegistryOf(this.host.scene);
    reg.remove(this.light);
    this.light = null;
    if (phase === 'off') return;
    const spec: LightSpec = def?.lightByPhase?.[phase] ?? def?.light ?? BOSS_FX.ONFIRE.LIGHT;
    // offset = 프레임 안 [x, y] 도트 → 피벗 기준 월드 (없으면 offsetY = 발에서 위로)
    const o = def ? lightOffsetOf(spec.offset) : null;
    const k = def ? artScale(def) : 1;
    const at = o && def ? { dx: (o.x - def.pivot.x) * k, dy: (o.y - def.pivot.y) * k } : {};
    this.light = reg.add(spec, { x: b.x, y: b.y, anchor: b, ...at });
  }

  // --- 불 피해: 타는 몸에 닿으면 ---

  private touchFire(b: Mob, time: number): void {
    if (time < this.nextTouchAt) return;
    const pad = this.P.touchPadPx;
    const bb = b.body;
    this.touch.setTo(bb.x - pad, bb.y - pad, bb.width + pad * 2, bb.height + pad * 2);
    const pb = this.host.player.body;
    this.playerRect.setTo(pb.x, pb.y, pb.width, pb.height);
    if (!Phaser.Geom.Intersects.RectangleToRectangle(this.touch, this.playerRect)) return;
    this.nextTouchAt = time + this.P.touchTickMs;
    this.debug.touchHits++;
    this.host.player.takeHit(this.P.touchAttack, time, {
      dirX: pb.center.x - bb.center.x,
      dirY: pb.center.y - bb.center.y,
    });
  }

  summary(): Record<string, unknown> {
    return {
      phase: this.state.phase,
      burning: this.burning,
      art: Boolean(this.def),
      overlay: this.sprite
        ? { frame: this.sprite.frame.name, visible: this.sprite.visible, x: this.sprite.x, y: this.sprite.y }
        : this.fallback
          ? 'fallback'
          : null,
      light: this.light
        ? { radius: this.light.radius, intensity: this.light.intensity, offsetY: this.light.offsetY }
        : null,
      ...this.debug,
    };
  }

  /** 끄기 (보스 사망·방 정리) */
  stop(): void {
    this.hideArt();
    lightRegistryOf(this.host.scene).remove(this.light);
    this.light = null;
    this.lightPhase = 'off';
    this.state.phase = 'off';
    this.state.leftAt = 0;
  }

  destroy(): void {
    this.stop();
  }
}
