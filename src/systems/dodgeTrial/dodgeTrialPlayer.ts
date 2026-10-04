/**
 * 회피 시험 주인공 (화면 쪽): WASD 이동 · 스페이스 대쉬(무적, data/player.json dash) · 피격 밀려남 · 떨어짐(가라앉기) ·
 * 기둥에 막힘. 바닥 판정은 러너가 넘기는 `TrialGround` 로만 본다(과제마다 경기장이 바뀐다).
 * 48라운드 Q7 "맞으면 피격되서 밀려나고" 유지 · 51라운드: 떨어지면 그 과제만 실패하고 다음 과제에서 중앙으로 돌아온다.
 * 좌표 pos = 판정 원 중심(월드 px), 발 = pos.y + FOOT_OFFSET.
 */
import Phaser from 'phaser';
import { DEPTH, FEEL, TILE, entityDepth } from '../../core/Constants';
import { PLAYER_DATA } from '../../data';
import { audio } from '../audio/audio';
import { SFX } from '../audio/audioMap';
import { DODGE_TRIAL } from './dodgeTrial';
import type { FxPool } from '../fx/fx';
import { artScale, facingOf, type Facing } from '../sprites/spriteDefs';
import { spriteLibrary } from '../sprites/sprites';

export interface TrialInput {
  mx: number;
  my: number;
  dash: boolean;
}

/** 지금 경기장의 바닥·기둥 (러너가 과제·경과 시간에 맞춰 넘긴다) */
export interface TrialGround {
  /** 발 자리 점수: 발 중심이 바닥이 아니면 -1, 아니면 둘레 4점 중 바닥 수 */
  standScore(x: number, y: number): number;
  /** 발이 기둥과 겹치면 밀어낸 자리, 아니면 그대로 */
  pushOut(x: number, y: number): { x: number; y: number };
}

const TEX_PLAYER_PH = 'trial_player_ph';

export class TrialPlayer {
  readonly pos = new Phaser.Math.Vector2();
  /** 디버그: 맞지 않고 떨어지지 않음 */
  god = false;
  /** 이번 과제 대쉬 수 */
  dashes = 0;
  private readonly sprite: Phaser.GameObjects.Sprite;
  private readonly shadow: Phaser.GameObjects.Ellipse;
  private readonly animated: boolean;
  private facing: Facing = 'down';
  private readonly lastDir = new Phaser.Math.Vector2(0, 1);
  private readonly dashDir = new Phaser.Math.Vector2();
  private dashUntil = 0;
  private dashReadyAt = 0;
  private invulnUntil = 0;
  private hurtUntil = 0;
  private flashUntil = 0;
  private knock: { vx: number; vy: number; startAt: number; until: number } | null = null;
  private movingInput = false;
  private sunk = false;
  /** 지금 시트의 도트 배율 (artScale) */
  private baseScale = 1;

  constructor(
    private readonly scene: Phaser.Scene,
    private readonly fx: FxPool,
    private readonly ghostTint: number,
    private readonly placeholderTint: number,
  ) {
    if (!scene.textures.exists(TEX_PLAYER_PH)) {
      const g = scene.make.graphics({ x: 0, y: 0 }, false);
      g.fillStyle(0xffffff, 1);
      g.fillRect(0, 0, 10, 14);
      g.generateTexture(TEX_PLAYER_PH, 10, 14);
      g.destroy();
    }
    const tex = spriteLibrary.textureKey('player', 'idle');
    const idle = spriteLibrary.sheet('player', 'idle');
    this.animated = Boolean(idle && tex && scene.textures.exists(tex));
    this.sprite = scene.add.sprite(0, 0, this.animated ? tex! : TEX_PLAYER_PH);
    if (this.animated) this.fit('idle');
    else this.sprite.setOrigin(0.5, 1);
    const SH = DODGE_TRIAL.PLAYER.SHADOW;
    this.shadow = scene.add.ellipse(0, 0, SH.W, SH.H, 0x000000, SH.ALPHA).setDepth(DEPTH.SHADOW);
  }

  get objects(): Phaser.GameObjects.GameObject[] {
    return [this.sprite, this.shadow];
  }

  get isAnimated(): boolean {
    return this.animated;
  }

  get animKey(): string | null {
    return this.sprite.anims.currentAnim?.key ?? null;
  }

  get knocked(): boolean {
    return this.knock !== null;
  }

  get fallen(): boolean {
    return this.sunk;
  }

  dashing(time: number): boolean {
    return time < this.dashUntil;
  }

  invulnerable(time: number): boolean {
    return this.god || time < this.invulnUntil;
  }

  /** 맞을 수 있는 상태 (무적·밀려나는 중·떨어짐이 아님) */
  vulnerable(time: number): boolean {
    return !this.sunk && !this.knock && !this.invulnerable(time);
  }

  /** 과제 시작: 중앙에 다시 선다 (떨어졌으면 되살림) */
  reset(x: number, y: number, time: number): void {
    this.pos.set(x, y);
    this.knock = null;
    this.dashUntil = 0;
    this.dashReadyAt = 0;
    this.invulnUntil = 0;
    this.hurtUntil = 0;
    this.flashUntil = 0;
    this.dashes = 0;
    this.facing = 'down';
    this.lastDir.set(0, 1);
    if (this.sunk) {
      this.scene.tweens.killTweensOf(this.sprite);
      this.sprite.setScale(this.baseScale).setAlpha(1);
      this.shadow.setVisible(true);
      this.sunk = false;
    }
    this.sync(time, false);
  }

  /**
   * 한 프레임 이동. canAct = 입력을 받는다(제목 카드 동안 false). 밀려나다 바닥 밖으로 나가면 'fell' 을 돌려준다.
   * 걸어서·대쉬로는 바닥 밖으로 못 나간다.
   */
  update(time: number, dt: number, input: TrialInput, ground: TrialGround, canAct: boolean): 'fell' | null {
    if (this.sunk) return null;
    this.movingInput = canAct && (input.mx !== 0 || input.my !== 0);
    const D = PLAYER_DATA.dash;
    const dir = new Phaser.Math.Vector2(canAct ? input.mx : 0, canAct ? input.my : 0);
    if (dir.lengthSq() > 0) {
      dir.normalize();
      this.lastDir.copy(dir);
      this.facing = facingOf(dir.x, dir.y, this.facing);
    }
    if (this.knock) {
      const k = this.knock;
      const p = Math.min(1, (time - k.startAt) / Math.max(1, k.until - k.startAt));
      const f = 1 - p; // 감속
      const before = this.pos.clone();
      const q = ground.pushOut(this.pos.x + k.vx * f * dt, this.pos.y + k.vy * f * dt);
      this.pos.set(q.x, q.y);
      if (time >= k.until) this.knock = null;
      if (ground.standScore(this.pos.x, this.pos.y) < 0) {
        if (!this.god) return 'fell';
        this.pos.copy(before);
      }
      return null;
    }
    if (canAct && input.dash && time >= this.dashReadyAt) {
      this.dashDir.copy(dir.lengthSq() > 0 ? dir : this.lastDir);
      this.dashUntil = time + D.durationMs;
      this.dashReadyAt = time + D.cooldownMs;
      if (D.invulnerable) this.invulnUntil = Math.max(this.invulnUntil, this.dashUntil);
      this.dashes += 1;
      audio.playSfx(SFX.dash);
      this.spawnGhosts();
    }
    let vx: number;
    let vy: number;
    if (time < this.dashUntil) {
      const v = (D.distanceTiles * TILE) / (D.durationMs / 1000);
      vx = this.dashDir.x * v * dt;
      vy = this.dashDir.y * v * dt;
    } else {
      const v = PLAYER_DATA.stats.speedTiles * TILE;
      vx = dir.x * v * dt;
      vy = dir.y * v * dt;
    }
    if (vx === 0 && vy === 0) return null;
    // 가장자리 여유(둘레 4점)가 지금보다 나빠지지 않는 쪽으로만 (축별로 미끄러짐) + 기둥은 밀어냄
    const cur = Math.max(0, ground.standScore(this.pos.x, this.pos.y));
    const ok = (x: number, y: number) => {
      const s = ground.standScore(x, y);
      return s >= 4 || (s >= 0 && s >= cur);
    };
    const { x, y } = this.pos;
    const tryAt = (nx: number, ny: number) => {
      const q = ground.pushOut(nx, ny);
      if (!ok(q.x, q.y)) return false;
      this.pos.set(q.x, q.y);
      return true;
    };
    if (tryAt(x + vx, y + vy)) return null;
    if (vx !== 0 && tryAt(x + vx, y)) return null;
    if (vy !== 0) tryAt(x, y + vy);
    return null;
  }

  /** 피격: 방향(dx, dy) 으로 밀려남 + 무적 + 흰 칠 + 흔들림 */
  hit(time: number, dx: number, dy: number): void {
    const P = DODGE_TRIAL.PLAYER;
    const len = Math.hypot(dx, dy) || 1;
    const dist = P.KNOCK_TILES * TILE;
    // 감속 이동 거리 = v0 × T / 2 → v0 = 2D / T
    const v0 = (2 * dist) / (P.KNOCK_MS / 1000);
    this.knock = { vx: (dx / len) * v0, vy: (dy / len) * v0, startAt: time, until: time + P.KNOCK_MS };
    this.dashUntil = 0;
    this.invulnUntil = time + P.INVULN_MS;
    this.hurtUntil = time + P.KNOCK_MS + 120;
    this.flashUntil = time + P.FLASH_MS;
    this.facing = facingOf(-dx, -dy, this.facing);
    const hurt = spriteLibrary.animKey('player', 'hurt', this.facing);
    if (hurt) {
      this.fit('hurt');
      this.sprite.play(hurt);
    }
    this.fx.play(FEEL.FX_IDS.PLAYER_HIT, this.pos.x, this.pos.y, {
      depth: entityDepth(this.pos.y) + DEPTH.OVERLAY_STEP * 3,
    });
    this.scene.cameras.main.shake(P.SHAKE_MS, P.SHAKE_INTENSITY);
    audio.playSfx(SFX.hitPlayer);
  }

  /** 떨어짐: 바닥 아래 어둠으로 가라앉는다 (바닥 뒤로 그려 가장자리 너머로 떨어지는 느낌) */
  sink(): void {
    if (this.sunk) return;
    const P = DODGE_TRIAL.PLAYER;
    this.sunk = true;
    this.knock = null;
    this.sprite.setDepth(DEPTH.TILES + 0.07);
    this.shadow.setVisible(false);
    this.scene.tweens.add({
      targets: this.sprite,
      alpha: 0,
      scaleX: this.baseScale * 0.5,
      scaleY: this.baseScale * 0.5,
      y: `+=${P.FALL_DROP_PX}`,
      duration: P.FALL_MS,
      ease: 'Quad.easeIn',
    });
  }

  /** 그림 맞추기: 위치·깊이·깜빡임(무적)·흰 칠(피격)·동작 */
  sync(time: number, moving: boolean): void {
    if (this.sunk) return;
    const P = DODGE_TRIAL.PLAYER;
    const footY = this.pos.y + P.FOOT_OFFSET_PX;
    this.sprite.setPosition(Math.round(this.pos.x), Math.round(footY)).setDepth(entityDepth(footY));
    this.shadow.setPosition(Math.round(this.pos.x), Math.round(footY));
    const blinking = !this.god && time < this.invulnUntil && time >= this.dashUntil;
    this.sprite.setAlpha(blinking && Math.floor(time / P.BLINK_MS) % 2 === 0 ? 0.35 : 1);
    if (time < this.flashUntil) this.sprite.setTintFill(0xffffff);
    else if (this.animated) this.sprite.clearTint();
    else this.sprite.setTint(this.placeholderTint);
    if (!this.animated || time < this.hurtUntil) return;
    const want = time < this.dashUntil ? 'dash' : moving && this.movingInput ? 'walk' : 'idle';
    const action = spriteLibrary.animKey('player', want, this.facing) ? want : 'idle';
    const key = spriteLibrary.animKey('player', action, this.facing);
    if (key && this.sprite.anims.currentAnim?.key !== key) {
      this.fit(action);
      this.sprite.play(key, true);
    }
  }

  /**
   * 52라운드: 동작 시트의 도트 배율·피벗으로 배율·원점 (게임 EntityVisual 과 같은 규칙 — 화면 32×48).
   * 50라운드 v2 부터 배율을 안 맞춰 2배(v3 면 4배)로 보이던 것을 바로잡는다
   */
  private fit(action: string): void {
    const def = spriteLibrary.sheet('player', action);
    if (!def) return;
    this.baseScale = artScale(def);
    this.sprite.setOrigin(def.pivot.x / def.frameWidth, def.pivot.y / def.frameHeight);
    if (!this.sunk) this.sprite.setScale(this.baseScale);
  }

  get facingDir(): Facing {
    return this.facing;
  }

  destroy(): void {
    this.scene.tweens.killTweensOf(this.sprite);
    this.sprite.destroy();
    this.shadow.destroy();
  }

  private spawnGhosts(): void {
    const P = DODGE_TRIAL.PLAYER;
    const D = PLAYER_DATA.dash;
    for (let i = 1; i <= P.GHOSTS; i++) {
      const t = i / (P.GHOSTS + 1);
      this.scene.time.delayedCall(D.durationMs * t, () => {
        if (!this.sprite.active) return;
        const g = this.scene.add
          .image(this.sprite.x, this.sprite.y, this.sprite.texture.key, this.sprite.frame.name)
          .setOrigin(this.sprite.originX, this.sprite.originY)
          .setScale(this.sprite.scaleX, this.sprite.scaleY)
          .setAlpha(P.GHOST_ALPHA)
          .setTint(this.ghostTint)
          .setDepth(this.sprite.depth - DEPTH.OVERLAY_STEP);
        this.scene.tweens.add({ targets: g, alpha: 0, duration: P.GHOST_MS, onComplete: () => g.destroy() });
      });
    }
  }
}
