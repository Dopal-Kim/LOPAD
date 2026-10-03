/**
 * 49라운드 3: 탄생 전장(첫 노드) 조작 안내 — 단계 머신. Phaser 의존 없음 (EventBus 연결은 tutorialDirector.ts).
 *
 * 단계(data/route.json tutorial.steps)마다 땅의 표식이 하나 있다. 단계가 켜지면 표식이 빛나고(step 이벤트),
 * 표식에 다가가면 안내 문구(prompt — `promptOnStart` 면 켜지자마자), 행동을 count 번 마치면 다음 단계.
 * 행동은 단계가 켜진 동안이면 표식에 닿기 전에 해도 센다(익숙한 사람은 빨리 지나간다).
 * - arrive: 표식에 닿으면 완료
 * - hitDummy: 허수아비 근처를 공격 (근접 = 공격 지점·주인공에서 dummyHitTiles, 원거리 = 조준 원뿔 안 rangedHitTiles)
 * - dash · secondary: 그 동작을 하면
 * - fight: 켜지면 약한 적 전투 요청(fight 이벤트), 전멸 알림(fightCleared)으로 완료
 * 마지막 단계가 끝나면 done (출구 열림은 호스트가).
 */

export type TutorialAction = 'arrive' | 'hitDummy' | 'dash' | 'secondary' | 'fight';

export interface TutorialFightDef {
  /** 전장 중앙 기준 타일 오프셋 */
  at: [number, number];
  radiusTiles: number;
  spawns: { enemy: string; count: number; hpMult: number; attackMult: number }[];
}

export interface TutorialStepDef {
  id: string;
  action: TutorialAction;
  count?: number;
  /** 표식 자리: 전장 중앙 기준 타일 오프셋 */
  sign: [number, number];
  promptOnStart?: boolean;
  /** 49라운드 아트: 표식 시트 이름 조각 (`tutorial_sign_<signName>`, 없으면 id) */
  signName?: string;
  /** 안내 문구 (자리표시). `{name}`·`{description}` = 무기 보조 동작 */
  text: string;
  /** 53라운드: 안내 패널 키 표시 (UI_EVENTS.TUTORIAL_STEP keys, 예 ['W','A','S','D']) */
  keys?: string[];
  fight?: TutorialFightDef;
}

export interface TutorialDef {
  signSprite: string[];
  dummySprite: string[];
  approachTiles: number;
  dummyHitTiles: number;
  rangedHitTiles: number;
  rangedConeDeg: number;
  dummies: [number, number][];
  steps: TutorialStepDef[];
  doneText: string;
}

export type TutorialEvent =
  | { type: 'step'; step: number; sign: number }
  | { type: 'prompt'; step: number; text: string }
  | { type: 'fight'; step: number; fight: TutorialFightDef }
  | { type: 'dummyHit'; index: number }
  | { type: 'done'; text: string };

export interface Pt {
  x: number;
  y: number;
}

export interface AttackInput {
  /** 공격 지점 (px) */
  x: number;
  y: number;
  dirX: number;
  dirY: number;
}

export function fillText(text: string, vars: Record<string, string>): string {
  return text.replace(/\{(\w+)\}/g, (_m, key: string) => vars[key] ?? '');
}

export class TutorialMachine {
  private index = -1;
  private progress = 0;
  private prompted = false;
  private finished = false;

  constructor(
    readonly def: TutorialDef,
    /** 표식 중심 (px), steps 와 같은 순서 */
    private readonly signs: readonly Pt[],
    /** 허수아비 중심 (px) */
    private readonly dummies: readonly Pt[],
    /** 타일 한 칸 (px) */
    private readonly tilePx: number,
    private readonly vars: Record<string, string> = {},
  ) {}

  get started(): boolean {
    return this.index >= 0;
  }

  get done(): boolean {
    return this.finished;
  }

  /** 지금 단계 번호 (시작 전 -1, 끝나면 steps.length) */
  get stepIndex(): number {
    return this.index;
  }

  get step(): TutorialStepDef | null {
    return this.def.steps[this.index] ?? null;
  }

  /** 첫 단계를 켠다 (탄생 연출이 끝난 뒤) */
  start(): TutorialEvent[] {
    if (this.started) return [];
    return this.enter(0);
  }

  /** 매 프레임: 표식 접근 → 문구 · arrive 완료 */
  update(player: Pt): TutorialEvent[] {
    const st = this.step;
    if (!st || this.finished) return [];
    const out: TutorialEvent[] = [];
    const sign = this.signs[this.index];
    const near = sign ? dist(player, sign) <= this.def.approachTiles * this.tilePx : false;
    if (near && !this.prompted) {
      this.prompted = true;
      out.push(this.prompt());
    }
    if (st.action === 'arrive' && near) out.push(...this.complete());
    return out;
  }

  /** 공격 1회 (근접·원거리 공통) */
  attack(a: AttackInput, player: Pt, ranged: boolean): TutorialEvent[] {
    const out: TutorialEvent[] = [];
    let hit = false;
    const melee = this.def.dummyHitTiles * this.tilePx;
    const far = this.def.rangedHitTiles * this.tilePx;
    const cone = Math.cos((this.def.rangedConeDeg * Math.PI) / 180);
    this.dummies.forEach((d, i) => {
      let ok = dist(a, d) <= melee || dist(player, d) <= melee;
      if (!ok && ranged) {
        const vx = d.x - player.x;
        const vy = d.y - player.y;
        const len = Math.hypot(vx, vy);
        const dl = Math.hypot(a.dirX, a.dirY);
        ok = len > 0 && dl > 0 && len <= far && (vx * a.dirX + vy * a.dirY) / (len * dl) >= cone;
      }
      if (ok) {
        hit = true;
        out.push({ type: 'dummyHit', index: i });
      }
    });
    if (hit && this.step?.action === 'hitDummy') out.push(...this.count());
    return out;
  }

  /** 대쉬·보조 동작 */
  action(kind: 'dash' | 'secondary'): TutorialEvent[] {
    if (this.step?.action !== kind) return [];
    return this.count();
  }

  /** 약한 적 전투가 끝남 */
  fightCleared(): TutorialEvent[] {
    if (this.step?.action !== 'fight') return [];
    return this.complete();
  }

  /** 전부 건너뛰기 (디버그·재방문) */
  skip(): TutorialEvent[] {
    if (this.finished) return [];
    this.index = this.def.steps.length;
    this.finished = true;
    return [{ type: 'done', text: this.def.doneText }];
  }

  private prompt(): TutorialEvent {
    return { type: 'prompt', step: this.index, text: fillText(this.step!.text, this.vars) };
  }

  private count(): TutorialEvent[] {
    this.progress += 1;
    if (this.progress >= Math.max(1, this.step?.count ?? 1)) return this.complete();
    return [];
  }

  private complete(): TutorialEvent[] {
    return this.enter(this.index + 1);
  }

  private enter(i: number): TutorialEvent[] {
    this.index = i;
    this.progress = 0;
    this.prompted = false;
    const st = this.step;
    if (!st) {
      this.finished = true;
      return [{ type: 'done', text: this.def.doneText }];
    }
    const out: TutorialEvent[] = [{ type: 'step', step: i, sign: i }];
    if (st.promptOnStart) {
      this.prompted = true;
      out.push(this.prompt());
    }
    if (st.action === 'fight' && st.fight) out.push({ type: 'fight', step: i, fight: st.fight });
    return out;
  }
}

function dist(a: Pt, b: Pt): number {
  return Math.hypot(a.x - b.x, a.y - b.y);
}
