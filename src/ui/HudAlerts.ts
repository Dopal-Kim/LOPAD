import Phaser from 'phaser';
import { UI_SCREEN } from '../contract/ui';
import { AlertPlan, laneDelay, type AlertAction, type AlertKind, type LeavingSlot } from './alertPlan';
import { debugExpose } from './debug';
import { GlowText } from './glow';
import { swatch } from './StructureHud';
import { ALERT_UI as A } from './themeAlerts';
import { hexToNum } from './theme';

type Glow = Parameters<GlowText['setGlowStyle']>[0];

const ALL_KINDS: readonly AlertKind[] = ['boss', 'break', 'enemy', 'warn', 'growth', 'room', 'info'];

export interface AlertTiming {
  inMs: number;
  holdMs: number;
  outMs: number;
  /** 나타날 때 위에서 내려오는 px */
  drop?: number;
}

/** 알림 카드 그림: 화면 x 그대로(가운데 맞춤은 스스로), y 0 = 카드 위 끝. 높이를 함께 돌려준다 */
export type AlertBuild = (scene: Phaser.Scene) => { box: Phaser.GameObjects.Container; h: number };

export interface AlertSpec {
  kind: AlertKind;
  /** 같은 key 가 보이거나 줄에 있으면 합친다 (`merge`) */
  key?: string;
  timing: AlertTiming;
  build: AlertBuild;
  /** 같은 key 가 있을 때: 앞 것과 합친 새 알림 (null = 새 것을 버림). 없으면 새 것으로 바꾼다 */
  merge?: (prev: AlertSpec) => AlertSpec | null;
  /** 이 알림이 오면 접을 종류 (보스 국면 → 파훼) */
  supersedes?: readonly AlertKind[];
  /** 떴을 때 (깜빡임·흔들림 등) */
  onShow?: (box: Phaser.GameObjects.Container) => void;
  ttlMs?: number;
  /** 헤드리스 확인용 이름 */
  label?: string;
}

interface Item {
  id: number;
  spec: AlertSpec;
  holder?: Phaser.GameObjects.Container;
  box?: Phaser.GameObjects.Container;
  h: number;
  targetY: number;
  timer?: Phaser.Time.TimerEvent;
  /** 사라지는 중 (자리 계산에서 뺀다) */
  leaving: boolean;
  /** 들어온 시각 (scene.time.now) */
  pushedAt: number;
  /** 사라지는 중이면 다 사라지는 시각 (같은 레인 교차 페이드 금지 — 62 루프 3 UI H) */
  leaveEndsAt?: number;
}

/**
 * 62라운드 P0-6 위 가운데 알림 줄 하나 (`alertPlan.ts` 규칙을 그린다). HUD 의 위 가운데 카드 — 방 이름 배너, '주의'(+문 닫힘),
 * 처음 보는 적, 보스 이름·국면 카드, 파훼·결정타, 개성·공명 알림, 세트 단계 등 짧은 안내 — 는 모두 여기로 들어온다.
 * 동시에 2장까지 위에서부터 중요도 순으로 쌓고(겹치지 않음), 넘치면 줄 세우기·합치기·낮은 것 생략.
 * 위 끝은 `top()`(튜토리얼 단계 카드·도전 판 아래). 막혀 있으면(전환·탄생 연출) 줄만 선다.
 */
export class HudAlerts {
  private plan = new AlertPlan(A.max);
  private items = new Map<number, Item>();
  private lastTop = -1;

  constructor(
    private scene: Phaser.Scene,
    /** hold = 지금 줄에서만 기다릴 종류 (P19: 전투 중 개성·안내) */
    private deps: { blocked: () => boolean; top: () => number; hold?: () => readonly AlertKind[] },
  ) {}

  /** 그 종류가 보이거나 줄에 있다 */
  busy(kind: AlertKind): boolean {
    return this.plan.has(kind);
  }

  get idle(): boolean {
    return this.plan.idle;
  }

  /** 보이는 알림의 아래 끝 (없으면 top) */
  get bottom(): number {
    let y = this.deps.top();
    for (const e of this.plan.visible) {
      const it = this.items.get(e.id);
      if (it && !it.leaving) y = Math.max(y, it.targetY + it.h);
    }
    return y;
  }

  push(spec: AlertSpec): void {
    if (spec.supersedes?.length) this.foldKinds(spec.supersedes);
    if (spec.key) {
      const prev = this.plan.findKey(spec.key);
      const it = prev ? this.items.get(prev.id) : undefined;
      if (prev && it) {
        const next = spec.merge ? spec.merge(it.spec) : spec;
        if (!next) return;
        it.spec = { ...next, key: spec.key };
        if (it.holder) this.rebuild(it);
        this.expose();
        return;
      }
    }
    const now = this.scene.time.now;
    const r = this.plan.push(spec.kind, now, this.deps.blocked() || this.held().includes(spec.kind), {
      key: spec.key ?? null,
      ttlMs: spec.ttlMs,
    });
    this.items.set(r.id, { id: r.id, spec, h: 0, targetY: 0, leaving: false, pushedAt: now });
    this.apply(r.actions);
  }

  /** 매 STATE: 오래 기다린 것은 버리고 자리가 나면 띄운다. 위 끝이 바뀌면 자리를 옮긴다 */
  tick(): void {
    this.apply(this.plan.tick(this.scene.time.now, this.deps.blocked(), this.held()));
    const top = this.deps.top();
    if (top !== this.lastTop) this.layout();
  }

  /** 종류별로 접는다 (없으면 전부). keep 은 남긴다 */
  clear(keep: readonly AlertKind[] = []): void {
    this.apply(this.plan.clear(keep));
  }

  /**
   * 62 루프 2 (P1-11, 시스템 A 요청): 이 시각 앞에 들어온 알림만 접는다 (노드 진입 — 같은 프레임에 먼저 온 새 방 알림은 남는다).
   * keep 종류는 남긴다
   */
  clearBefore(t: number, keep: readonly AlertKind[] = []): void {
    const actions: AlertAction[] = [];
    for (const it of this.items.values())
      if (it.pushedAt < t && !keep.includes(it.spec.kind)) actions.push(...this.plan.remove(it.id));
    this.apply(actions);
  }

  private held(): readonly AlertKind[] {
    return this.deps.hold?.() ?? [];
  }

  /** 그 종류만 접는다 */
  fold(kind: AlertKind): void {
    this.foldKinds([kind]);
  }

  private foldKinds(kinds: readonly AlertKind[]): void {
    this.apply(this.plan.clear(ALL_KINDS.filter((k) => !kinds.includes(k))));
  }

  destroy(): void {
    for (const it of this.items.values()) this.kill(it);
    this.items.clear();
    this.plan.clear();
  }

  // ---- 실행

  private apply(actions: AlertAction[]): void {
    if (!actions.length) return;
    for (const a of actions) {
      const it = this.items.get(a.id);
      if (!it) continue;
      if (a.type === 'show') this.show(it);
      else if (a.type === 'fold') this.foldItem(it);
      else {
        this.kill(it);
        this.items.delete(it.id);
      }
    }
    this.layout();
    this.expose();
  }

  private show(it: Item): void {
    const sc = this.scene;
    const holder = sc.add.container(0, 0).setDepth(A.depth);
    it.holder = holder;
    // 처음 자리는 지금 차례로 바로 (미끄러지지 않게)
    it.targetY = this.slotY(it.id);
    holder.setY(it.targetY);
    const t = it.spec.timing;
    holder.setAlpha(0);
    // 62 루프 3 UI H (P0-N3): 같은 자리에서 앞 카드가 사라지는 중이면 다 사라진 뒤에 들어온다 (교차 페이드 금지)
    const wait = this.fill(it, (h) => this.laneWait(it, it.targetY, h));
    sc.tweens.add({ targets: holder, alpha: 1, duration: t.inMs, delay: wait });
    this.arm(it, wait + t.inMs + t.holdMs);
  }

  /** 사라지는 중인 다른 카드와 [y, y+h] 가 겹치면 그 카드가 다 사라질 때까지 기다릴 ms */
  private laneWait(self: Item, y: number, h: number): number {
    const leaving: LeavingSlot[] = [];
    for (const o of this.items.values())
      if (o !== self && o.leaving && o.holder && o.leaveEndsAt !== undefined)
        leaving.push({ y: o.holder.y, h: o.h, endsAt: o.leaveEndsAt });
    return laneDelay(y, h, leaving, this.scene.time.now);
  }

  /** 카드 그림을 (다시) 넣는다 (`delayOf(h)` = 들어오기를 기다리는 ms — 돌려준다) */
  private fill(it: Item, delayOf: (h: number) => number = () => 0): number {
    const sc = this.scene;
    const holder = it.holder!;
    if (it.box) {
      sc.tweens.killTweensOf([it.box, ...it.box.list]);
      it.box.destroy();
    }
    const b = it.spec.build(sc);
    it.box = b.box;
    it.h = b.h;
    holder.add(b.box);
    const delay = delayOf(b.h);
    const drop = it.spec.timing.drop ?? 0;
    if (drop) {
      b.box.setY(-drop);
      sc.tweens.add({ targets: b.box, y: 0, duration: it.spec.timing.inMs, ease: 'Quad.easeIn', delay });
    }
    if (delay > 0)
      sc.time.delayedCall(delay, () => {
        if (b.box.active) it.spec.onShow?.(b.box);
      });
    else it.spec.onShow?.(b.box);
    return delay;
  }

  /** 합쳐진 알림: 그림을 바꾸고 머무는 시간을 넉넉히 */
  private rebuild(it: Item): void {
    this.fill(it);
    it.holder!.setAlpha(1);
    this.scene.tweens.killTweensOf(it.holder!);
    const left = it.timer ? Math.max(0, it.timer.getRemaining()) : 0;
    this.arm(it, Math.max(left, A.mergeHoldMs));
    this.layout();
  }

  private arm(it: Item, ms: number): void {
    it.timer?.remove();
    it.timer = this.scene.time.delayedCall(ms, () => this.fadeOut(it, it.spec.timing.outMs, true));
  }

  private fadeOut(it: Item, ms: number, notify: boolean): void {
    const holder = it.holder;
    it.timer?.remove();
    it.timer = undefined;
    it.leaving = true;
    it.leaveEndsAt = this.scene.time.now + ms;
    if (!holder) {
      this.finish(it, notify);
      return;
    }
    this.scene.tweens.killTweensOf(holder);
    this.scene.tweens.add({ targets: holder, alpha: 0, duration: ms, onComplete: () => this.finish(it, notify) });
  }

  private finish(it: Item, notify: boolean): void {
    this.kill(it);
    this.items.delete(it.id);
    if (notify) this.apply(this.plan.gone(it.id, this.scene.time.now, this.deps.blocked(), this.held()));
    else this.layout();
  }

  /** 밀려 접힘 (planner 는 이미 뺐다) */
  private foldItem(it: Item): void {
    if (!it.holder) {
      this.items.delete(it.id);
      return;
    }
    this.fadeOut(it, A.foldMs, false);
  }

  private kill(it: Item): void {
    it.timer?.remove();
    it.timer = undefined;
    if (it.holder) {
      this.scene.tweens.killTweensOf(it.holder);
      if (it.box) this.scene.tweens.killTweensOf([it.box, ...it.box.list]);
      it.holder.destroy();
    }
    it.holder = undefined;
    it.box = undefined;
  }

  /** id 의 차례 y (보이는 것 위에서부터) */
  private slotY(id: number): number {
    let y = this.deps.top();
    for (const e of this.plan.visible) {
      if (e.id === id) return y;
      const it = this.items.get(e.id);
      if (it && it.holder && !it.leaving) y += it.h + A.gap;
    }
    return y;
  }

  private layout(): void {
    this.lastTop = this.deps.top();
    for (const e of this.plan.visible) {
      const it = this.items.get(e.id);
      if (!it?.holder || it.leaving) continue;
      const y = this.slotY(e.id);
      if (y === it.targetY) continue;
      it.targetY = y;
      // 사라지는 카드 자리로 올라갈 때도 다 사라진 뒤에 (겹쳐 지나가지 않게)
      const lo = Math.min(y, it.holder.y);
      const wait = this.laneWait(it, lo, Math.abs(y - it.holder.y) + it.h);
      this.scene.tweens.add({ targets: it.holder, y, duration: A.slideMs, ease: 'Quad.easeOut', delay: wait });
    }
  }

  private expose(): void {
    debugExpose('alerts', {
      visible: this.plan.visible.map((e) => `${e.kind}:${this.items.get(e.id)?.spec.label ?? ''}`),
      queued: this.plan.queued.map((e) => `${e.kind}:${this.items.get(e.id)?.spec.label ?? ''}`),
    });
  }
}

// ---------------------------------------------------------------------------------------------
// 하데스식 깔끔한 배너 조각 (방 이름·주의·짧은 안내 공용)

export interface BannerLine {
  text: string;
  style: Glow;
  scale?: 1 | 2;
  /** 이 줄 아래 틈 */
  gap?: number;
}

/**
 * 가운데 배너: 글 폭에 맞춘 잉크 띠(양 끝 3단으로 흐려짐) + 위·아래 1px 강조선 + 가운데 맞춘 줄들. y 0 = 띠 위 끝.
 * 돌려주는 `lines` 로 깜빡임 등을 건다.
 */
export function bannerCard(
  scene: Phaser.Scene,
  lines: BannerLine[],
  stageIndex: number,
  lineHex?: string,
): { box: Phaser.GameObjects.Container; h: number; texts: GlowText[] } {
  const W = UI_SCREEN.WIDTH;
  const texts = lines.map(
    (l) => new GlowText(scene, 0, 0, l.text, l.style, { scale: l.scale ?? 1, stageIndex, align: 'center' }),
  );
  let y = A.bandPad;
  texts.forEach((t, i) => {
    t.placeCenter(W / 2, y);
    y += t.displayHeight + (i < lines.length - 1 ? (lines[i].gap ?? 2) : 0);
  });
  const h = y + A.bandPad;
  const textW = Math.max(0, ...texts.map((t) => t.displayWidth));
  const bw = Math.min(A.bandMaxW, Math.max(A.bandMinW, textW + A.bandFade * 2 + 24));
  const g = scene.add.graphics();
  bandRect(scene, g, Math.round(W / 2 - bw / 2), 0, bw, h, stageIndex, lineHex);
  const box = scene.add.container(0, 0, [g, ...texts]);
  return { box, h, texts };
}

/** 잉크 띠: 가운데는 진하게, 양 끝 `bandFade` 는 3단으로 옅게 + 위·아래 강조 1px (가운데만 — lineHex 면 그 색, P19 예고 색) */
export function bandRect(
  scene: Phaser.Scene,
  g: Phaser.GameObjects.Graphics,
  x: number,
  y: number,
  w: number,
  h: number,
  stageIndex: number,
  lineHex?: string,
): void {
  const ink = swatch(scene, stageIndex, { gray: 0 });
  const f = Math.min(A.bandFade, Math.floor(w / 4));
  const step = Math.max(1, Math.floor(f / 3));
  const mid = w - step * 6;
  g.fillStyle(ink, A.bandAlpha).fillRect(x + step * 3, y, mid, h);
  for (let k = 0; k < 3; k++) {
    const a = (A.bandAlpha * (k + 1)) / 4;
    g.fillStyle(ink, a).fillRect(x + k * step, y, step, h);
    g.fillStyle(ink, a).fillRect(x + w - (k + 1) * step, y, step, h);
  }
  const line = lineHex ? hexToNum(lineHex) : swatch(scene, stageIndex, { slot: 20 });
  g.fillStyle(line, 1)
    .fillRect(x + step * 3, y, mid, 1)
    .fillRect(x + step * 3, y + h - 1, mid, 1);
}
