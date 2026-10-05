/**
 * 54라운드 Q8·Q11 보스방 촛대 (연회장 4개): 상태 lit(서 있음·단단함·광원) → fallen(쓰러짐·통과·불씨) → relit(바닥에서 다시 켬·통과·밝은 광원).
 * 그림 우선순위: 구조물 시트(arena.candle.sprite — 상태 lit·fallen_unlit·relit) → 지역 소품 시트의 서 있는 촛대(propName, 쓰러지면 눕힘)
 * → 임시 그림(받침·불꽃). 쓰러진 촛대는 다시 켤 자리 안내(깜빡이는 고리)가 어둠 위에 보인다.
 */
import Phaser from 'phaser';
import { BOSS_ART, BOSS_FX, DEPTH, QUARTER, RENDER, TILE, entityDepth } from '../../core/Constants';
import type { BossArenaParams } from '../../data/types';
import { lightRegistryOf, type LightSource } from '../lighting/lightRegistry';
import { spriteLibrary } from '../sprites/sprites';
import {
  FX_ACTION,
  STRUCTURE_ACTION,
  artScale,
  frameDurations,
  structureStateFrames,
  type SheetJson,
} from '../sprites/spriteDefs';
import type { TileSkin } from '../../world/tileskin';

/** 61 E: out = 보스 처치 때 꺼짐 (서 있음 · 광원 없음 — 61 단계 4: 아트 unlit_standing, 시트에 없으면 lit 그림을 어둡게) */
export type CandleState = 'lit' | 'fallen' | 'relit' | 'out';

/** 상태 → 시트 상태 이름 (계약 §15) */
const SHEET_STATE: Record<CandleState, string> = {
  lit: 'lit',
  fallen: 'fallen_unlit',
  relit: 'relit',
  out: 'unlit_standing',
};
/** 서 있는 꺼진 그림(unlit_standing)이 없는 시트의 out: lit 그림 + 곱 틴트 */
const OUT_TINT = 0x5a5048;
/** 61 단계 4: 꺼진(out) 촛대를 다시 켤 때 광원 페이드 ms (아트: 켜는 순간은 lit 0 프레임 + 광원 페이드) */
const RELIGHT_FADE_MS = 400;

export interface Candle {
  readonly id: number;
  readonly tx: number;
  readonly ty: number;
  /** 발(바닥) 가운데 */
  readonly x: number;
  readonly y: number;
  state: CandleState;
  readonly rect: Phaser.Geom.Rectangle;
  view: Phaser.GameObjects.Image | Phaser.GameObjects.Sprite | Phaser.GameObjects.Graphics;
  hint: Phaser.GameObjects.Arc;
  /** 61라운드: 다시 켤 수 있는 촛대 반짝임 (어둠 위) — 61 E 아트 `fx/v3/boss1_candle_glint`(촛대와 같은 틀·피벗·flipX), 없으면 네 갈래 별 */
  glint: Phaser.GameObjects.Graphics | Phaser.GameObjects.Sprite;
  body: Phaser.GameObjects.Zone;
  light: LightSource | null;
  /** 시트 전환 애니 (lit→fall→fallen_unlit · fallen→relight→relit): 남은 프레임과 시각 */
  anim: { frames: number[]; ms: number[]; i: number; nextAt: number; final: number } | null;
}

/** 전환 상태 (아트 boss1_candelabra: fall · relight) */
const TRANSITION: Partial<Record<CandleState, string>> = { fallen: 'fall', relit: 'relight' };

/** 상태의 정지 프레임 (JSON stateHold — 없으면 그 상태 첫 프레임) */
function holdFrame(def: SheetJson, state: string): number {
  const hold = (def as { stateHold?: Record<string, number> }).stateHold?.[state];
  return typeof hold === 'number' ? hold : (structureStateFrames(def, state)[0] ?? 0);
}

export class CandleSet {
  readonly list: Candle[] = [];
  private readonly solids: Phaser.Physics.Arcade.StaticGroup;
  private readonly collider: Phaser.Physics.Arcade.Collider;
  private readonly sheet: string | null;

  constructor(
    private readonly scene: Phaser.Scene,
    tiles: readonly { x: number; y: number }[],
    private readonly P: BossArenaParams['candle'],
    player: Phaser.GameObjects.GameObject,
    private readonly propSkin: TileSkin | null,
    /** 전투장 가운데 x (서쪽 촛대 좌우 뒤집기) */
    private readonly centerX: number,
  ) {
    this.sheet = P.sprite.find((s) => spriteLibrary.has(s, STRUCTURE_ACTION)) ?? null;
    this.solids = scene.physics.add.staticGroup();
    this.collider = scene.physics.add.collider(player, this.solids);
    tiles.forEach((t, i) => this.list.push(this.make(i, t.x, t.y)));
  }

  private make(id: number, tx: number, ty: number): Candle {
    const x = (tx + 0.5) * TILE;
    const y = (ty + 1) * TILE;
    const body = this.scene.add.zone(x, (ty + 0.5) * TILE, TILE, TILE);
    this.solids.add(body);
    const hint = this.scene.add
      .circle(x, y - 4, BOSS_FX.CANDLE.HINT_RADIUS)
      .setStrokeStyle(1, BOSS_FX.CANDLE.HINT_COLOR, 1)
      .setDepth(DEPTH.LIGHTMAP + 0.05)
      .setVisible(false);
    const glint = this.makeGlint(x, y);
    const c: Candle = {
      id,
      tx,
      ty,
      x,
      y,
      state: 'lit',
      rect: new Phaser.Geom.Rectangle(tx * TILE - 2, ty * TILE - TILE, TILE + 4, TILE * 2),
      view: this.scene.add.graphics(),
      hint,
      glint,
      body,
      light: null,
      anim: null,
    };
    this.apply(c);
    return c;
  }

  /** 다시 켤 자리 반짝임: 아트 시트가 있으면 촛대 피벗에 같은 flipX 로 반복, 없으면 네 갈래 별 */
  private makeGlint(x: number, y: number): Candle['glint'] {
    const id = BOSS_ART.SHEETS.CANDLE_GLINT;
    const def = spriteLibrary.sheet(id, FX_ACTION);
    const tex = spriteLibrary.textureKey(id, FX_ACTION);
    const anim = spriteLibrary.animKey(id, FX_ACTION, 'down');
    if (def && tex && anim) {
      const spr = this.scene.add
        .sprite(x, y, tex, 0)
        .setOrigin(def.pivot.x / def.frameWidth, def.pivot.y / def.frameHeight)
        .setScale(artScale(def))
        .setFlipX(x < this.centerX)
        .setDepth(DEPTH.LIGHTMAP + 0.05)
        .setVisible(false);
      spr.play(anim);
      return spr;
    }
    const G = BOSS_FX.CANDLE.GLINT;
    const g = this.scene.add
      .graphics()
      .setPosition(x, y - G.LIFT_PX)
      .setDepth(DEPTH.LIGHTMAP + 0.05)
      .setVisible(false);
    drawGlint(g, G.SIZE, G.COLOR);
    return g;
  }

  /** 상태 바꾸기 (그림·충돌·광원) */
  set(c: Candle, state: CandleState): void {
    if (c.state === state) return;
    const prev = c.state;
    c.state = state;
    this.apply(c, prev);
  }

  private apply(c: Candle, prev?: CandleState): void {
    const standing = c.state === 'lit' || c.state === 'out';
    (c.body.body as Phaser.Physics.Arcade.StaticBody).enable = standing;
    c.view.destroy();
    c.view = this.draw(c, prev);
    c.hint.setVisible(c.state === 'fallen');
    c.glint.setVisible(c.state === 'fallen');
    const reg = lightRegistryOf(this.scene);
    reg.remove(c.light);
    const L =
      c.state === 'lit'
        ? this.P.light
        : c.state === 'relit'
          ? this.P.relitLight
          : c.state === 'fallen'
            ? this.P.emberLight
            : null;
    c.light = L ? reg.add(L, { x: c.x, y: c.y }) : null;
    // 61 단계 4: 꺼진 촛대를 다시 켜면 광원이 서서히
    if (c.light && prev === 'out') {
      const full = c.light.intensity;
      c.light.intensity = 0;
      this.scene.tweens.add({ targets: c.light, intensity: full, duration: RELIGHT_FADE_MS });
    }
  }

  private draw(c: Candle, prev?: CandleState): Candle['view'] {
    const sc = this.scene;
    const depth = entityDepth(c.y);
    // 1) 구조물 시트 (상태 프레임, 전환 상태가 있으면 그 프레임을 먼저). 아트: 서쪽 촛대는 좌우 뒤집기
    if (this.sheet) {
      const def = spriteLibrary.sheet(this.sheet, STRUCTURE_ACTION)!;
      const tex = spriteLibrary.textureKey(this.sheet, STRUCTURE_ACTION)!;
      // 61 단계 4: 서 있는 꺼진 그림(unlit_standing 10~13: 잔불·연기 → 13 유지)이 있으면 그것, 없으면 lit + 틴트
      const unlit = c.state === 'out' && Boolean(def.states?.[SHEET_STATE.out]);
      const sheetState = c.state === 'out' && !unlit ? 'lit' : SHEET_STATE[c.state];
      const final = holdFrame(def, sheetState);
      const tr = unlit ? SHEET_STATE.out : TRANSITION[c.state];
      const trFrames = tr && prev && def.states?.[tr] ? structureStateFrames(def, tr) : [];
      const durs = frameDurations(def);
      c.anim =
        trFrames.length > 0
          ? {
              frames: trFrames,
              ms: trFrames.map((f) => durs[f] ?? 100),
              i: 0,
              nextAt: sc.time.now + (durs[trFrames[0]] ?? 100),
              final,
            }
          : null;
      const spr = sc.add
        .sprite(c.x, c.y, tex, c.anim ? trFrames[0] : final)
        .setOrigin(def.pivot.x / def.frameWidth, def.pivot.y / def.frameHeight)
        .setScale(artScale(def))
        .setFlipX(c.x < this.centerX)
        .setDepth(depth);
      if (c.state === 'out' && !unlit) spr.setTint(OUT_TINT);
      return spr;
    }
    // 2) 지역 소품 시트의 서 있는 촛대 (쓰러지면 눕힌다)
    const prop = this.propSkin?.bigProps.find((b) => b.name === this.P.propName);
    if (this.propSkin && prop) {
      const key = this.propSkin.textureKey;
      const frame = `big:${prop.name}`;
      const tex = sc.textures.get(key);
      if (!tex.has(frame)) tex.add(frame, 0, prop.rect.x, prop.rect.y, prop.rect.w, prop.rect.h);
      const img = sc.add
        .image(c.x, c.y - QUARTER.V3_PIVOT_LIFT_LOGICAL / RENDER.WORLD_TO_SCREEN, key, frame)
        .setOrigin(prop.pivot.x / prop.rect.w, prop.pivot.y / prop.rect.h)
        .setScale(this.propSkin.worldScale)
        .setDepth(depth);
      if (c.state === 'out') img.setTint(OUT_TINT);
      else if (c.state !== 'lit') img.setRotation(Math.PI / 2).setTint(BOSS_FX.CANDLE.FALLEN);
      return img;
    }
    // 3) 임시 그림
    const K = BOSS_FX.CANDLE;
    const g = sc.add.graphics().setDepth(depth);
    if (c.state === 'lit' || c.state === 'out') {
      g.fillStyle(K.STAND, 1).fillRect(c.x - K.W / 2, c.y - K.H, K.W, K.H);
      if (c.state === 'lit') g.fillStyle(K.FLAME, 1).fillCircle(c.x, c.y - K.H - K.FLAME_R, K.FLAME_R);
    } else {
      g.fillStyle(K.FALLEN, 1).fillRect(c.x - K.H / 2, c.y - K.W, K.H, K.W);
      if (c.state === 'relit') g.fillStyle(K.FLAME, 1).fillCircle(c.x + K.H / 2, c.y - K.W - K.FLAME_R, K.FLAME_R);
    }
    return g;
  }

  /** 쓰러진 촛대 안내 깜빡임 */
  update(time: number): void {
    const on = Math.floor(time / BOSS_FX.CANDLE.HINT_MS) % 2 === 0;
    const G = BOSS_FX.CANDLE.GLINT;
    for (const c of this.list) {
      if (c.state === 'fallen') {
        c.hint.setAlpha(on ? 1 : 0.35);
        // 반짝임: 촛대마다 어긋난 위상으로 커졌다 작아진다 (0..1..0)
        const t = (((time + c.id * G.STAGGER_MS) % G.PERIOD_MS) + G.PERIOD_MS) % G.PERIOD_MS;
        const k = Math.sin((t / G.PERIOD_MS) * Math.PI);
        if (c.glint instanceof Phaser.GameObjects.Graphics)
          c.glint.setScale(G.MIN_SCALE + (1 - G.MIN_SCALE) * k).setAlpha(0.35 + 0.65 * k);
      }
      const a = c.anim;
      if (!a || time < a.nextAt || !(c.view instanceof Phaser.GameObjects.Sprite)) continue;
      a.i++;
      if (a.i >= a.frames.length) {
        c.view.setFrame(a.final);
        c.anim = null;
      } else {
        c.view.setFrame(a.frames[a.i]);
        a.nextAt = time + a.ms[a.i];
      }
    }
  }

  /** 61 E 처치 때 불 끄기: 불꽃 자리 (광원 위치 — 없으면 촛대 발 위) */
  flamePoint(c: Candle): { x: number; y: number } {
    const def = this.sheet ? spriteLibrary.sheet(this.sheet, STRUCTURE_ACTION) : undefined;
    const off = (def?.light as { offset?: { x: number; y: number } } | undefined)?.offset;
    if (!def || !off) return { x: c.x, y: c.y - TILE };
    return this.sheetPoint(c, def, off);
  }

  /**
   * 61 단계 4: 서 있는 촛대 초 심지들 (아트 wickAnchors.standing — 끌 때 boss1_flame_snuff 자리). 없으면 불꽃 자리 하나
   */
  wickPoints(c: Candle): { x: number; y: number }[] {
    const def = this.sheet ? spriteLibrary.sheet(this.sheet, STRUCTURE_ACTION) : undefined;
    const wicks = (def as { wickAnchors?: { standing?: { x: number; y: number }[] } } | undefined)?.wickAnchors
      ?.standing;
    if (!def || !wicks || wicks.length === 0) return [this.flamePoint(c)];
    return wicks.map((w) => this.sheetPoint(c, def, w));
  }

  /** 시트 도트 좌표 → 월드 (flipX 는 틀 안에서 뒤집힌다 — 도트 x → 틀 폭 − x) */
  private sheetPoint(c: Candle, def: SheetJson, p: { x: number; y: number }): { x: number; y: number } {
    const k = artScale(def);
    const dx = c.x < this.centerX ? def.frameWidth - p.x : p.x;
    return { x: c.x + (dx - def.pivot.x) * k, y: c.y + (p.y - def.pivot.y) * k };
  }

  /** 점에서 가장 가까운 쓰러진 촛대 (rangePx 안) */
  nearestFallen(x: number, y: number, rangePx: number): Candle | null {
    let best: Candle | null = null;
    let bd = rangePx;
    for (const c of this.list) {
      if (c.state !== 'fallen') continue;
      const d = Math.hypot(c.x - x, c.y - TILE / 2 - y);
      if (d <= bd) {
        bd = d;
        best = c;
      }
    }
    return best;
  }

  destroy(): void {
    this.scene.physics.world?.removeCollider(this.collider);
    const reg = lightRegistryOf(this.scene);
    for (const c of this.list) {
      reg.remove(c.light);
      c.view.destroy();
      c.hint.destroy();
      c.glint.destroy();
      c.body.destroy();
    }
    this.solids.destroy(true);
    this.list.length = 0;
  }
}

/** 네 갈래 별 (가운데 원점, 반지름 r) */
function drawGlint(g: Phaser.GameObjects.Graphics, r: number, color: number): void {
  const w = Math.max(1, r * 0.28);
  g.fillStyle(color, 1);
  g.fillTriangle(0, -r, -w, 0, w, 0);
  g.fillTriangle(0, r, -w, 0, w, 0);
  g.fillTriangle(-r, 0, 0, -w, 0, w);
  g.fillTriangle(r, 0, 0, -w, 0, w);
  g.fillCircle(0, 0, w);
}
