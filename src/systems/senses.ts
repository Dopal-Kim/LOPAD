/**
 * 감각 수치 (기획서 4장): 스테이지마다 "적을 잡는 방식"을 새로 할 때마다 +1.
 * 방식 분류는 임시(11라운드 확인 필요): attack(무기) · dashAttack(대쉬 공격) · parry(패링 경직/반사 처치).
 */
export type KillKind = 'attack' | 'dashAttack' | 'parry';

export class SenseTracker {
  private kindsThisStage = new Set<KillKind>();
  sense = 0;

  /** 처치를 기록하고, 이 스테이지에서 처음 쓴 방식이면 감각 +1 하고 true */
  recordKill(kind: KillKind): boolean {
    if (this.kindsThisStage.has(kind)) return false;
    this.kindsThisStage.add(kind);
    this.sense += 1;
    return true;
  }

  /** 스테이지가 바뀌면 방식 기록을 비운다 (감각 수치는 유지) */
  nextStage(): void {
    this.kindsThisStage.clear();
  }

  reset(): void {
    this.kindsThisStage.clear();
    this.sense = 0;
  }
}
