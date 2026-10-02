/**
 * 49라운드 7·3: 세트 배치 그림 — 소품(structures/set_<region>_<name>·battlefield_*), 엄폐 담 위 술통 더미,
 * 튜토리얼 표식·허수아비, 혼불(fx/soul_wisp). 시트가 로드돼 있으면 시트(StructureView 재사용), 없으면 옅은 플레이스홀더 도형.
 * 충돌은 없다(엄폐는 이미 벽 타일). 씬 shutdown 에서 `destroy()`.
 */
import Phaser from 'phaser';
import { STRUCTURE_FX, TILE, entityDepth } from '../core/Constants';
import { ROUTE, type SetPieceViewDef } from '../systems/route';
import { spriteLibrary } from '../systems/sprites';
import { FX_ACTION, STRUCTURE_ACTION } from '../systems/spriteDefs';
import type { DecorPlacement, SetPiecePlan } from '../systems/structures/setpiece';
import { StructureView } from './StructureView';

type Shape = Phaser.GameObjects.Rectangle | Phaser.GameObjects.Arc | Phaser.GameObjects.Sprite;

interface DecorItem {
  d: DecorPlacement;
  view: StructureView | null;
  shape: Phaser.GameObjects.Rectangle | null;
}

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
      return { d, view, shape: null };
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
    return { d, view: null, shape };
  }

  private makeWisp(x: number, y: number, i: number, n: number): void {
    const V = this.V;
    const t = n > 1 ? i / (n - 1) : 0;
    const cycle = V.wispCycleMs[0] + (V.wispCycleMs[1] - V.wispCycleMs[0]) * t;
    const texture = spriteLibrary.textureKey(V.wispSheet, FX_ACTION);
    const anim = spriteLibrary.animKey(V.wispSheet, FX_ACTION, 'down');
    let obj: Shape;
    if (texture && anim) {
      const s = this.scene.add.sprite(x, y, texture, 0);
      s.play({ key: anim, repeat: -1, startFrame: i });
      obj = s;
    } else {
      obj = this.scene.add.circle(x, y, V.wispRadiusPx, hex(V.wispColor), V.wispAlpha[1]);
    }
    obj.setDepth(entityDepth(y));
    this.wisps.push(obj);
    this.tweens.push(
      this.scene.tweens.add({
        targets: obj,
        y: y - V.wispBobPx,
        alpha: { from: V.wispAlpha[1], to: V.wispAlpha[0] },
        duration: cycle,
        yoyo: true,
        repeat: -1,
        ease: 'Sine.easeInOut',
        delay: (cycle / Math.max(1, n)) * i,
      }),
    );
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

  /** 허수아비 흔들림 (맞음) */
  pokeDummy(index: number): void {
    const s = this.dummies[index];
    if (!s) return;
    if (s.view?.hasState('hit')) s.view.setState('hit');
    const target = s.view?.sprite ?? s.shape;
    if (!target) return;
    this.scene.tweens.add({
      targets: target,
      angle: { from: -this.V.dummyPokeDeg, to: 0 },
      duration: this.V.dummyPokeMs,
      ease: 'Sine.easeOut',
    });
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
