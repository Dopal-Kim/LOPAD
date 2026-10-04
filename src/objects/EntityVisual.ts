/**
 * 플레이어·적 공통 외형 조합 (상속 대신 조합):
 * - 시트가 있으면 애니메이션 스프라이트 + 발 피벗 원점 + 발밑 바디 + 타원 그림자
 * - 없으면 단색 사각형 플레이스홀더 (기존 동작 유지)
 * - 깊이는 발 위치 y 로 정렬
 * - 50라운드 계약 §9: 시트마다 도트 배율(`pixelScale`)이 다를 수 있다(새 32×48 = 1, 기존 16×24 = 없음/2).
 *   동작을 바꿀 때 그 시트의 배율·피벗으로 스프라이트 배율·원점을 맞추고, 물리 바디는 월드 크기가 그대로이도록 다시 맞춘다
 */
import Phaser from 'phaser';
import { DEPTH, SPRITES, TEXTURES, entityDepth } from '../core/Constants';
import { spriteLibrary } from '../systems/sprites';
import {
  animDurationMs,
  artScale,
  bodyBaseAction,
  directionRow,
  fireDelayMs,
  frameAt,
  frameDurations,
  frameIndices,
  frameStarts,
  keyedDurations,
  parseAnimKey,
  startsOf,
  v3HitLift,
  cardinalOf,
  type Dir8,
  type Facing,
  type SheetJson,
} from '../systems/spriteDefs';

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
  /** spawnCorpse 가 남긴 시체 스프라이트 (사라지면 null) — 54라운드 Q28 보스 불길이 죽음 그림을 따라간다 */
  corpse: Phaser.GameObjects.Sprite | null = null;
  /** 현재 재생 중인 애니 키 (디버그) */
  current: string | null = null;
  /** 마지막 oneShot 의 2번째 프레임 시작까지 ms (재생 속도 반영). 시트가 없으면 0 */
  lastImpactMs = 0;
  /** 마지막 oneShot 의 프레임별 시작 시각 ms (재생 속도 반영). 시트가 없으면 빈 배열 */
  lastFrameStarts: number[] = [];
  /** 마지막 oneShot 의 전체 길이 ms (재생 속도 반영) */
  lastDurationMs = 0;
  /** 실제 시트 이름 (별칭이면 대상 이름, 예: stage2 → stage1) */
  readonly sheetName: string;
  private busyUntil = 0;
  private dead = false;
  /** 특정 프레임 유지 중(보스 예고·벽 경직): idle/walk 가 덮어쓰지 않는다 */
  private holdUntil = -1;
  private shadow: Phaser.GameObjects.Image | null = null;
  private readonly baseTint: number;
  /** 지금 맞춘 시트 배율·피벗 (바뀔 때만 바디를 다시 맞춘다) */
  private fitKey = '';
  /** 56라운드 Q36: 반투명 번쩍임 사본 · 그 시간 트윈 */
  private tintCopy: Phaser.GameObjects.Sprite | null = null;
  private tintTween: Phaser.Tweens.Tween | null = null;
  /** 53라운드 v3 적: 지금 맞춘 시트 (피격 연출 높이) */
  private fitDef: Pick<SheetJson, 'pivot' | 'pixelScale'> | null = null;

  constructor(
    private readonly host: Host,
    readonly name: string,
    private readonly bodyW: number,
    private readonly bodyH: number,
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
      this.fit(idle);
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

  /**
   * 시트 배율·피벗 맞춤: 원점 = 피벗, 배율 = 도트 배율 → 월드 (`artScale`). 바디는 발밑(가로 중앙, 아래 끝이 피벗 바로 아래)에
   * 월드 크기 bodyW×bodyH 로 — Arcade 바디 크기·오프셋은 프레임 단위 × 스프라이트 배율이라 배율로 나눠 넣는다
   */
  private fit(def: Pick<SheetJson, 'frameWidth' | 'frameHeight' | 'pivot' | 'pixelScale'>): void {
    const s = artScale(def);
    const key = `${def.frameWidth},${def.frameHeight},${def.pivot.x},${def.pivot.y},${s}`;
    if (key === this.fitKey) return;
    this.fitKey = key;
    this.fitDef = def;
    const host = this.host;
    host.setOrigin(def.pivot.x / def.frameWidth, def.pivot.y / def.frameHeight);
    host.setScale(s);
    // 바디의 배율 캐시(_sx)를 지금 배율로 맞춘 뒤 크기를 넣는다 (다음 물리 단계를 기다리지 않고 바로 맞는 크기)
    host.body.updateBounds();
    host.body.setSize(this.bodyW / s, this.bodyH / s, false);
    host.body.setOffset((def.frameWidth - this.bodyW / s) / 2, def.pivot.y + (1 - this.bodyH) / s);
  }

  /** 동작 시트로 배율·원점 맞춤 (시트가 없으면 그대로) */
  private fitAction(action: string): void {
    const def = spriteLibrary.sheet(this.name, action);
    if (def) this.fit(def);
  }

  /**
   * 53라운드 v3 적(주인공과 같은 1.5배 그림): 피격 연출(섬광·숫자)을 바디 중심에서 그림 중심으로 올리는 거리(월드).
   * 그림 중심 = 피벗 높이의 절반. 판정·바디는 그대로. 구 시트·v2 는 0 (기존 자리 그대로)
   */
  get hitLiftPx(): number {
    return this.fitDef ? v3HitLift(this.fitDef, this.bodyH) : 0;
  }

  /** 디버그: 발밑 그림자 자리·크기 (없으면 null) */
  get shadowInfo(): { x: number; y: number; w: number; h: number } | null {
    const s = this.shadow;
    return s ? { x: s.x, y: s.y, w: s.displayWidth, h: s.displayHeight } : null;
  }

  /** 48라운드 탄생 연출: 몸·그림자를 숨긴다 (다른 스프라이트가 대신 그린다) */
  setHidden(on: boolean): void {
    this.host.setVisible(!on);
    this.shadow?.setVisible(!on);
  }

  /** 일회성 동작 재생 중 (loop 가 덮어쓰지 않는 동안) */
  isBusy(time: number): boolean {
    return time < this.busyUntil;
  }

  /** 이 동작의 시트가 있는지 (애니 시트가 있을 때만) */
  hasAction(action: string): boolean {
    return this.animated && Boolean(spriteLibrary.sheet(this.name, action));
  }

  /** 이 개체의 동작 시트 정의 (JSON 메모 필드 읽기용). 없으면 undefined */
  sheet(action: string): ReturnType<typeof spriteLibrary.sheet> {
    return spriteLibrary.sheet(this.name, action);
  }

  /** 매 프레임: 깊이·그림자 위치 (56라운드: 반투명 번쩍임 사본도 몸 프레임을 따라간다) */
  sync(): void {
    this.host.setDepth(entityDepth(this.host.y));
    if (this.shadow) this.shadow.setPosition(this.host.x, this.host.y);
    if (this.tintCopy?.visible) this.copyHost(this.tintCopy);
  }

  /**
   * 56라운드 Q36: 반투명 색 번쩍임 (적 피격 = 호박 반투명) — 몸 위에 같은 프레임 사본을 채움색·알파로 겹친다.
   * 시간은 트윈으로 재므로 히트스톱(씬 시계 정지)에 늘어나지 않는다. 시트가 없으면 곱 틴트를 같은 시간만
   */
  flashOverlay(color: number, alpha: number, ms: number): void {
    const host = this.host;
    const scene = host.scene;
    this.tintTween?.stop();
    if (!this.animated) {
      host.setTint(color);
      this.tintTween = scene.tweens.addCounter({
        from: 0,
        to: 1,
        duration: ms,
        onComplete: () => {
          if (host.active) host.setTint(this.baseTint);
        },
      });
      return;
    }
    let copy = this.tintCopy;
    if (!copy) {
      copy = scene.add.sprite(host.x, host.y, host.texture.key).setVisible(false);
      this.tintCopy = copy;
      host.once(Phaser.GameObjects.Events.DESTROY, () => {
        this.tintTween?.stop();
        copy?.destroy();
        this.tintCopy = null;
      });
    }
    this.copyHost(copy);
    copy.setTintFill(color).setAlpha(alpha).setVisible(host.visible);
    this.tintTween = scene.tweens.addCounter({
      from: 0,
      to: 1,
      duration: ms,
      onComplete: () => copy?.setVisible(false),
    });
  }

  /** 디버그: 반투명 번쩍임이 보이는 중 */
  get overlayFlashing(): boolean {
    return Boolean(this.tintCopy?.visible);
  }

  private copyHost(copy: Phaser.GameObjects.Sprite): void {
    const h = this.host;
    copy
      .setTexture(h.texture.key, h.frame.name)
      .setOrigin(h.originX, h.originY)
      .setPosition(h.x, h.y)
      .setScale(h.scaleX, h.scaleY)
      .setFlip(h.flipX, h.flipY)
      .setDepth(h.depth + DEPTH.OVERLAY_STEP * 0.5);
  }

  get isDead(): boolean {
    return this.dead;
  }

  /** 프레임 유지 중인지 */
  get held(): boolean {
    return this.holdUntil === Infinity || this.holdUntil > this.hostTime();
  }

  /**
   * 반복 동작(idle/walk/run). 일회성 동작이 재생 중이거나 프레임 유지 중이면 무시.
   * rate = 재생 배속 (52라운드 Q10 보폭 맞춤 — 매 프레임 갱신). 걷기↔달리기·방향 전환은 프레임 위치를 이어 간다
   */
  loop(action: string, dir: Facing, time: number, rate = 1): void {
    this.facing = dir;
    if (this.holdUntil >= 0 && time >= this.holdUntil) this.release();
    if (!this.animated || this.dead || time < this.busyUntil || this.holdUntil >= 0) return;
    const key = spriteLibrary.animKey(this.name, action, dir);
    if (!key) return;
    if (key === this.current) {
      this.host.anims.timeScale = rate;
      return;
    }
    this.fitAction(action);
    // 53라운드 Q19: 무기별 자세 변형(walk_free 등)도 같은 기본 동작으로 본다 — 걷기↔달리기·무기 교체 때 프레임을 잇는다
    const stride = (a: string) => ['walk', 'run'].includes(bodyBaseAction(a));
    const prevAction = this.current ? parseAnimKey(this.current, this.sheetName)?.action : undefined;
    const sameAction = prevAction !== undefined && bodyBaseAction(prevAction) === bodyBaseAction(action);
    const strideSwap = stride(action) && prevAction !== undefined && stride(prevAction);
    const cur = this.host.anims.currentFrame;
    const frames = spriteLibrary.sheet(this.name, action)?.frames ?? 1;
    const startFrame = SPRITES.KEEP_WALK_FRAME && (sameAction || strideSwap) && cur ? (cur.index - 1) % frames : 0;
    this.host.anims.timeScale = rate;
    this.host.play({ key, startFrame }, true);
    this.current = key;
  }

  /**
   * 일회성 동작(attack/dash/hurt/death). fitMs 를 주면 그 시간에 맞춰 재생 속도를 조정.
   * 반환: 실제 재생 시간 ms (시트가 없으면 0)
   */
  oneShot(action: string, dir: Dir8, time: number, fitMs?: number, key?: { frame: number; atMs: number }): number {
    // 56라운드: 8행 시트는 대각 행으로 재생하고, 이동·대기 그림의 방향은 가로 성분 4방향으로 이어 간다
    this.facing = cardinalOf(dir);
    this.lastImpactMs = 0;
    this.lastFrameStarts = [];
    this.lastDurationMs = 0;
    if (!this.animated || this.dead) return 0;
    const def = spriteLibrary.sheet(this.name, action);
    const anim = spriteLibrary.animKey(this.name, action, dir);
    if (!def || !anim) return 0;
    this.fit(def);
    this.holdUntil = -1;
    const natural = animDurationMs(def);
    // 51라운드 Q3: 예비 동작·휘두름을 따로 늘이는 두 구간 맞춤 (판정 프레임 시작 = key.atMs)
    const keyed = key ? keyedDurations(frameDurations(def), key.frame, key.atMs, fitMs ?? natural) : null;
    let ms: number;
    if (keyed) {
      const k = `${anim}#k${key!.frame}-${Math.round(key!.atMs)}-${Math.round(fitMs ?? natural)}`;
      const texture = spriteLibrary.textureKey(this.name, action);
      if (texture && !this.host.scene.anims.exists(k))
        this.host.scene.anims.create({
          key: k,
          frames: frameIndices(def, dir).map((frame, i) => ({ key: texture, frame, duration: keyed[i] })),
          frameRate: def.fps,
          repeat: 0,
        });
      this.host.anims.timeScale = 1;
      this.host.play(k, false);
      this.current = k;
      ms = keyed.reduce((a, b) => a + b, 0);
      this.lastFrameStarts = startsOf(keyed);
    } else {
      const scale = fitMs && fitMs > 0 ? natural / fitMs : 1;
      this.host.anims.timeScale = scale;
      this.host.play(anim, false);
      this.current = anim;
      ms = natural / scale;
      this.lastFrameStarts = frameStarts(def, scale);
    }
    this.busyUntil = time + ms;
    this.lastDurationMs = ms;
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
  hold(action: string, dir: Dir8, column: number, time: number, durationMs = Infinity): boolean {
    this.facing = cardinalOf(dir);
    if (!this.animated || this.dead) return false;
    const def = spriteLibrary.sheet(this.name, action);
    const texture = spriteLibrary.textureKey(this.name, action);
    if (!def || !texture) return false;
    const row = directionRow(def, dir);
    const c = Math.max(0, Math.min(def.frames - 1, column));
    this.fit(def);
    this.host.anims.stop();
    this.host.setTexture(texture, row * def.frames + c);
    this.current = `${this.sheetName}_${action}_${dir}#hold${c}`;
    this.holdUntil = durationMs === Infinity ? Infinity : time + durationMs;
    this.busyUntil = 0;
    return true;
  }

  /** 지정한 열만 반복 (보스 돌진 1↔2). `release()` 까지 유지. 시트가 없으면 false */
  loopFrames(action: string, dir: Dir8, columns: number[], frameMs: number): boolean {
    this.facing = cardinalOf(dir);
    if (!this.animated || this.dead) return false;
    const key = spriteLibrary.phaseAnim(this.host.scene, this.name, action, dir, columns, frameMs);
    if (!key) return false;
    this.fitAction(action);
    this.host.anims.timeScale = 1;
    this.host.play(key, true);
    this.current = key;
    this.holdUntil = Infinity;
    this.busyUntil = 0;
    return true;
  }

  /**
   * 48라운드: 지정한 열만 1회 재생 (특수 자세의 구간 — 패링 창 f0~2, 성공 f3~4 등). fitMs 를 주면 그 시간에 맞춘다.
   * 반환: 재생 시간 ms (시트가 없으면 0)
   */
  playFrames(action: string, dir: Dir8, columns: number[], time: number, fitMs?: number): number {
    this.facing = cardinalOf(dir);
    if (!this.animated || this.dead || columns.length === 0) return 0;
    const def = spriteLibrary.sheet(this.name, action);
    const base = spriteLibrary.animKey(this.name, action, dir);
    const texture = spriteLibrary.textureKey(this.name, action);
    if (!def || !base || !texture) return 0;
    const cols = columns.filter((c) => c >= 0 && c < def.frames);
    if (cols.length === 0) return 0;
    this.fit(def);
    const key = `${base}#s${cols.join('-')}`;
    const d = frameDurations(def);
    if (!this.host.scene.anims.exists(key)) {
      this.host.scene.anims.create({
        key,
        frames: cols.map((c) => ({ key: texture, frame: frameAt(def, dir, c), duration: d[c] })),
        frameRate: def.fps,
        repeat: 0,
      });
    }
    const natural = cols.reduce((a, c) => a + d[c], 0);
    const scale = fitMs && fitMs > 0 ? natural / fitMs : 1;
    this.holdUntil = -1;
    this.host.anims.timeScale = scale;
    this.host.play(key, false);
    this.current = key;
    const ms = natural / scale;
    this.busyUntil = time + ms;
    // 56라운드 Q39 버그: 구간 재생도 '마지막 재생'의 프레임 시각을 남긴다 (열 번호 → 시작 ms, 재생하지 않은 열은 비움).
    // 예전에는 직전 oneShot 의 시각이 남아 활 조준 사격의 발사 지연이 그 값(260ms)을 재사용했다
    const starts: number[] = [];
    let acc = 0;
    for (const c of cols) {
      if (starts[c] === undefined) starts[c] = acc / scale;
      acc += d[c];
    }
    this.lastFrameStarts = starts;
    this.lastDurationMs = ms;
    this.lastImpactMs = 0;
    return ms;
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

  /**
   * 일회성 동작의 발사 프레임 시작 ms (적중·발사 타이밍). 53라운드 적 v3: JSON `fireFrame` 이 있으면 그 프레임 시작
   * (구 프레임을 나눠 그린 v3 — 구 시트 2번째 프레임과 같은 시각), 없으면 첫 프레임 길이. 시트가 없으면 0
   */
  impactDelayMs(action: string): number {
    if (!this.animated) return 0;
    const def = spriteLibrary.sheet(this.name, action);
    if (!def || def.frames < 2) return 0;
    return fireDelayMs(def);
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
      .setOrigin(def.pivot.x / def.frameWidth, def.pivot.y / def.frameHeight)
      .setScale(artScale(def))
      .setDepth(entityDepth(this.host.y));
    corpse.play(key);
    this.corpse = corpse;
    corpse.once(Phaser.GameObjects.Events.DESTROY, () => {
      if (this.corpse === corpse) this.corpse = null;
    });
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
