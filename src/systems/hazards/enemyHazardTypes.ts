/**
 * 61라운드 단계 2: 일반 적이 남기는 위험물 창구 (MobContext.hazards — 씬의 EnemyHazards 가 구현). 형식만 두어 순환 import 를 피한다.
 */
import type { LiquorPoolParams, RollParams, ThrowParams } from '../../data/enemyTypes';

/** 화염 술병 한 병에 쓰는 수치 (행상 ThrowParams 의 일부 — 61 P13 보스 포물선 술병도 같은 병) */
export type BottleParams = Pick<
  ThrowParams,
  'flightMs' | 'arcTiles' | 'burstRadiusTiles' | 'burstAttack' | 'poolMs' | 'poolTickMs' | 'poolAttack'
>;

export interface HazardPt {
  x: number;
  y: number;
}

export interface EnemyHazardApi {
  /**
   * 독주 행상 화염 술병: from = 손 아래 땅 자리, handPx = 손 높이(월드), to = 떨어질 자리. 비행 flightMs → 폭발 → 불 웅덩이.
   * attackScale = 층 적 공격 배율. 61 P13: 보스 포물선 술병도 이 길 (attackScale 1)
   */
  throwBottle(from: HazardPt, handPx: number, to: HazardPt, p: BottleParams, attackScale: number): void;
  /** 술통 짐꾼 술통 굴림: from = 술통 바닥 접점, dir = 굴러갈 방향(단위) */
  rollBarrel(
    from: HazardPt,
    dirX: number,
    dirY: number,
    p: RollParams,
    liquor: LiquorPoolParams,
    attackScale: number,
  ): void;
  /** 술 웅덩이 (깨진 술통·쓰러진 적): 반경 px · 지속 ms */
  liquorPool(x: number, y: number, radiusPx: number, ms: number, liquor: LiquorPoolParams, attackScale: number): void;
}
