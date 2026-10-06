/**
 * 보스방 기둥 (BossArena 에서 분리 — 61라운드 E 6-1 정리) + 61 E 균열 단계 (아트 2 `structures/v3/boss1_pillar` stages 표).
 * 그림 우선순위: 구조물 시트(arena.pillarSprite) → 지역 소품 시트(QuarterView 가 그림) → 임시 기둥(몸·윗면).
 * 균열: 보스 돌진이 그 기둥에 부딪힐 때마다 단 +1 → `crack<n>`(충격 → 먼지 → 정지) 1회 후 stateHold 프레임 유지.
 * 61 단계 5 (P13 §3): 3단 다음 충돌에서 **무너진다** — 시트에 `collapse`·`rubble` 이 있으면 무너짐 1회 → 잔해 유지,
 * 없으면 crack3 그림을 보스 반대쪽으로 기울이며 사라지게 하고 낮은 돌무더기를 그린다. 무너짐이 끝나면 칸을 연다
 * (걷기·투사체 통과 — 잔해는 바닥 높이 그림일 뿐). 시트 무너짐은 23 프레임(solidOffFrame)에 땅에 부딪혀 그때 연다. 서 있는 기둥 발자국은 가려짐 판정·보스 우회 조향이 쓴다(`standing`).
 */
import Phaser from 'phaser';
import { BOSS_ART, BOSS_FX, DEPTH, TILE, entityDepth } from '../../core/Constants';
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
import { hashSeed, Rng } from '../rng';
import { nextCrack } from './bossArtRules';
import type { Box } from './pillarGeom';

/** 로드된 기둥 구조물 시트 이름 (없으면 null) */
export function pillarSheet(A: Pick<BossArenaParams, 'pillarSprite'>): string | null {
  return A.pillarSprite?.find((s) => spriteLibrary.has(s, STRUCTURE_ACTION)) ?? null;
}

type PillarView = Phaser.GameObjects.Sprite | Phaser.GameObjects.Graphics;

interface Pillar {
  /** 칸 사각형 (타일) */
  rect: { x: number; y: number; w: number; h: number };
  /** 그림 (지역 소품 시트가 그리는 기둥이면 null — 칸·단계만 관리) */
  view: PillarView | null;
  stage: number;
  /** 'standing' → 'collapsing'(무너지는 중, 아직 칸 막힘) → 'rubble'(칸 열림) */
  state: 'standing' | 'collapsing' | 'rubble';
  /** 재생 중인 프레임 · 다음 프레임 시각 · 끝나면 머물 프레임 */
  anim: { frames: number[]; i: number; nextAt: number; final: number; loop?: number[] } | null;
  /** 땅에 부딪히는 시각 (칸을 여는 순간) */
  collapseEndAt: number;
  rubble: Phaser.GameObjects.Graphics | null;
}

export class PillarSet {
  private readonly list: Pillar[] = [];
  private readonly sheet: string | null;
  private readonly def: SheetJson | null;
  /** 디버그: 무너진 수 */
  collapsed = 0;

  constructor(
    private readonly scene: Phaser.Scene,
    private readonly world: TileWorld,
    A: BossArenaParams,
    rects: readonly { x: number; y: number; w: number; h: number }[],
    /** 무너진 기둥이 땅에 부딪힘 (칸이 열리는 순간 — 흔들림·소리, 방이 연결) */
    private readonly onCollapse: (index: number, at: { x: number; y: number }) => void = () => {},
  ) {
    this.sheet = pillarSheet(A);
    this.def = this.sheet ? (spriteLibrary.sheet(this.sheet, STRUCTURE_ACTION) ?? null) : null;
    const add = (r: Pillar['rect'], view: PillarView | null) =>
      this.list.push({ rect: r, view, stage: 0, state: 'standing', anim: null, collapseEndAt: 0, rubble: null });
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
        add(r, view);
      }
      return;
    }
    if (world.hasBigPropArt(A.pillarProp)) {
      for (const r of rects) add(r, null);
      return;
    }
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
      add(r, g);
    }
  }

  /** 칸을 막고 있는 기둥 발자국 (월드 px, pad 만큼 부풀림 — 무너지는 중도 땅에 닿기 전까진 단단하다) — 가려짐·우회 조향 */
  standing(padX = 0, padY = padX): Box[] {
    return this.list
      .filter((p) => p.state !== 'rubble')
      .map((p) => ({
        x: p.rect.x * TILE - padX,
        y: p.rect.y * TILE - padY,
        w: p.rect.w * TILE + padX * 2,
        h: p.rect.h * TILE + padY * 2,
      }));
  }

  /** 점(보스 바디 사각형)에 닿는 서 있는 기둥 — 바디가 기둥 칸 사각형에서 reach 안이면 */
  private near(body: { x: number; y: number; w: number; h: number }, reach: number): Pillar | null {
    let best: Pillar | null = null;
    let bd = Infinity;
    for (const p of this.list) {
      if (p.state !== 'standing') continue;
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

  /**
   * 보스 돌진이 벽에 막힘: 그 자리 기둥이면 균열 한 단, 3단 다음이면 무너짐. 반환 = 새 단 (4 = 무너짐) · 기둥이 아니면 null.
   * fromX = 부딪힌 쪽(보스 x) — 임시 무너짐은 그 반대쪽으로 쓰러진다
   */
  crackAt(body: { x: number; y: number; w: number; h: number }): number | null {
    const p = this.near(body, BOSS_ART.PILLAR_HIT_REACH_PX);
    return p ? this.crackIndex(this.list.indexOf(p), body.x + body.w / 2) : null;
  }

  /** i 번째 기둥에 균열 한 단 (디버그 겸용). 무너졌으면 null */
  crackIndex(i: number, fromX?: number): number | null {
    const p = this.list[i];
    if (!p || p.state !== 'standing') return null;
    const next = nextCrack(p.stage, BOSS_ART.PILLAR_MAX_STAGE);
    if (!next) return null;
    p.stage = next.stage;
    if (next.collapse) this.collapse(p, fromX);
    else this.playState(p, next.state, `crack${next.stage}_idle`);
    return p.stage;
  }

  /**
   * 무너짐 시작: 시트 `collapse` → `rubble`(stateHold 프레임 유지), 없으면 crack3 을 보스 반대쪽으로 기울이며 사라짐 + 돌무더기.
   * 땅에 부딪히는 프레임(시트 collapse.solidOffFrame — 23, 없으면 임시 길이의 끝)에 칸을 열고 흔들림·소리(onCollapse)
   */
  private collapse(p: Pillar, fromX?: number): void {
    const now = this.scene.time.now;
    const C = BOSS_ART.PILLAR_COLLAPSE;
    p.state = 'collapsing';
    const def = this.def;
    const view = p.view;
    if (def && view instanceof Phaser.GameObjects.Sprite && def.states?.collapse) {
      const frames = structureStateFrames(def, 'collapse');
      const rubble = def.states?.rubble ? structureStateFrames(def, 'rubble') : [];
      const meta = def as unknown as { stateHold?: Record<string, number>; collapse?: { solidOffFrame?: number } };
      const hold = meta.stateHold?.rubble ?? rubble[rubble.length - 1] ?? frames[frames.length - 1];
      const all = [...frames, ...rubble];
      const d = frameDurations(def);
      view.setFrame(all[0]);
      p.anim = { frames: all, i: 0, nextAt: now + (d[all[0]] ?? 100), final: hold };
      // 충돌을 끄는 프레임까지의 시간 (그 프레임 시작)
      const off = meta.collapse?.solidOffFrame;
      const upTo = off !== undefined && frames.includes(off) ? frames.indexOf(off) : frames.length;
      p.collapseEndAt = now + frames.slice(0, upTo).reduce((a, f) => a + (d[f] ?? 100), 0);
    } else {
      // 임시: 보스 반대쪽으로 기울며 흐려짐 (시트 기둥은 피벗 = 바닥이라 밑동에서 넘어간다)
      p.collapseEndAt = now + C.MS;
      const cx = (p.rect.x + p.rect.w / 2) * TILE;
      if (view instanceof Phaser.GameObjects.Sprite) {
        const side = fromX === undefined ? 1 : fromX <= cx ? 1 : -1;
        p.anim = null;
        this.scene.tweens.add({ targets: view, angle: side * C.TILT_DEG, duration: C.MS, ease: 'Quad.easeIn' });
        this.scene.tweens.add({
          targets: view,
          alpha: 0,
          delay: C.MS * C.FADE_FROM,
          duration: C.MS * (1 - C.FADE_FROM),
        });
      } else if (view) this.scene.tweens.add({ targets: view, alpha: 0, duration: C.MS });
      p.rubble = this.drawRubble(p, this.list.indexOf(p));
    }
  }

  /** 임시 잔해: 발자국 안 낮은 돌무더기 (바닥 소품 높이 — 개체가 위로 지나간다) */
  private drawRubble(p: Pillar, i: number): Phaser.GameObjects.Graphics {
    const R = BOSS_ART.PILLAR_COLLAPSE.RUBBLE;
    const rng = new Rng(hashSeed(`pillar-rubble:${i}:${p.rect.x},${p.rect.y}`));
    const x0 = p.rect.x * TILE;
    const y0 = p.rect.y * TILE;
    const w = p.rect.w * TILE;
    const h = p.rect.h * TILE;
    const g = this.scene.add.graphics().setDepth(DEPTH.PROPS).setAlpha(0);
    for (let k = 0; k < R.STONES; k++) {
      const r = R.MIN_R + rng.next() * (R.MAX_R - R.MIN_R);
      const x = x0 + r + rng.next() * (w - r * 2);
      const y = y0 + h * 0.35 + rng.next() * h * 0.55;
      g.fillStyle(R.EDGE, 1).fillEllipse(x, y + 1, r * 2 + 2, r * 2 * R.SQUASH + 2);
      g.fillStyle(R.BODY, 1).fillEllipse(x, y, r * 2, r * 2 * R.SQUASH);
      g.fillStyle(R.TOP, 1).fillEllipse(x - r * 0.25, y - r * 0.2, r, r * R.SQUASH);
    }
    this.scene.tweens.add({ targets: g, alpha: 1, delay: BOSS_ART.PILLAR_COLLAPSE.MS * 0.4, duration: 160 });
    return g;
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
    const d = this.def ? frameDurations(this.def) : [];
    for (const p of this.list) {
      if (p.state === 'collapsing' && time >= p.collapseEndAt) this.settle(p);
      const a = p.anim;
      if (!a || time < a.nextAt || !(p.view instanceof Phaser.GameObjects.Sprite)) continue;
      a.i++;
      if (a.i >= a.frames.length) {
        // 잔해 루프(stateLoop.rubble)면 이어서 그 프레임을 돈다
        if (a.loop) {
          p.anim = { frames: a.loop, i: 0, nextAt: time + (d[a.loop[0]] ?? 100), final: a.loop[0], loop: a.loop };
          p.view.setFrame(a.loop[0]);
        } else {
          p.view.setFrame(a.final);
          p.anim = null;
        }
      } else {
        p.view.setFrame(a.frames[a.i]);
        a.nextAt = time + (d[a.frames[a.i]] ?? 100);
      }
    }
  }

  /** 땅에 부딪힘: 칸을 연다(걷기·투사체 통과) · 잔해는 액터 아래 높이로(depthHint below_actors) · 흔들림·소리 */
  private settle(p: Pillar): void {
    p.state = 'rubble';
    this.world.openArea(p.rect.x, p.rect.y, p.rect.w, p.rect.h);
    if (p.view instanceof Phaser.GameObjects.Sprite && p.view.alpha > 0) p.view.setDepth(DEPTH.PROPS);
    this.collapsed++;
    this.onCollapse(this.list.indexOf(p), {
      x: (p.rect.x + p.rect.w / 2) * TILE,
      y: (p.rect.y + p.rect.h) * TILE,
    });
  }

  summary(): { stage: number; state: string; box: Box }[] {
    return this.list.map((p) => ({
      stage: p.stage,
      state: p.state,
      box: { x: p.rect.x * TILE, y: p.rect.y * TILE, w: p.rect.w * TILE, h: p.rect.h * TILE },
    }));
  }

  destroy(): void {
    for (const p of this.list) {
      p.view?.destroy();
      p.rubble?.destroy();
    }
    this.list.length = 0;
  }
}
