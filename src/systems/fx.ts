/**
 * 공격 이펙트 풀 (계약 art-assets.md §3·§3.1).
 * `fx/<이름>.json` 시트를 spriteLibrary 에서 찾아 재생한다. 스프라이트는 Group 풀에서 재사용하고,
 * 일회성은 재생이 끝나면, 루프는 `durationMs` 가 지나거나 따라가는 대상이 비활성화되면 비활성으로 돌린다.
 * 시트가 없으면 `has()` 가 false 이고 `play()` 는 null — 호출 쪽이 플레이스홀더 연출을 유지한다.
 */
import Phaser from 'phaser';
import { PROTOTYPE } from '../core/Constants';
import { spriteLibrary } from './sprites';
import { FX_ACTION, animDurationMs, animKey, frameDurations, frameIndices, type Facing } from './spriteDefs';

/** 따라갈 대상 (플레이어·투사체). 비활성화되면 이펙트도 멈춘다 */
export interface FxFollowTarget {
  x: number;
  y: number;
  active: boolean;
  depth: number;
  rotation: number;
}

export interface FxPlayOptions {
  /** 4방향 시트의 행. `directions: ["any"]` 시트는 무시된다 */
  dir?: Facing;
  /** 투사체 앵커(`rotate: true`): 진행 각도(rad). 우향으로 그려졌으므로 그대로 회전 */
  angle?: number;
  /** 절대 깊이. follow 가 있고 depthOffset 이 있으면 대상 깊이 + 오프셋을 매 프레임 쓴다 */
  depth?: number;
  depthOffset?: number;
  follow?: FxFollowTarget;
  /** follow 대상의 회전을 따른다 (관통 빛줄) */
  followRotation?: boolean;
  /** 루프 시트의 재생 시간. 없으면 follow 대상이 사라질 때까지 */
  durationMs?: number;
  /** 시트의 마지막 `tailFrames` 프레임만 루프 (잔월: 거합 4~6프레임 반복) */
  tailFrames?: number;
  /** 일회성 재생이 끝난 뒤 마지막 프레임을 이 시간만큼 유지하고 페이드 (피 바닥 얼룩) */
  holdLastMs?: number;
}

export interface FxHandle {
  readonly sprite: Phaser.GameObjects.Sprite;
  readonly token: number;
}

interface FxState {
  token: number;
  follow?: FxFollowTarget;
  followRotation: boolean;
  depthOffset?: number;
  expireAt: number;
  fading: boolean;
}

export class FxPool {
  private readonly group: Phaser.GameObjects.Group;
  private readonly states = new Map<Phaser.GameObjects.Sprite, FxState>();
  private nextToken = 1;

  constructor(private readonly scene: Phaser.Scene) {
    this.group = scene.add.group({
      classType: Phaser.GameObjects.Sprite,
      maxSize: PROTOTYPE.FX_POOL,
      runChildUpdate: false,
    });
  }

  /** 이펙트 시트가 로드돼 있는지 */
  has(id: string): boolean {
    const texture = spriteLibrary.textureKey(id, FX_ACTION);
    return Boolean(texture && this.scene.textures.exists(texture));
  }

  /** 시트 자연 재생 길이 ms (없으면 0) */
  durationOf(id: string): number {
    const def = spriteLibrary.sheet(id, FX_ACTION);
    return def ? animDurationMs(def) : 0;
  }

  play(id: string, x: number, y: number, opts: FxPlayOptions = {}): FxHandle | null {
    const def = spriteLibrary.sheet(id, FX_ACTION);
    const texture = spriteLibrary.textureKey(id, FX_ACTION);
    const key = spriteLibrary.animKey(id, FX_ACTION, opts.dir ?? 'down');
    if (!def || !texture || !key || !this.scene.textures.exists(texture)) return null;
    const sprite = this.group.get(x, y) as Phaser.GameObjects.Sprite | null;
    if (!sprite) return null;
    const token = this.nextToken++;
    sprite.off(Phaser.Animations.Events.ANIMATION_COMPLETE);
    sprite
      .setTexture(texture, 0)
      .setOrigin(def.pivot.x / def.frameWidth, def.pivot.y / def.frameHeight)
      .setPosition(x, y)
      .setRotation(def.rotate ? (opts.angle ?? 0) : 0)
      .setAlpha(1)
      .setScale(1)
      .setActive(true)
      .setVisible(true);
    const follow = opts.follow;
    const depth = opts.depth ?? (follow && opts.depthOffset !== undefined ? follow.depth + opts.depthOffset : 0);
    sprite.setDepth(depth);
    const anim = opts.tailFrames ? this.tailAnim(id, key, texture, opts.tailFrames, opts.dir ?? 'down') : key;
    sprite.anims.timeScale = 1;
    sprite.play(anim, true);
    const now = this.scene.time.now;
    const state: FxState = {
      token,
      follow,
      followRotation: Boolean(opts.followRotation && def.rotate),
      depthOffset: follow ? opts.depthOffset : undefined,
      expireAt: opts.durationMs ? now + opts.durationMs : Infinity,
      fading: false,
    };
    this.states.set(sprite, state);
    const loop = Boolean(def.loop) || Boolean(opts.tailFrames);
    if (!loop) {
      const hold = opts.holdLastMs ?? 0;
      sprite.once(Phaser.Animations.Events.ANIMATION_COMPLETE, () => {
        const st = this.states.get(sprite);
        if (st?.token !== token) return;
        if (hold > 0)
          st.expireAt = this.scene.time.now + hold; // update() 가 만료 시 페이드
        else this.release(sprite);
      });
    }
    return { sprite, token };
  }

  isActive(h: FxHandle | null): boolean {
    return Boolean(h && this.states.get(h.sprite)?.token === h.token);
  }

  /** 4방향 루프 이펙트의 방향 바꾸기 (질풍: 플레이어 방향을 따른다) */
  setDir(h: FxHandle | null, id: string, dir: Facing): void {
    if (!h || !this.isActive(h)) return;
    const key = spriteLibrary.animKey(id, FX_ACTION, dir);
    if (key && h.sprite.anims.currentAnim?.key !== key) h.sprite.play(key, true);
  }

  /** 루프 이펙트 종료 (짧은 페이드) */
  stop(h: FxHandle | null): void {
    if (!h || !this.isActive(h)) return;
    this.fadeOut(h.sprite);
  }

  /** 매 프레임: 따라가기·만료 */
  update(time: number): void {
    for (const [sprite, st] of this.states) {
      if (st.fading) continue;
      const f = st.follow;
      if (f) {
        if (!f.active) {
          this.release(sprite);
          continue;
        }
        sprite.setPosition(f.x, f.y);
        if (st.depthOffset !== undefined) sprite.setDepth(f.depth + st.depthOffset);
        if (st.followRotation) sprite.setRotation(f.rotation);
      }
      if (time >= st.expireAt) this.fadeOut(sprite);
    }
  }

  /** 히트스톱: 활성 이펙트 애니 일시 정지·재개 (따라가기·만료는 update 를 건너뛰는 호출 쪽이 멈춘다) */
  setPaused(on: boolean): void {
    for (const sprite of this.states.keys()) {
      if (on) sprite.anims.pause();
      else sprite.anims.resume();
    }
  }

  /** 활성 이펙트 요약 (디버그) */
  summary(): { anim: string | null; x: number; y: number; frame: number; depth: number; rotation: number }[] {
    return [...this.states.keys()].map((s) => ({
      anim: s.anims.currentAnim?.key ?? null,
      x: s.x,
      y: s.y,
      frame: s.anims.currentFrame?.index ?? 0,
      depth: s.depth,
      rotation: s.rotation,
    }));
  }

  destroy(): void {
    for (const sprite of this.states.keys()) sprite.off(Phaser.Animations.Events.ANIMATION_COMPLETE);
    this.states.clear();
    this.group.destroy(true);
  }

  private fadeOut(sprite: Phaser.GameObjects.Sprite): void {
    const st = this.states.get(sprite);
    if (!st) return;
    st.fading = true;
    const token = st.token;
    this.scene.tweens.add({
      targets: sprite,
      alpha: 0,
      duration: PROTOTYPE.FX_FADE_MS,
      onComplete: () => {
        if (this.states.get(sprite)?.token === token) this.release(sprite);
      },
    });
  }

  private release(sprite: Phaser.GameObjects.Sprite): void {
    this.states.delete(sprite);
    sprite.off(Phaser.Animations.Events.ANIMATION_COMPLETE);
    sprite.anims.stop();
    sprite.setActive(false).setVisible(false).setAlpha(1).setRotation(0);
  }

  /** 마지막 n 프레임만 반복하는 애니 (키 `<애니>#tail<n>`, 텍스처 변형별로 1회 생성) */
  private tailAnim(id: string, key: string, texture: string, n: number, dir: Facing): string {
    const tailKey = `${key}#tail${n}`;
    if (!this.scene.anims.exists(tailKey)) {
      const def = spriteLibrary.sheet(id, FX_ACTION)!;
      const all = frameIndices(def, dir);
      const durations = frameDurations(def);
      const start = Math.max(0, all.length - n);
      this.scene.anims.create({
        key: tailKey,
        frames: all.slice(start).map((frame, i) => ({ key: texture, frame, duration: durations[start + i] })),
        frameRate: def.fps,
        repeat: -1,
      });
    }
    return tailKey;
  }
}

/** 변형 접미를 뗀 기본 애니 키 (테스트·디버그) */
export function baseFxAnimKey(id: string, dir: Facing): string {
  return animKey(id, FX_ACTION, dir);
}
