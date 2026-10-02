/**
 * 구조물 그림 (47라운드, 계약 art-assets §5). 시트가 있으면 상태별 프레임·애니, 없으면 플레이스홀더 도형
 * (데이터 placeholder.color 채움 + 짧은 글자). 층 램프 스왑은 spriteLibrary 의 현재 층 변형(@f<n>)을 그대로 쓴다.
 * 위치 기준 = 발판(footprint) 아래 가운데 (계약 pivot). 시트에 없는 상태는 대체 상태 → idle 첫 프레임.
 */
import Phaser from 'phaser';
import { DEPTH, STRUCTURE_FX, entityDepth } from '../core/Constants';
import { spriteLibrary } from '../systems/sprites';
import { STRUCTURE_ACTION, frameDurations, structureStateFrames, type SheetDef } from '../systems/spriteDefs';

/** 시트에 그 상태가 없을 때 차례로 볼 대체 상태 */
export function stateFallbacks(state: string): string[] {
  const out = [state];
  if (state.endsWith('_top')) out.push(state.slice(0, -4));
  if (state.endsWith('_f2')) out.push(state.slice(0, -3));
  if (state === 'ready') out.push('active');
  if (/^used\d$/.test(state)) out.push('idle');
  if (/^damaged\d/.test(state)) out.push('idle');
  out.push('idle');
  return [...new Set(out)];
}

export interface StructureViewOptions {
  /** 아트 시트 id (crate_f1 …) */
  sheet: string;
  /** 발판 사각형 (px) */
  rect: Phaser.Geom.Rectangle;
  color: string;
  label: string;
  /** 바닥에 깔림 (링·룰렛) */
  floor: boolean;
  /** 시트 정수 배율 */
  scale?: number;
  /** 눈치챌 수 있을 만큼만 (숨은 벽: 금 1px) */
  subtle?: boolean;
}

export class StructureView {
  readonly sprite: Phaser.GameObjects.Sprite | null = null;
  private readonly shape: Phaser.GameObjects.Rectangle | null = null;
  private readonly crack: Phaser.GameObjects.Graphics | null = null;
  private readonly label: Phaser.GameObjects.Text | null = null;
  readonly def: SheetDef | undefined;
  private state = 'idle';
  private pulse: Phaser.Tweens.Tween | null = null;
  private readonly scale: number;

  constructor(
    private readonly scene: Phaser.Scene,
    private readonly opts: StructureViewOptions,
  ) {
    const r = opts.rect;
    this.scale = opts.scale ?? 1;
    const def = spriteLibrary.sheet(opts.sheet, STRUCTURE_ACTION);
    const texture = spriteLibrary.textureKey(opts.sheet, STRUCTURE_ACTION);
    if (def && texture && scene.textures.exists(texture)) {
      this.def = def;
      this.sprite = scene.add
        .sprite(r.centerX, r.bottom, texture, structureStateFrames(def, 'idle')[0])
        .setOrigin(def.pivot.x / def.frameWidth, def.pivot.y / def.frameHeight)
        .setScale(this.scale);
    } else if (opts.subtle) {
      // 숨은 벽: 벽 타일 위 금 간 1px 호박 빛 (40라운드 '문 틈 빛'과 같은 언어)
      const g = scene.add.graphics();
      g.lineStyle(1, STRUCTURE_FX.CRACK_COLOR, 0.9);
      g.beginPath();
      g.moveTo(r.x + r.width * 0.3, r.y + 2);
      g.lineTo(r.x + r.width * 0.45, r.centerY);
      g.lineTo(r.x + r.width * 0.6, r.bottom - 2);
      g.strokePath();
      this.crack = g;
    } else {
      this.shape = scene.add
        .rectangle(r.centerX, r.centerY, r.width, r.height, this.color, this.fillAlpha)
        .setStrokeStyle(STRUCTURE_FX.STROKE_WIDTH, opts.floor ? this.color : STRUCTURE_FX.STROKE_COLOR, 1);
      this.label = scene.add
        .text(r.centerX, r.centerY, opts.label, { font: STRUCTURE_FX.LABEL_FONT, color: STRUCTURE_FX.LABEL_COLOR })
        .setOrigin(0.5);
    }
    this.applyDepth();
  }

  private get color(): number {
    return Phaser.Display.Color.HexStringToColor(this.opts.color).color;
  }

  private get fillAlpha(): number {
    return this.opts.floor ? STRUCTURE_FX.FLOOR_FILL_ALPHA : STRUCTURE_FX.FILL_ALPHA;
  }

  /** 아트 시트가 있는지 */
  get art(): boolean {
    return this.sprite !== null;
  }

  get current(): string {
    return this.state;
  }

  /** 시트에 그 상태(대체 없이)가 있는지 */
  hasState(name: string): boolean {
    return Boolean(this.def?.states?.[name]?.length);
  }

  /** 구조물 윗변 y (안내 표시 위치) */
  get topY(): number {
    if (this.sprite) return this.sprite.y - this.sprite.displayOriginY * this.scale;
    return this.opts.rect.top;
  }

  /** 시트 프레임 좌표(px) → 월드 좌표. 시트가 없으면 null */
  frameToWorld(fx: number, fy: number): { x: number; y: number } | null {
    const d = this.def;
    if (!d || !this.sprite) return null;
    return { x: this.sprite.x + (fx - d.pivot.x) * this.scale, y: this.sprite.y + (fy - d.pivot.y) * this.scale };
  }

  /** 발판 아래 가운데로 옮긴다 (굴러가는 술통) */
  moveTo(cx: number, bottom: number): void {
    const r = this.opts.rect;
    r.x = cx - r.width / 2;
    r.y = bottom - r.height;
    this.sprite?.setPosition(cx, bottom);
    this.shape?.setPosition(cx, r.centerY);
    this.label?.setPosition(cx, r.centerY);
    this.applyDepth();
  }

  /** 회전 (구르는 술통: 그려진 방향 기준). 플레이스홀더는 무시 */
  setRotation(rad: number): void {
    this.sprite?.setRotation(rad);
  }

  /** 특정 프레임에 멈춰 보인다 (룰렛 정지 칸) */
  showFrame(frame: number): void {
    if (!this.sprite || !this.def) return;
    this.sprite.anims.stop();
    this.sprite.setFrame(Math.max(0, Math.min(this.def.frames - 1, frame)));
  }

  setState(state: string): void {
    if (state === this.state && state !== 'hit') return;
    const prev = this.state;
    this.state = state;
    this.pulse?.stop();
    this.pulse = null;
    if (this.sprite && this.def) {
      this.playSheetState(state);
      if (state === 'hit' || state.startsWith('hit_')) {
        // hit 은 1프레임: 짧게 보이고 이전 상태로
        this.scene.time.delayedCall(STRUCTURE_FX.HIT_FLASH_MS, () => {
          if (this.sprite?.active && this.state === state) this.setState(prev.startsWith('hit') ? 'idle' : prev);
        });
      }
      return;
    }
    this.placeholderState(state, prev);
  }

  private placeholderState(state: string, prev: string): void {
    const targets = [this.shape, this.label, this.crack].filter((o): o is NonNullable<typeof o> => o !== null);
    if (state === 'used') {
      for (const t of targets) t.setAlpha(STRUCTURE_FX.USED_ALPHA);
    } else if (state === 'broken') {
      this.debris();
      for (const t of targets) t.setVisible(false);
    } else if (state === 'active' || state === 'ready') {
      for (const t of targets) t.setAlpha(1);
      if (this.shape)
        this.pulse = this.scene.tweens.add({
          targets: this.shape,
          alpha: state === 'ready' ? 0.55 : 0.7,
          duration: state === 'ready' ? 260 : 420,
          yoyo: true,
          repeat: -1,
        });
    } else if (state === 'hit' || state.startsWith('hit_')) {
      this.state = prev;
      if (this.shape) {
        this.shape.setFillStyle(STRUCTURE_FX.HIT_FLASH_COLOR, 1);
        this.scene.time.delayedCall(STRUCTURE_FX.HIT_FLASH_MS, () => {
          if (this.shape?.active) this.shape.setFillStyle(this.color, this.fillAlpha);
        });
      }
      if (this.crack) {
        this.crack.setAlpha(1);
        this.scene.tweens.add({ targets: this.crack, alpha: 0.6, duration: STRUCTURE_FX.HIT_FLASH_MS * 2, yoyo: true });
      }
    } else if (/^damaged\d/.test(state)) {
      // 금이 더 굵게 보인다
      this.crack?.setScale(1, 1).setAlpha(1);
      for (const t of targets) t.setVisible(true);
    } else {
      for (const t of targets) t.setAlpha(/^used\d$/.test(state) ? 0.75 : 1).setVisible(true);
    }
  }

  private playSheetState(state: string): void {
    const sprite = this.sprite!;
    const def = this.def!;
    const name = stateFallbacks(state).find((s) => def.states?.[s]?.length) ?? 'idle';
    const frames = structureStateFrames(def, name);
    const texture = spriteLibrary.textureKey(this.opts.sheet, STRUCTURE_ACTION)!;
    if (state === 'broken' && !def.states?.broken) {
      this.debris();
      sprite.setVisible(false);
      return;
    }
    sprite.setVisible(true).setAlpha(state === 'used' && !def.states?.used ? STRUCTURE_FX.USED_ALPHA : 1);
    if (frames.length <= 1) {
      sprite.anims.stop();
      sprite.setFrame(frames[0]);
      return;
    }
    const loop = def.stateLoop?.[name] ?? (name === 'active' || name === 'ready');
    const key = `${texture}#${name}`;
    if (!this.scene.anims.exists(key)) {
      const all = frameDurations(def);
      this.scene.anims.create({
        key,
        frames: frames.map((f) => ({ key: texture, frame: f, duration: all[f % all.length] })),
        repeat: loop ? -1 : 0,
      });
    }
    sprite.play(key, true);
  }

  /** 파편 몇 점 (부서짐 애니가 없을 때) */
  private debris(): void {
    const r = this.opts.rect;
    for (let i = 0; i < STRUCTURE_FX.DEBRIS_COUNT; i++) {
      const a = (Math.PI * 2 * i) / STRUCTURE_FX.DEBRIS_COUNT + 0.4;
      const dot = this.scene.add.rectangle(r.centerX, r.centerY, 3, 3, this.color, 1).setDepth(DEPTH.FX_GROUND);
      this.scene.tweens.add({
        targets: dot,
        x: r.centerX + Math.cos(a) * STRUCTURE_FX.DEBRIS_DIST_PX,
        y: r.centerY + Math.sin(a) * STRUCTURE_FX.DEBRIS_DIST_PX,
        alpha: 0,
        duration: STRUCTURE_FX.DEBRIS_MS,
        onComplete: () => dot.destroy(),
      });
    }
  }

  private applyDepth(): void {
    const r = this.opts.rect;
    const depth = this.opts.floor || this.def?.depth === 'floor' ? STRUCTURE_FX.FLOOR_DEPTH : entityDepth(r.bottom);
    this.sprite?.setDepth(depth);
    this.shape?.setDepth(depth);
    this.label?.setDepth(depth + DEPTH.OVERLAY_STEP);
    this.crack?.setDepth(DEPTH.PROPS + 0.05);
  }

  destroy(): void {
    this.pulse?.stop();
    this.sprite?.destroy();
    this.shape?.destroy();
    this.label?.destroy();
    this.crack?.destroy();
  }
}
