/**
 * 집단 돌격 (35라운드 2단계, 징집병): 같은 방의 같은 적이 `minCount` 이상이고 누군가 플레이어 `rangeTiles` 안에 들어오면
 * 전원이 동시에 `speedMult` 배로 `durationMs` 동안 달려들고, 그 뒤 `cooldownMs` 동안은 다시 발동하지 않는다.
 * 방(씬) 단위 공유 상태라 적 개체가 아니라 여기서 관리한다. Phaser 의존 없음.
 */
import type { PackParams } from '../data/types';

interface PackState {
  until: number;
  nextAt: number;
}

export class PackCharge {
  private readonly packs = new Map<string, PackState>();

  /**
   * 적 하나가 매 프레임 보고한다: 같은 종 수·플레이어 거리(칸). 조건이 맞고 쿨타임이 지났으면 발동.
   * 반환: 지금 돌격 중이면 true (방금 발동 포함)
   */
  report(id: string, P: PackParams, allies: number, distTiles: number, time: number): boolean {
    const st = this.packs.get(id) ?? { until: 0, nextAt: 0 };
    if (!this.packs.has(id)) this.packs.set(id, st);
    if (time < st.until) return true;
    if (allies >= P.minCount && distTiles <= P.rangeTiles && time >= st.nextAt) {
      st.until = time + P.durationMs;
      st.nextAt = st.until + P.cooldownMs;
      return true;
    }
    return false;
  }

  /** 방금 발동한 것인지 (이벤트 1회 발행용): 발동 시각이 time 과 같으면 true */
  isActive(id: string, time: number): boolean {
    const st = this.packs.get(id);
    return Boolean(st && time < st.until);
  }

  /** 돌격 시작 시각 (없으면 -Infinity) */
  startedAt(id: string, P: PackParams): number {
    const st = this.packs.get(id);
    return st ? st.until - P.durationMs : -Infinity;
  }

  reset(): void {
    this.packs.clear();
  }
}
