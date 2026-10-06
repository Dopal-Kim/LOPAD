/**
 * 61 단계 5 (P13 §3) 기둥 숨기 방지 — 방 쪽 상태: 주인공이 보스 기준으로 서 있는 기둥에 가려진 누적 시간(포물선 술병 방아쇠 —
 * 보스 패턴 `lobBottle` 이 `BossArenaApi.hiddenMs` 로 본다) · 보스 우회 조향 웨이포인트(`steer`). 기하는 `pillarGeom`.
 */
import { BOSS_ART } from '../../core/Constants';
import type { Vec } from '../../objects/boss/types';
import type { PillarSet } from './pillars';
import { lineBlocked, newSteerMemo, steerWaypoint, stepHidden } from './pillarGeom';

export class PillarCover {
  /** 가려진 누적 ms (보이면 DECAY 배로 줄어듦) · 지금 가려졌나 */
  hiddenMs = 0;
  hidden = false;
  private readonly memo = newSteerMemo();
  /** 디버그: 우회 웨이포인트를 쓴 프레임 수 · 마지막 웨이포인트 */
  steered = 0;
  lastWaypoint: Vec | null = null;

  constructor(private readonly pillars: PillarSet) {}

  /** 매 프레임: boss = 보스 바디 중심 (없거나 잠든 동안 null — 누적하지 않고 줄인다) */
  update(boss: Vec | null, player: Vec, deltaMs: number): void {
    const C = BOSS_ART.COVER;
    this.hidden = boss !== null && lineBlocked(boss, player, this.pillars.standing(C.PAD_PX));
    this.hiddenMs = stepHidden(this.hiddenMs, this.hidden, deltaMs, C.DECAY);
  }

  /** 포물선 술병을 던졌다 — 누적을 비운다 (다음 술병은 다시 가려진 만큼) */
  reset(): void {
    this.hiddenMs = 0;
  }

  /**
   * 보스 바디 중심 from 에서 to 로 갈 다음 점 — 서 있는 기둥을 바디 반폭(hw, hh)만큼 부풀려 막히면 모서리로 돈다
   */
  steer(from: Vec, to: Vec, hw: number, hh: number): Vec {
    const S = BOSS_ART.STEER;
    const boxes = this.pillars.standing(hw + S.BODY_PAD_PX, hh + S.BODY_PAD_PX);
    const wp = steerWaypoint(from, to, boxes, this.memo, {
      marginPx: S.MARGIN_PX,
      stickPx: S.STICK_PX,
      reachPx: S.REACH_PX,
    });
    if (wp !== to) {
      this.steered++;
      this.lastWaypoint = { x: Math.round(wp.x), y: Math.round(wp.y) };
    } else this.lastWaypoint = null;
    return wp;
  }

  summary(): Record<string, unknown> {
    return {
      hidden: this.hidden,
      hiddenMs: Math.round(this.hiddenMs),
      steered: this.steered,
      waypoint: this.lastWaypoint,
    };
  }
}
