/**
 * 공격 이펙트 풀 (계약 art-assets.md §3·§3.1·§3.2).
 * `fx/<이름>.json` 시트를 spriteLibrary 에서 찾아 재생한다. 스프라이트는 Group 풀에서 재사용하고,
 * 일회성은 재생이 끝나면, 루프는 `durationMs` 가 지나거나 따라가는 대상이 비활성화되면 비활성으로 돌린다.
 * 시트가 없으면 `has()` 가 false 이고 `play()` 는 null — 호출 쪽이 플레이스홀더 연출을 유지한다.
 * §3.2 양산 필드: `scale`(배율), `flash`(atFrame 시작에 화면 섬광), `shake`(섬광 프레임 또는 타격 프레임에 흔들림),
 * `secondStage`(같은 시트 안 2단 판정 프레임에 섬광·흔들림 한 번 더), `trail`(fromFrame 부터 리본) 은 `hooks` 로 바깥(Game) 에
 * 위임한다 — 크기·프레임 수·시간은 전부 JSON 에서 읽는다. 시각 이벤트는 이펙트 자체의 재생 시간(히트스톱 동안 멈춤)으로 잰다.
 * 53라운드 Q64: 이펙트는 조명(라이트맵) **위**에 그린다 — 깊이를 `fxLitDepth` 로 라이트맵 위 띠에 옮긴다(이펙트끼리 순서는 유지).
 * 53라운드 계약 §10: `variant`(2단 갈래·가열 변주) = 색 교체 텍스처 + flash·shake·trail·마지막 프레임 유지 덮어쓰기.
 * 재생 옵션·훅 형식은 `fxTypes`(55라운드 6-1 분리).
 * 55라운드 Q14 ①: `hitstopFrame` 을 주면 히트스톱이 걸릴 때 그 프레임(판정 백열·적중 holdFrame)에 멈춘다 — 아직 그 앞이면
 * 그 프레임으로 건너뛰어 멈추고, 끝나면 그 프레임을 처음부터 이어 재생한다.
 */
import Phaser from 'phaser';
import { PROTOTYPE, fxLitDepth } from '../../core/Constants';
import { spriteLibrary } from '../sprites/sprites';
import { lightFor, lightRegistryOf, type LightSource } from '../lighting/lightRegistry';
import {
  FX_ACTION,
  animDurationMs,
  fxDrawScale,
  frameDurations,
  frameIndices,
  frameStarts,
  fxImpactFrame,
  type FxFlashSpec,
  type FxShakeSpec,
  type SheetJson,
} from '../sprites/spriteDefs';
import type { FxFollowTarget, FxHandle, FxHooks, FxPlayOptions } from './fxTypes';

export type { FxFollowTarget, FxHandle, FxHooks, FxPlayOptions, FxTrailRequest } from './fxTypes';

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
  /** 55라운드 Q23 재생 배속 (예약 훅 시계도 같은 배속) */
  timeScale: number;
  timed: FxTimed[];
  /** 50라운드: 이 이펙트의 광원 (시트 JSON light · fallback · 무기 이펙트 순간광) */
  light?: LightSource;
  /** 60라운드 `loopRange` 수명 시트: 끝낼 때 재생할 사라짐 구간 (루프 끝 다음 열부터 마지막 열) — 없으면 페이드 */
  outro?: { anim: string };
  /** 55라운드: 히트스톱 정지 프레임 열 · 그 프레임으로 건너뛰어 멈췄는지 */
  hitstopFrame?: number;
  heldAt?: Phaser.Animations.AnimationFrame;
  def: SheetJson;
}

export class FxPool {
  private readonly group: Phaser.GameObjects.Group;
  private readonly states = new Map<Phaser.GameObjects.Sprite, FxState>();
  private nextToken = 1;
  hooks: FxHooks = {};
  /** 60라운드 계약 art §21 갈래 런 교체 규칙 (원 시트 id → 교체 시트 id, 교체 시트가 로드돼 있을 때만) */
  private readonly aliases = new Map<string, string>();

  constructor(private readonly scene: Phaser.Scene) {
    this.group = scene.add.group({
      classType: Phaser.GameObjects.Sprite,
      maxSize: PROTOTYPE.FX_POOL,
      runChildUpdate: false,
    });
  }

  /**
   * 60라운드 계약 art §21 갈래 런 교체 (`katana_fall_wide`↔`katana_fall` 등, 같은 규격 1:1): 지금 런의 교체 표로 바꾼다.
   * 이후 has·sheet·play 등은 원 id 로 불러도 교체 시트를 쓴다 (교체 시트가 없으면 원 시트)
   */
  setAliases(map: Readonly<Record<string, string>>): void {
    this.aliases.clear();
    for (const [from, to] of Object.entries(map)) if (from !== to) this.aliases.set(from, to);
  }

  /** 교체 표를 거친 실제 시트 id */
  resolve(id: string): string {
    const to = this.aliases.get(id);
    return to && this.loaded(to) ? to : id;
  }

  private loaded(id: string): boolean {
    const texture = spriteLibrary.textureKey(id, FX_ACTION);
    return Boolean(texture && this.scene.textures.exists(texture));
  }

  /** 이펙트 시트가 로드돼 있는지 */
  has(id: string): boolean {
    return this.loaded(this.resolve(id));
  }

  /** 시트 자연 재생 길이 ms (없으면 0) */
  durationOf(id: string): number {
    const def = spriteLibrary.sheet(this.resolve(id), FX_ACTION);
    return def ? animDurationMs(def) : 0;
  }

  /** 시트 프레임 수 (없으면 0) */
  framesOf(id: string): number {
    return spriteLibrary.sheet(this.resolve(id), FX_ACTION)?.frames ?? 0;
  }

  /** 시트 JSON (없으면 null) */
  sheet(id: string): SheetJson | null {
    return spriteLibrary.sheet(this.resolve(id), FX_ACTION) ?? null;
  }

  /** 예비 프레임 보정: 타격 프레임(`fxImpactFrame`)이 spawn 시점에 오도록 먼저 시작해야 하는 ms */
  leadMs(id: string): number {
    const def = spriteLibrary.sheet(this.resolve(id), FX_ACTION);
    if (!def) return 0;
    return frameStarts(def)[fxImpactFrame(def)] ?? 0;
  }

  play(rawId: string, x: number, y: number, opts: FxPlayOptions = {}): FxHandle | null {
    const id = this.resolve(rawId);
    const def = spriteLibrary.sheet(id, FX_ACTION);
    // 계약 §10 색 교체 변주가 있으면 그 텍스처·애니 (만들 수 없으면 원본)
    const swapped = opts.variant?.swaps.length
      ? spriteLibrary.recolored(this.scene, id, FX_ACTION, opts.variant.swaps)
      : null;
    const texture = swapped?.texture ?? spriteLibrary.textureKey(id, FX_ACTION);
    const key = swapped?.anim(opts.dir ?? 'down') ?? spriteLibrary.animKey(id, FX_ACTION, opts.dir ?? 'down');
    if (!def || !texture || !key || !this.scene.textures.exists(texture)) return null;
    const sprite = this.group.get(x, y) as Phaser.GameObjects.Sprite | null;
    if (!sprite) return null;
    const token = this.nextToken++;
    sprite.off(Phaser.Animations.Events.ANIMATION_COMPLETE);
    // 56라운드: 남은 애니 체인(loopFrom)을 비운 뒤 멈춘다 — stop() 은 체인 다음 애니를 재생하기 때문
    sprite.anims.chain();
    sprite.anims.stop();
    // 50라운드: 새 2배 도트 이펙트(pixelScale 1)는 0.5 배로 그려 화면 크기를 맞춘다
    const scale = fxDrawScale(def);
    const row = frameIndices(def, opts.dir ?? 'down')[0] ?? 0;
    sprite
      .setTexture(texture, row + Math.max(0, Math.min(def.frames - 1, opts.staticFrame ?? 0)))
      .setOrigin(def.pivot.x / def.frameWidth, def.pivot.y / def.frameHeight)
      .setPosition(x, y)
      .setRotation(def.rotate ? (opts.angle ?? 0) : 0)
      .setAlpha(opts.alpha ?? 1)
      .setScale(scale * (opts.scaleMult ?? 1))
      .setFlipY(Boolean(opts.flipY))
      .setFlipX(Boolean(opts.flipX))
      .setActive(true)
      .setVisible(true);
    if (opts.tint !== undefined) {
      if (opts.tintFill) sprite.setTintFill(opts.tint);
      else sprite.setTint(opts.tint);
    } else sprite.clearTint();
    const follow = opts.follow;
    const depth = opts.depth ?? (follow && opts.depthOffset !== undefined ? follow.depth + opts.depthOffset : 0);
    sprite.setDepth(opts.belowLighting ? depth : fxLitDepth(depth));
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
      timeScale: opts.timeScale && opts.timeScale > 0 ? opts.timeScale : 1,
      timed: [],
      hitstopFrame: opts.hitstopFrame,
      def,
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
      sprite.anims.timeScale = state.timeScale;
      sprite.play(anim, true);
      // 56라운드: 한 번 재생 뒤 loopFrom 열부터 반복 (Phaser 애니 체인)
      const loopFrom =
        opts.loopFrom !== undefined && opts.loopFrom > 0 && opts.loopFrom < def.frames ? opts.loopFrom : null;
      if (loopFrom !== null && !opts.tailFrames)
        sprite.chain(this.tailAnim(id, key, texture, def.frames - loopFrom, opts.dir ?? 'down'));
      // 60라운드 수명 시트 (계약 art §21 loopRange): 앞 구간 1회 → [a, b] 반복 → 끝낼 때(finish·durationMs) 뒤 구간 1회
      const range = !opts.tailFrames && loopFrom === null ? this.validRange(def, opts.loopRange) : null;
      if (range) this.startRange(sprite, state, id, key, texture, def, range, opts.dir ?? 'down');
      const loop = Boolean(def.loop) || Boolean(opts.tailFrames) || loopFrom !== null || range !== null;
      if (!loop) {
        const hold = opts.holdLastMs ?? opts.variant?.holdLastMs ?? 0;
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
    const v = opts.variant;
    const flash = (spec: FxFlashSpec | undefined, frame: number) => {
      if (spec && h.flash) this.schedule(state, at(spec.atFrame, frame), () => h.flash?.(spec));
    };
    const shake = (spec: FxShakeSpec | undefined, frame: number) => {
      if (spec && h.shake && spec.px > 0 && spec.ms > 0) this.schedule(state, at(frame, impact), () => h.shake?.(spec));
    };
    // 계약 §10 2단 갈래: flashOverride·shakeOverride·trailOverride 가 시트 값을 대신한다
    const flashSpec = v?.flash ?? def.flash;
    flash(flashSpec, impact);
    shake(v?.shake ?? def.shake, flashSpec?.atFrame ?? impact);
    const second = def.secondStage;
    if (second) {
      const frame = second.frame ?? second.flash?.atFrame ?? impact;
      flash(second.flash, frame);
      shake(second.shake, frame);
    }
    const trailSpec = v?.trail ?? def.trail;
    if (trailSpec && h.trail && opts.trail !== false) {
      const spec = trailSpec;
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
  setDir(h: FxHandle | null, id: string, dir: string): void {
    if (!h || !this.isActive(h)) return;
    const key = spriteLibrary.animKey(this.resolve(id), FX_ACTION, dir);
    if (key && h.sprite.anims.currentAnim?.key !== key) h.sprite.play(key, true);
  }

  /** 고정 프레임 이펙트(진행도 주도)의 열 바꾸기 */
  setFrame(h: FxHandle | null, id: string, column: number, dir: string = 'down'): void {
    if (!h || !this.isActive(h)) return;
    const def = spriteLibrary.sheet(this.resolve(id), FX_ACTION);
    if (!def) return;
    const row = frameIndices(def, dir)[0] ?? 0;
    const frame = row + Math.max(0, Math.min(def.frames - 1, column));
    if (h.sprite.frame.name !== String(frame)) h.sprite.setFrame(frame);
  }

  /**
   * 60라운드 수명 시트 끝내기: `loopRange` 로 시작한 이펙트면 사라짐 구간(루프 끝 다음 열부터)을 한 번 재생하고 비활성,
   * 아니면 페이드 (stop 과 같다)
   */
  finish(h: FxHandle | null): void {
    if (!h || !this.isActive(h)) return;
    const st = this.states.get(h.sprite)!;
    if (!st.outro) {
      this.fadeOut(h.sprite);
      return;
    }
    this.playOutro(h.sprite, st);
  }

  private playOutro(sprite: Phaser.GameObjects.Sprite, st: FxState): void {
    const outro = st.outro;
    if (!outro) return;
    st.outro = undefined;
    st.expireAt = Infinity;
    const token = st.token;
    sprite.anims.chain();
    sprite.off(Phaser.Animations.Events.ANIMATION_COMPLETE);
    sprite.play(outro.anim, true);
    sprite.once(Phaser.Animations.Events.ANIMATION_COMPLETE, () => {
      if (this.states.get(sprite)?.token === token) this.release(sprite);
    });
  }

  private validRange(def: SheetJson, r: readonly [number, number] | undefined): [number, number] | null {
    if (!r) return null;
    const [a, b] = r;
    return Number.isInteger(a) && Number.isInteger(b) && a >= 0 && b >= a && b < def.frames ? [a, b] : null;
  }

  /** 수명 시트: 앞 구간(0..a-1)을 이미 재생 중인 애니 대신 걸고 [a, b] 반복을 잇는다. 뒤 구간이 있으면 outro 로 */
  private startRange(
    sprite: Phaser.GameObjects.Sprite,
    st: FxState,
    id: string,
    key: string,
    texture: string,
    def: SheetJson,
    [a, b]: [number, number],
    dir: string,
  ): void {
    const loopAnim = this.rangeAnim(id, key, texture, a, b, dir, true);
    if (a > 0) {
      sprite.play(this.rangeAnim(id, key, texture, 0, a - 1, dir, false), true);
      sprite.chain(loopAnim);
    } else sprite.play(loopAnim, true);
    if (b + 1 < def.frames) st.outro = { anim: this.rangeAnim(id, key, texture, b + 1, def.frames - 1, dir, false) };
  }

  /** 열 구간 애니 (키 `<애니>#r<from>-<to>[L]`, 텍스처 변형별로 1회 생성) */
  private rangeAnim(
    id: string,
    key: string,
    texture: string,
    from: number,
    to: number,
    dir: string,
    loop: boolean,
  ): string {
    const rk = `${key}#r${from}-${to}${loop ? 'L' : ''}`;
    if (!this.scene.anims.exists(rk)) {
      const def = spriteLibrary.sheet(id, FX_ACTION)!;
      const all = frameIndices(def, dir);
      const durations = frameDurations(def);
      this.scene.anims.create({
        key: rk,
        frames: all.slice(from, to + 1).map((frame, i) => ({ key: texture, frame, duration: durations[from + i] })),
        frameRate: def.fps,
        repeat: loop ? -1 : 0,
      });
    }
    return rk;
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
      st.elapsed += Math.max(0, time - st.lastTick) * st.timeScale;
      st.lastTick = time;
      this.fireDue(st);
      if (st.fading) continue;
      const f = st.follow;
      if (f) {
        if (!f.active) {
          this.release(sprite);
          continue;
        }
        const o = st.followOffset;
        sprite.setPosition(f.x + (o?.x ?? 0), f.y + (o?.y ?? 0));
        if (st.depthOffset !== undefined) sprite.setDepth(fxLitDepth(f.depth + st.depthOffset));
        if (st.followRotation) sprite.setRotation(f.rotation);
      }
      if (time >= st.expireAt) {
        if (st.outro) this.playOutro(sprite, st);
        else if (st.noFade) this.release(sprite);
        else this.fadeOut(sprite);
      }
    }
  }

  /** 재생 경과가 지난 예약 이벤트 실행 */
  private fireDue(st: FxState): void {
    if (st.timed.length === 0) return;
    const due = st.timed.filter((e) => e.atMs <= st.elapsed);
    if (due.length === 0) return;
    st.timed = st.timed.filter((e) => e.atMs > st.elapsed);
    for (const e of due) e.fire();
  }

  /**
   * 히트스톱: 활성 이펙트 애니 일시 정지·재개 (따라가기·만료는 update 를 건너뛰는 호출 쪽이 멈춘다).
   * 재생 옵션·훅 형식은 `fxTypes`(55라운드 6-1 분리).
   * 55라운드 Q14 ①: `hitstopFrame` 이 있고 아직 그 앞이면 그 프레임으로 건너뛰어 멈추고(판정 백열이 보이게), 재개하면 그 프레임부터
   */
  setPaused(on: boolean): void {
    const now = this.scene.time.now;
    for (const [sprite, st] of this.states) {
      if (on) {
        const jump = this.holdFrameOf(sprite, st);
        if (jump) {
          sprite.anims.pause(jump);
          st.heldAt = jump;
        } else sprite.anims.pause();
        // 예약 시계를 보이는 프레임에 맞춘다 (판정 프레임의 섬광·흔들림이 정지 뒤로 밀리지 않게)
        const col = (sprite.anims.currentFrame?.index ?? 1) - 1;
        if (st.hitstopFrame !== undefined && sprite.anims.currentAnim) {
          st.elapsed = Math.max(st.elapsed, frameStarts(st.def)[col] ?? st.elapsed);
          this.fireDue(st);
        }
      } else {
        sprite.anims.resume();
        if (st.heldAt) {
          // 건너뛴 프레임을 처음부터 (누적 시간을 비운다)
          sprite.anims.accumulator = 0;
          sprite.anims.nextTick = st.heldAt.duration || sprite.anims.msPerFrame;
          st.heldAt = undefined;
        }
        st.lastTick = now; // 멈춘 시간은 재생 경과에 넣지 않는다
      }
    }
  }

  /** 히트스톱에 건너뛸 프레임 (정지 프레임이 아직 오지 않았을 때만) */
  private holdFrameOf(sprite: Phaser.GameObjects.Sprite, st: FxState): Phaser.Animations.AnimationFrame | null {
    const hold = st.hitstopFrame;
    const anim = sprite.anims.currentAnim;
    const cur = sprite.anims.currentFrame;
    if (hold === undefined || !anim || !cur || !sprite.anims.isPlaying) return null;
    const target = anim.frames[hold];
    return target && cur.index - 1 < hold ? target : null;
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
    sprite.anims.chain();
    sprite.anims.stop();
    sprite.setActive(false).setVisible(false).setAlpha(1).setRotation(0).setScale(1).setFlipY(false).clearTint();
  }

  /** 마지막 n 프레임만 반복하는 애니 (키 `<애니>#tail<n>`, 텍스처 변형별로 1회 생성) */
  private tailAnim(id: string, key: string, texture: string, n: number, dir: string): string {
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
