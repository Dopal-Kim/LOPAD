/**
 * 플레이어·적 공통 외형 조합 (상속 대신 조합):
 * - 시트가 있으면 애니메이션 스프라이트 + 발 피벗 원점 + 발밑 바디 + 타원 그림자
 * - 없으면 단색 사각형 플레이스홀더 (기존 동작 유지)
 * - 깊이는 발 위치 y 로 정렬
 */
import Phaser from 'phaser';
import { DEPTH, SPRITES, TEXTURES, entityDepth } from '../core/Constants';
import { spriteLibrary } from '../systems/sprites';
import { animDurationMs, frameDurations, frameStarts, type Facing } from '../systems/spriteDefs';

type Body = Phaser.Physics.Arcade.Body;
type Host = Phaser.GameObjects.Sprite & { body: Body };

/** 플레이스홀더 사각형 텍스처 (크기별 1장, 흰색 — 틴트로 색을 입힌다) */
export function placeholderTexture(scene: Phaser.Scene, w: number, h: number): string {
  const key = `${TEXTURES.PLACEHOLDER_PREFIX}${w}x${h}`;
  if (!scene.textures.exists(key)) {
    const c = scene.textures.createCanvas(key, w, h)!;
    c.context.fillStyle = '#ffffff';
    c.context.fillRect(0, 0, w, h);
    c.refresh();
  }
  return key;
}

/** 발밑 타원 그림자 텍스처 (폭별 1장) */
export function shadowTexture(scene: Phaser.Scene, w: number): string {
  const h = Math.max(2, Math.round(w * SPRITES.SHADOW_RATIO));
  const key = `${TEXTURES.SHADOW_PREFIX}${w}`;
  if (!scene.textures.exists(key)) {
    const g = scene.make.graphics({ x: 0, y: 0 }, false);
    g.fillStyle(SPRITES.SHADOW_COLOR, 1);
    g.fillEllipse(w / 2, h / 2, w, h);
    g.generateTexture(key, w, h);
    g.destroy();
  }
  return key;
}

export class EntityVisual {
  /** 애니메이션 시트가 있는지 */
  readonly animated: boolean;
  facing: Facing = 'down';
  /** 현재 재생 중인 애니 키 (디버그) */
  current: string | null = null;
  /** 마지막 oneShot 의 2번째 프레임 시작까지 ms (재생 속도 반영). 시트가 없으면 0 */
  lastImpactMs = 0;
  /** 마지막 oneShot 의 프레임별 시작 시각 ms (재생 속도 반영). 시트가 없으면 빈 배열 */
  lastFrameStarts: number[] = [];
  /** 실제 시트 이름 (별칭이면 대상 이름, 예: stage2 → stage1) */
  readonly sheetName: string;
  private busyUntil = 0;
  private dead = false;
  /** 특정 프레임 유지 중(보스 예고·벽 경직): idle/walk 가 덮어쓰지 않는다 */
  private holdUntil = -1;
  private shadow: Phaser.GameObjects.Image | null = null;
  private readonly baseTint: number;

  constructor(
    private readonly host: Host,
    readonly name: string,
    bodyW: number,
    bodyH: number,
    placeholderColor: number,
  ) {
    const scene = host.scene;
    this.baseTint = placeholderColor;
    this.sheetName = spriteLibrary.resolve(name);
    const idle = spriteLibrary.sheet(name, 'idle');
    const texture = spriteLibrary.textureKey(name, 'idle');
    this.animated = Boolean(idle && texture && scene.textures.exists(texture));
    if (idle && texture && this.animated) {
      host.setTexture(texture, 0);
      host.setOrigin(idle.pivot.x / idle.frameWidth, idle.pivot.y / idle.frameHeight);
      // 바디는 발밑: 가로 중앙, 아래 끝이 피벗 행 바로 아래
      host.body.setSize(bodyW, bodyH, false);
      host.body.setOffset((idle.frameWidth - bodyW) / 2, idle.pivot.y + 1 - bodyH);
      const sw = bodyW + SPRITES.SHADOW_PAD;
      this.shadow = scene.add
        .image(host.x, host.y, shadowTexture(scene, sw))
        .setAlpha(SPRITES.SHADOW_ALPHA)
        .setDepth(DEPTH.SHADOW);
      host.once(Phaser.GameObjects.Events.DESTROY, () => this.shadow?.destroy());
    } else {
      host.setTexture(placeholderTexture(scene, bodyW, bodyH));
      host.setOrigin(0.5, 0.5);
      host.body.setSize(bodyW, bodyH, true);
      host.setTint(placeholderColor);
    }
    this.sync();
  }

  /** 매 프레임: 깊이·그림자 위치 */
  sync(): void {
    this.host.setDepth(entityDepth(this.host.y));
    if (this.shadow) this.shadow.setPosition(this.host.x, this.host.y);
  }

  get isDead(): boolean {
    return this.dead;
  }

  /** 프레임 유지 중인지 */
  get held(): boolean {
    return this.holdUntil === Infinity || this.holdUntil > this.hostTime();
  }

  /** 반복 동작(idle/walk). 일회성 동작이 재생 중이거나 프레임 유지 중이면 무시 */
  loop(action: 'idle' | 'walk', dir: Facing, time: number): void {
    this.facing = dir;
    if (this.holdUntil >= 0 && time >= this.holdUntil) this.release();
    if (!this.animated || this.dead || time < this.busyUntil || this.holdUntil >= 0) return;
    const key = spriteLibrary.animKey(this.name, action, dir);
    if (!key || key === this.current) return;
    const sameAction = this.current?.startsWith(`${this.sheetName}_${action}_`) ?? false;
    const cur = this.host.anims.currentFrame;
    const startFrame = SPRITES.KEEP_WALK_FRAME && sameAction && cur ? cur.index - 1 : 0;
    this.host.anims.timeScale = 1;
    this.host.play({ key, startFrame }, true);
    this.current = key;
  }

  /**
   * 일회성 동작(attack/dash/hurt/death). fitMs 를 주면 그 시간에 맞춰 재생 속도를 조정.
   * 반환: 실제 재생 시간 ms (시트가 없으면 0)
   */
  oneShot(action: string, dir: Facing, time: number, fitMs?: number): number {
    this.facing = dir;
    this.lastImpactMs = 0;
    this.lastFrameStarts = [];
    if (!this.animated || this.dead) return 0;
    const def = spriteLibrary.sheet(this.name, action);
    const key = spriteLibrary.animKey(this.name, action, dir);
    if (!def || !key) return 0;
    this.holdUntil = -1;
    const natural = animDurationMs(def);
    const scale = fitMs && fitMs > 0 ? natural / fitMs : 1;
    this.host.anims.timeScale = scale;
    this.host.play(key, false);
    this.current = key;
    const ms = natural / scale;
    this.busyUntil = time + ms;
    this.lastFrameStarts = frameStarts(def, scale);
    if (def.frames >= 2) this.lastImpactMs = this.lastFrameStarts[1];
    if (action === 'death') this.dead = true;
    return ms;
  }

  /** 마지막 oneShot 의 `column` 번째 프레임 시작까지 ms (없으면 0) */
  frameStartMs(column: number): number {
    return this.lastFrameStarts[column] ?? 0;
  }

  /**
   * 한 프레임 유지 (보스 예고 frame 0, 벽 경직·부채꼴 frame 3). `untilMs` 가 Infinity 면 `release()` 까지.
   * 시트가 없으면 아무것도 하지 않는다 (false)
   */
  hold(action: string, dir: Facing, column: number, time: number, durationMs = Infinity): boolean {
    this.facing = dir;
    if (!this.animated || this.dead) return false;
    const def = spriteLibrary.sheet(this.name, action);
    const texture = spriteLibrary.textureKey(this.name, action);
    if (!def || !texture) return false;
    const row = Math.max(0, def.directions.indexOf(dir));
    const c = Math.max(0, Math.min(def.frames - 1, column));
    this.host.anims.stop();
    this.host.setTexture(texture, row * def.frames + c);
    this.current = `${this.sheetName}_${action}_${dir}#hold${c}`;
    this.holdUntil = durationMs === Infinity ? Infinity : time + durationMs;
    this.busyUntil = 0;
    return true;
  }

  /** 지정한 열만 반복 (보스 돌진 1↔2). `release()` 까지 유지. 시트가 없으면 false */
  loopFrames(action: string, dir: Facing, columns: number[], frameMs: number): boolean {
    this.facing = dir;
    if (!this.animated || this.dead) return false;
    const key = spriteLibrary.phaseAnim(this.host.scene, this.name, action, dir, columns, frameMs);
    if (!key) return false;
    this.host.anims.timeScale = 1;
    this.host.play(key, true);
    this.current = key;
    this.holdUntil = Infinity;
    this.busyUntil = 0;
    return true;
  }

  /** 유지·반복 해제 → 다음 loop() 에서 idle/walk 로 돌아간다 */
  release(): void {
    if (this.holdUntil < 0) return;
    this.holdUntil = -1;
    this.current = null;
  }

  private hostTime(): number {
    return this.host.scene?.time.now ?? 0;
  }

  /** 일회성 동작의 첫 프레임 길이 (적중·발사 타이밍을 2번째 프레임에 맞출 때). 시트가 없으면 0 */
  impactDelayMs(action: string): number {
    if (!this.animated) return 0;
    const def = spriteLibrary.sheet(this.name, action);
    if (!def || def.frames < 2) return 0;
    return frameDurations(def)[0];
  }

  /** 상태 색(경직·예고 등): 플레이스홀더는 채움색, 시트는 곱 틴트 */
  paint(color: number): void {
    this.host.setTint(color);
  }

  /** 짧은 번쩍임: 시트는 전체 채움 틴트 */
  flash(color: number): void {
    if (this.animated) this.host.setTintFill(color);
    else this.host.setTint(color);
  }

  restore(): void {
    if (this.animated) this.host.clearTint();
    else this.host.setTint(this.baseTint);
  }

  /**
   * 사망 시체: 호스트는 바로 파괴되므로 별도 스프라이트가 death 를 재생하고 유지 후 사라진다.
   * 시트가 없으면 아무것도 남기지 않는다
   */
  spawnCorpse(): void {
    if (!this.animated) return;
    const scene = this.host.scene;
    const def = spriteLibrary.sheet(this.name, 'death');
    const key = spriteLibrary.animKey(this.name, 'death', this.facing);
    const texture = spriteLibrary.textureKey(this.name, 'death');
    if (!def || !key || !texture) return;
    const corpse = scene.add
      .sprite(this.host.x, this.host.y, texture, 0)
      .setOrigin(this.host.originX, this.host.originY)
      .setDepth(entityDepth(this.host.y));
    corpse.play(key);
    const shadow = this.shadow;
    this.shadow = null; // 시체와 함께 사라진다
    const targets = shadow ? [corpse, shadow] : [corpse];
    scene.tweens.add({
      targets,
      alpha: 0,
      delay: animDurationMs(def) + SPRITES.CORPSE_HOLD_MS,
      duration: SPRITES.CORPSE_FADE_MS,
      onComplete: () => {
        corpse.destroy();
        shadow?.destroy();
      },
    });
  }
}
