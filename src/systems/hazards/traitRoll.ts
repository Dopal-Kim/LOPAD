/**
 * 62 루프 4 개성 '술통 굴리기'(대검 g_mem_caskRoll): 넷째 타에 맞은 술통(구조물 cask · 술통 짐꾼 술통)이 적을 꿰뚫고 굴러가며 술 자국을
 * 남기고, 불에 닿으면 터진다. 굴리는 몸(구조물 굴림·EnemyHazards 술통)은 저마다 움직이고, 맞힘·자국·거리·불 판정은 이 한 곳에서 한다.
 * Phaser 의존 없음 — 효과(피해·웅덩이·폭발)는 개성 쪽 콜백.
 */
import type { HazardPt } from './enemyHazardTypes';

export interface TraitRollSpec {
  /** 구르는 속도 · 최대 거리 · 술 자국 간격 (px) */
  speedPx: number;
  maxPx: number;
  trailEveryPx: number;
  /** 처음 닿은 적 한 번씩 */
  hit(target: unknown, dir: HazardPt): void;
  /** 술 자국 한 칸 (구르는 자리) */
  trail(x: number, y: number): void;
  /** 불에 닿아 터짐 */
  burst(x: number, y: number): void;
}

export type TraitRollStep = 'roll' | 'burst' | 'end';

export class TraitRoll {
  private readonly hitSet = new Set<unknown>();
  private sinceTrail = 0;
  traveled = 0;

  constructor(readonly spec: TraitRollSpec) {}

  /** 한 걸음 뒤: 불이면 터짐 · 닿은 적 맞힘 · 자국 · 다 굴렀으면 end (벽은 굴리는 쪽이 따로 깨뜨린다) */
  step(
    x: number,
    y: number,
    moved: number,
    dir: HazardPt,
    touching: readonly unknown[],
    onFire: boolean,
  ): TraitRollStep {
    if (onFire) {
      this.spec.burst(x, y);
      return 'burst';
    }
    for (const m of touching)
      if (!this.hitSet.has(m)) {
        this.hitSet.add(m);
        this.spec.hit(m, dir);
      }
    this.traveled += moved;
    this.sinceTrail += moved;
    if (this.sinceTrail >= this.spec.trailEveryPx) {
      this.sinceTrail = 0;
      this.spec.trail(x, y);
    }
    return this.traveled >= this.spec.maxPx ? 'end' : 'roll';
  }
}

/** 굴리기 시작 (술통마다 하나 — 맞힌 적 기록이 따로). at = 술통 자리 */
export type TraitRollFactory = (at: HazardPt) => TraitRoll;
