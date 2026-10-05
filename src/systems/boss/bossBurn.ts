/**
 * 54라운드 Q18 보스 불타기: 보스가 불붙은 술 웅덩이(LiquorPools 불 칸) 위에 서 있으면 **피해 없이** 불타는 상태 —
 * 몸 불길 오버레이(`fx/v3/boss1_onfire` phaseFrames ignite → loop, 나오면 lingerMs 뒤 out) + 불빛(JSON lightByPhase·light).
 * 타는 동안 플레이어가 보스 몸에 닿으면 touchTickMs 마다 불 피해(접촉 공격과 별개). 오버레이 시트가 없으면 기존 fire_pool 을 몸에 얹는다(임시).
 * 54라운드 Q23·Q28: 넘어짐·죽음의 누운 그림에는 누운 불길(`boss1_onfire` 의 `lyingSheet` → `fx/v3/boss1_onfire_down`, 0행)을
 * `useFor` 매핑대로 바꿔 끼고(국면·열은 그대로 이어 씀) `frameOffsets` 만큼 그림·빛을 옮긴다(`onfireMap`). 누운 시트가 없으면 숨김.
 * 보스가 타다 죽으면 시체(죽음 그림)를 따라 계속 타다가 죽음 마지막 프레임에서 out (Q28 임시).
 * 상태 흐름은 `burnMath` (테스트), 이 파일은 그림·빛·피해 연결. BossArena 가 만들고 매 프레임 update.
 */
import Phaser from 'phaser';
import { BOSS_FX, DEPTH, fxLitDepth } from '../../core/Constants';
import type { BossOnFireParams } from '../../data/types';
import type { Mob } from '../../objects/Mob';
import type { FxHandle, FxPool } from '../fx/fx';
import { lightRegistryOf, type LightSource } from '../lighting/lightRegistry';
import { spriteLibrary } from '../sprites/sprites';
import {
  FX_ACTION,
  artScale,
  directionRow,
  frameDurations,
  type Facing,
  type LightSpec,
  type SheetDef,
} from '../sprites/spriteDefs';
import { lightOffsetOf } from '../../world/tileskin';
import {
  burnColumn,
  forceOut,
  isBurning,
  newBurnState,
  phaseLengthMs,
  stepBurn,
  type BurnPhase,
  type BurnTiming,
} from './burnMath';
import { chooseOverlay, mappedActions, type OverlayChoice } from './onfireMap';

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

/** 불길이 얹히는 대상: 살아 있는 보스 또는 시체(죽음 그림) */
interface BurnTarget {
  obj: Phaser.GameObjects.Sprite;
  spriteId: string;
  facing: Facing;
  corpse: boolean;
  /** 61라운드: 대상 그림 배율 (보스 renderScale) — 불길·불빛도 같은 배율 */
  scale: number;
}

/** 지금 그릴 불길 (시트 · 행 · 옮김 — 월드) */
interface OverlayPick {
  def: SheetDef;
  tex: string;
  row: number;
  choice: OverlayChoice;
  dx: number;
  dy: number;
}

export class BossBurn {
  readonly state = newBurnState();
  private sprite: Phaser.GameObjects.Sprite | null = null;
  private fallback: FxHandle | null = null;
  private light: LightSource | null = null;
  /** 광원을 만든 조건 (국면·시트·대상) — 바뀌면 다시 만든다 */
  private lightKey = '';
  /** 죽은 보스: 시체를 따라 타다가 죽음 마지막 프레임에서 out */
  private dead: { visual: Mob['visual']; spriteId: string } | null = null;
  private nextTouchAt = 0;
  private readonly foot = new Phaser.Geom.Rectangle();
  private readonly touch = new Phaser.Geom.Rectangle();
  private readonly playerRect = new Phaser.Geom.Rectangle();
  /** 디버그 */
  readonly debug = { ignites: 0, touchHits: 0 };
  /** 디버그: 마지막으로 불길을 얹은 대상 그림 (텍스처·프레임) */
  private lastTarget: { texture: string; frame: string | number; corpse: boolean } | null = null;

  constructor(
    private readonly host: BossBurnHost,
    private readonly P: BossOnFireParams,
  ) {}

  private get def(): SheetDef | undefined {
    const d = spriteLibrary.sheet(BOSS_FX.SHEETS.ONFIRE, FX_ACTION);
    const tex = spriteLibrary.textureKey(BOSS_FX.SHEETS.ONFIRE, FX_ACTION);
    return d && tex && this.host.scene.textures.exists(tex) ? d : undefined;
  }

  /** 누운 불길 시트 (서 있는 시트 JSON lyingSheet → 기본 이름). 로드되지 않았으면 undefined */
  private lyingDef(stand: SheetDef | undefined): SheetDef | undefined {
    const name = stand?.lyingSheet ?? BOSS_FX.SHEETS.ONFIRE_DOWN;
    const d = spriteLibrary.sheet(name, FX_ACTION);
    const tex = spriteLibrary.textureKey(name, FX_ACTION);
    return stand && d && tex && this.host.scene.textures.exists(tex) ? d : undefined;
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
    if (this.dead) {
      this.updateDead(time);
      return;
    }
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
    this.render(
      { obj: b, spriteId: b.spriteId, facing: b.visual.facing, corpse: false, scale: b.visual.drawScale },
      def,
      time,
    );
    if (this.burning) this.touchFire(b, time);
  }

  /**
   * 보스가 죽었다 (BOSS_DIED — 시체는 이 직후 생긴다). 타는 중이면 시체를 따라 계속 타고, 아니면 끈다.
   * 시체가 없으면(죽음 시트 없음) 다음 프레임에 끈다
   */
  onBossDied(b: Mob | null): void {
    if (!b || this.state.phase === 'off') {
      this.stop();
      return;
    }
    this.dead = { visual: b.visual, spriteId: b.spriteId };
    this.nextTouchAt = Infinity;
  }

  /** 시체 위: 타는 중이면 그대로(불 위로 취급), 죽음 마지막 프레임에서 out → 끝나면 끈다 */
  private updateDead(time: number): void {
    const d = this.dead!;
    const corpse = d.visual.corpse;
    if (!corpse || !corpse.active) {
      this.stop();
      return;
    }
    const def = this.def;
    const t = this.timing(def);
    if (this.burning) {
      stepBurn(this.state, true, time, t);
      const deathDef = spriteLibrary.sheet(d.spriteId, 'death');
      const col = deathDef ? Number(corpse.frame.name) % deathDef.frames : 0;
      // 마지막 프레임 (시트를 모르면 재생이 끝났을 때 — 히트스톱 등으로 멈춘 것은 끝이 아니다)
      const ended = deathDef ? col >= deathDef.frames - 1 : !corpse.anims.isPlaying && !corpse.anims.isPaused;
      if (ended) forceOut(this.state, time);
    } else stepBurn(this.state, false, time, t);
    if (this.state.phase === 'off') {
      this.stop();
      return;
    }
    this.render(
      { obj: corpse, spriteId: d.spriteId, facing: d.visual.facing, corpse: true, scale: d.visual.drawScale },
      def,
      time,
    );
  }

  private render(t: BurnTarget, def: SheetDef | undefined, time: number): void {
    this.lastTarget = { texture: t.obj.texture.key, frame: t.obj.frame.name, corpse: t.corpse };
    const pick = def ? this.pick(t, def) : null;
    this.draw(t, pick, time);
    this.syncLight(t, def, pick);
  }

  /** 지금 대상 그림(동작·열)에 맞는 불길 시트 (onfireMap) */
  private pick(t: BurnTarget, stand: SheetDef): OverlayPick {
    const lying = this.lyingDef(stand);
    const { action, column } = this.poseOf(t, lying);
    const choice = chooseOverlay(action, column, lying ?? null);
    if (choice.sheet === 'lying' && lying) {
      const k = artScale(lying) * t.scale;
      return {
        def: lying,
        tex: spriteLibrary.textureKey(lying.name, FX_ACTION)!,
        row: 0,
        choice,
        dx: choice.dx * k,
        dy: choice.dy * k,
      };
    }
    return {
      def: stand,
      tex: spriteLibrary.textureKey(BOSS_FX.SHEETS.ONFIRE, FX_ACTION)!,
      row: directionRow(stand, t.facing),
      choice,
      dx: 0,
      dy: 0,
    };
  }

  /** 대상 스프라이트가 지금 보이는 보스 시트 동작(매핑에 있는 것만)과 그 열 */
  private poseOf(t: BurnTarget, lying: SheetDef | undefined): { action: string | null; column: number } {
    const key = t.obj.texture.key;
    for (const a of mappedActions(lying ?? null)) {
      if (spriteLibrary.textureKey(t.spriteId, a) !== key) continue;
      const d = spriteLibrary.sheet(t.spriteId, a);
      const idx = Number(t.obj.frame.name);
      return { action: a, column: d && Number.isFinite(idx) ? idx % d.frames : 0 };
    }
    return { action: null, column: 0 };
  }

  // --- 그림 ---

  private draw(t: BurnTarget, pick: OverlayPick | null, time: number): void {
    const phase = this.state.phase;
    if (phase === 'off') {
      this.hideArt();
      return;
    }
    if (!pick) {
      if (t.corpse) this.hideArt();
      else this.drawFallback(t.obj, phase);
      return;
    }
    const { def, tex } = pick;
    if (!this.sprite) this.sprite = this.host.scene.add.sprite(t.obj.x, t.obj.y, tex, 0);
    // 두 시트(서 있는·누운)는 열 배치·프레임 시간이 같다 — 국면·경과로 구한 열을 그대로 이어 쓴다(점화 반복 없음)
    const cols = def.phaseFrames?.[phase] ?? [];
    const col = burnColumn(cols, frameDurations(def), time - this.state.since, phase === 'loop');
    const frame = pick.row * def.frames + col;
    if (this.sprite.texture.key !== tex) this.sprite.setTexture(tex, frame);
    // 보스 스프라이트와 같은 자리(+누운 프레임 옮김)·같은 방향 행, 보스 바로 위 깊이(조명 위 띠 — fx 규칙)
    this.sprite
      .setOrigin(def.pivot.x / def.frameWidth, def.pivot.y / def.frameHeight)
      .setScale(artScale(def) * t.scale)
      .setPosition(t.obj.x + pick.dx, t.obj.y + pick.dy)
      .setFrame(frame)
      .setAlpha(t.obj.alpha)
      .setDepth(fxLitDepth(t.obj.depth + DEPTH.OVERLAY_STEP))
      .setVisible(t.obj.visible && pick.choice.sheet !== 'hide');
  }

  /** 시트가 없을 때 임시: fire_pool 루프를 몸에 얹고 out 이면 페이드 */
  private drawFallback(b: Phaser.GameObjects.Sprite, phase: BurnPhase): void {
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

  private hideArt(): void {
    this.sprite?.destroy();
    this.sprite = null;
    if (this.fallback && this.host.fx.isActive(this.fallback)) this.host.fx.stop(this.fallback, 0, false);
    this.fallback = null;
  }

  // --- 불빛 (국면별: JSON lightByPhase → light → 임시) ---

  /**
   * 국면·시트(서 있는/누운)·대상이 바뀌면 광원을 다시 만들고, 같으면 누운 프레임 옮김만 따라간다.
   * offset = 프레임 안 [x, y] 도트 → 피벗 기준 월드 (없으면 offsetY = 발에서 위로) + frameOffsets
   */
  private syncLight(t: BurnTarget, stand: SheetDef | undefined, pick: OverlayPick | null): void {
    const phase = this.state.phase;
    const reg = lightRegistryOf(this.host.scene);
    if (phase === 'off') {
      reg.remove(this.light);
      this.light = null;
      this.lightKey = '';
      return;
    }
    const def = pick?.def ?? stand;
    const spec: LightSpec = def?.lightByPhase?.[phase] ?? def?.light ?? BOSS_FX.ONFIRE.LIGHT;
    const o = def ? lightOffsetOf(spec.offset) : null;
    const k = def ? artScale(def) * t.scale : 1;
    const base = o && def ? { dx: (o.x - def.pivot.x) * k, dy: (o.y - def.pivot.y) * k } : null;
    const at = base ? { dx: base.dx + (pick?.dx ?? 0), dy: base.dy + (pick?.dy ?? 0) } : {};
    const key = `${phase}|${def?.name ?? '-'}|${t.corpse ? 'corpse' : 'boss'}`;
    if (key === this.lightKey && this.light) {
      if (at.dx !== undefined && at.dy !== undefined) {
        this.light.offsetX = at.dx;
        this.light.offsetY = -at.dy;
      }
      return;
    }
    this.lightKey = key;
    reg.remove(this.light);
    this.light = reg.add(spec, { x: t.obj.x, y: t.obj.y, anchor: t.obj, ...at });
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
      dead: Boolean(this.dead),
      target: this.lastTarget,
      overlay: this.sprite
        ? {
            sheet: this.sprite.texture.key,
            frame: this.sprite.frame.name,
            visible: this.sprite.visible,
            x: this.sprite.x,
            y: this.sprite.y,
          }
        : this.fallback
          ? 'fallback'
          : null,
      light: this.light
        ? {
            radius: this.light.radius,
            intensity: this.light.intensity,
            offsetX: this.light.offsetX,
            offsetY: this.light.offsetY,
          }
        : null,
      ...this.debug,
    };
  }

  /** 끄기 (보스 사망·방 정리) */
  stop(): void {
    this.hideArt();
    lightRegistryOf(this.host.scene).remove(this.light);
    this.light = null;
    this.lightKey = '';
    this.dead = null;
    this.nextTouchAt = 0;
    this.state.phase = 'off';
    this.state.leftAt = 0;
  }

  destroy(): void {
    this.stop();
  }
}
