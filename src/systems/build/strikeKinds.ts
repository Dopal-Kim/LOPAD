/**
 * 57라운드 공통 사건 분류 (설계안 0.4, Phaser 의존 없음): 강공(중량 태그) · 원거리 판정(원격 태그).
 * 강공: 칼 일섬·대치 일격·1단 홀드 동작 / 대검 차지 내려찍기·균열·공중제비 찍기 / 단검 등 뒤 치명 찌르기·낙인 기폭 /
 * 활 가득 당긴 화살(가득·완벽·버팀)·화살비. 연격 막타(데이터 heavy)는 강공이 아니다 — '강공'은 새 동작·차지 계열.
 */
import type { PlayerAttackPayload } from '../../core/EventBus';

/** 강공으로 치는 새 동작 id (공격 수단 표 · 갈래 수단) */
export const STRONG_MOVES: readonly string[] = ['iai_draw', 'leap_slam', 'backstab', 'spin', 'unblockable', 'issen'];

export type StrikeLike = Pick<PlayerAttackPayload, 'issen' | 'move' | 'charge' | 'crackLine' | 'bowPower' | 'slam'> & {
  /** 빌드 축이 붙인 동작 이름 (갈래 수단 · 낙인 기폭 · 화살비) */
  buildMove?: string;
};

export function isStrongAttack(p: StrikeLike): boolean {
  if (p.issen || p.crackLine || p.slam) return true;
  if (p.charge !== undefined && p.charge > 0) return true;
  if (p.move && STRONG_MOVES.includes(p.move)) return true;
  if (
    p.buildMove &&
    (STRONG_MOVES.includes(p.buildMove) || p.buildMove === 'brandBurst' || p.buildMove === 'arrowRain')
  )
    return true;
  return p.bowPower === 'full' || p.bowPower === 'perfect' || p.bowPower === 'strained';
}
