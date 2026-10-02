/**
 * 48라운드 Q6 탄생 연출 (계약 art §6.3, UI §10.3). 새 런 첫 노드(황폐한 탄생지)에서 1회.
 *
 * 시트가 있으면: 카메라 2→4배(ZOOM_IN) → player_birth 재생 + fx/birth_dust 소용돌이(segments.swirl 루프)
 * → burstFrame 시작에 흩어짐(segments.scatter 1회)·잔불 섬광·약한 흔들림 → 마지막 프레임(= idle down 0) 뒤 플레이어로 교체
 * → 잠깐 멈춤 → 4→2배 복귀. 시트가 없으면 흙 알갱이가 모이며 플레이어가 서서히 나타나는 폴백.
 * 아무 키로 건너뛰면 즉시 끝 상태(플레이어 보임, 2배)로. 카메라 배율은 호스트가 매 프레임 `zoom` 을 읽어 적용한다.
 */
import Phaser from 'phaser';
import { BIRTH, CAMERA, DEPTH, entityDepth } from '../core/Constants';
import { spriteLibrary } from './sprites';
import { BIRTH_ACTION, BIRTH_FX, FX_ACTION, frameDurations, frameStarts, type SheetDef } from './spriteDefs';

export interface BirthHost {
  scene: Phaser.Scene;
  /** 주인공 발 위치 */
  x: number;
  y: number;
  /** 몸 숨김 (연출 스프라이트가 대신 그린다) */
  hidePlayer(on: boolean): void;
  /** 폴백: 플레이어 투명도 (0..1) */
  setPlayerAlpha(a: number): void;
  /** 잔불 터짐: 섬광·흔들림 */
  burst(): void;
  /** 끝 (건너뛰기 포함). 호스트가 조작을 풀고 BIRTH_DONE 을 낸다 */
  done(skipped: boolean): void;
}

type Phase = 'zoomIn' | 'play' | 'hold' | 'zoomOut' | 'done';

/** 시트 재생이 이 배수만큼 늦어지면 끊는다 (안전장치) */
const PLAY_TIMEOUT_MULT = 3;

const ease = (t: number) => 0.5 - 0.5 * Math.cos(Math.PI * Math.max(0, Math.min(1, t)));

export class BirthSequence {
  private phase: Phase = 'zoomIn';
  private phaseAt = 0;
  private readonly sheet: SheetDef | undefined;
  private readonly dustSheet: SheetDef | undefined;
  private body: Phaser.GameObjects.Sprite | null = null;
  private dust: Phaser.GameObjects.Sprite | null = null;
  private readonly bits: Phaser.GameObjects.Rectangle[] = [];
  private playMs = 0;
  private burstAtMs = 0;
  private bursted = false;
  /** 현재 카메라 배율 (호스트가 적용) */
  zoom: number = CAMERA.ZOOM;
  /** 디버그 */
  skipped = false;

  constructor(private readonly host: BirthHost) {
    const scene = host.scene;
    const sheet = spriteLibrary.sheet('player', BIRTH_ACTION);
    const tex = spriteLibrary.textureKey('player', BIRTH_ACTION);
    this.sheet = sheet && tex && scene.textures.exists(tex) ? sheet : undefined;
    const dust = spriteLibrary.sheet(BIRTH_FX, FX_ACTION);
    const dtex = spriteLibrary.textureKey(BIRTH_FX, FX_ACTION);
    this.dustSheet = dust && dtex && scene.textures.exists(dtex) ? dust : undefined;
  }

  /** 시트 연출인지 (false = 폴백) */
  get usesSheet(): boolean {
    return Boolean(this.sheet);
  }

  get active(): boolean {
    return this.phase !== 'done';
  }

  get state(): {
    phase: Phase;
    zoom: number;
    sheet: boolean;
    dust: boolean;
    bursted: boolean;
    skipped: boolean;
    bodyAnim: string | null;
    bodyFrame: string | null;
    dustAnim: string | null;
  } {
    return {
      phase: this.phase,
      zoom: this.zoom,
      sheet: Boolean(this.sheet),
      dust: Boolean(this.dustSheet),
      bursted: this.bursted,
      skipped: this.skipped,
      bodyAnim: this.body?.anims.currentAnim?.key ?? null,
      bodyFrame: this.body ? String(this.body.frame.name) : null,
      dustAnim: this.dust?.anims.currentAnim?.key ?? null,
    };
  }

  start(now: number): void {
    const scene = this.host.scene;
    this.host.hidePlayer(true);
    this.phase = 'zoomIn';
    this.phaseAt = now;
    this.zoom = CAMERA.ZOOM;
    if (this.sheet) {
      const tex = spriteLibrary.textureKey('player', BIRTH_ACTION)!;
      this.body = scene.add
        .sprite(this.host.x, this.host.y, tex, 0)
        .setOrigin(this.sheet.pivot.x / this.sheet.frameWidth, this.sheet.pivot.y / this.sheet.frameHeight)
        .setDepth(entityDepth(this.host.y));
      this.playMs = frameDurations(this.sheet).reduce((a, b) => a + b, 0);
      const bf =
        typeof this.sheet.burstFrame === 'number' ? this.sheet.burstFrame : Math.floor(this.sheet.frames * 0.6);
      this.burstAtMs = frameStarts(this.sheet)[Math.max(0, Math.min(this.sheet.frames - 1, bf))] ?? 0;
    } else {
      this.playMs = BIRTH.FALLBACK_MS;
      this.burstAtMs = BIRTH.FALLBACK_MS * BIRTH.FALLBACK_BURST_AT;
    }
  }

  /** 매 프레임 */
  update(now: number): void {
    if (this.phase === 'done') return;
    const t = now - this.phaseAt;
    switch (this.phase) {
      case 'zoomIn':
        this.zoom = CAMERA.ZOOM + (BIRTH.ZOOM - CAMERA.ZOOM) * ease(t / BIRTH.ZOOM_IN_MS);
        if (t >= BIRTH.ZOOM_IN_MS) this.beginPlay(now);
        break;
      case 'play':
        // 시트: 잔불·끝은 애니 프레임 이벤트로 (느린 프레임에서도 그림과 맞게). 안전장치로 3배 시간이 지나면 끝
        if (!this.sheet) {
          if (!this.bursted && t >= this.burstAtMs) this.doBurst();
          this.updateFallback(t);
          if (t >= this.playMs) this.endPlay(now);
        } else if (t >= this.playMs * PLAY_TIMEOUT_MULT) this.endPlay(now);
        break;
      case 'hold':
        if (t >= BIRTH.HOLD_MS) {
          this.phase = 'zoomOut';
          this.phaseAt = now;
        }
        break;
      case 'zoomOut':
        this.zoom = BIRTH.ZOOM + (CAMERA.ZOOM - BIRTH.ZOOM) * ease(t / BIRTH.ZOOM_OUT_MS);
        if (t >= BIRTH.ZOOM_OUT_MS) this.finish(false);
        break;
    }
  }

  /** 아무 키: 즉시 끝 상태로 */
  skip(): void {
    if (this.phase === 'done') return;
    this.skipped = true;
    this.finishBody();
    this.finish(true);
  }

  destroy(): void {
    this.body?.destroy();
    this.dust?.destroy();
    for (const b of this.bits) b.destroy();
    this.bits.length = 0;
    this.body = null;
    this.dust = null;
  }

  private beginPlay(now: number): void {
    this.zoom = BIRTH.ZOOM;
    this.phase = 'play';
    this.phaseAt = now;
    const scene = this.host.scene;
    if (this.sheet && this.body) {
      const key = spriteLibrary.animKey('player', BIRTH_ACTION, 'down');
      const bf =
        typeof this.sheet.burstFrame === 'number' ? this.sheet.burstFrame : Math.floor(this.sheet.frames * 0.6);
      this.body.on(
        Phaser.Animations.Events.ANIMATION_UPDATE,
        (_a: unknown, frame: Phaser.Animations.AnimationFrame) => {
          if (!this.bursted && frame.index - 1 >= bf) this.doBurst();
        },
      );
      this.body.once(Phaser.Animations.Events.ANIMATION_COMPLETE, () => this.endPlay(this.host.scene.time.now));
      if (key) this.body.play(key);
      else this.endPlay(now);
    } else this.spawnFallbackBits();
    // 바닥 흙 소용돌이 (segments.swirl 루프, 없으면 0~3 루프)
    if (this.dustSheet) {
      const tex = spriteLibrary.textureKey(BIRTH_FX, FX_ACTION)!;
      this.dust = scene.add
        .sprite(this.host.x, this.host.y, tex, 0)
        .setOrigin(
          this.dustSheet.pivot.x / this.dustSheet.frameWidth,
          this.dustSheet.pivot.y / this.dustSheet.frameHeight,
        )
        .setDepth(DEPTH.FX_GROUND);
      const key = this.segmentAnim('swirl', [0, 1, 2, 3], true);
      if (key) this.dust.play(key);
    }
  }

  /** 몸 연출 끝 → 플레이어로 교체 → 잠깐 멈춤 */
  private endPlay(now: number): void {
    if (this.phase !== 'play') return;
    if (!this.bursted) this.doBurst();
    this.finishBody();
    this.phase = 'hold';
    this.phaseAt = now;
  }

  private doBurst(): void {
    this.bursted = true;
    this.host.burst();
    if (this.dust) {
      const key = this.segmentAnim('scatter', [4, 5, 6, 7, 8], false);
      if (key) {
        this.dust.play(key);
        this.dust.once(Phaser.Animations.Events.ANIMATION_COMPLETE, () => {
          this.dust?.destroy();
          this.dust = null;
        });
      }
    }
    if (!this.sheet) this.emberBurst();
  }

  /** 연출 몸 → 실제 플레이어 (마지막 프레임 = idle down 0 이라 이어진다) */
  private finishBody(): void {
    this.body?.destroy();
    this.body = null;
    for (const b of this.bits) b.destroy();
    this.bits.length = 0;
    this.host.hidePlayer(false);
    this.host.setPlayerAlpha(1);
  }

  private finish(skipped: boolean): void {
    this.phase = 'done';
    this.zoom = CAMERA.ZOOM;
    this.dust?.destroy();
    this.dust = null;
    this.host.done(skipped);
  }

  /** birth_dust 구간 애니 (JSON segments 가 있으면 그 프레임) — 1회 생성 */
  private segmentAnim(name: 'swirl' | 'scatter', fallback: number[], loop: boolean): string | null {
    const def = this.dustSheet;
    if (!def) return null;
    const scene = this.host.scene;
    const tex = spriteLibrary.textureKey(BIRTH_FX, FX_ACTION)!;
    const key = `${tex}#${name}`;
    if (!scene.anims.exists(key)) {
      const seg = (def as unknown as { segments?: Record<string, { frames?: number[] }> }).segments?.[name]?.frames;
      const frames = (seg && seg.length > 0 ? seg : fallback).filter((f) => f >= 0 && f < def.frames);
      if (frames.length === 0) return null;
      const d = frameDurations(def);
      scene.anims.create({
        key,
        frames: frames.map((f) => ({ key: tex, frame: f, duration: d[f] })),
        frameRate: def.fps,
        repeat: loop ? -1 : 0,
      });
    }
    return key;
  }

  // --- 폴백 (시트 없음): 흙 알갱이가 발밑으로 모이고 플레이어가 서서히 나타난다 ---

  private spawnFallbackBits(): void {
    const scene = this.host.scene;
    for (let i = 0; i < BIRTH.DUST_COUNT; i++) {
      const a = (i / BIRTH.DUST_COUNT) * Math.PI * 2;
      const r = BIRTH.DUST_RADIUS_PX * (0.6 + ((i * 37) % 10) / 25);
      const b = scene.add
        .rectangle(
          this.host.x + Math.cos(a) * r,
          this.host.y + Math.sin(a) * r * 0.45,
          BIRTH.DUST_SIZE,
          BIRTH.DUST_SIZE,
        )
        .setFillStyle(BIRTH.DUST_COLOR, 0.9)
        .setDepth(DEPTH.FX_GROUND);
      b.setData('a', a).setData('r', r);
      this.bits.push(b);
    }
    this.host.hidePlayer(false);
    this.setPlayerAlpha(0);
  }

  private updateFallback(t: number): void {
    const k = Math.min(1, t / this.playMs);
    for (const b of this.bits) {
      const a = (b.getData('a') as number) + k * Math.PI * 1.5;
      const r = (b.getData('r') as number) * (1 - k);
      b.setPosition(this.host.x + Math.cos(a) * r, this.host.y - 6 * k + Math.sin(a) * r * 0.45);
      b.setAlpha(1 - k * 0.6);
    }
    this.setPlayerAlpha(ease(k));
  }

  private emberBurst(): void {
    const scene = this.host.scene;
    for (let i = 0; i < BIRTH.EMBER_COUNT; i++) {
      const a = (i / BIRTH.EMBER_COUNT) * Math.PI * 2;
      const e = scene.add
        .rectangle(this.host.x, this.host.y - 8, 1, 1)
        .setFillStyle(BIRTH.EMBER_COLOR, 1)
        .setDepth(DEPTH.HIT_FX);
      scene.tweens.add({
        targets: e,
        x: this.host.x + Math.cos(a) * BIRTH.EMBER_DIST_PX,
        y: this.host.y - 8 + Math.sin(a) * BIRTH.EMBER_DIST_PX * 0.6,
        alpha: 0,
        duration: BIRTH.EMBER_MS,
        onComplete: () => e.destroy(),
      });
    }
  }

  /** 폴백: 호스트 플레이어를 보이게 두고 알파만 (hidePlayer(false) 뒤) */
  private setPlayerAlpha(a: number): void {
    this.host.setPlayerAlpha(a);
  }
}
