/**
 * 61라운드 단계 2 (P3): 새 적 소개 — 이번 런에 처음 나온 적 종류마다 짧은 자막 한 번 (data/enemies.json `intro`).
 * 런 시드가 바뀌면(새 런) 처음부터. Phaser 없음.
 */
export class EnemyIntro {
  private runKey: string | null = null;
  private readonly seen = new Set<string>();

  /** 이번 웨이브 적 id 중 이 런에서 처음 보는 것 (순서 유지, 중복 제거) — 부르면 본 것으로 친다 */
  newcomers(runKey: string, ids: readonly string[]): string[] {
    if (runKey !== this.runKey) {
      this.runKey = runKey;
      this.seen.clear();
    }
    const out: string[] = [];
    for (const id of ids) {
      if (this.seen.has(id)) continue;
      this.seen.add(id);
      out.push(id);
    }
    return out;
  }
}

/** 런 하나에 하나 (모듈 단위 — 노드마다 씬이 다시 만들어져도 이어진다) */
export const enemyIntro = new EnemyIntro();
