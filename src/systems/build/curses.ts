/**
 * 57라운드 Q36·Q37 대가형 저주 (설계안 4.1·4.2): 지속 = 노드 수(보스 노드도 1노드), 동시 1개, 층을 넘어도 남은 노드 유지,
 * 정화 없음. 저주 궤짝만 처치 수 기준. '피의 계약'(개성 칸)은 이득 ×pactBenefitMult · 지속 +pactExtraNodes. Phaser 의존 없음.
 *
 * 노드 세기: 받은 노드(그 자리)는 세지 않고, 다음 노드부터 n개가 영향 노드다 — 받은 뒤 처음 들어간 노드에서 '무장'만 하고,
 * 그다음 노드 진입마다 1씩 줄어 0이 되면 끝 (2노드 = 다음 노드 두 개 동안). nodeFilter 'combat' 이면 전투 노드만 센다.
 */
import type { CurseDef } from '../../data/buildTypes';

export interface CurseSave {
  id: string;
  nodesLeft: number | null;
  killsLeft: number | null;
  armed: boolean;
  pact: boolean;
  /** 받은 순간 줄인 최대 HP (끝나면 되돌림) */
  maxHpTaken: number;
}

export class CurseState {
  nodesLeft: number | null;
  killsLeft: number | null;
  armed = false;
  maxHpTaken = 0;

  constructor(
    readonly def: CurseDef,
    readonly pact = false,
    pactExtraNodes = 0,
  ) {
    this.nodesLeft = def.nodes !== undefined ? def.nodes + (pact ? pactExtraNodes : 0) : null;
    this.killsLeft = def.kills !== undefined ? def.kills : null;
  }

  get id(): string {
    return this.def.id;
  }

  /** 노드 진입. combat = 전투가 있는 노드. 저주가 끝났으면 true */
  onNodeEntered(combat: boolean): boolean {
    if (this.nodesLeft === null) return false;
    if (this.def.nodeFilter === 'combat' && !combat) return false;
    if (!this.armed) {
      this.armed = true;
      return false;
    }
    this.nodesLeft -= 1;
    return this.nodesLeft <= 0;
  }

  /** 처치 1회 (처치 수 기준 저주만). 끝났으면 true */
  onKill(): boolean {
    if (this.killsLeft === null) return false;
    this.killsLeft -= 1;
    return this.killsLeft <= 0;
  }

  toSave(): CurseSave {
    return {
      id: this.def.id,
      nodesLeft: this.nodesLeft,
      killsLeft: this.killsLeft,
      armed: this.armed,
      pact: this.pact,
      maxHpTaken: this.maxHpTaken,
    };
  }

  static restore(def: CurseDef, s: CurseSave): CurseState {
    const c = new CurseState(def, Boolean(s.pact));
    c.nodesLeft = typeof s.nodesLeft === 'number' ? s.nodesLeft : c.nodesLeft;
    c.killsLeft = typeof s.killsLeft === 'number' ? s.killsLeft : c.killsLeft;
    c.armed = Boolean(s.armed);
    c.maxHpTaken = Math.max(0, Number(s.maxHpTaken) || 0);
    return c;
  }
}

/** 피의 계약: 이득 수치 배율 (정수 이득은 반올림) */
export function scaledBenefit(v: number, pact: boolean, mult: number): number {
  return pact ? v * mult : v;
}

/** 계약 칸에서 저주 하나 (pactPool 에서 무작위, 지금 저주와 같은 것 제외) */
export function pickPactCurse(pool: readonly string[], roll: number): string | null {
  if (pool.length === 0) return null;
  return pool[Math.min(pool.length - 1, Math.floor(roll * pool.length))];
}
