/**
 * 55라운드 Q22 대검 홀드 차지 (계약 §17): 좌클릭을 holdMs 넘게 누르고 있으면 차지 → 단계(0.4/0.8/1.2초 — 데이터 stages.atMs)
 * → 떼면 그 단계의 차지 내려찍기. holdMs 전에 떼면 일반 연격(tap). 단계에 닿기 전에 떼도 일반 연격(stage 0 — tap 과 같게).
 * 차지 시계는 누른 때와 행동 가능해진 때(직전 타 다음 타 허용) 중 늦은 쪽부터. Phaser 의존 없음.
 */
import type { ComboChargeDef } from '../../data/types';

export type ChargePhase = 'idle' | 'pending' | 'charging';

export type ChargeEvent =
  /** 짧게 눌렀다 뗌 (또는 단계 전에 뗌) → 일반 연격 */
  | { kind: 'tap' }
  /** 차지 시작 (holdMs 넘김) */
  | { kind: 'start' }
  /** 단계 도달 (1부터) */
  | { kind: 'stage'; stage: number }
  /** 떼서 차지 내려찍기 (stage ≥ 1) */
  | { kind: 'release'; stage: number };

export class ChargeHold {
  private phase_: ChargePhase = 'idle';
  private pressAt = -Infinity;
  private readySince: number | null = null;
  private origin = 0;
  private stage_ = 0;

  constructor(private readonly def: ComboChargeDef) {}

  get phase(): ChargePhase {
    return this.phase_;
  }

  /** 지금 단계 (차지 중이 아니면 0) */
  get stage(): number {
    return this.phase_ === 'charging' ? this.stage_ : 0;
  }

  /** 차지 중 (이동 감속·자세 유지) */
  get charging(): boolean {
    return this.phase_ === 'charging';
  }

  /** 누름이 차지가 될지 아직 모르는 동안은 일반 연격을 미룬다 */
  get pending(): boolean {
    return this.phase_ === 'pending';
  }

  /** 차지 시작부터 경과 ms (차지 시계 = 누른 때·행동 가능해진 때 중 늦은 쪽) */
  elapsed(now: number): number {
    return this.phase_ === 'charging' ? now - this.origin : 0;
  }

  /** 좌클릭 누름 (차지 후보) */
  press(now: number): void {
    this.phase_ = 'pending';
    this.pressAt = now;
    this.readySince = null;
    this.stage_ = 0;
  }

  /** 차지·후보를 버린다 (대쉬·가드·피격·무기 교체) */
  cancel(): boolean {
    const was = this.phase_ !== 'idle';
    this.phase_ = 'idle';
    this.readySince = null;
    this.stage_ = 0;
    return was;
  }

  /** 단계 수 */
  get stageCount(): number {
    return this.def.stages.length;
  }

  /** 경과 ms → 단계 (0 = 아직, 1..n) */
  stageAt(elapsedMs: number): number {
    let s = 0;
    for (const st of this.def.stages) if (elapsedMs >= st.atMs) s += 1;
    return s;
  }

  /**
   * 매 프레임. held = 좌클릭을 누르고 있음, ready = 지금 차지를 시작할 수 있음(행동 가능·다음 타 허용·강한 타 가능)
   */
  update(now: number, held: boolean, ready: boolean): ChargeEvent[] {
    const out: ChargeEvent[] = [];
    if (this.phase_ === 'pending') {
      if (!held) {
        this.phase_ = 'idle';
        out.push({ kind: 'tap' });
        return out;
      }
      if (!ready) {
        this.readySince = null;
        return out;
      }
      if (this.readySince === null) this.readySince = now;
      const from = Math.max(this.pressAt, this.readySince);
      if (now - from < this.def.holdMs) return out;
      this.phase_ = 'charging';
      this.origin = from;
      this.stage_ = 0;
      out.push({ kind: 'start' });
    }
    if (this.phase_ === 'charging') {
      const s = this.stageAt(now - this.origin);
      while (this.stage_ < s) {
        this.stage_ += 1;
        out.push({ kind: 'stage', stage: this.stage_ });
      }
      if (!held) {
        const stage = this.stage_;
        this.phase_ = 'idle';
        this.stage_ = 0;
        out.push(stage > 0 ? { kind: 'release', stage } : { kind: 'tap' });
      }
    }
    return out;
  }
}
