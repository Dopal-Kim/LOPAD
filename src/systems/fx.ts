/**
 * 공격 이펙트 풀 (계약 art-assets.md §3·§3.1·§3.2).
 * `fx/<이름>.json` 시트를 spriteLibrary 에서 찾아 재생한다. 스프라이트는 Group 풀에서 재사용하고,
 * 일회성은 재생이 끝나면, 루프는 `durationMs` 가 지나거나 따라가는 대상이 비활성화되면 비활성으로 돌린다.
 * 시트가 없으면 `has()` 가 false 이고 `play()` 는 null — 호출 쪽이 플레이스홀더 연출을 유지한다.
 * §3.2 양산 필드: `scale`(배율), `flash`(atFrame 시작에 화면 섬광), `shake`(섬광 프레임 또는 타격 프레임에 흔들림),
 * `secondStage`(같은 시트 안 2단 판정 프레임에 섬광·흔들림 한 번 더), `trail`(fromFrame 부터 리본) 은 `hooks` 로 바깥(Game) 에
 * 위임한다 — 크기·프레임 수·시간은 전부 JSON 에서 읽는다. 시각 이벤트는 이펙트 자체의 재생 시간(히트스톱 동안 멈춤)으로 잰다.
 */
import Phaser from 'phaser';
import { PROTOTYPE } from '../core/Constants';
import { spriteLibrary } from './sprites';
import { lightFor, lightRegistryOf, type LightSource } from './lighting/lightRegistry';
import {
  FX_ACTION,
  animDurationMs,
  artScale,
  animKey,
  frameDurations,
  frameIndices,
  frameStarts,
  fxImpactFrame,
  sheetScale,
  type Facing,
  type FxFlashSpec,
  type FxShakeSpec,
  type FxTrailSpec,
  type SheetJson,
} from './spriteDefs';

/** 따라갈 대상 (플레이어·투사체·적). 비활성화되면 이펙트도 멈춘다 */
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
  /** follow 대상 기준 오프셋 (몸 중심 등) */
  followOffset?: { x: number; y: number };
  /** follow 대상의 회전을 따른다 (관통 빛줄) */
  followRotation?: boolean;
  /** 루프 시트의 재생 시간. 없으면 follow 대상이 사라질 때까지 */
  durationMs?: number;
  /** 시트의 마지막 `tailFrames` 프레임만 루프 (잔월: 거합 4~6프레임 반복) */
  tailFrames?: number;
  /** 일회성 재생이 끝난 뒤 마지막 프레임을 이 시간만큼 유지하고 페이드 (피 바닥 얼룩) */
  holdLastMs?: number;
  /** 애니 대신 고정 프레임 (진행도 주도 aim_charge). `setFrame` 으로 바꾸고 `stop` 으로 끝낸다 */
  staticFrame?: number;
  /** 틴트 (dash_trail 무기 보조색). 없으면 원색 */
  tint?: number;
  /** true 면 `setTintFill`(평면 틴트 — 어두운 무채 시트용, JSON tint.method), 아니면 곱셈 `setTint` */
  tintFill?: boolean;
  /** JSON `trail` 이 따라갈 궤적 (베기 호 등). 없으면 스프라이트 위치(앵커가 player_pivot 이면 몸 중심) */
  trailSource?: () => { x: number; y: number } | null;
  /** false 면 JSON flash·shake·trail 훅을 쓰지 않는다 (달리기·워프 먼지처럼 반복·보조 재생) */
  hooks?: boolean;
  /** 시트 배율에 곱하는 배율 (45라운드 달리기 먼지: dash_dust 를 작게). 기본 1 */
  scaleMult?: number;
  /** 시작 알파 (기본 1) */
  alpha?: number;
}

export interface FxHandle {
  readonly sprite: Phaser.GameObjects.Sprite;
  readonly token: number;
}

/** 리본 트레일 요청 (훅 인자) */
export interface FxTrailRequest {
  spec: FxTrailSpec;
  /** 위치 공급. null 이면 끝 */
  source: () => { x: number; y: number } | null;
  /** 이펙트 스프라이트 깊이 (리본은 바로 아래) */
  depth: number;
}

/** §3.2 필드를 바깥 시스템으로 넘기는 훅 (Game 이 등록) */
export interface FxHooks {
  shake?: (spec: FxShakeSpec) => void;
  flash?: (spec: FxFlashSpec) => void;
  /** 리본 트레일 시작. 반환: 샘플링 끝내기 */
  trail?: (req: FxTrailRequest) => (() => void) | null;
  /** 몸 중심 = 발 피벗에서 위로 px (player_pivot 앵커 트레일 기본 궤적) */
  bodyCenterUpPx?: number;
}

/** 이펙트 재생 시간 기준 예약 이벤트 (atMs = 재생 시작부터) */
interface FxTimed {
  atMs: number;
  fire: () => void;
}

interface FxState {
  token: number;
  follow?: FxFollowTarget;
  followOffset?: { x: number; y: number };
  followRotation: boolean;
  depthOffset?: number;
  expireAt: number;
  fading: boolean;
  noFade: boolean;
  stopTrail?: () => void;
  /** 재생 경과 ms (update 사이 시간 합, 히트스톱 동안 안 늘어남) */
  elapsed: number;
  lastTick: number;
  timed: FxTimed[];
  /** 50라운드: 이 이펙트의 광원 (시트 JSON light · fallback · 무기 이펙트 순간광) */
  light?: LightSource;
}

export class FxPool {
  private readonly group: Phaser.GameObjects.Group;
  private readonly states = new Map<Phaser.GameObjects.Sprite, FxState>();
  private nextToken = 1;
  hooks: FxHooks = {};

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

  /** 시트 프레임 수 (없으면 0) */
  framesOf(id: string): number {
    return spriteLibrary.sheet(id, FX_ACTION)?.frames ?? 0;
  }

  /** 시트 JSON (없으면 null) */
  sheet(id: string): SheetJson | null {
    return spriteLibrary.sheet(id, FX_ACTION) ?? null;
  }

  /** 예비 프레임 보정: 타격 프레임(`fxImpactFrame`)이 spawn 시점에 오도록 먼저 시작해야 하는 ms */
  leadMs(id: string): number {
    const def = spriteLibrary.sheet(id, FX_ACTION);
    if (!def) return 0;
    return frameStarts(def)[fxImpactFrame(def)] ?? 0;
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
    sprite.anims.stop();
    // 50라운드: 새 2배 도트 이펙트(pixelScale 1)는 0.5 배로 그려 화면 크기를 맞춘다
    const scale = sheetScale(def) * artScale(def);
    const row = frameIndices(def, opts.dir ?? 'down')[0] ?? 0;
    sprite
      .setTexture(texture, row + Math.max(0, Math.min(def.frames - 1, opts.staticFrame ?? 0)))
      .setOrigin(def.pivot.x / def.frameWidth, def.pivot.y / def.frameHeight)
      .setPosition(x, y)
      .setRotation(def.rotate ? (opts.angle ?? 0) : 0)
      .setAlpha(opts.alpha ?? 1)
      .setScale(scale * (opts.scaleMult ?? 1))
      .setActive(true)
      .setVisible(true);
    if (opts.tint !== undefined) {
      if (opts.tintFill) sprite.setTintFill(opts.tint);
      else sprite.setTint(opts.tint);
    } else sprite.clearTint();
    const follow = opts.follow;
    const depth = opts.depth ?? (follow && opts.depthOffset !== undefined ? follow.depth + opts.depthOffset : 0);
    sprite.setDepth(depth);
    const now = this.scene.time.now;
    const state: FxState = {
      token,
      follow,
      followOffset: opts.followOffset,
      followRotation: Boolean(opts.followRotation && def.rotate),
      depthOffset: follow ? opts.depthOffset : undefined,
      expireAt: opts.durationMs ? now + opts.durationMs : Infinity,
      fading: false,
      noFade: false,
      elapsed: 0,
      lastTick: now,
      timed: [],
    };
    this.states.set(sprite, state);
    // 50라운드 조명: 광원이 있는 이펙트는 재생 동안 주변을 밝힌다 (루프가 아니면 수명 동안 서서히 약해지는 순간광)
    const light = lightFor(id, def);
    if (light) {
      const life = def.loop || opts.durationMs ? (opts.durationMs ?? Infinity) : animDurationMs(def);
      state.light = lightRegistryOf(this.scene).add(light, {
        x,
        y,
        anchor: sprite,
        now,
        until: now + life,
        fade: !def.loop,
      });
    }
    if (opts.staticFrame === undefined) {
      const anim = opts.tailFrames ? this.tailAnim(id, key, texture, opts.tailFrames, opts.dir ?? 'down') : key;
      sprite.anims.timeScale = 1;
      sprite.play(anim, true);
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
    }
    if (opts.hooks !== false) this.applySheetHooks(def, sprite, state, opts);
    return { sprite, token };
  }

  /**
   * §3.2: flash 는 atFrame 시작, shake 는 flash.atFrame(없으면 타격 프레임) 시작, secondStage 는 그 프레임에서 한 번 더,
   * trail 은 fromFrame 시작부터 (궤적 = opts.trailSource → 스프라이트 위치). 프레임 시작 = 이 시트의 frameDurationsMs 누적
   */
  private applySheetHooks(
    def: SheetJson,
    sprite: Phaser.GameObjects.Sprite,
    state: FxState,
    opts: FxPlayOptions,
  ): void {
    const h = this.hooks;
    const starts = frameStarts(def);
    const at = (frame: number | undefined, fallback: number) =>
      starts[Math.max(0, Math.min(def.frames - 1, frame ?? fallback))] ?? 0;
    const impact = fxImpactFrame(def);
    const flash = (spec: FxFlashSpec | undefined, frame: number) => {
      if (spec && h.flash) this.schedule(state, at(spec.atFrame, frame), () => h.flash?.(spec));
    };
    const shake = (spec: FxShakeSpec | undefined, frame: number) => {
      if (spec && h.shake && spec.px > 0 && spec.ms > 0) this.schedule(state, at(frame, impact), () => h.shake?.(spec));
    };
    flash(def.flash, impact);
    shake(def.shake, def.flash?.atFrame ?? impact);
    const second = def.secondStage;
    if (second) {
      const frame = second.frame ?? second.flash?.atFrame ?? impact;
      flash(second.flash, frame);
      shake(second.shake, frame);
    }
    if (def.trail && h.trail) {
      const spec = def.trail;
      const up = def.anchor === 'player_pivot' ? (h.bodyCenterUpPx ?? 0) : 0;
      const source =
        opts.trailSource ??
        (() => (this.states.get(sprite)?.token === state.token ? { x: sprite.x, y: sprite.y - up } : null));
      this.schedule(state, at(spec.fromFrame, 0), () => {
        state.stopTrail = h.trail?.({ spec, source, depth: sprite.depth }) ?? undefined;
      });
    }
  }

  /** 재생 시간 atMs 에 실행 (0 이면 즉시). 이펙트가 먼저 끝나면 취소 */
  private schedule(state: FxState, atMs: number, fire: () => void): void {
    if (atMs <= 0) fire();
    else state.timed.push({ atMs, fire });
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

  /** 고정 프레임 이펙트(진행도 주도)의 열 바꾸기 */
  setFrame(h: FxHandle | null, id: string, column: number, dir: Facing = 'down'): void {
    if (!h || !this.isActive(h)) return;
    const def = spriteLibrary.sheet(id, FX_ACTION);
    if (!def) return;
    const row = frameIndices(def, dir)[0] ?? 0;
    const frame = row + Math.max(0, Math.min(def.frames - 1, column));
    if (h.sprite.frame.name !== String(frame)) h.sprite.setFrame(frame);
  }

  /** 종료. `holdMs` 뒤에 끝내고, fade 가 false 면 페이드 없이 즉시 비활성 */
  stop(h: FxHandle | null, holdMs = 0, fade = true): void {
    if (!h || !this.isActive(h)) return;
    const st = this.states.get(h.sprite)!;
    if (holdMs > 0) {
      st.expireAt = Math.min(st.expireAt, this.scene.time.now + holdMs);
      st.noFade = !fade;
      return;
    }
    if (fade) this.fadeOut(h.sprite);
    else this.release(h.sprite);
  }

  /** 매 프레임: 예약 이벤트·따라가기·만료 */
  update(time: number): void {
    for (const [sprite, st] of this.states) {
      st.elapsed += Math.max(0, time - st.lastTick);
      st.lastTick = time;
      if (st.timed.length > 0) {
        const due = st.timed.filter((e) => e.atMs <= st.elapsed);
        if (due.length > 0) {
          st.timed = st.timed.filter((e) => e.atMs > st.elapsed);
          for (const e of due) e.fire();
        }
      }
      if (st.fading) continue;
      const f = st.follow;
      if (f) {
        if (!f.active) {
          this.release(sprite);
          continue;
        }
        const o = st.followOffset;
        sprite.setPosition(f.x + (o?.x ?? 0), f.y + (o?.y ?? 0));
        if (st.depthOffset !== undefined) sprite.setDepth(f.depth + st.depthOffset);
        if (st.followRotation) sprite.setRotation(f.rotation);
      }
      if (time >= st.expireAt) {
        if (st.noFade) this.release(sprite);
        else this.fadeOut(sprite);
      }
    }
  }

  /** 히트스톱: 활성 이펙트 애니 일시 정지·재개 (따라가기·만료는 update 를 건너뛰는 호출 쪽이 멈춘다) */
  setPaused(on: boolean): void {
    const now = this.scene.time.now;
    for (const [sprite, st] of this.states) {
      if (on) sprite.anims.pause();
      else {
        sprite.anims.resume();
        st.lastTick = now; // 멈춘 시간은 재생 경과에 넣지 않는다
      }
    }
  }

  /** 활성 이펙트 요약 (디버그) */
  summary(): {
    anim: string | null;
    texture: string;
    x: number;
    y: number;
    frame: number;
    depth: number;
    rotation: number;
    scale: number;
    tint: number | null;
  }[] {
    return [...this.states.keys()].map((s) => ({
      anim: s.anims.currentAnim?.key ?? null,
      texture: s.texture.key,
      x: s.x,
      y: s.y,
      frame: s.anims.currentAnim ? (s.anims.currentFrame?.index ?? 0) : Number(s.frame.name) + 1,
      depth: s.depth,
      rotation: s.rotation,
      scale: s.scaleX,
      tint: s.isTinted ? s.tintTopLeft : null,
    }));
  }

  destroy(): void {
    for (const [sprite, st] of this.states) {
      sprite.off(Phaser.Animations.Events.ANIMATION_COMPLETE);
      st.stopTrail?.();
    }
    this.states.clear();
    this.group.destroy(true);
  }

  private fadeOut(sprite: Phaser.GameObjects.Sprite): void {
    const st = this.states.get(sprite);
    if (!st) return;
    st.fading = true;
    st.stopTrail?.();
    st.stopTrail = undefined;
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
    const st = this.states.get(sprite);
    st?.stopTrail?.();
    if (st?.light) lightRegistryOf(this.scene).remove(st.light);
    this.states.delete(sprite);
    sprite.off(Phaser.Animations.Events.ANIMATION_COMPLETE);
    sprite.anims.stop();
    sprite.setActive(false).setVisible(false).setAlpha(1).setRotation(0).setScale(1).clearTint();
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
