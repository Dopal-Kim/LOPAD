/**
 * 조준 궤적 점선 (35라운드 3단계, 계약 §3.2 `aim_line` 8×2, `tile: true`, 피벗 (0,1) = 선 시작).
 * 43라운드 B: 2프레임 상태 시트 — JSON `stateFrames {charging: 0, complete: 1}` 로 차지 중/완료 프레임을 고른다(없으면 f0 만).
 * TileSprite 폭 = 사거리, 회전 = 조준 각도, 바닥 깊이. 시트가 없으면 Graphics 점선(4 on / 4 off) 플레이스홀더.
 * 51·52라운드 계약 art §10: 갈래 조준선(`aim_line_snipe`)은 진행도 구동(progressDriven) — frame = min(4, floor(progress×5)), 완료 = 5.
 */
import Phaser from 'phaser';
import { COLORS, DEPTH, ENEMY_FX } from '../core/Constants';
import { spriteLibrary } from './sprites';
import { aimLineFrame } from './branchFx';
import { FX_ACTION } from './spriteDefs';

const BASE_ID = 'aim_line';

export type AimLineState = 'charging' | 'complete';

export class AimLine {
  private obj: Phaser.GameObjects.TileSprite | Phaser.GameObjects.Graphics | null = null;
  private lengthPx = 0;
  /** 시트 사용 여부 (디버그) */
  sheet = false;
  /** 현재 상태 (디버그) */
  state: AimLineState = 'charging';
  /** 지금 그리는 시트 id (디버그) · 열 */
  id = BASE_ID;
  frame = 0;

  constructor(private readonly scene: Phaser.Scene) {}

  get visible(): boolean {
    return this.obj !== null;
  }

  /**
   * 매 프레임: 시작점·각도·길이·차지 진행도(0..1, 1 = 완료). `sheetId` = 갈래 조준선 (시트가 없으면 기본 aim_line)
   */
  show(x: number, y: number, angle: number, lengthPx: number, progress = 0, sheetId = BASE_ID): void {
    const len = Math.max(1, Math.round(lengthPx));
    const id = sheetId !== BASE_ID && this.loaded(sheetId) ? sheetId : BASE_ID;
    if (this.obj && id !== this.id) this.hide();
    this.id = id;
    if (!this.obj) this.obj = this.make(x, y, len);
    this.state = progress >= 1 ? 'complete' : 'charging';
    this.applyFrame(progress);
    this.obj.setPosition(Math.round(x), Math.round(y)).setRotation(angle);
    if (len !== this.lengthPx) {
      this.lengthPx = len;
      if (this.obj instanceof Phaser.GameObjects.TileSprite) this.obj.setSize(len, this.obj.height);
      else this.redraw(this.obj);
    }
  }

  hide(): void {
    this.obj?.destroy();
    this.obj = null;
    this.lengthPx = 0;
    this.state = 'charging';
    this.frame = 0;
  }

  private loaded(id: string): boolean {
    const t = spriteLibrary.textureKey(id, FX_ACTION);
    return Boolean(t && this.scene.textures.exists(t));
  }

  /** 상태·진행도 프레임 (시트만): 진행도 구동 시트는 progressFrames, 아니면 stateFrames charging/complete (없으면 f0) */
  private applyFrame(progress: number): void {
    const obj = this.obj;
    if (!(obj instanceof Phaser.GameObjects.TileSprite)) return;
    const def = spriteLibrary.sheet(this.id, FX_ACTION);
    if (!def) return;
    const col = def.progressDriven
      ? aimLineFrame(def, progress)
      : aimLineFrame({ stateFrames: def.stateFrames, frames: def.frames }, progress >= 1 ? 1 : 0);
    if (col !== this.frame || obj.frame.name !== String(col)) {
      this.frame = col;
      obj.setFrame(col);
    }
  }

  destroy(): void {
    this.hide();
  }

  private make(x: number, y: number, len: number): Phaser.GameObjects.TileSprite | Phaser.GameObjects.Graphics {
    const def = spriteLibrary.sheet(this.id, FX_ACTION);
    const texture = spriteLibrary.textureKey(this.id, FX_ACTION);
    if (def && texture && this.scene.textures.exists(texture)) {
      this.sheet = true;
      this.lengthPx = len;
      return this.scene.add
        .tileSprite(x, y, len, def.frameHeight, texture, 0)
        .setOrigin(def.pivot.x / def.frameWidth, def.pivot.y / def.frameHeight)
        .setDepth(DEPTH.FX_GROUND);
    }
    this.sheet = false;
    const g = this.scene.add.graphics().setDepth(DEPTH.FX_GROUND);
    this.lengthPx = len;
    this.redraw(g);
    return g;
  }

  private redraw(g: Phaser.GameObjects.Graphics): void {
    g.clear();
    g.lineStyle(1, COLORS.PLAYER_AIM, ENEMY_FX.PLACEHOLDER.ALPHA);
    for (let x = 0; x < this.lengthPx; x += 8) {
      g.beginPath();
      g.moveTo(x, 0);
      g.lineTo(Math.min(this.lengthPx, x + 4), 0);
      g.strokePath();
    }
  }
}
