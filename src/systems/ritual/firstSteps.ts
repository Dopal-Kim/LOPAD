/**
 * 62 P1-10 첫 생 첫 걸음 (Phaser 의존 없음): 첫 생의 첫 노드들 동안만 화면 아래 작은 4동사 키 막대(`UiSnapshot.keyBar`).
 * 두 번째 생부터는 막대도 '싸우는 법' 패널도 없다 — 조작 전체 표는 일시정지 메뉴에만.
 * 이번 생이 첫 생인지 = 시작 의식이 운명을 정할 때 넘긴 지난 생 수(begin). 이어하기(새로 고침)로 모르면 일기장에서 한 번 읽는다.
 */
import { diaryNow, inFirstLife } from '../narrative/diary';

let livesBefore: number | null = null;

export const firstSteps = {
  /** 시작 의식: 운명이 정해짐 (지난 생 수 — 0 이면 첫 생) */
  begin(lives: number): void {
    livesBefore = lives;
  },
  /** 이번 생이 첫 생인가 */
  firstLife(): boolean {
    if (livesBefore === null) livesBefore = inFirstLife(diaryNow()) ? 0 : 1;
    return livesBefore === 0;
  },
  /** 키 막대: 첫 생 · 노드 단 col 이 nodes 보다 앞 (시험장·수련장은 호출 쪽이 뺀다) */
  keyBar(col: number | null | undefined, nodes: number): boolean {
    return col !== null && col !== undefined && col < nodes && this.firstLife();
  },
  /** 테스트용 */
  reset(): void {
    livesBefore = null;
  },
};
