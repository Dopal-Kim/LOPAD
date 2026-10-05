/**
 * 보스방 기둥 (BossArena 에서 분리 — 61라운드 E 6-1 정리) + 61 E 균열 단계 (아트 2 `structures/v3/boss1_pillar` stages 표).
 * 그림 우선순위: 구조물 시트(arena.pillarSprite) → 지역 소품 시트(QuarterView 가 그림) → 임시 기둥(몸·윗면).
 * 균열: 보스 돌진이 그 기둥에 부딪힐 때마다 단 +1 → `crack<n>`(충격 → 먼지 → 정지) 1회 후 stateHold 프레임 유지.
 * 최대 단(3) 뒤로는 무너뜨리지 않고 3단을 유지한다 — 다시 부딪히면 `crack3_hit` 후 3단 정지 그림 (무너짐 그림 없음, 싸움 중 엄폐가 사라지지 않게).
 */
import Phaser from 'phaser';
import { BOSS_ART, BOSS_FX, TILE, entityDepth } from '../../core/Constants';
import type { BossArenaParams } from '../../data/types';
import { spriteLibrary } from '../sprites/sprites';
import {
  STRUCTURE_ACTION,
  artScale,
  frameDurations,
  structureStateFrames,
  type SheetJson,
} from '../sprites/spriteDefs';
import type { TileWorld } from '../../world/TileWorld';
import { nextCrack } from './bossArtRules';

/** 로드된 기둥 구조물 시트 이름 (없으면 null) */
export function pillarSheet(A: Pick<BossArenaParams, 'pillarSprite'>): string | null {
  return A.pillarSprite?.find((s) => spriteLibrary.has(s, STRUCTURE_ACTION)) ?? null;
}

interface Pillar {
  rect: { x: number; y: number; w: number; h: number };
  view: Phaser.GameObjects.Sprite | Phaser.GameObjects.Graphics;
  stage: number;
  /** 재생 중인 프레임 · 다음 프레임 시각 · 끝나면 머물 프레임 */
  anim: { frames: number[]; i: number; nextAt: number; final: number } | null;
}

export class PillarSet {
  private readonly list: Pillar[] = [];
  private readonly sheet: string | null;
  private readonly def: SheetJson | null;

  constructor(
    private readonly scene: Phaser.Scene,
    world: TileWorld,
    A: BossArenaParams,
    rects: readonly { x: number; y: number; w: number; h: number }[],
  ) {
    this.sheet = pillarSheet(A);
    this.def = this.sheet ? (spriteLibrary.sheet(this.sheet, STRUCTURE_ACTION) ?? null) : null;
    if (this.sheet && this.def) {
      const tex = spriteLibrary.textureKey(this.sheet, STRUCTURE_ACTION)!;
      const def = this.def;
      const frame = structureStateFrames(def, 'idle')[0] ?? 0;
      for (const r of rects) {
        const x = (r.x + r.w / 2) * TILE;
        const bottom = (r.y + r.h) * TILE;
        const view = scene.add
          .sprite(x, bottom, tex, frame)
          .setOrigin(def.pivot.x / def.frameWidth, def.pivot.y / def.frameHeight)
          .setScale(artScale(def))
          .setDepth(entityDepth(bottom));
        this.list.push({ rect: r, view, stage: 0, anim: null });
      }
      return;
    }
    if (world.hasBigPropArt(A.pillarProp)) return;
    const P = BOSS_FX.PILLAR;
    for (const r of rects) {
      const x = r.x * TILE;
      const bottom = (r.y + r.h) * TILE;
      const w = r.w * TILE;
      const top = bottom - P.HEIGHT_PX;
      const g = scene.add.graphics().setDepth(entityDepth(bottom));
      g.fillStyle(P.BODY, 1).fillRect(x, top, w, P.HEIGHT_PX);
      g.fillStyle(P.TOP, 1).fillRect(x, top, w, r.h * TILE * 0.5);
      g.lineStyle(1, P.EDGE, 1).strokeRect(x, top, w, P.HEIGHT_PX);
      this.list.push({ rect: r, view: g, stage: 0, anim: null });
    }
  }

  /** 점(보스 바디 사각형)에 닿는 기둥 — 바디가 기둥 칸 사각형에서 reach 안이면 */
  private near(body: { x: number; y: number; w: number; h: number }, reach: number): Pillar | null {
    let best: Pillar | null = null;
    let bd = Infinity;
    for (const p of this.list) {
      const rx = p.rect.x * TILE;
      const ry = p.rect.y * TILE;
      const rw = p.rect.w * TILE;
      const rh = p.rect.h * TILE;
      const dx = Math.max(rx - (body.x + body.w), 0, body.x - (rx + rw));
      const dy = Math.max(ry - (body.y + body.h), 0, body.y - (ry + rh));
      const d = Math.hypot(dx, dy);
      if (d <= reach && d < bd) {
        bd = d;
        best = p;
      }
    }
    return best;
  }

  /** 보스 돌진이 벽에 막힘: 그 자리 기둥이면 균열 한 단. 반환 = 새 단 (기둥이 아니면 null) */
  crackAt(body: { x: number; y: number; w: number; h: number }): number | null {
    const p = this.near(body, BOSS_ART.PILLAR_HIT_REACH_PX);
    return p ? this.crackIndex(this.list.indexOf(p)) : null;
  }

  /** 디버그: i 번째 기둥에 균열 한 단 */
  crackIndex(i: number): number | null {
    const p = this.list[i];
    if (!p) return null;
    const next = nextCrack(p.stage, BOSS_ART.PILLAR_MAX_STAGE);
    p.stage = next.stage;
    this.playState(p, next.state, `crack${next.stage}_idle`);
    return p.stage;
  }

  private playState(p: Pillar, state: string, rest: string): void {
    const def = this.def;
    if (!def || !(p.view instanceof Phaser.GameObjects.Sprite) || !def.states?.[state]) return;
    const frames = structureStateFrames(def, state);
    if (frames.length === 0) return;
    // 정지 그림 = `crack<n>_idle` (JSON stateHold 와 같은 프레임)
    const final = (def.states?.[rest] ? structureStateFrames(def, rest)[0] : undefined) ?? frames[frames.length - 1];
    const d = frameDurations(def);
    p.view.setFrame(frames[0]);
    p.anim = { frames, i: 0, nextAt: this.scene.time.now + (d[frames[0]] ?? 100), final };
  }

  update(time: number): void {
    if (!this.def) return;
    const d = frameDurations(this.def);
    for (const p of this.list) {
      const a = p.anim;
      if (!a || time < a.nextAt || !(p.view instanceof Phaser.GameObjects.Sprite)) continue;
      a.i++;
      if (a.i >= a.frames.length) {
        p.view.setFrame(a.final);
        p.anim = null;
      } else {
        p.view.setFrame(a.frames[a.i]);
        a.nextAt = time + (d[a.frames[a.i]] ?? 100);
      }
    }
  }

  summary(): { stage: number }[] {
    return this.list.map((p) => ({ stage: p.stage }));
  }

  destroy(): void {
    for (const p of this.list) p.view.destroy();
    this.list.length = 0;
  }
}
