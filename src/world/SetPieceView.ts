/**
 * 49라운드 7·3: 세트 배치 그림 — 소품(structures/set_<region>_<name>·battlefield_*), 엄폐 담 위 술통 더미,
 * 튜토리얼 표식·허수아비, 혼불(fx/soul_wisp). 시트가 로드돼 있으면 시트(StructureView 재사용), 없으면 옅은 플레이스홀더 도형.
 * 충돌은 없다(엄폐는 이미 벽 타일). 씬 shutdown 에서 `destroy()`.
 */
import Phaser from 'phaser';
import { STRUCTURE_FX, TILE, entityDepth } from '../core/Constants';
import { ROUTE, type SetPieceViewDef } from '../systems/route';
import { spriteLibrary } from '../systems/sprites/sprites';
import { FX_ACTION, STRUCTURE_ACTION, artScale } from '../systems/sprites/spriteDefs';
import { lightFor, lightRegistryOf } from '../systems/lighting/lightRegistry';
import type { DecorPlacement, SetPiecePlan } from '../systems/structures/setpiece';
import { StructureView } from './StructureView';

type Shape = Phaser.GameObjects.Rectangle | Phaser.GameObjects.Arc | Phaser.GameObjects.Sprite;

interface DecorItem {
  d: DecorPlacement;
  view: StructureView | null;
  shape: Phaser.GameObjects.Rectangle | null;
  /** 그린 시트 이름 (없으면 null) */
  sheet: string | null;
}

/** 61 E 허수아비 v3 (아트 2 `tutorial_dummy`): 맞음 그림이 기울기를 그린다 — 이 상태가 있으면 회전·흰 점멸 대신 상태 재생 */
const DUMMY_HEAVY_STATE = 'hit_heavy';

const hex = (c: string) => Phaser.Display.Color.HexStringToColor(c).color;

/** 시트 후보 중 로드된 첫 시트 (없으면 null) */
export function loadedSheet(candidates: readonly string[]): string | null {
  return candidates.find((s) => spriteLibrary.has(s, STRUCTURE_ACTION)) ?? null;
}

export class SetPieceView {
  private readonly items: DecorItem[] = [];
  private readonly signs: DecorItem[] = [];
  private readonly dummies: DecorItem[] = [];
  private readonly wisps: Shape[] = [];
  private readonly tweens: Phaser.Tweens.Tween[] = [];
  private signPulse: Phaser.Tweens.Tween | null = null;
  /** 허수아비 맞음 → 대기 복귀 예약 (마지막 맞음만) */
  private readonly dummyHitToken = new Map<DecorItem, number>();
  private readonly V: SetPieceViewDef;

  constructor(
    private readonly scene: Phaser.Scene,
    readonly plan: SetPiecePlan,
    view: SetPieceViewDef | undefined = ROUTE.view,
  ) {
    if (!view) throw new Error('[setpiece] data/route.json view 없음');
    this.V = view;
    for (const d of plan.decor) {
      const item = this.makeDecor(d);
      this.items.push(item);
      if (d.role === 'sign') this.signs.push(item);
      if (d.role === 'dummy') this.dummies.push(item);
    }
    plan.wisps.forEach((w, i) => this.makeWisp(w.x * TILE, w.y * TILE, i, plan.wisps.length));
    this.highlightSign(null);
  }

  /** 시트로 그려진 소품 수 / 전체 (디버그) */
  get summary(): { decor: number; art: number; wisps: number; wispArt: boolean } {
    return {
      decor: this.items.length,
      art: this.items.filter((i) => i.view !== null).length,
      wisps: this.wisps.length,
      wispArt: this.wisps.some((w) => w instanceof Phaser.GameObjects.Sprite),
    };
  }

  private makeDecor(d: DecorPlacement): DecorItem {
    const rect = new Phaser.Geom.Rectangle(d.tx * TILE, d.ty * TILE, d.w * TILE, d.h * TILE);
    const sheet = loadedSheet(d.sprites);
    if (sheet) {
      const view = new StructureView(this.scene, { sheet, rect, color: d.color, label: '', floor: d.floor });
      if (view.hasState('active')) view.setState('active');
      return { d, view, shape: null, sheet };
    }
    const V = this.V;
    const alpha =
      d.role === 'sign' ? V.signAlpha : d.floor ? V.floorDecorAlpha : d.role === 'cover' ? V.coverAlpha : V.decorAlpha;
    // 허수아비: 발판보다 키가 큰 기둥 / 표식: 작은 마름모 / 그 외: 발판 사각형
    let shape: Phaser.GameObjects.Rectangle;
    if (d.role === 'dummy') {
      shape = this.scene.add
        .rectangle(rect.centerX, rect.bottom, rect.width * 0.5, rect.height * 1.5, hex(d.color), alpha)
        .setOrigin(0.5, 1);
    } else if (d.role === 'sign') {
      shape = this.scene.add
        .rectangle(rect.centerX, rect.centerY, rect.width * 0.6, rect.height * 0.6, hex(V.signColor), alpha)
        .setAngle(45);
    } else {
      shape = this.scene.add.rectangle(rect.centerX, rect.centerY, rect.width, rect.height, hex(d.color), alpha);
    }
    shape.setDepth(d.floor || d.role === 'sign' ? STRUCTURE_FX.FLOOR_DEPTH : entityDepth(rect.bottom));
    return { d, view: null, shape, sheet: null };
  }

  private makeWisp(x: number, y: number, i: number, n: number): void {
    const w = spawnWisp(this.scene, this.V, x, y, i, n);
    this.wisps.push(w.obj);
    this.tweens.push(w.tween);
  }

  /** 지금 단계 표식만 밝게 깜빡인다 (null = 전부 옅게) */
  highlightSign(index: number | null): void {
    const V = this.V;
    this.signPulse?.stop();
    this.signPulse = null;
    this.signs.forEach((s, i) => {
      const on = i === index;
      if (s.view) s.view.setState(on && s.view.hasState('active') ? 'active' : 'idle');
      const target = s.view?.sprite ?? s.shape;
      if (!target) return;
      target.setAlpha(on ? V.signActiveAlpha : V.signAlpha);
      if (on)
        this.signPulse = this.scene.tweens.add({
          targets: target,
          alpha: V.signAlpha,
          duration: V.signPulseMs,
          yoyo: true,
          repeat: -1,
        });
    });
  }

  /**
   * 허수아비 맞음: 흔들림(dirX 쪽으로 넘어갔다 돌아옴 — strength 배, 대검 ≈ 2) · 61라운드 플레이 점검: 흰 점멸 flashMs.
   * dirX 가 0 이면 옛 방향(왼쪽)
   */
  pokeDummy(index: number, strength = 1, dirX = 0, flashMs = 0, heavy = false): void {
    const s = this.dummies[index];
    if (!s) return;
    if (s.view?.hasState(DUMMY_HEAVY_STATE)) {
      this.playDummyHit(s, s.view, heavy, dirX);
      return;
    }
    if (s.view?.hasState('hit')) s.view.setState('hit');
    const target = s.view?.sprite ?? s.shape;
    if (!target) return;
    const side = dirX > 0 ? 1 : -1;
    this.scene.tweens.add({
      targets: target,
      angle: { from: side * this.V.dummyPokeDeg * strength, to: 0 },
      duration: this.V.dummyPokeMs * Math.max(1, strength),
      ease: 'Back.easeOut',
    });
    if (flashMs > 0 && 'setTintFill' in target) {
      const t = target as Phaser.GameObjects.Sprite;
      t.setTintFill(0xffffff);
      this.scene.time.delayedCall(flashMs, () => {
        if (t.active) t.clearTint();
      });
    }
  }

  /**
   * 61 E 허수아비 v3: 맞음(hit) · 막타·강공(hit_heavy) 1회 → 대기. 그림은 왼쪽에서 맞아 오른쪽으로 밀리는 기준 — 오른쪽에서 맞으면 flipX.
   * 첫 칸이 하얗게 번쩍이는 그림이라(flashFrames) 흰 점멸·회전을 따로 하지 않는다
   */
  private playDummyHit(s: DecorItem, view: StructureView, heavy: boolean, dirX: number): void {
    const state = heavy ? DUMMY_HEAVY_STATE : 'hit';
    view.setState(state);
    view.sprite?.setFlipX(dirX < 0);
    const def = s.sheet ? spriteLibrary.sheet(s.sheet, STRUCTURE_ACTION) : undefined;
    const frames = def?.states?.[state] ?? [];
    const ms = frames.reduce((a, f) => a + (def?.frameDurationsMs?.[f] ?? 100), 0);
    const token = (this.dummyHitToken.get(s) ?? 0) + 1;
    this.dummyHitToken.set(s, token);
    this.scene.time.delayedCall(ms, () => {
      if (this.dummyHitToken.get(s) === token && view.sprite?.active) view.setState('idle');
    });
  }

  /** 허수아비 중심 (월드 px — 맞음 불꽃 자리: 시트 anchors.hitCenter, 없으면 그림 가운데). 없으면 null */
  dummyCenter(index: number): { x: number; y: number } | null {
    const s = this.dummies[index];
    const t = s?.view?.sprite ?? s?.shape;
    if (!t) return null;
    const def = s.sheet ? spriteLibrary.sheet(s.sheet, STRUCTURE_ACTION) : undefined;
    const hc = (def?.anchors as { hitCenter?: { x: number; y: number } } | undefined)?.hitCenter;
    if (def && hc && t instanceof Phaser.GameObjects.Sprite) {
      const k = artScale(def);
      const dx = t.flipX ? def.frameWidth - hc.x : hc.x;
      return { x: t.x + (dx - def.pivot.x) * k, y: t.y + (hc.y - def.pivot.y) * k };
    }
    const b = t.getBounds();
    return { x: b.centerX, y: b.centerY };
  }

  destroy(): void {
    this.signPulse?.stop();
    for (const t of this.tweens) t.stop();
    for (const i of this.items) {
      i.view?.destroy();
      i.shape?.destroy();
    }
    for (const w of this.wisps) w.destroy();
    this.items.length = 0;
    this.wisps.length = 0;
  }
}

/**
 * 혼불 하나 (fx/soul_wisp 시트, 없으면 옅은 원) + 은은한 빛(시트 JSON light → fallback soul_wisp) + 위아래 일렁임.
 * 세트 배치(탄생 전장)와 53라운드 황무지 둑 위 혼불(BorderView)이 같이 쓴다. depth 를 주면 그 깊이, 아니면 Y 정렬
 */
export function spawnWisp(
  scene: Phaser.Scene,
  V: SetPieceViewDef,
  x: number,
  y: number,
  i: number,
  n: number,
  depth?: number,
): { obj: Shape; tween: Phaser.Tweens.Tween } {
  const t = n > 1 ? i / (n - 1) : 0;
  const cycle = V.wispCycleMs[0] + (V.wispCycleMs[1] - V.wispCycleMs[0]) * t;
  const texture = spriteLibrary.textureKey(V.wispSheet, FX_ACTION);
  const anim = spriteLibrary.animKey(V.wispSheet, FX_ACTION, 'down');
  let obj: Shape;
  const def = spriteLibrary.sheet(V.wispSheet, FX_ACTION);
  if (texture && anim) {
    const s = scene.add.sprite(x, y, texture, 0).setScale(def ? artScale(def) : 1);
    s.play({ key: anim, repeat: -1, startFrame: i });
    obj = s;
  } else {
    obj = scene.add.circle(x, y, V.wispRadiusPx, hex(V.wispColor), V.wispAlpha[1]);
  }
  obj.setDepth(depth ?? entityDepth(y));
  // 50라운드 조명: 혼불은 은은한 빛
  const light = lightFor(V.wispSheet, def);
  if (light) lightRegistryOf(scene).add(light, { x, y, anchor: obj });
  const tween = scene.tweens.add({
    targets: obj,
    y: y - V.wispBobPx,
    alpha: { from: V.wispAlpha[1], to: V.wispAlpha[0] },
    duration: cycle,
    yoyo: true,
    repeat: -1,
    ease: 'Sine.easeInOut',
    delay: (cycle / Math.max(1, n)) * i,
  });
  return { obj, tween };
}
