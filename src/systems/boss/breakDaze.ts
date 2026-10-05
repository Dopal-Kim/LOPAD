/**
 * 61라운드 E 파훼 창 표시 (아트 2 `fx/v3/boss1_break_daze`): 보스가 파훼로 무너져 받는 피해 ×1.5 인 동안 머리 위를 도는 잔·별 고리.
 * 위치 = 이 시트 JSON `headTopAnchors[보스 동작][방향][열]` (보스 시트 도트 — 보스 피벗 기준으로 환산), 없는 동작은 idle 같은 방향 0 열.
 */
import type Phaser from 'phaser';
import { BOSS_ART, DEPTH } from '../../core/Constants';
import type { FxHandle, FxPool } from '../fx/fx';
import { spriteLibrary } from '../sprites/sprites';
import { headTopDot } from './bossArtRules';

export interface DazeBoss {
  sprite: Phaser.GameObjects.Sprite;
  /** 파훼 창 (없으면 null) */
  brokenWindow(now: number): { leftMs: number } | null;
}

export class BreakDaze {
  private handle: FxHandle | null = null;
  private readonly at = { x: 0, y: 0, active: true, depth: DEPTH.HIT_FX, rotation: 0 };
  /** 보스 몸 동작 텍스처 키 → 동작 이름 (headTopAnchors 키) */
  private readonly actions: string[];

  constructor(
    private readonly fx: FxPool,
    private readonly bossId: string,
  ) {
    const def = fx.sheet(BOSS_ART.SHEETS.BREAK_DAZE);
    const t = def?.headTopAnchors;
    this.actions = t && typeof t === 'object' ? Object.keys(t) : [];
  }

  get showing(): boolean {
    return this.fx.isActive(this.handle);
  }

  update(boss: DazeBoss | null, now: number): void {
    const id = BOSS_ART.SHEETS.BREAK_DAZE;
    const on = Boolean(boss?.sprite.active && boss.brokenWindow(now) && this.fx.has(id));
    if (!on || !boss) {
      this.stop();
      return;
    }
    const pos = this.headTop(boss.sprite);
    if (!pos) {
      this.stop();
      return;
    }
    this.at.x = pos.x;
    this.at.y = pos.y - BOSS_ART.DAZE_LIFT_PX;
    if (!this.fx.isActive(this.handle))
      this.handle = this.fx.play(id, this.at.x, this.at.y, { follow: this.at, depth: DEPTH.HIT_FX, hooks: false });
  }

  /** 보스 스프라이트의 지금 프레임 머리 꼭대기 (월드) */
  private headTop(s: Phaser.GameObjects.Sprite): { x: number; y: number } | null {
    const table = this.fx.sheet(BOSS_ART.SHEETS.BREAK_DAZE)?.headTopAnchors;
    const key = s.texture.key;
    const action = this.actions.find((a) => spriteLibrary.textureKey(this.bossId, a) === key) ?? 'idle';
    const def = spriteLibrary.sheet(this.bossId, action) ?? spriteLibrary.sheet(this.bossId, 'idle');
    if (!def) return null;
    const idx = Number(s.frame.name);
    const col = Number.isFinite(idx) && key === spriteLibrary.textureKey(this.bossId, action) ? idx % def.frames : 0;
    const row = Number.isFinite(idx) ? Math.floor(idx / def.frames) : 0;
    const dir = def.directions[row] ?? 'down';
    const dot = headTopDot(table, action, dir, col);
    if (!dot) return null;
    return { x: s.x + (dot[0] - def.pivot.x) * s.scaleX, y: s.y + (dot[1] - def.pivot.y) * s.scaleY };
  }

  stop(): void {
    if (this.handle) this.fx.stop(this.handle, 0, false);
    this.handle = null;
  }

  destroy(): void {
    this.stop();
  }
}
